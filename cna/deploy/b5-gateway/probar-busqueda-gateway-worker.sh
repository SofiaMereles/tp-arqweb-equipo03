#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 && $(hostnamectl --static) == cna-node1 ]] || {
  echo 'Ejecutar con sudo solo en VM-2 cna-node1.' >&2; exit 1;
}
container=$(docker ps --filter label=com.docker.swarm.service.name=cna_search -q)
[[ -n $container && $container != *$'\n'* ]] || exit 1
printf 'Nodo: %s\n' "$(hostnamectl --static)"
docker exec -i "$container" timeout 25 python -u - "${1:-3}" <<'PY'
import http.client
import json
import re
import socket
import ssl
import sys
from datetime import datetime, timezone
from search_svc.config import Settings

settings=Settings()
page_id=int(sys.argv[1])
context=ssl.create_default_context(cafile=str(settings.bookstack_ca))
context.minimum_version=ssl.TLSVersion.TLSv1_3
context.maximum_version=ssl.TLSVersion.TLSv1_3
context.set_alpn_protocols(['http/1.1'])

class Gateway(http.client.HTTPSConnection):
    def connect(self):
        # Equivalente a curl --resolve: IP privada fija, conservando Host,
        # SNI y verificacion del nombre api.bookstack.local.
        raw=socket.create_connection(('192.168.145.129',443),timeout=self.timeout)
        self.sock=context.wrap_socket(raw,server_hostname='api.bookstack.local')

connection=Gateway('api.bookstack.local',timeout=8,context=context)
try:
    connection.connect()
    protocol=connection.sock.version()
    connection.request('GET','/v2/search?q=alfa&entity_type=page',
                       headers={'X-API-Key':settings.api_key})
    response=connection.getresponse()
    headers=response.headers
    payload=json.loads(response.read())
    print(datetime.now(timezone.utc).isoformat())
    print('URL: https://api.bookstack.local/v2/search?q=alfa&entity_type=page')
    print('TLS:',protocol,'; CA y nombre del certificado verificados.')
    print('HTTP:',response.status)
    if response.status != 200:
        print(json.dumps(payload,ensure_ascii=False))
        raise RuntimeError('La consulta autenticada no devolvio 200')
    assert protocol=='TLSv1.3'
    request_id=headers.get('X-Request-ID','')
    assert re.fullmatch('[a-f0-9]{32}',request_id), 'Falta request_id generado por Nginx'
    for name in ('Strict-Transport-Security','X-Content-Type-Options','Referrer-Policy',
                 'X-Frame-Options','Content-Security-Policy'):
        assert headers.get(name), 'Falta cabecera: '+name
    result=next(item for item in payload['items'] if item['entity_id']==page_id)
    assert '<mark>alfa</mark>' in result['highlights']['body'].lower()
    assert result['url'].startswith('https://bookstack.local/books/')
    print('X-Request-ID:',request_id)
    print('Cabeceras de seguridad: presentes.')
    print(json.dumps(payload,ensure_ascii=False,indent=2))
    print('PASS: busqueda autenticada por gateway, TLS 1.3, pagina 3 y resaltado alfa.')
    print('Estado ANTES de editar. Falta comprobar la actualizacion por Webhook real.')
finally:
    connection.close()
PY
