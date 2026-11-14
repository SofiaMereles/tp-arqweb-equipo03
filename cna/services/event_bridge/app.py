import asyncio
import hmac
import json
import logging
import re
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.exceptions import HTTPException
from .config import Settings
from .normalization import Normalizer
from .store import Store
from .publisher import Publisher


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(dict(timestamp=datetime.now(timezone.utc).isoformat(), level=record.levelname.lower(),
                               service='event-bridge', request_id=getattr(record, 'request_id', '-'),
                               message=record.getMessage(),
                               **({'error_type': record.error_type} if hasattr(record, 'error_type') else {})))


LOG = logging.getLogger('event-bridge')
if not LOG.handlers:
    import sys
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    LOG.addHandler(handler)
LOG.setLevel(logging.INFO)
LOG.propagate = False


def create_app(settings=None, store=None, broker=None):
    settings = settings or Settings()
    store = store or Store(settings)
    broker = broker or Publisher(settings, store)
    normalizer = Normalizer(settings.contract_dir)
    registry = CollectorRegistry()
    requests = Counter('http_requests_total', 'Peticiones HTTP por código', ['code'], registry=registry)
    latency = Histogram('http_request_duration_seconds', 'Duración de solicitudes HTTP', registry=registry)

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(broker.run())
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    def error(request, status, code, message):
        return JSONResponse(status_code=status, content={'error': {'code': code, 'message': message,
                            'request_id': request.state.request_id}})

    @app.middleware('http')
    async def instrument(request, call_next):
        started = time.perf_counter()
        supplied = request.headers.get('X-Request-ID', '')
        request.state.request_id = supplied if re.fullmatch(r'[A-Za-z0-9._-]{1,128}', supplied) else uuid4().hex
        try:
            if request.url.path.startswith('/v2/') and not hmac.compare_digest(
                    request.headers.get('X-API-Key', '').encode(), settings.api_key.encode()):
                response = error(request, 401, 'unauthorized', 'Credencial ausente o inválida.')
            else:
                response = await call_next(request)
        except Exception as exc:
            LOG.error('request_failed', extra={'request_id': request.state.request_id, 'error_type': type(exc).__name__})
            response = error(request, 503, 'service_unavailable', 'El servicio o una dependencia no está disponible.')
        requests.labels(str(response.status_code)).inc()
        latency.observe(time.perf_counter() - started)
        response.headers['X-Request-ID'] = request.state.request_id
        LOG.info('http_request', extra={'request_id': request.state.request_id})
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return error(request, 400, 'invalid_request', 'Solicitud inválida.')

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error(request, exc.status_code, 'not_found' if exc.status_code == 404 else 'invalid_request',
                     'Recurso inexistente.' if exc.status_code == 404 else 'Solicitud inválida.')

    @app.get('/healthz')
    def health():
        return {'status': 'ok', 'service': 'event-bridge'}

    @app.get('/readyz')
    async def ready(request: Request):
        try:
            await asyncio.to_thread(store.ping)
            await broker.ping()
        except Exception:
            return error(request, 503, 'service_unavailable', 'El servicio o una dependencia no está disponible.')
        return {'status': 'ready', 'service': 'event-bridge'}

    @app.get('/metrics')
    def metrics():
        return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

    @app.post('/internal/webhooks/bookstack')
    async def webhook(request: Request):
        supplied = request.query_params.get('token', '')
        if not hmac.compare_digest(supplied.encode(), settings.webhook_token.encode()):
            return error(request, 401, 'unauthorized', 'Credencial ausente o inválida.')
        try:
            data = bytearray()
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data) > settings.max_webhook_bytes:
                    raise ValueError('Payload demasiado grande')
            def reject_constant(value):
                raise ValueError('Constante JSON invalida')
            raw = json.loads(data, parse_constant=reject_constant)
            fingerprint, event = normalizer.normalize(raw, request.state.request_id)
        except Exception:
            return error(request, 400, 'invalid_request', 'Webhook inválido.')
        receipt = await asyncio.to_thread(store.accept, fingerprint, event, raw)
        receipt['request_id'] = request.state.request_id
        return JSONResponse(status_code=202 if receipt['state']=='accepted' else 200, content=receipt)

    return app
