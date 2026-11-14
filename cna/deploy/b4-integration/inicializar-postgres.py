"""Alta de base y rol S1 desde una tarea administrativa efÃ­mera, sin tocar S2."""
import sys
from pathlib import Path
import psycopg
from psycopg import sql

STAGE = 'inicio'


def stage(name):
    global STAGE
    STAGE = name
    print('Paso:', name, flush=True)


def denied_audit_connection(exc):
    # Los errores durante libpq.connect pueden llegar sin SQLSTATE.
    # Solo aceptar el rechazo especÃ­fico de CONNECT, no fallos de DNS,
    # red o autenticaciÃ³n. Antes se comprobÃ³ acceso vÃ¡lido a bridge_db.
    if exc.sqlstate == '42501':
        return True
    message = str(exc).casefold()
    return (exc.sqlstate is None and 'permission denied for database' in message
            and '"audit_db"' in message)


def redact(message, secrets):
    for secret in secrets:
        if secret:
            message = message.replace(secret, '[oculto]')
    return message[:800]


def main():
    import json
    guard=json.loads(Path("/port-filter.json").read_text())
    assert guard == {"node":"cna-node1","source":"192.168.145.129","ports":[8081,8085]}, "Falta preparar el filtro de puertos de VM-2"
    admin = Path('/run/secrets/pg_admin_password').read_text().strip()
    password = Path('/run/secrets/bridge_db_password').read_text().strip()
    args = dict(host='postgres', user='postgres', password=admin, connect_timeout=5)
    stage('conexion administrativa a PostgreSQL')
    with psycopg.connect(**args, dbname='postgres', autocommit=True) as conn:
        stage('verificar o crear bridge_owner y bridge_db')
        role = conn.execute("SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname='bridge_owner'").fetchone()
        if role:
            if any(role):
                raise RuntimeError('El rol existente tiene privilegios administrativos inesperados')
        else:
            conn.execute(sql.SQL('CREATE ROLE bridge_owner LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE').format(sql.Literal(password)))
        database = conn.execute("SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname='bridge_db'").fetchone()
        if database:
            if database[0] != 'bridge_owner':
                raise RuntimeError('La base existente pertenece a otro rol')
        else:
            conn.execute('CREATE DATABASE bridge_db OWNER bridge_owner')
        conn.execute('REVOKE CONNECT ON DATABASE bridge_db FROM PUBLIC')
        conn.execute('GRANT CONNECT ON DATABASE bridge_db TO bridge_owner')
        assert conn.execute("SELECT has_database_privilege('audit_owner','bridge_db','CONNECT')").fetchone()[0] is False
        assert conn.execute("SELECT has_database_privilege('search_owner','bridge_db','CONNECT')").fetchone()[0] is False
        assert conn.execute("SELECT has_database_privilege('bridge_owner','search_db','CONNECT')").fetchone()[0] is False
        assert conn.execute("SELECT has_database_privilege('bridge_owner','audit_db','CONNECT')").fetchone()[0] is False
    stage('permisos del esquema bridge_db')
    with psycopg.connect(**args, dbname='bridge_db') as conn:
        conn.execute('REVOKE ALL ON SCHEMA public FROM PUBLIC')
        conn.execute('GRANT ALL ON SCHEMA public TO bridge_owner')
    stage('conexion valida como bridge_owner a bridge_db')
    with psycopg.connect(host='postgres', dbname='bridge_db', user='bridge_owner',password=password,connect_timeout=5) as conn:
        assert conn.execute('SELECT current_user').fetchone()[0] == 'bridge_owner'
    stage('rechazo esperado de bridge_owner al conectar a audit_db')
    try:
        with psycopg.connect(host='postgres', dbname='audit_db', user='bridge_owner',password=password,connect_timeout=5):
            raise RuntimeError('El rol S1 puede acceder a audit_db')
    except psycopg.Error as exc:
        if not denied_audit_connection(exc):
            raise
        print('Rechazo de CONNECT a audit_db confirmado.', flush=True)
    print('PASS: bridge_db y bridge_owner listos; rol sin privilegios administrativos.')
    print('Aislamiento: bridge_owner no conecta a audit_db; audit_owner no tiene CONNECT a bridge_db.')
    print('No se modificaron registros de auditoria ni datos de BookStack.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        values=[]
        for filename in ('pg_admin_password','bridge_db_password'):
            path=Path('/run/secrets')/filename
            if path.is_file():
                values.append(path.read_text().strip())
        print('FAIL inicializacion PostgreSQL:',type(exc).__name__,'; paso:',STAGE,
              '; SQLSTATE:',getattr(exc,'sqlstate',None),flush=True)
        print(redact(str(exc),values),flush=True)
        sys.exit(1)
