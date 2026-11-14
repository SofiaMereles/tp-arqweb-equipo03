#!/usr/bin/env bash
set -euo pipefail
umask 077
[[ $EUID -eq 0 && $(hostnamectl --static) == arqwebserver ]] || {
  echo 'Ejecutar con sudo solo en VM-1 arqwebserver.' >&2; exit 1;
}
cd "$(dirname "$(readlink -f "$0")")"
source build.env
[[ $(docker node inspect cna-node1 --format '{{.Status.State}}') == ready ]] || exit 1
for required in cna_nats_token cna_pg_admin_password; do
  docker secret inspect "$required" >/dev/null
done
private=/home/arqweb/.cna-private
install -d -o arqweb -g arqweb -m 700 "$private"
for name in cna_bridge_db_password cna_bridge_webhook_token; do
  if ! docker secret inspect "$name" >/dev/null 2>&1; then
    if [[ $name == cna_bridge_webhook_token ]]; then
      openssl rand -hex 32 > "$private/bridge-webhook-token"
      chmod 600 "$private/bridge-webhook-token"
      chown arqweb:arqweb "$private/bridge-webhook-token"
      docker secret create "$name" "$private/bridge-webhook-token" >/dev/null
    else
      openssl rand -hex 32 | docker secret create "$name" - >/dev/null
    fi
  fi
done
[[ -f "$private/bridge-webhook-token" ]] || {
  echo 'El secreto existe pero falta su copia privada para configurar BookStack; revisar sin rotarlo.' >&2; exit 1;
}
printf 'http://192.168.145.130:8085/internal/webhooks/bookstack?token=%s\n' "$(cat "$private/bridge-webhook-token")" > "$private/bookstack-webhook-url.txt"
chmod 600 "$private/bookstack-webhook-url.txt"
chown arqweb:arqweb "$private/bookstack-webhook-url.txt"
hash=$(sha256sum inicializar-postgres.py | cut -c1-12)
config="cna_bridge_init_$hash"
if ! docker config inspect "$config" >/dev/null 2>&1; then
  docker config create "$config" inicializar-postgres.py >/dev/null
fi
job=cna_bridge_db_init
if docker service inspect "$job" >/dev/null 2>&1; then
  docker service rm "$job" >/dev/null
fi
docker service create --detach=true --no-resolve-image --name "$job" \
  --constraint node.hostname==cna-node1 --restart-condition none --network cna_backend \
  --secret source=cna_pg_admin_password,target=pg_admin_password \
  --secret source=cna_bridge_db_password,target=bridge_db_password \
  --mount type=bind,source=/var/lib/cna-port-filter/ready.json,target=/port-filter.json,readonly \
  --config "source=$config,target=/initialize.py,mode=0444" \
  --read-only --limit-memory 96M --limit-cpu 0.25 \
  --entrypoint python "$BRIDGE_IMAGE" -u /initialize.py >/dev/null
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
[[ $completed == true ]] || { echo 'Inicializacion del puente pendiente; revisar su tarea.' >&2; exit 1; }
if docker service inspect cna_bridge >/dev/null 2>&1; then
  docker service update --detach=true --no-resolve-image --image "$BRIDGE_IMAGE" cna_bridge
else
  docker service create --detach=true --no-resolve-image --name cna_bridge \
    --label com.docker.stack.namespace=cna --constraint node.hostname==cna-node1 \
    --restart-condition any --network cna_backend \
    --publish published=8085,target=8000,protocol=tcp,mode=host \
    --secret source=cna_bridge_db_password,target=bridge_db_password \
    --secret source=cna_bridge_webhook_token,target=webhook_token \
    --secret source=cna_nats_token,target=nats_token \
    --env SERVICE_API_KEY_FILE=/run/secrets/webhook_token \
    --env WEBHOOK_TOKEN_FILE=/run/secrets/webhook_token \
    --env PGHOST=postgres --env PGDATABASE=bridge_db --env PGUSER=bridge_owner \
    --env PGPASSWORD_FILE=/run/secrets/bridge_db_password \
    --env NATS_URL=nats://nats:4222 --env NATS_TOKEN_FILE=/run/secrets/nats_token \
    --read-only --mount type=tmpfs,destination=/tmp,tmpfs-size=8388608 \
    --limit-memory 128M --limit-cpu 0.25 "$BRIDGE_IMAGE" >/dev/null
fi
if ! docker service inspect cna_search --format '{{range .Endpoint.Spec.Ports}}{{println .PublishedPort}}{{end}}' | grep -Fxq 8081; then
  docker service update --detach=true --publish-add published=8081,target=8000,protocol=tcp,mode=host cna_search
fi
printf '\nPuente y busqueda publicados para acceso privado desde VM-1.\n'
docker stack services cna
printf 'URL del Webhook en archivo privado: %s/bookstack-webhook-url.txt\n' "$private"
printf 'No incluir el contenido de ese archivo en capturas ni en el repositorio.\n'
