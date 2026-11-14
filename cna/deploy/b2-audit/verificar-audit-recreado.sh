#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 && $(hostnamectl --static) == cna-node1 ]] || {
  echo 'Ejecutar con sudo solo en VM-2 cna-node1.' >&2; exit 1;
}
[[ $# -eq 2 ]] || { echo 'Uso: verificar-audit-recreado.sh EVENT_ID ENTITY_ID' >&2; exit 1; }
container=$(docker ps --filter label=com.docker.swarm.service.name=cna_audit -q)
[[ -n $container && $container != *$'\n'* ]] || exit 1
printf 'Nodo: %s\nContenedor actual: %s\n' "$(hostnamectl --static)" "$container"
docker exec -i "$container" timeout 65 python -u - "$1" "$2" <<'PY'
import json
import sys
import time
import urllib.request
import urllib.error
from urllib.parse import urlencode
from uuid import UUID
from datetime import datetime, timezone, timedelta
from audit_svc.config import Settings

event_id = str(UUID(sys.argv[1]))
entity_id = str(int(sys.argv[2]))
settings = Settings()
request_id = 'B2-S2-persistencia-' + event_id

def fetch(path):
    request = urllib.request.Request('http://127.0.0.1:8000' + path,
        headers={'X-API-Key': settings.api_key, 'X-Request-ID': request_id})
    with urllib.request.urlopen(request, timeout=4) as response:
        assert response.headers.get('X-Request-ID') == request_id, 'No se propago X-Request-ID'
        return response.read().decode()

print(datetime.now(timezone.utc).isoformat())
health = json.loads(fetch('/healthz'))
assert health == {'status': 'ok', 'service': 'audit-svc'}
print('/healthz: 200 OK')
deadline = time.monotonic() + 35
while True:
    try:
        ready = json.loads(fetch('/readyz'))
        assert ready == {'status': 'ready', 'service': 'audit-svc'}
        break
    except urllib.error.HTTPError as exc:
        if exc.code != 503 or time.monotonic() >= deadline:
            raise
        time.sleep(1)
print('/readyz: 200 OK')
query = {'entity': 'page', 'id': entity_id}
result = json.loads(fetch('/v2/audit?' + urlencode(query)))
assert result['total'] == 1 and len(result['items']) == 1, 'El registro no se conservo como registro unico'
record = result['items'][0]
assert record['event_id'] == event_id, 'No coincide el evento original'
print(json.dumps(result, ensure_ascii=False, indent=2))
occurred = datetime.fromisoformat(record['occurred_at'])
window = dict(query, **{'from': (occurred-timedelta(seconds=1)).isoformat(),
                      'to': (occurred+timedelta(seconds=1)).isoformat()})
assert json.loads(fetch('/v2/audit?' + urlencode(window)))['total'] == 1
window['from'] = (occurred+timedelta(days=1)).isoformat()
window['to'] = (occurred+timedelta(days=2)).isoformat()
assert json.loads(fetch('/v2/audit?' + urlencode(window)))['total'] == 0
print('Filtros por entidad/ID y rango de fechas: OK (inclusion y exclusion).')
metrics = fetch('/metrics')
for name in ('http_requests_total', 'http_request_duration_seconds_bucket',
             'http_request_duration_seconds_sum', 'http_request_duration_seconds_count'):
    assert name in metrics, 'Falta metrica: ' + name
print('Metricas Prometheus: contador por codigo e histograma disponibles.')
for line in metrics.splitlines():
    if line.startswith(('http_requests_total{', 'http_request_duration_seconds_count ')):
        print(line)
print('X-Request-ID propagado:', request_id)
print('PASS: el evento original se conserva tras recrear auditoria; no se publicaron eventos en esta comprobacion.')
PY
printf '\nUltimos logs de auditoria (JSON):\n'
docker logs --tail 5 "$container" 2>&1
