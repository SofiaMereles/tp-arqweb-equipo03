import asyncio
import json
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import jsonschema
import yaml
from search_svc.app import create_app
from search_svc.documents import plain, highlight, document, hit
from search_svc.bookstack import Reader
from search_svc.broker import Broker, handle
from search_svc.store import Store
from datetime import datetime, timezone
from unittest.mock import MagicMock
from audit_svc.events import Events

CONTRACTS = Path(os.environ.get('CONTRACT_DIR', Path(__file__).resolve().parents[2] / 'contracts'))
ROW = dict(entity_type='page', entity_id=3, title='Prueba CNA', url='https://bookstack.local/books/pruebas-cna/page/prueba',
           score=0.6, book_id=2, book_title='Pruebas CNA', highlight_title='Prueba CNA',
           highlight_body='integrador nube \ue000alfa\ue001', highlight_book_title='Pruebas CNA')
EVENT = dict(event_id='f2e691d1-e873-49ab-a974-ecf7e31e20e9', type='bookstack.page.updated',
             version='1.0', occurred_at='2026-11-13T22:00:00Z', request_id='search-event-test',
             payload={'page_id': 3, 'actor': {'id': 3, 'name': 'Prueba'}})


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.store, self.reader = Mock(), Mock()
        self.store.search.return_value = [dict(ROW)]
        self.reader.detail.return_value = {'id': 3}
        self.client = TestClient(create_app(SimpleNamespace(api_key='search-test'), self.store,
                                            SimpleNamespace(ping=AsyncMock()), self.reader))
        self.headers = {'X-API-Key': 'search-test', 'X-Request-ID': 'search-request-test'}

    def test_authentication_required(self):
        self.assertEqual(self.client.get('/v2/search?q=alfa').status_code, 401)
        self.store.search.assert_not_called()

    def test_search_response_matches_openapi(self):
        response = self.client.get('/v2/search?q=alfa', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        contract = yaml.safe_load((CONTRACTS/'search-svc.openapi.yaml').read_text(encoding='utf-8'))
        schema = {'components': contract['components'], '$ref': '#/components/schemas/SearchResults'}
        jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).validate(response.json())
        self.assertEqual(response.headers['X-Request-ID'], 'search-request-test')
        self.reader.detail.assert_called_once_with('page', 3, 'search-request-test')
        self.assertIn('<mark>alfa</mark>', response.json()['items'][0]['highlights']['body'])

    def test_bad_query_returns_400(self):
        for query in ['', 'q=%20%20', 'q=a&limit=0', 'q=a&offset=-1', 'q=a&entity_type=user', 'q='+'x'*201]:
            with self.subTest(query=query):
                self.assertEqual(self.client.get('/v2/search?'+query, headers=self.headers).status_code, 400)
        self.store.search.assert_not_called()

    def test_zero_results_is_200(self):
        self.store.search.return_value = []
        response = self.client.get('/v2/search?q=unknown', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total'], 0)
        self.assertEqual(response.json()['items'], [])

    def test_deleted_or_unreadable_candidate_is_not_exposed(self):
        self.reader.detail.return_value = None
        response = self.client.get('/v2/search?q=alfa', headers=self.headers)
        self.assertEqual(response.json()['total'], 0)
        self.assertEqual(response.json()['items'], [])

    def test_entity_filter_and_pagination(self):
        self.store.search.return_value = [dict(ROW), dict(ROW,entity_id=4)]
        response = self.client.get('/v2/search?q=alfa&entity_type=page&limit=1&offset=1',headers=self.headers)
        self.store.search.assert_called_once_with('alfa','page')
        self.assertEqual(response.json()['items'][0]['entity_id'],4)
        self.assertEqual(response.json()['total'],2)

    def test_health_readiness_and_metrics(self):
        self.store.ping.side_effect = RuntimeError('database unavailable')
        self.assertEqual(self.client.get('/healthz').status_code,200)
        self.assertEqual(self.client.get('/readyz').status_code,503)
        metrics = self.client.get('/metrics').text
        self.assertIn('http_requests_total{code="503"}',metrics)
        self.assertIn('http_request_duration_seconds_bucket',metrics)


class DocumentTests(unittest.TestCase):
    def test_html_text_extraction_skips_scripts_and_styles(self):
        self.assertEqual(plain('<p>nube &amp; alfa</p><script>alert(1)</script><style>bad</style>'),'nube & alfa')

    def test_highlighting_escapes_source_and_only_adds_mark(self):
        text=highlight('<img src=x onerror=alert(1)>\ue000alfa\ue001')
        self.assertIn('&lt;img',text)
        self.assertIn('<mark>alfa</mark>',text)
        self.assertNotIn('<img',text)

    def test_native_book_and_page_links(self):
        book={'id':2,'name':'Pruebas CNA','slug':'pruebas-cna','updated_at':'2026-11-13T01:00:00Z'}
        page={'id':3,'name':'Pagina','slug':'pagina','html':'<p>nube alfa</p>','updated_at':'2026-11-13T02:00:00Z'}
        result=document('page',page,book,'https://bookstack.local')
        self.assertEqual(result['url'],'https://bookstack.local/books/pruebas-cna/page/pagina')
        self.assertEqual(document('book',book,book,'https://bookstack.local')['entity_type'],'book')
        with self.assertRaises(ValueError):
            document('page',dict(page,url='https://attacker.invalid/'),book,'https://bookstack.local')

    def test_listing_reads_every_page(self):
        reader=object.__new__(Reader)
        reader.settings=SimpleNamespace(page_size=2)
        reader.get=Mock(side_effect=[{'total':3,'data':[{'id':1},{'id':2}]},{'total':3,'data':[{'id':3}]}])
        self.assertEqual([r['id'] for r in reader.listing('pages','request')],[1,2,3])
        self.assertIn('offset=2',reader.get.call_args.args[0])

    def test_partial_listing_does_not_silently_truncate(self):
        reader=object.__new__(Reader)
        reader.settings=SimpleNamespace(page_size=2)
        reader.get=Mock(return_value={'total':3,'data':[]})
        with self.assertRaises(RuntimeError):
            list(reader.listing('pages','request'))


class ConsumerTests(unittest.IsolatedAsyncioTestCase):
    def message(self,event):
        return SimpleNamespace(data=json.dumps(event).encode(),subject=event['type'],
                               metadata=SimpleNamespace(num_delivered=1),ack_sync=AsyncMock(),nak=AsyncMock(),term=AsyncMock())

    async def test_ack_after_projection_commit(self):
        order=[]
        store=Mock()
        store.record.side_effect=lambda event: order.append('commit')
        message=self.message(EVENT)
        message.ack_sync.side_effect=lambda **kwargs: order.append('ack')
        await handle(message,store,Events(CONTRACTS),SimpleNamespace(publish=AsyncMock()),5)
        self.assertEqual(order,['commit','ack'])

    async def test_page_deleted_event_is_passed_to_transactional_store(self):
        event=dict(EVENT,type='bookstack.page.deleted')
        store=Mock()
        message=self.message(event)
        await handle(message,store,Events(CONTRACTS),SimpleNamespace(publish=AsyncMock()),5)
        store.record.assert_called_once_with(event)
        message.ack_sync.assert_awaited_once()

    async def test_failed_projection_is_retried_without_ack(self):
        store=Mock()
        store.record.side_effect=RuntimeError('upstream unavailable')
        message=self.message(EVENT)
        await handle(message,store,Events(CONTRACTS),SimpleNamespace(publish=AsyncMock()),5)
        message.nak.assert_awaited_once()
        message.ack_sync.assert_not_awaited()


class BrokerWaitingTests(unittest.IsolatedAsyncioTestCase):
    async def check_idle_timeout(self, timeout_error):
        settings=SimpleNamespace(contract_dir=CONTRACTS, nats_url='nats://broker:4222',
                                 nats_token='test', reconcile_seconds=3600, max_attempts=5)
        store=Mock()
        message=object()
        subscription=SimpleNamespace(fetch=AsyncMock(side_effect=[timeout_error, [message], asyncio.CancelledError()]))
        js=SimpleNamespace(pull_subscribe=AsyncMock(return_value=subscription))
        connection=SimpleNamespace(jetstream=Mock(return_value=js), close=AsyncMock())
        broker=Broker(settings, store, Mock())
        with patch('search_svc.broker.nats.connect', new_callable=AsyncMock, return_value=connection) as connect, \
             patch('search_svc.broker.ensure_streams', new_callable=AsyncMock), \
             patch('search_svc.broker.handle', new_callable=AsyncMock) as process:
            with self.assertRaises(asyncio.CancelledError):
                await broker.run()
        connect.assert_awaited_once()
        store.reconcile.assert_called_once_with('search-initial-index')
        process.assert_awaited_once_with(message, store, broker.events, js, 5)
        self.assertEqual(subscription.fetch.await_count, 3)
        connection.close.assert_awaited_once()

    async def test_idle_asyncio_timeout_keeps_subscription_and_initial_index(self):
        await self.check_idle_timeout(asyncio.TimeoutError())

    async def test_idle_nats_timeout_keeps_subscription_and_initial_index(self):
        from nats.errors import TimeoutError as NatsTimeoutError
        await self.check_idle_timeout(NatsTimeoutError())


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.reader=Mock()
        self.store=Store(SimpleNamespace(bookstack_url='https://bookstack.local'),self.reader)
        self.conn=MagicMock()
        self.conn.__enter__.return_value=self.conn
        self.store.connect=Mock(return_value=self.conn)

    def test_delete_event_removes_page_without_fetching_content(self):
        self.conn.execute.side_effect=[Mock(),Mock(fetchone=Mock(return_value={'event_id':EVENT['event_id']})),
                                       Mock(fetchone=Mock(return_value=None)),Mock(),Mock()]
        self.assertTrue(self.store.record(dict(EVENT,type='bookstack.page.deleted')))
        statements=[call.args[0] for call in self.conn.execute.call_args_list]
        self.assertTrue(any("DELETE FROM search_documents" in sql for sql in statements))
        self.reader.detail.assert_not_called()

    def test_duplicate_does_not_repeat_projection_or_api_calls(self):
        self.conn.execute.side_effect=[Mock(),Mock(fetchone=Mock(return_value=None))]
        self.assertFalse(self.store.record(EVENT))
        self.reader.detail.assert_not_called()
        self.assertEqual(self.conn.execute.call_count,2)

    def test_stale_event_does_not_overwrite_newer_entity(self):
        self.conn.execute.side_effect=[Mock(),Mock(fetchone=Mock(return_value={'event_id':EVENT['event_id']})),
             Mock(fetchone=Mock(return_value={'clock':datetime(2026,11,14,tzinfo=timezone.utc)}))]
        self.assertFalse(self.store.record(EVENT))
        self.reader.detail.assert_not_called()
        self.assertEqual(self.conn.execute.call_count,3)

    def test_failed_initial_api_scan_does_not_clear_previous_index(self):
        self.reader.listing.side_effect=RuntimeError('upstream unavailable')
        with self.assertRaises(RuntimeError):
            self.store.reconcile('request')
        statements=[call.args[0] for call in self.conn.execute.call_args_list]
        self.assertFalse(any('DELETE' in sql for sql in statements))
