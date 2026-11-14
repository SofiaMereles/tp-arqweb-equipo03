import asyncio
import json
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock, AsyncMock
import yaml
import jsonschema
from event_bridge.app import create_app
from event_bridge.normalization import Normalizer
from event_bridge.publisher import publish_pending
from event_bridge.store import Store
from fastapi.testclient import TestClient

CONTRACTS=Path(os.environ.get('CONTRACT_DIR',Path(__file__).resolve().parents[2]/'contracts'))
RAW=dict(event='page_update',triggered_at='2026-11-13T21:00:00Z',triggered_by={'id':3,'name':'Alba'},
         webhook_id=1,related_item={'id':3,'book_id':2,'current_revision':{'id':5}})
EVENT_ID='38213507-ee9d-4c9b-8ed8-e901cd1b62e6'


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.store=Mock()
        self.store.accept.return_value={'event_id':EVENT_ID,'state':'accepted'}
        settings=SimpleNamespace(api_key='unused',webhook_token='private-test-token',
                                 contract_dir=CONTRACTS,max_webhook_bytes=2097152)
        self.client=TestClient(create_app(settings,self.store,SimpleNamespace(ping=AsyncMock())))
        self.path='/internal/webhooks/bookstack?token=private-test-token'

    def test_invalid_token_is_401_before_persistence(self):
        response=self.client.post('/internal/webhooks/bookstack?token=wrong',json=RAW)
        self.assertEqual(response.status_code,401)
        self.store.accept.assert_not_called()

    def test_durable_receipt_matches_openapi(self):
        response=self.client.post(self.path,json=RAW,headers={'X-Request-ID':'bridge-test'})
        self.assertEqual(response.status_code,202)
        self.assertEqual(response.headers['X-Request-ID'],'bridge-test')
        contract=yaml.safe_load((CONTRACTS/'event-bridge.openapi.yaml').read_text(encoding='utf-8'))
        jsonschema.Draft202012Validator({'components':contract['components'],'$ref':'#/components/schemas/WebhookReceipt'}).validate(response.json())
        self.assertEqual(self.store.accept.call_args.args[1]['request_id'],'bridge-test')

    def test_duplicate_receipt_is_200_and_original_id(self):
        self.store.accept.return_value={'event_id':EVENT_ID,'state':'duplicate'}
        response=self.client.post(self.path,json=RAW)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['event_id'],EVENT_ID)

    def test_invalid_webhooks_not_persisted(self):
        for change in ({'event':'unknown'},{'triggered_at':'yesterday'},{'related_item':{}},
                       {'triggered_at':'2026-11-13T01:00:00'}):
            with self.subTest(change=change):
                self.assertEqual(self.client.post(self.path,json=dict(RAW,**change)).status_code,400)
        self.store.accept.assert_not_called()

    def test_failed_commit_returns_503_not_202(self):
        self.store.accept.side_effect=RuntimeError('private password detail')
        response=self.client.post(self.path,json=RAW)
        self.assertEqual(response.status_code,503)
        self.assertNotIn('password',response.text)

    def test_query_token_is_not_logged(self):
        with self.assertLogs('event-bridge',level='INFO') as logs:
            self.client.post(self.path,json=RAW)
        self.assertNotIn('private-test-token',' '.join(logs.output))

    def test_health_and_readiness_separate(self):
        self.store.ping.side_effect=RuntimeError('database down')
        self.assertEqual(self.client.get('/healthz').status_code,200)
        self.assertEqual(self.client.get('/readyz').status_code,503)


class NormalizationTests(unittest.TestCase):
    def test_canonical_body_not_json_key_order_defines_deduplication(self):
        normalizer=Normalizer(CONTRACTS)
        a,event=normalizer.normalize(RAW,'first-request')
        b,another=normalizer.normalize(dict(reversed(list(RAW.items()))),'retry-request')
        self.assertEqual(a,b)
        self.assertNotEqual(event['event_id'],another['event_id'])
        self.assertEqual(event['payload']['source_revision'],5)

    def test_each_required_page_event_maps_to_asyncapi(self):
        normalizer=Normalizer(CONTRACTS)
        for raw,expected in [('page_create','created'),('page_update','updated'),('page_delete','deleted')]:
            _,event=normalizer.normalize(dict(RAW,event=raw),'request')
            self.assertEqual(event['type'],'bookstack.page.'+expected)
            self.assertEqual(event['payload']['actor'],{'id':3,'name':'Alba'})

    def test_different_webhook_or_timestamp_does_not_collapse_events(self):
        n=Normalizer(CONTRACTS)
        a,_=n.normalize(RAW,'one')
        b,_=n.normalize(dict(RAW,webhook_id=2),'two')
        c,_=n.normalize(dict(RAW,triggered_at='2026-11-13T21:00:01Z'),'three')
        self.assertNotEqual(a,b)
        self.assertNotEqual(a,c)


class PublisherTests(unittest.IsolatedAsyncioTestCase):
    async def test_sent_marker_is_after_publish_ack(self):
        order=[]
        store=Mock()
        _,event=Normalizer(CONTRACTS).normalize(RAW,'request')
        store.claim.return_value=[{'event_id':event['event_id'],'event':event}]
        store.sent.side_effect=lambda eid:order.append('mark-sent')
        js=SimpleNamespace(publish=AsyncMock(side_effect=lambda *a,**kw:order.append('puback')))
        await publish_pending(js,store)
        self.assertEqual(order,['puback','mark-sent'])

    async def test_failed_publish_leaves_outbox_pending(self):
        store=Mock()
        _,event=Normalizer(CONTRACTS).normalize(RAW,'request')
        store.claim.return_value=[{'event_id':event['event_id'],'event':event}]
        js=SimpleNamespace(publish=AsyncMock(side_effect=RuntimeError('broker down')))
        with self.assertRaises(RuntimeError):
            await publish_pending(js,store)
        store.sent.assert_not_called()


class TransactionTests(unittest.TestCase):
    def test_outbox_failure_propagates_for_transaction_rollback(self):
        store=Store(Mock())
        conn=MagicMock()
        conn.__enter__.return_value=conn
        conn.execute.side_effect=[Mock(fetchone=Mock(return_value={'event_id':EVENT_ID})),RuntimeError('outbox failed')]
        store.connect=Mock(return_value=conn)
        _,event=Normalizer(CONTRACTS).normalize(RAW,'request')
        with self.assertRaises(RuntimeError):
            store.accept('fingerprint',event,RAW)
        self.assertEqual(conn.__exit__.call_args.args[0],RuntimeError)
