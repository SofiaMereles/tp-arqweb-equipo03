import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

DDL = '''
CREATE TABLE IF NOT EXISTS bridge_inbox (
 fingerprint text PRIMARY KEY, event_id uuid UNIQUE NOT NULL,
 received_at timestamptz NOT NULL DEFAULT now(), raw_payload jsonb NOT NULL,
 event jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS bridge_outbox (
 event_id uuid PRIMARY KEY REFERENCES bridge_inbox(event_id),
 event jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 sent_at timestamptz, lease_until timestamptz
);
CREATE INDEX IF NOT EXISTS bridge_pending ON bridge_outbox(created_at) WHERE sent_at IS NULL;
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
            if not conn.execute("SELECT to_regclass('public.bridge_outbox') AS relation").fetchone()['relation']:
                raise RuntimeError('Inbox/outbox no inicializados')

    def accept(self, fingerprint, event, raw):
        with self.connect() as conn:
            inserted = conn.execute('''INSERT INTO bridge_inbox(fingerprint,event_id,raw_payload,event)
              VALUES (%s,%s,%s,%s) ON CONFLICT(fingerprint) DO NOTHING RETURNING event_id''',
              (fingerprint, event['event_id'], Jsonb(raw), Jsonb(event))).fetchone()
            if inserted:
                conn.execute('INSERT INTO bridge_outbox(event_id,event) VALUES (%s,%s)',
                             (event['event_id'], Jsonb(event)))
                receipt = {'event_id': event['event_id'], 'state': 'accepted'}
            else:
                existing = conn.execute('SELECT event_id FROM bridge_inbox WHERE fingerprint=%s', (fingerprint,)).fetchone()
                receipt = {'event_id': str(existing['event_id']), 'state': 'duplicate'}
        # El 202 se devuelve solo despues del COMMIT de ambas tablas.
        return receipt

    def claim(self):
        with self.connect() as conn:
            return conn.execute('''UPDATE bridge_outbox SET lease_until=now()+interval '30 seconds'
              WHERE event_id IN (SELECT event_id FROM bridge_outbox
                WHERE sent_at IS NULL AND (lease_until IS NULL OR lease_until<now())
                ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 10)
              RETURNING event_id,event''').fetchall()

    def sent(self, event_id):
        with self.connect() as conn:
            conn.execute('UPDATE bridge_outbox SET sent_at=now(),lease_until=NULL WHERE event_id=%s', (event_id,))
