import json
import ssl
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPSHandler, ProxyHandler


class Reader:
    def __init__(self, settings):
        self.settings = settings
        context = ssl.create_default_context(cafile=str(settings.bookstack_ca))
        self.opener = build_opener(ProxyHandler({}), HTTPSHandler(context=context))

    def get(self, path, request_id, missing_ok=False):
        request = Request(self.settings.bookstack_url + path, headers={
            'Authorization': 'Token ' + self.settings.bookstack_token,
            'Accept': 'application/json', 'X-Request-ID': request_id,
        })
        try:
            with self.opener.open(request, timeout=self.settings.api_timeout) as response:
                return json.loads(response.read())
        except HTTPError as exc:
            if missing_ok and exc.code in (403, 404):
                return None
            # No incluir cabeceras, credenciales ni cuerpo del servidor en logs/errores.
            raise RuntimeError(f'BookStack HTTP {exc.code}') from None

    def listing(self, kind, request_id):
        offset = 0
        while True:
            listing = self.get(f'/api/{kind}?count={self.settings.page_size}&offset={offset}', request_id)
            rows, total = listing['data'], listing['total']
            if not isinstance(rows, list) or not isinstance(total, int) or total < 0:
                raise ValueError('Respuesta paginada invalida')
            if not rows and offset < total:
                raise RuntimeError('Catalogo cambio durante paginacion; reintentar')
            yield from rows
            offset += len(rows)
            if offset >= total:
                return

    def detail(self, kind, entity_id, request_id):
        if kind not in ('page', 'book') or int(entity_id) < 1:
            raise ValueError('Entidad invalida')
        return self.get(f'/api/{kind}s/{int(entity_id)}', request_id, missing_ok=True)

    def ping(self, request_id):
        self.get('/api/pages?count=1&offset=0', request_id)
