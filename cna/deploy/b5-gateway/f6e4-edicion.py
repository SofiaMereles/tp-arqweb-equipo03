"""Observación F6-E4 y CA-3: lectura por gateway, sin publicar eventos de prueba."""
import asyncio
import http.client
import json
import re
import socket
import ssl
import sys
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode
import nats
from search_svc.config import Settings
from search_svc.bookstack import Reader
from search_svc.documents import clock
from search_svc.store import Store


def latency_upper_bound(updated_at, gateway_date):
    # Date del gateway y updated_at de BookStack usan ambos el reloj de VM-1.
    # Date solo tiene resolución de segundos: sumar uno produce una cota
    # conservadora, sin asumir sincronización entre VM-1 y VM-2.
    updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
    if updated.tzinfo is None:
        raise ValueError('updated_at no declara zona horaria; no se puede afirmar CA-3')
    observed_limit = parsedate_to_datetime(gateway_date) + timedelta(seconds=1)
    return (observed_limit-updated).total_seconds()


class Gateway:
    def __init__(self, settings):
        self.settings = settings
        self.context=ssl.create_default_context(cafile=str(settings.bookstack_ca))
        self.context.minimum_version=ssl.TLSVersion.TLSv1_3
        self.context.maximum_version=ssl.TLSVersion.TLSv1_3

    def search(self, term):
        context=self.context
        class Connection(http.client.HTTPSConnection):
            def connect(self):
                raw=socket.create_connection(('192.168.145.129',443),timeout=self.timeout)
                self.sock=context.wrap_socket(raw,server_hostname='api.bookstack.local')
        conn=Connection('api.bookstack.local',timeout=6,context=context)
        try:
            conn.request('GET','/v2/search?'+urlencode({'q':term,'entity_type':'page'}),
                         headers={'X-API-Key':self.settings.api_key})
            response=conn.getresponse()
            payload=json.loads(response.read())
            if response.status != 200:
                raise RuntimeError('Gateway HTTP '+str(response.status))
            return payload,{key.lower():value for key,value in response.headers.items()}
        finally:
            conn.close()


async def main(page_id):
    settings=Settings()
    if settings.reconcile_seconds < 300:
        raise RuntimeError('Preparar primero la ventana de prueba: RECONCILE_SECONDS=3600 en VM-1.')
    reader=Reader(settings)
    store=Store(settings,reader)
    gateway=Gateway(settings)
    deadline=time.monotonic()+30
    while True:
        try:
            store.ping()
            baseline,headers=await asyncio.to_thread(gateway.search,'alfa')
            break
        except Exception:
            if time.monotonic()>deadline:
                raise
            await asyncio.sleep(1)
    if not any(row['entity_id']==page_id for row in baseline['items']):
        raise RuntimeError('La pagina ya no contiene alfa. Preparar el estado inicial antes de medir.')
    page_before=await asyncio.to_thread(reader.detail,'page',page_id,'F6-E4-before')
    nc=await nats.connect(settings.nats_url,token=settings.nats_token,connect_timeout=5,max_reconnect_attempts=1)
    try:
        js=nc.jetstream(timeout=3)
        baseline_seq=(await js.stream_info('BOOKSTACK_PAGES')).state.last_seq
        with store.connect() as conn:
            reconciliation_before=conn.execute('SELECT reconciled_at FROM search_state WHERE id=1').fetchone()['reconciled_at']
        print('F6-E4 / P36 y CA-3. Estado inicial: alfa encontrado por gateway.',flush=True)
        print('AHORA, en el navegador: editar la pagina de prueba, cambiar alfa por beta y guardar.',flush=True)
        print('Esta terminal observa por hasta 180 segundos; no publica eventos ni modifica paginas.',flush=True)
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            result,headers=await asyncio.to_thread(gateway.search,'beta')
            found=next((row for row in result['items'] if row['entity_id']==page_id),None)
            if found:
                break
            await asyncio.sleep(0.5)
        else:
            raise RuntimeError('No se observo beta en 180 s; revisar entrega del Webhook, sin aprobar F6-E4.')
        page_after=await asyncio.to_thread(reader.detail,'page',page_id,'F6-E4-after')
        assert clock(page_after['updated_at'])>clock(page_before['updated_at']), 'No se confirma una edicion nueva'
        old,_=await asyncio.to_thread(gateway.search,'alfa')
        assert not any(row['entity_id']==page_id for row in old['items']), 'La pagina sigue coincidiendo con alfa'
        # El ultimo evento page.updated debe ser nuevo y corresponder a la pagina
        # controlada. No se confunde el contenido del indice con recepcion de evento.
        message=await js.get_last_msg('BOOKSTACK_PAGES',subject='bookstack.page.updated')
        event=json.loads(message.data)
        assert message.seq>baseline_seq and event['payload']['page_id']==page_id, 'Falta evento nuevo para esta pagina'
        with store.connect() as conn:
            applied=conn.execute('SELECT applied_at FROM search_events WHERE event_id=%s',(event['event_id'],)).fetchone()
            reconciliation_after=conn.execute('SELECT reconciled_at FROM search_state WHERE id=1').fetchone()['reconciled_at']
        assert applied, 'El consumidor de S1 no confirmo este evento en su base'
        assert reconciliation_before==reconciliation_after, 'Hubo reconciliacion REST durante el ensayo; no atribuir cambio solo a evento'
        date=headers.get('Date') or headers.get('date')
        request_id=headers.get('X-Request-ID') or headers.get('x-request-id')
        assert date and re.fullmatch('[a-f0-9]{32}',request_id or ''), 'Faltan cabeceras del gateway'
        upper=latency_upper_bound(page_after['updated_at'],date)
        print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
        print('alfa: la pagina ya no aparece; beta: pagina encontrada.',flush=True)
        print('Evento real recibido de JetStream:',json.dumps(event,ensure_ascii=False),flush=True)
        print('Evento persistido por S1:',event['event_id'],flush=True)
        print('Request ID de la consulta gateway:',request_id,flush=True)
        print('updated_at del monolito:',page_after['updated_at'],'; Date del gateway:',date,flush=True)
        print('Cota conservadora edicion -> respuesta gateway:',round(upper,3),'segundos.',flush=True)
        assert 0<=upper<5, 'CA-3 no aprobado: la cota no esta entre 0 y menos de 5 s; revisar tiempos antes de concluir'
        print('PASS F6-E4: cambio real alfa -> beta visible via gateway, con evento procesado por S1.',flush=True)
        print('PASS CA-3: cota conservadora menor de 5 s; no hubo reconciliacion REST durante la prueba.',flush=True)
    finally:
        await nc.close()


if __name__=='__main__':
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv)>1 else 3))
