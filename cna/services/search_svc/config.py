from pathlib import Path
from audit_svc.config import Settings as BaseSettings, value


class Settings(BaseSettings):
    def __init__(self):
        super().__init__()
        self.pg_database = value('PGDATABASE', 'search_db')
        self.pg_user = value('PGUSER', 'search_owner')
        self.bookstack_url = value('BOOKSTACK_URL', 'https://bookstack.local').rstrip('/')
        self.bookstack_token = value('BOOKSTACK_TOKEN')
        self.bookstack_ca = Path(value('BOOKSTACK_CA_FILE'))
        self.api_timeout = float(value('BOOKSTACK_TIMEOUT', '4'))
        self.page_size = int(value('BOOKSTACK_PAGE_SIZE', '100'))
        self.reconcile_seconds = float(value('RECONCILE_SECONDS', '60'))
        if not 1 <= self.page_size <= 100 or self.reconcile_seconds < 10:
            raise ValueError('Paginacion o intervalo invalido')
