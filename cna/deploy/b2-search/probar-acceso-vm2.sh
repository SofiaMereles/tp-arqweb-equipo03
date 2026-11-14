#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 && $(hostnamectl --static) == arqwebserver ]] || {
  echo 'Ejecutar con sudo desde VM-1 arqwebserver; Swarm ejecutara la prueba en VM-2.' >&2; exit 1;
}
cd "$(dirname "$(readlink -f "$0")")"
[[ $(docker node inspect cna-node1 --format '{{.Status.State}}') == ready ]] || {
  echo 'Encender VM-2 cna-node1 y esperar a que el nodo quede Ready.' >&2; exit 1;
}
docker secret inspect cna_bookstack_api_token >/dev/null
docker config inspect cna_bookstack_ca_v1 >/dev/null
job=cna_bookstack_probe
if docker service inspect "$job" >/dev/null 2>&1; then
  echo 'La tarea de prueba ya existe. Consultar docker service logs cna_bookstack_probe antes de repetir.' >&2
  exit 1
fi
image=$(docker service inspect cna_audit --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}')
hash=$(sha256sum probar-bookstack.py | cut -c1-12)
config="cna_bookstack_probe_$hash"
if ! docker config inspect "$config" >/dev/null 2>&1; then
  docker config create "$config" probar-bookstack.py >/dev/null
fi
docker service create --detach=true --no-resolve-image --name "$job" \
  --constraint node.hostname==cna-node1 --restart-condition none \
  --network cna_backend --host bookstack.local:192.168.145.129 \
  --secret source=cna_bookstack_api_token,target=bookstack_api_token \
  --config source=cna_bookstack_ca_v1,target=/etc/ssl/cna-bookstack.crt,mode=0444 \
  --config "source=$config,target=/probe-bookstack.py,mode=0444" \
  --env BOOKSTACK_URL=https://bookstack.local \
  --env BOOKSTACK_TOKEN_FILE=/run/secrets/bookstack_api_token \
  --env BOOKSTACK_CA_FILE=/etc/ssl/cna-bookstack.crt \
  --env 'EXPECTED_BOOK=Pruebas CNA' --env 'EXPECTED_PAGE=Prueba de búsqueda CNA' \
  --read-only --limit-memory 96M --limit-cpu 0.25 \
  --entrypoint python "$image" -u /probe-bookstack.py >/dev/null
printf 'Prueba de lectura enviada a VM-2. Esperando resultado...\n'
for ((attempt=0; attempt<45; attempt++)); do
  task=$(docker service ps "$job" --no-trunc --format '{{.ID}}' | head -n 1)
  if [[ -n $task ]]; then
    state=$(docker inspect --type task "$task" --format '{{.Status.State}}')
    case $state in
      complete)
        docker service logs --raw "$job"
        printf '\nPrueba completada. Conservar la salida como evidencia.\n'
        exit 0 ;;
      failed|rejected)
        docker service logs --raw "$job" || true
        docker service ps --no-trunc "$job"
        exit 1 ;;
    esac
  fi
  sleep 1
done
docker service logs --raw "$job" || true
docker service ps --no-trunc "$job"
echo 'La tarea sigue pendiente. No repetir la creacion antes de revisar el estado.' >&2
exit 1
