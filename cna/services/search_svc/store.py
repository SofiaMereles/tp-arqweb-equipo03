from datetime import datetime, timezone
import psycopg
from psycopg.rows import dict_row
from .documents import clock, document

DDL = '''
CREATE TABLE IF NOT EXISTS search_documents (
 entity_type text NOT NULL CHECK (entity_type IN ('book','page')),
 entity_id bigint NOT NULL,
 title text NOT NULL, body text NOT NULL, url text NOT NULL,
 book_id bigint NOT NULL, book_title text NOT NULL,
 source_at timestamptz NOT NULL,
 terms tsvector GENERATED ALWAYS AS (
   setweight(to_tsvector('spanish', title),'A') ||
   setweight(to_tsvector('spanish', body),'B') ||
   setweight(to_tsvector('spanish', book_title),'C')) STORED,
 PRIMARY KEY(entity_type, entity_id)
);
CREATE INDEX IF NOT EXISTS search_terms_gin ON search_documents USING GIN(terms);
CREATE TABLE IF NOT EXISTS search_versions (
 entity_type text NOT NULL, entity_id bigint NOT NULL, clock timestamptz NOT NULL,
 PRIMARY KEY(entity_type, entity_id)
);
CREATE TABLE IF NOT EXISTS search_events (event_id uuid PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS search_state (id integer PRIMARY KEY CHECK(id=1), reconciled_at timestamptz NOT NULL);
'''


class Store:
    def __init__(self, settings, reader):
        self.settings, self.reader = settings, reader

    def connect(self):
        return psycopg.connect(**self.settings.connection_args(), row_factory=dict_row)

    def initialize(self):
        with self.connect() as conn:
            conn.execute(DDL)

    @staticmethod
    def lock(conn):
        # Serializa carga inicial, reconciliacion y eventos incluso entre procesos.
        conn.execute('SELECT pg_advisory_xact_lock(81001)')

    @staticmethod
    def put(conn, doc, state_clock=None):
        columns = ('entity_type', 'entity_id', 'title', 'body', 'url', 'book_id', 'book_title', 'source_at')
        conn.execute('''INSERT INTO search_documents
          (entity_type,entity_id,title,body,url,book_id,book_title,source_at)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
          ON CONFLICT(entity_type,entity_id) DO UPDATE SET
          title=EXCLUDED.title, body=EXCLUDED.body, url=EXCLUDED.url,
          book_id=EXCLUDED.book_id, book_title=EXCLUDED.book_title, source_at=EXCLUDED.source_at''',
          tuple(doc[key] for key in columns))
        conn.execute('''INSERT INTO search_versions(entity_type,entity_id,clock) VALUES (%s,%s,%s)
          ON CONFLICT(entity_type,entity_id) DO UPDATE SET clock=GREATEST(search_versions.clock,EXCLUDED.clock)''',
          (doc['entity_type'], doc['entity_id'], max(doc['source_at'], state_clock or doc['source_at'])))

    def reconcile(self, request_id):
        with self.connect() as conn:
            self.lock(conn)
            # El snapshot se reemplaza solo al completar TODAS las llamadas REST.
            # Si falla una pagina, el rollback conserva el indice anterior.
            books, docs = {}, []
            for row in self.reader.listing('books', request_id):
                book = self.reader.detail('book', row['id'], request_id)
                if book:
                    books[book['id']] = book
                    docs.append(document('book', book, book, self.settings.bookstack_url))
            for row in self.reader.listing('pages', request_id):
                page = self.reader.detail('page', row['id'], request_id)
                if not page:
                    continue
                book = books.get(page['book_id'])
                if book:
                    docs.append(document('page', page, book, self.settings.bookstack_url))
            conn.execute('DELETE FROM search_documents')
            for doc in docs:
                self.put(conn, doc)
            conn.execute('''INSERT INTO search_state(id,reconciled_at) VALUES (1,now())
              ON CONFLICT(id) DO UPDATE SET reconciled_at=EXCLUDED.reconciled_at''')
        return dict(books=len(books), pages=sum(d['entity_type'] == 'page' for d in docs))

    def record(self, event):
        entity_id, at = event['payload']['page_id'], clock(event['occurred_at'])
        with self.connect() as conn:
            self.lock(conn)
            inserted = conn.execute('INSERT INTO search_events(event_id) VALUES (%s) ON CONFLICT DO NOTHING RETURNING event_id',
                                    (event['event_id'],)).fetchone()
            if not inserted:
                return False
            version = conn.execute("SELECT clock FROM search_versions WHERE entity_type='page' AND entity_id=%s", (entity_id,)).fetchone()
            if version and version['clock'] > at:
                return False
            page = None if event['type'] == 'bookstack.page.deleted' else self.reader.detail('page', entity_id, event['request_id'])
            book = self.reader.detail('book', page['book_id'], event['request_id']) if page else None
            if page and book:
                self.put(conn, document('book', book, book, self.settings.bookstack_url))
                self.put(conn, document('page', page, book, self.settings.bookstack_url), at)
            else:
                conn.execute("DELETE FROM search_documents WHERE entity_type='page' AND entity_id=%s", (entity_id,))
                conn.execute('''INSERT INTO search_versions(entity_type,entity_id,clock) VALUES ('page',%s,%s)
                  ON CONFLICT(entity_type,entity_id) DO UPDATE SET clock=GREATEST(search_versions.clock,EXCLUDED.clock)''',
                  (entity_id, at))
        return True

    def ping(self):
        with self.connect() as conn:
            if not conn.execute('SELECT reconciled_at FROM search_state WHERE id=1').fetchone():
                raise RuntimeError('Carga inicial pendiente')

    def search(self, query, entity_type):
        extra = ' AND entity_type=%s' if entity_type else ''
        # Parametros en SQL; tsquery se construye como dato, no como SQL ejecutable.
        sql = '''WITH q AS (SELECT websearch_to_tsquery('spanish', %s) AS terms)
          SELECT d.*, ts_rank_cd(d.terms,q.terms)::double precision AS score,
          ts_headline('spanish',title,q.terms,'StartSel=\ue000,StopSel=\ue001,HighlightAll=true') AS highlight_title,
          ts_headline('spanish',body,q.terms,'StartSel=\ue000,StopSel=\ue001,MaxWords=40,MinWords=10') AS highlight_body,
          ts_headline('spanish',book_title,q.terms,'StartSel=\ue000,StopSel=\ue001,HighlightAll=true') AS highlight_book_title
          FROM search_documents d CROSS JOIN q WHERE d.terms @@ q.terms''' + extra + '''
          ORDER BY score DESC, entity_type, entity_id'''
        with self.connect() as conn:
            return conn.execute(sql, (query, entity_type) if entity_type else (query,)).fetchall()
