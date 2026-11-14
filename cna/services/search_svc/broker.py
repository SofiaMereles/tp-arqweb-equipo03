import asyncio
import json
import logging
import random
import time
import nats
from nats.js.api import ConsumerConfig, AckPolicy
from audit_svc.broker import ensure_streams
from audit_svc.events import Events

LOG = logging.getLogger('search-svc')


async def handle(message, store, events, js, attempts):
    request_id = '-'
    try:
        event = json.loads(message.data)
        events.validate(event)
        request_id = event['request_id']
        if event['type'] != message.subject or not event['type'].startswith('bookstack.page.'):
            raise ValueError('Subject inesperado')
        await asyncio.to_thread(store.record, event)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        count = message.metadata.num_delivered
        LOG.warning('event_retry', extra={'request_id': request_id, 'error_type': type(exc).__name__})
        if count >= attempts:
            await js.publish('dlq.search-svc.' + message.subject, message.data,
                             headers={'X-Failure': type(exc).__name__, 'X-Delivery-Attempts': str(count)})
            await message.term()
        else:
            await message.nak(delay=min(30, 2 ** count) + random.random())
        return
    await message.ack_sync(timeout=3)
    LOG.info('event_applied', extra={'request_id': request_id})


class Broker:
    def __init__(self, settings, store, reader):
        self.settings, self.store, self.reader = settings, store, reader
        self.events = Events(settings.contract_dir)
        self.nc = None
        self.connected = False

    async def run(self):
        try:
            while True:
                try:
                    await asyncio.to_thread(self.store.initialize)
                    async def report_error(exc):
                        LOG.warning('broker_error', extra={'error_type': type(exc).__name__})
                    self.nc = await nats.connect(self.settings.nats_url, token=self.settings.nats_token,
                        connect_timeout=5, max_reconnect_attempts=2, error_cb=report_error)
                    js = self.nc.jetstream()
                    await ensure_streams(js)
                    durable = 'search-svc-pages-v1'
                    subscription = await js.pull_subscribe('bookstack.page.*', durable=durable,
                        stream='BOOKSTACK_PAGES', config=ConsumerConfig(durable_name=durable,
                        ack_policy=AckPolicy.EXPLICIT, ack_wait=60, max_ack_pending=20))
                    # El consumidor ya existe mientras se recorre la carga inicial.
                    counts = await asyncio.to_thread(self.store.reconcile, 'search-initial-index')
                    LOG.info('initial_index_complete', extra={'counts': counts})
                    self.connected = True
                    reconciled = time.monotonic()
                    while True:
                        try:
                            messages = await subscription.fetch(10, timeout=0.5)
                        # fetch puede agotar el plazo con asyncio.TimeoutError
                        # o su subclase nats.errors.TimeoutError. Ambos significan
                        # que esta espera termino sin mensajes, no que haya que
                        # reconectar y repetir la carga inicial REST.
                        except asyncio.TimeoutError:
                            messages = []
                        for message in messages:
                            try:
                                await handle(message, self.store, self.events, js, self.settings.max_attempts)
                            except Exception as exc:
                                LOG.warning('delivery_unconfirmed', extra={'error_type': type(exc).__name__})
                        if time.monotonic() - reconciled >= self.settings.reconcile_seconds:
                            await asyncio.to_thread(self.store.reconcile, 'search-reconcile')
                            reconciled = time.monotonic()
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
            raise RuntimeError('Indice o consumidor no disponible')
        await self.nc.flush(timeout=3)
        await self.nc.jetstream().account_info()
        await asyncio.to_thread(self.reader.ping, 'search-readiness')
