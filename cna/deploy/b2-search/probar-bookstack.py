"""Prueba de lectura desde VM-2; usa secreto y CA montados por Swarm."""
import json
import os
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPSHandler, ProxyHandler


def main():
    base = os.environ['BOOKSTACK_URL'].rstrip('/')
    credential = Path(os.environ['BOOKSTACK_TOKEN_FILE']).read_text().strip()
    if ':' not in credential or '\n' in credential or '\r' in credential:
        raise ValueError('Formato del secreto inesperado')
    context = ssl.create_default_context(cafile=os.environ['BOOKSTACK_CA_FILE'])
    opener = build_opener(ProxyHandler({}), HTTPSHandler(context=context))
    expected_page = os.environ['EXPECTED_PAGE']
    expected_book = os.environ['EXPECTED_BOOK']
    request_id = 'PRE-B2-S1-lectura-api'

    def get(path):
        request = Request(base + path, headers={
            'Authorization': 'Token ' + credential, 'X-Request-ID': request_id,
            'Accept': 'application/json',
        })
        with opener.open(request, timeout=8) as response:
            return json.loads(response.read())

    print(datetime.now(timezone.utc).isoformat(), flush=True)
    print('Origen: tarea de prueba fijada a cna-node1 (VM-2).', flush=True)
    found = None
    offset = 0
    # Se pagina solo para localizar la página de control. No es la indexación de S1.
    for _ in range(100):
        listing = get(f'/api/pages?count=100&offset={offset}')
        rows = listing['data']
        print(f'API paginas: HTTP 200; total visible={listing["total"]}; offset={offset}', flush=True)
        for row in rows:
            if row['name'] == expected_page:
                candidate = get('/api/pages/' + str(row['id']))
                book = get('/api/books/' + str(candidate['book_id']))
                if book['name'] == expected_book:
                    found = candidate
                    break
        if found or not rows or offset + len(rows) >= listing['total']:
            break
        offset += len(rows)
    if found is None:
        raise RuntimeError('La cuenta no ve la pagina de control en el libro esperado. Revisar contenido y permisos.')
    content = ' '.join(str(found.get(field, '')) for field in ('html', 'raw_html', 'text', 'markdown'))
    if 'integrador nube alfa' not in content:
        raise RuntimeError('La pagina es visible pero falta la frase de control inicial.')
    print('Libro:', expected_book, flush=True)
    print('Pagina:', found['name'], '; ID:', found['id'], '; book_id:', found['book_id'], flush=True)
    print('Contenido de control leido: integrador nube alfa', flush=True)
    # Operación de lectura protegida por permiso administrativo. No altera usuarios.
    try:
        get('/api/users?count=1')
    except HTTPError as exc:
        if exc.code != 403:
            raise RuntimeError(f'Comprobacion de permisos devolvio HTTP {exc.code}; se esperaba 403') from None
        print('Consulta administrativa de usuarios: HTTP 403, acceso denegado.', flush=True)
    else:
        raise RuntimeError('El token permite consultar usuarios; revisar que pertenezca al rol de lectura.')
    print('PASS: VM-2 lee la pagina por API con TLS verificado y sin permiso para administrar usuarios.', flush=True)
    print('No se modificaron paginas ni se imprimio el token. La indexacion de S1 aun no se ejecuto.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except HTTPError as exc:
        print('FAIL: API devolvio HTTP', exc.code, flush=True)
        sys.exit(1)
    except Exception as exc:
        # Los errores de red no contienen la cabecera de autorización.
        print('FAIL:', type(exc).__name__, str(exc), flush=True)
        sys.exit(1)
