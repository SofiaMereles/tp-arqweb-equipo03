import hashlib
import json
from uuid import uuid4
import jsonschema
import yaml
from audit_svc.events import Events, date_filter

TYPES = {'page_create': 'bookstack.page.created', 'page_update': 'bookstack.page.updated',
         'page_delete': 'bookstack.page.deleted'}


class Normalizer:
    def __init__(self, contract_dir):
        contract = yaml.safe_load((contract_dir / 'event-bridge.openapi.yaml').read_text(encoding='utf-8'))
        schema = {'components': contract['components'], '$ref': '#/components/schemas/BookStackWebhook'}
        self.validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        self.events = Events(contract_dir)

    def normalize(self, body, request_id):
        self.validator.validate(body)
        date_filter(body['triggered_at'])
        canonical = json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
        fingerprint = hashlib.sha256((str(body['webhook_id']) + ':' + canonical).encode()).hexdigest()
        item = body['related_item']
        payload = dict(page_id=item['id'], actor={'id': body['triggered_by']['id'], 'name': body['triggered_by']['name']})
        if item.get('book_id') is not None:
            payload['book_id'] = item['book_id']
        revision = item.get('current_revision') or {}
        revision_id = revision.get('revision_number') or revision.get('id')
        if isinstance(revision_id, int) and not isinstance(revision_id, bool) and revision_id > 0:
            payload['source_revision'] = revision_id
        event = dict(event_id=str(uuid4()), type=TYPES[body['event']], version='1.0',
                     occurred_at=body['triggered_at'], request_id=request_id, payload=payload)
        self.events.validate(event)
        return fingerprint, event
