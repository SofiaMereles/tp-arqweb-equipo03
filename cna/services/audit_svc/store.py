import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from .events import project

DDL = '''
CREATE TABLE IF NOT EXISTS audit_records (
  event_id uuid PRIMARY KEY,
  type text NOT NULL,
  occurred_at timestamptz NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT now(),
  request_id text NOT NULL,
  actor jsonb NOT NULL,
  entity_type text NOT NULL,
  entity_id text NOT NULL,
  action text NOT NULL
);
CREATE INDEX IF NOT EXISTS audit_entity_date ON audit_records(entity_type, entity_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS audit_date ON audit_records(occurred_at DESC, event_id);
'''


class Store:
    def __init__(self, settings):
        self.settings = settings

    def connect(self):
        return psycopg.connect(**self.settings.connection_args(), row_factory=dict_row)

    def initialize(self):
        with self.connect() as conn:
            conn.execute(DDL)

    def ping(self):
        with self.connect() as conn:
            conn.execute('SELECT 1').fetchone()

    def record(self, event):
        row = project(event)
        with self.connect() as conn:
            result = conn.execute('''INSERT INTO audit_records
              (event_id,type,occurred_at,request_id,actor,entity_type,entity_id,action)
              VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
              ON CONFLICT (event_id) DO NOTHING RETURNING event_id''',
              (row['event_id'], row['type'], row['occurred_at'], row['request_id'], Jsonb(row['actor']),
               row['entity']['type'], row['entity']['id'], row['action'])).fetchone()
        # La salida del contexto confirmó COMMIT antes de devolver el resultado al consumidor.
        return result is not None

    def query(self, entity, entity_id, start, end, limit, offset):
        conditions, args = [], []
        for column, operator, val in [('entity_type', '=', entity), ('entity_id', '=', entity_id),
                                      ('occurred_at', '>=', start), ('occurred_at', '<=', end)]:
            if val is not None:
                conditions.append(f'{column} {operator} %s')
                args.append(val)
        where = ' WHERE ' + ' AND '.join(conditions) if conditions else ''
        # Mismo snapshot para total y página, incluso si ingresan eventos concurrentes.
        with self.connect() as conn:
            conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            total = conn.execute('SELECT count(*) AS total FROM audit_records' + where, args).fetchone()['total']
            rows = conn.execute('SELECT * FROM audit_records' + where +
                                ' ORDER BY occurred_at DESC, event_id DESC LIMIT %s OFFSET %s',
                                [*args, limit, offset]).fetchall()
        items = []
        for row in rows:
            items.append(dict(event_id=str(row['event_id']), type=row['type'],
                              occurred_at=row['occurred_at'].isoformat(), recorded_at=row['recorded_at'].isoformat(),
                              request_id=row['request_id'], actor=row['actor'],
                              entity={'type': row['entity_type'], 'id': row['entity_id']}, action=row['action']))
        return dict(total=total, limit=limit, offset=offset, items=items)
