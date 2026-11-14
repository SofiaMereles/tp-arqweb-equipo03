#!/usr/bin/env bash
set -euo pipefail
umask 077
[[ $EUID -eq 0 && $(hostnamectl --static) == arqwebserver ]] || {
  echo 'Ejecutar con sudo solo en VM-1 arqwebserver.' >&2; exit 1;
}
cd "$(dirname "$(readlink -f "$0")")"
source build.env
export AUDIT_IMAGE
[[ $(docker info --format '{{.Swarm.ControlAvailable}}') == true ]] || exit 1
[[ $(docker node inspect cna-node1 --format '{{.Status.State}}') == ready ]] || {
  echo 'VM-2 no esta Ready.' >&2; exit 1;
}
for secret in pg_admin_password audit_db_password audit_api_key nats_token; do
  if ! docker secret inspect "cna_$secret" >/dev/null 2>&1; then
    openssl rand -hex 32 | docker secret create "cna_$secret" - >/dev/null
  fi
done
if ! docker config inspect cna_nats_start_v2 >/dev/null 2>&1; then
  docker config create cna_nats_start_v2 nats-start.sh >/dev/null
fi
docker stack deploy --resolve-image never -c stack.yaml cna
printf '\nStack de auditoria enviado al cluster. No se modifico BookStack ni Nginx.\n'
docker stack services cna
printf '\nEsperar que postgres, nats y audit indiquen 1/1; las dependencias pueden tardar en iniciar.\n'
