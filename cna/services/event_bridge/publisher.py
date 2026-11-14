import asyncio
import json
import logging
import nats
from audit_svc.broker import ensure_streams

LOG = logging.getLogger('event-bridge')


async def publish_pending(js, store):
    rows = await asyncio.to_thread(store.claim)
    for row in rows:
        event = row['event']
        await js.publish(event['type'], json.dumps(event, ensure_ascii=False).encode(),
                         headers={'Nats-Msg-Id': str(row['event_id'])}, timeout=5)
        # js.publish retorna despues de recibir PubAck, no al enviar al socket.
        await asyncio.to_thread(store.sent, row['event_id'])
        LOG.info('event_published', extra={'request_id': event['request_id'], 'event_id': str(row['event_id'])})
    return len(rows)


class Publisher:
    def __init__(self, settings, store):
        self.settings, self.store = settings, store
        self.running = False
        self.nc = None

    async def run(self):
        try:
            while True:
                try:
                    await asyncio.to_thread(self.store.initialize)
                    self.running = True
                    async def report_error(exc):
                        LOG.warning('broker_error', extra={'error_type': type(exc).__name__})
                    self.nc = await nats.connect(self.settings.nats_url, token=self.settings.nats_token,
                        connect_timeout=5, max_reconnect_attempts=2, error_cb=report_error)
                    js = self.nc.jetstream()
                    await ensure_streams(js)
                    while True:
                        count = await publish_pending(js, self.store)
                        if not count:
                            await asyncio.sleep(0.2)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    LOG.warning('publisher_reconnecting', extra={'error_type': type(exc).__name__})
                    if self.nc:
                        await self.nc.close()
                    await asyncio.sleep(2)
        finally:
            self.running = False
            if self.nc:
                await self.nc.close()

    async def ping(self):
        # La aceptacion durable depende de PostgreSQL; se puede guardar inbox
        # mientras NATS no responde. El publicador reintentara el outbox.
        if not self.running:
            raise RuntimeError('Almacen durable no inicializado')
