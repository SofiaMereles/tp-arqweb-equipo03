#!/usr/bin/env bash
set -euo pipefail
umask 077
[[ $EUID -eq 0 && $(hostnamectl --static) == arqwebserver ]] || {
  echo 'Ejecutar con sudo solo en VM-1 arqwebserver.' >&2; exit 1;
}
cd "$(dirname "$(readlink -f "$0")")"
source build.env
[[ $(docker node inspect cna-node1 --format '{{.Status.State}}') == ready ]] || {
  echo 'Encender VM-2 y esperar Ready.' >&2; exit 1;
}
for required in cna_bookstack_api_token cna_nats_token cna_pg_admin_password; do
  docker secret inspect "$required" >/dev/null
done
docker config inspect cna_bookstack_ca_v1 >/dev/null
for secret in cna_search_db_password cna_search_api_key; do
  if ! docker secret inspect "$secret" >/dev/null 2>&1; then
    openssl rand -hex 32 | docker secret create "$secret" - >/dev/null
  fi
done
# Tarea de migración separada: no se reinicia PostgreSQL ni se entrega su
# credencial administrativa al contenedor de búsqueda.
hash=$(sha256sum inicializar-postgres.py | cut -c1-12)
config="cna_search_init_$hash"
if ! docker config inspect "$config" >/dev/null 2>&1; then
  docker config create "$config" inicializar-postgres.py >/dev/null
fi
job=cna_search_db_init
if docker service inspect "$job" >/dev/null 2>&1; then
  docker service rm "$job" >/dev/null
fi
docker service create --detach=true --no-resolve-image --name "$job" \
  --constraint node.hostname==cna-node1 --restart-condition none --network cna_backend \
  --secret source=cna_pg_admin_password,target=pg_admin_password \
  --secret source=cna_search_db_password,target=search_db_password \
  --config "source=$config,target=/initialize.py,mode=0444" \
  --read-only --limit-memory 96M --limit-cpu 0.25 \
  --entrypoint python "$SEARCH_IMAGE" -u /initialize.py >/dev/null
completed=false
for ((attempt=0; attempt<45; attempt++)); do
  task=$(docker service ps "$job" --no-trunc --format '{{.ID}}' | head -n 1)
  if [[ -n $task ]]; then
    state=$(docker inspect --type task "$task" --format '{{.Status.State}}')
    case $state in
      complete) completed=true; break ;;
      failed|rejected)
        docker service logs --raw "$job" || true
        docker service ps --no-trunc "$job"
        exit 1 ;;
    esac
  fi
  sleep 1
done
docker service logs --raw "$job" || true
[[ $completed == true ]] || { echo 'Inicializacion todavia no completada; revisar su tarea.' >&2; exit 1; }
if docker service inspect cna_search >/dev/null 2>&1; then
  docker service update --detach=true --no-resolve-image --image "$SEARCH_IMAGE" cna_search
else
  docker service create --detach=true --no-resolve-image --name cna_search \
    --label com.docker.stack.namespace=cna --constraint node.hostname==cna-node1 \
    --restart-condition any --network cna_backend --host bookstack.local:192.168.145.129 \
    --secret source=cna_search_db_password,target=search_db_password \
    --secret source=cna_search_api_key,target=search_api_key \
    --secret source=cna_nats_token,target=nats_token \
    --secret source=cna_bookstack_api_token,target=bookstack_api_token \
    --config source=cna_bookstack_ca_v1,target=/etc/ssl/cna-bookstack.crt,mode=0444 \
    --env SERVICE_API_KEY_FILE=/run/secrets/search_api_key \
    --env PGHOST=postgres --env PGDATABASE=search_db --env PGUSER=search_owner \
    --env PGPASSWORD_FILE=/run/secrets/search_db_password \
    --env NATS_URL=nats://nats:4222 --env NATS_TOKEN_FILE=/run/secrets/nats_token \
    --env BOOKSTACK_URL=https://bookstack.local \
    --env BOOKSTACK_TOKEN_FILE=/run/secrets/bookstack_api_token \
    --env BOOKSTACK_CA_FILE=/etc/ssl/cna-bookstack.crt \
    --env BOOKSTACK_PAGE_SIZE=100 --env RECONCILE_SECONDS=60 \
    --read-only --mount type=tmpfs,destination=/tmp,tmpfs-size=8388608 \
    --limit-memory 192M --limit-cpu 0.50 "$SEARCH_IMAGE" >/dev/null
fi
printf '\nS1 enviado a VM-2; no se publicaron puertos externos.\n'
docker stack services cna
printf 'Esperar a que cna_search quede 1/1 y comprobar su readyz e indice inicial.\n'
