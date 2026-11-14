#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 && $(hostnamectl --static) == cna-node1 ]] || {
  echo 'Ejecutar con sudo solo en VM-2 cna-node1.' >&2; exit 1;
}
container=$(docker ps --filter label=com.docker.swarm.service.name=cna_audit -q)
[[ -n $container && $container != *$'\n'* ]] || exit 1
docker exec -i "$container" timeout 45 python -u - <<'PY'
import asyncio
import socket
import time
import urllib.request
import urllib.error
from urllib.parse import urlsplit
import nats
from audit_svc.config import Settings
from audit_svc.store import Store

settings = Settings()
print('DIAGNOSTICO S2: solo lectura; no se muestran secretos.')
for path in ('/healthz', '/readyz'):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000' + path, timeout=4) as response:
            print(path, response.status, response.read().decode())
    except urllib.error.HTTPError as exc:
        print(path, exc.code, exc.read().decode())
    except Exception as exc:
        print(path, 'ERROR', type(exc).__name__)
try:
    with Store(settings).connect() as conn:
        row = conn.execute("SELECT current_user AS role, to_regclass('public.audit_records') AS tabla").fetchone()
        print('POSTGRES: OK', row)
except Exception as exc:
    print('POSTGRES: ERROR', type(exc).__name__)

async def diagnose():
    address = urlsplit(settings.nats_url)
    hostname, port = address.hostname, address.port or 4222
    print('Nombre NATS configurado:', hostname, 'puerto:', port)
    resolved_ip = None
    try:
        started = time.monotonic()
        addresses = await asyncio.wait_for(asyncio.get_running_loop().getaddrinfo(
            hostname, port, type=socket.SOCK_STREAM), timeout=8)
        resolved_ip = addresses[0][4][0]
        print('DNS ASYNC: OK', resolved_ip, 'segundos:', round(time.monotonic()-started, 3))
    except Exception as exc:
        print('DNS ASYNC: ERROR', type(exc).__name__)

    async def on_error(exc):
        print('NATS callback:', type(exc).__name__)

    urls = [('nombre', settings.nats_url)]
    if resolved_ip:
        urls.append(('IP diagnostica, sin cambiar configuracion', f'nats://{resolved_ip}:{port}'))
    for label, url in urls:
        nc = None
        try:
            print('Conectando NATS por', label)
            nc = await asyncio.wait_for(nats.connect(url, token=settings.nats_token,
                connect_timeout=5, max_reconnect_attempts=0, allow_reconnect=False,
                error_cb=on_error), timeout=10)
            print('AUTENTICACION NATS: OK')
            js = nc.jetstream(timeout=3)
            info = await js.account_info()
            print('JETSTREAM: OK; streams:', info.streams)
            for stream, durable in [('BOOKSTACK_PAGES', 'audit-svc-pages-v1'),
                                     ('PLATFORM_EVENTS', 'audit-svc-platform-v1')]:
                try:
                    info = await js.consumer_info(stream, durable)
                    print('CONSUMIDOR:', stream, durable, 'OK; pendientes:', info.num_pending)
                except Exception as exc:
                    print('CONSUMIDOR:', stream, durable, 'ERROR', type(exc).__name__)
            break
        except Exception as exc:
            print('CONEXION NATS:', type(exc).__name__)
        finally:
            if nc:
                await nc.close()

asyncio.run(diagnose())
print('FIN DIAGNOSTICO')
PY
