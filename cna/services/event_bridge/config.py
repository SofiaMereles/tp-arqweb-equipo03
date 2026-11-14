from audit_svc.config import Settings as BaseSettings, value


class Settings(BaseSettings):
    def __init__(self):
        super().__init__()
        self.pg_database = value('PGDATABASE', 'bridge_db')
        self.pg_user = value('PGUSER', 'bridge_owner')
        self.webhook_token = value('WEBHOOK_TOKEN')
        self.max_webhook_bytes = int(value('MAX_WEBHOOK_BYTES', '2097152'))
