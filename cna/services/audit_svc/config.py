import os
from pathlib import Path


def value(name, default=None):
    """Un secreto puede indicarse por ruta mediante NAME_FILE."""
    path = os.environ.get(name + '_FILE')
    result = Path(path).read_text().strip() if path else os.environ.get(name, default)
    if result is None or result == '':
        raise ValueError(f'Falta configurar {name} o {name}_FILE')
    return result


class Settings:
    def __init__(self):
        self.api_key = value('SERVICE_API_KEY')
        self.pg_host = value('PGHOST', 'postgres')
        self.pg_port = int(value('PGPORT', '5432'))
        self.pg_database = value('PGDATABASE', 'audit_db')
        self.pg_user = value('PGUSER', 'audit_owner')
        self.pg_password = value('PGPASSWORD')
        self.nats_url = value('NATS_URL', 'nats://nats:4222')
        self.nats_token = value('NATS_TOKEN')
        self.max_attempts = int(value('MAX_EVENT_ATTEMPTS', '5'))
        if self.max_attempts < 1:
            raise ValueError('MAX_EVENT_ATTEMPTS debe ser positivo')
        self.contract_dir = Path(value('CONTRACT_DIR', str(Path(__file__).resolve().parents[2] / 'contracts')))

    def connection_args(self):
        return dict(host=self.pg_host, port=self.pg_port, dbname=self.pg_database,
                    user=self.pg_user, password=self.pg_password, connect_timeout=3)
