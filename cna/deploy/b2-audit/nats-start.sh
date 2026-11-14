#!/bin/sh
set -eu
token=$(cat "${NATS_TOKEN_FILE:-/run/secrets/nats_token}")
case "$token" in
  ''|*[!0-9a-fA-F]*) echo 'Formato inesperado del secreto NATS.' >&2; exit 1 ;;
esac
# El parser de NATS vuelve a analizar el valor del entorno como configuración.
# printf incluye comillas literales, conservando intacto el secreto original.
NATS_TOKEN=$(printf '"%s"' "$token")
export NATS_TOKEN
unset token
exec nats-server -c /etc/nats/nats.conf
