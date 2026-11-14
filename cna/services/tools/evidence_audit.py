"""Prueba F6-E5 contra PostgreSQL y JetStream reales. Ejecutar dentro de audit-svc."""
import asyncio
import json
import time
import urllib.request
from datetime import datetime, timezone
from uuid import uuid4
import nats
from audit_svc.config import Settings


def get(path, settings):
    request = urllib.request.Request('http://127.0.0.1:8000' + path,
                                    headers={'X-API-Key': settings.api_key, 'X-Request-ID': 'F6-E5-evidence'})
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read())


async def main():
    settings = Settings()
    get('/readyz', settings)
    event_id, entity_id = str(uuid4()), int(uuid4().int % 1000000000) + 1000000000
    event = dict(event_id=event_id, type='bookstack.page.updated', version='1.0',
                 occurred_at=datetime.now(timezone.utc).isoformat(), request_id='F6-E5-' + uuid4().hex,
                 payload={'page_id': entity_id, 'actor': {'id': None, 'name': 'Prueba controlada F6-E5'}})
    nc = await nats.connect(settings.nats_url, token=settings.nats_token)
    try:
        js = nc.jetstream()
        # No se usa Nats-Msg-Id: deben existir DOS mensajes en el broker, no una deduplicación de transporte.
        a = await js.publish(event['type'], json.dumps(event).encode())
        b = await js.publish(event['type'], json.dumps(event).encode())
        assert b.seq != a.seq, 'JetStream no guardó dos mensajes distintos'
        query = f'/v2/audit?entity=page&id={entity_id}'
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            result = await asyncio.to_thread(get, query, settings)
            consumer = await js.consumer_info('BOOKSTACK_PAGES', 'audit-svc-pages-v1')
            if result['total'] == 1 and consumer.ack_floor.stream_seq >= b.seq:
                break
            await asyncio.sleep(0.5)
        else:
            raise RuntimeError('No se procesaron ambas entregas dentro de 30 segundos')
        assert result['items'][0]['event_id'] == event_id
        print(datetime.now(timezone.utc).isoformat())
        print('F6-E5 / P37 - audit-svc')
        print('Evento de prueba controlado; no es una edición real del monolito.')
        print(f'event_id: {event_id}')
        print(f'JetStream: dos publicaciones confirmadas, secuencias {a.seq} y {b.seq}')
        print('Ambos mensajes procesados por el consumidor durable.')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print('PASS: mismo event_id publicado dos veces -> un solo registro en PostgreSQL.')
    finally:
        await nc.close()


if __name__ == '__main__':
    asyncio.run(main())
