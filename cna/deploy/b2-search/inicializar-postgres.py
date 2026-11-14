"""Alta de base y rol S1 desde una tarea administrativa efímera, sin tocar S2."""
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
    # Solo aceptar el rechazo específico de CONNECT, no fallos de DNS,
    # red o autenticación. Antes se comprobó acceso válido a search_db.
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
    admin = Path('/run/secrets/pg_admin_password').read_text().strip()
    password = Path('/run/secrets/search_db_password').read_text().strip()
    args = dict(host='postgres', user='postgres', password=admin, connect_timeout=5)
    stage('conexion administrativa a PostgreSQL')
    with psycopg.connect(**args, dbname='postgres', autocommit=True) as conn:
        stage('verificar o crear search_owner y search_db')
        role = conn.execute("SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname='search_owner'").fetchone()
        if role:
            if any(role):
                raise RuntimeError('El rol existente tiene privilegios administrativos inesperados')
        else:
            conn.execute(sql.SQL('CREATE ROLE search_owner LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE').format(sql.Literal(password)))
        database = conn.execute("SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname='search_db'").fetchone()
        if database:
            if database[0] != 'search_owner':
                raise RuntimeError('La base existente pertenece a otro rol')
        else:
            conn.execute('CREATE DATABASE search_db OWNER search_owner')
        conn.execute('REVOKE CONNECT ON DATABASE search_db FROM PUBLIC')
        conn.execute('GRANT CONNECT ON DATABASE search_db TO search_owner')
        assert conn.execute("SELECT has_database_privilege('audit_owner','search_db','CONNECT')").fetchone()[0] is False
        assert conn.execute("SELECT has_database_privilege('search_owner','audit_db','CONNECT')").fetchone()[0] is False
    stage('permisos del esquema search_db')
    with psycopg.connect(**args, dbname='search_db') as conn:
        conn.execute('REVOKE ALL ON SCHEMA public FROM PUBLIC')
        conn.execute('GRANT ALL ON SCHEMA public TO search_owner')
    stage('conexion valida como search_owner a search_db')
    with psycopg.connect(host='postgres', dbname='search_db', user='search_owner',password=password,connect_timeout=5) as conn:
        assert conn.execute('SELECT current_user').fetchone()[0] == 'search_owner'
    stage('rechazo esperado de search_owner al conectar a audit_db')
    try:
        with psycopg.connect(host='postgres', dbname='audit_db', user='search_owner',password=password,connect_timeout=5):
            raise RuntimeError('El rol S1 puede acceder a audit_db')
    except psycopg.Error as exc:
        if not denied_audit_connection(exc):
            raise
        print('Rechazo de CONNECT a audit_db confirmado.', flush=True)
    print('PASS: search_db y search_owner listos; rol sin privilegios administrativos.')
    print('Aislamiento: search_owner no conecta a audit_db; audit_owner no tiene CONNECT a search_db.')
    print('No se modificaron registros de auditoria ni datos de BookStack.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        values=[]
        for filename in ('pg_admin_password','search_db_password'):
            path=Path('/run/secrets')/filename
            if path.is_file():
                values.append(path.read_text().strip())
        print('FAIL inicializacion PostgreSQL:',type(exc).__name__,'; paso:',STAGE,
              '; SQLSTATE:',getattr(exc,'sqlstate',None),flush=True)
        print(redact(str(exc),values),flush=True)
        sys.exit(1)
