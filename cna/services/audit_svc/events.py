from datetime import datetime, timezone
import jsonschema
import yaml

TYPES = {
    'bookstack.page.created': 'PageCreatedEvent',
    'bookstack.page.updated': 'PageUpdatedEvent',
    'bookstack.page.deleted': 'PageDeletedEvent',
    'export.requested': 'ExportRequestedEvent',
    'export.completed': 'ExportCompletedEvent',
    'media.uploaded': 'MediaUploadedEvent',
}


class Events:
    def __init__(self, contract_dir):
        contract = yaml.safe_load((contract_dir / 'bookstack.asyncapi.yaml').read_text(encoding='utf-8'))
        self.validators = {}
        for name, schema in TYPES.items():
            document = {'components': contract['components'], '$ref': f'#/components/schemas/{schema}'}
            self.validators[name] = jsonschema.Draft202012Validator(document, format_checker=jsonschema.FormatChecker())

    def validate(self, event):
        if not isinstance(event, dict) or event.get('type') not in self.validators:
            raise ValueError('Tipo de evento no soportado')
        self.validators[event['type']].validate(event)
        # jsonschema puede instalarse sin el validador opcional RFC3339.
        # Esta comprobación no depende de extras y exige una fecha real con zona.
        if not isinstance(event['occurred_at'], str) or not date_filter(event['occurred_at']):
            raise ValueError('occurred_at inválido')
        return event


def project(event):
    payload = event['payload']
    if event['type'].startswith('bookstack.page.'):
        entity = {'type': 'page', 'id': str(payload['page_id'])}
    elif event['type'].startswith('export.'):
        entity = {'type': 'export', 'id': payload['job_id']}
    else:
        entity = {'type': 'media', 'id': payload['media_id']}
    return dict(event_id=event['event_id'], type=event['type'], occurred_at=event['occurred_at'],
                request_id=event['request_id'], actor=payload['actor'], entity=entity,
                action=event['type'].rsplit('.', 1)[-1])


def date_filter(value):
    if value is None:
        return None
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('La fecha requiere zona horaria')
    return result.astimezone(timezone.utc)
