#!/bin/sh
set -eu
export AUDIT_DB_PASSWORD="$(cat /run/secrets/audit_db_password)"
psql --username postgres --dbname postgres --set ON_ERROR_STOP=1 <<'SQL'
\getenv audit_password AUDIT_DB_PASSWORD
SELECT format('CREATE ROLE audit_owner LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE', :'audit_password') \gexec
CREATE DATABASE audit_db OWNER audit_owner;
REVOKE CONNECT ON DATABASE audit_db FROM PUBLIC;
GRANT CONNECT ON DATABASE audit_db TO audit_owner;
\connect audit_db
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO audit_owner;
SQL
unset AUDIT_DB_PASSWORD
