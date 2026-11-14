import asyncio
import json
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient
from audit_svc.app import create_app
from audit_svc.events import Events, project, date_filter
from audit_svc.broker import handle

CONTRACTS = Path(os.environ.get('CONTRACT_DIR', Path(__file__).resolve().parents[2] / 'contracts'))
EVENT = dict(event_id='f2e691d1-e873-49ab-a974-ecf7e31e20e9', type='bookstack.page.created',
             version='1.0', occurred_at='2026-11-13T02:00:00Z', request_id='test-audit-01',
             payload={'page_id': 42, 'actor': {'id': 3, 'name': 'Prueba'}})


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.store = Mock()
        self.store.query.return_value = dict(total=0, limit=20, offset=0, items=[])
        self.broker = SimpleNamespace(ping=AsyncMock())
        self.client = TestClient(create_app(SimpleNamespace(api_key='test-key'), self.store, self.broker))
        self.headers = {'X-API-Key': 'test-key', 'X-Request-ID': 'evidence-test'}

    def test_authentication_is_required(self):
        response = self.client.get('/v2/audit')
        self.assertEqual(response.status_code, 401)
        self.store.query.assert_not_called()

    def test_request_id_and_contract(self):
        import yaml
        import jsonschema
        response = self.client.get('/v2/audit', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['X-Request-ID'], 'evidence-test')
        contract = yaml.safe_load((CONTRACTS / 'audit-svc.openapi.yaml').read_text(encoding='utf-8'))
        document = {'components': contract['components'], '$ref': '#/components/schemas/AuditResults'}
        jsonschema.Draft202012Validator(document).validate(response.json())

    def test_invalid_filters_are_400(self):
        for query in ['id=42', 'entity=unknown', 'limit=101', 'offset=-1',
                      'from=2026-11-14T00:00:00Z&to=2026-11-13T00:00:00Z',
                      'from=2026-11-13T00:00:00']:
            with self.subTest(query=query):
                self.assertEqual(self.client.get('/v2/audit?' + query, headers=self.headers).status_code, 400)
        self.store.query.assert_not_called()

    def test_valid_filters_reach_store(self):
        response = self.client.get('/v2/audit?entity=page&id=42&limit=10&offset=2', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.store.query.assert_called_once_with('page', '42', None, None, 10, 2)

    def test_liveness_is_separate_from_readiness(self):
        self.store.ping.side_effect = RuntimeError('private connection string')
        self.assertEqual(self.client.get('/healthz').status_code, 200)
        response = self.client.get('/readyz')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private connection', response.text)

    def test_unavailable_database_returns_uniform_503(self):
        self.store.query.side_effect = RuntimeError('password must not appear')
        response = self.client.get('/v2/audit', headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['error']['request_id'], 'evidence-test')
        self.assertNotIn('password', response.text)

    def test_metrics_include_codes_and_latency_histogram(self):
        self.client.get('/healthz')
        self.client.get('/v2/audit')
        response = self.client.get('/metrics')
        self.assertIn('http_requests_total{code="401"}', response.text)
        self.assertIn('http_request_duration_seconds_bucket', response.text)


class EventTests(unittest.TestCase):
    def setUp(self):
        self.events = Events(CONTRACTS)

    def test_event_validates_against_actual_asyncapi(self):
        self.events.validate(EVENT)
        row = project(EVENT)
        self.assertEqual(row['entity'], {'type': 'page', 'id': '42'})
        self.assertEqual(row['actor']['name'], 'Prueba')
        self.assertEqual(row['request_id'], 'test-audit-01')

    def test_invalid_or_unsupported_event_is_rejected(self):
        for change in [{'event_id': 'not-uuid'}, {'version': '3.0'}, {'payload': {}}, {'occurred_at': 'yesterday'}]:
            with self.subTest(change=change), self.assertRaises(Exception):
                self.events.validate(dict(EVENT, **change))

    def test_date_requires_timezone(self):
        self.assertEqual(date_filter('2026-11-13T01:00:00-03:00').hour, 4)
        with self.assertRaises(ValueError):
            date_filter('2026-11-13T01:00:00')


class ConsumerTests(unittest.IsolatedAsyncioTestCase):
    def message(self, delivery=1):
        return SimpleNamespace(data=json.dumps(EVENT).encode(), subject=EVENT['type'],
                               metadata=SimpleNamespace(num_delivered=delivery),
                               ack_sync=AsyncMock(), nak=AsyncMock(), term=AsyncMock())

    async def test_ack_is_after_successful_transaction(self):
        order = []
        store = Mock()
        store.record.side_effect = lambda event: order.append('commit') or True
        message = self.message()
        message.ack_sync.side_effect = lambda **kwargs: order.append('ack')
        await handle(message, store, Events(CONTRACTS), SimpleNamespace(publish=AsyncMock()), 5)
        self.assertEqual(order, ['commit', 'ack'])

    async def test_failed_transaction_is_not_acknowledged(self):
        store = Mock()
        store.record.side_effect = RuntimeError('database unavailable')
        message = self.message()
        await handle(message, store, Events(CONTRACTS), SimpleNamespace(publish=AsyncMock()), 5)
        message.ack_sync.assert_not_awaited()
        message.nak.assert_awaited_once()

    async def test_lost_ack_does_not_dlq_an_already_committed_record(self):
        store = Mock()
        store.record.return_value = True
        js = SimpleNamespace(publish=AsyncMock())
        message = self.message(5)
        message.ack_sync.side_effect = TimeoutError('ack lost')
        with self.assertRaises(TimeoutError):
            await handle(message, store, Events(CONTRACTS), js, 5)
        js.publish.assert_not_awaited()
        message.term.assert_not_awaited()

    async def test_failed_dlq_publish_does_not_terminate_original(self):
        store = Mock()
        store.record.side_effect = RuntimeError('database unavailable')
        js = SimpleNamespace(publish=AsyncMock(side_effect=RuntimeError('broker unavailable')))
        message = self.message(5)
        with self.assertRaises(RuntimeError):
            await handle(message, store, Events(CONTRACTS), js, 5)
        message.term.assert_not_awaited()
        message.ack_sync.assert_not_awaited()
