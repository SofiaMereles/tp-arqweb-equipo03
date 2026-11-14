import asyncio
import json
import logging
import random
import nats
from nats.js.api import ConsumerConfig, AckPolicy, StorageType
from nats.js.errors import NotFoundError

LOG = logging.getLogger('audit-svc')
STREAMS = {'BOOKSTACK_PAGES': ['bookstack.page.*'],
           'PLATFORM_EVENTS': ['export.requested', 'export.completed', 'media.uploaded'],
           'CNA_DLQ': ['dlq.>']}


async def ensure_streams(js):
    for name, subjects in STREAMS.items():
        try:
            await js.stream_info(name)
        except NotFoundError:
            await js.add_stream(name=name, subjects=subjects, storage=StorageType.FILE,
                                max_bytes=64 * 1024 * 1024, max_age=7 * 86400)


async def handle(message, store, events, js, max_attempts):
    event = None
    try:
        event = json.loads(message.data)
        events.validate(event)
        if message.subject != event['type']:
            raise ValueError('El subject no coincide con type')
        inserted = await asyncio.to_thread(store.record, event)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        attempt = message.metadata.num_delivered
        request_id = event.get('request_id', '-') if isinstance(event, dict) else '-'
        LOG.warning('event_retry', extra={'request_id': request_id, 'error_type': type(exc).__name__})
        if attempt >= max_attempts:
            # PubAck de JetStream antes de terminar el original; si falla, se reintentará.
            await js.publish('dlq.audit-svc.' + message.subject, message.data,
                             headers={'X-Failure': type(exc).__name__, 'X-Delivery-Attempts': str(attempt),
                                      'X-Request-ID': request_id})
            await message.term()
        else:
            await message.nak(delay=min(30, 2 ** attempt) + random.random())
        return
    # Un fallo de confirmación no convierte en inválido un evento ya confirmado en PostgreSQL.
    # Se deja pendiente para una redelivery idempotente; no se manda a DLQ por perder el ACK.
    await message.ack_sync(timeout=3)
    LOG.info('event_recorded' if inserted else 'event_duplicate', extra={'request_id': event['request_id']})


class Broker:
    def __init__(self, settings, store, events):
        self.settings, self.store, self.events = settings, store, events
        self.nc = None
        self.connected = False

    async def run(self):
        try:
            while True:
                try:
                    await asyncio.to_thread(self.store.initialize)
                    self.nc = await nats.connect(self.settings.nats_url, token=self.settings.nats_token,
                                                 connect_timeout=3, max_reconnect_attempts=-1)
                    js = self.nc.jetstream()
                    await ensure_streams(js)
                    subscriptions = []
                    for stream, durable in [('BOOKSTACK_PAGES', 'audit-svc-pages-v1'),
                                             ('PLATFORM_EVENTS', 'audit-svc-platform-v1')]:
                        config = ConsumerConfig(durable_name=durable, ack_policy=AckPolicy.EXPLICIT,
                                                ack_wait=30, max_ack_pending=20)
                        subscriptions.append(await js.pull_subscribe('>', durable=durable, stream=stream, config=config))
                    self.connected = True
                    while True:
                        for subscription in subscriptions:
                            try:
                                messages = await subscription.fetch(10, timeout=1)
                            except nats.errors.TimeoutError:
                                continue
                            for message in messages:
                                try:
                                    await handle(message, self.store, self.events, js, self.settings.max_attempts)
                                except Exception as exc:
                                    LOG.warning('delivery_unconfirmed', extra={'error_type': type(exc).__name__})
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    self.connected = False
                    LOG.warning('consumer_reconnecting', extra={'error_type': type(exc).__name__})
                    if self.nc:
                        await self.nc.close()
                    await asyncio.sleep(2)
        finally:
            self.connected = False
            if self.nc:
                await self.nc.close()

    async def ping(self):
        if not self.connected or self.nc is None or not self.nc.is_connected:
            raise RuntimeError('Consumidor no disponible')
        await self.nc.flush(timeout=2)
        await self.nc.jetstream().account_info()
