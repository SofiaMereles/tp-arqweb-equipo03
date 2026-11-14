#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 && $(hostnamectl --static) == cna-node1 ]] || {
  echo 'Ejecutar con sudo solo en VM-2 cna-node1.' >&2; exit 1;
}
cd "$(dirname "$(readlink -f "$0")")/../.."
source deploy/b2-audit/build.env
docker info >/dev/null
[[ $(docker info --format '{{.Swarm.LocalNodeState}}') == active ]] || exit 1
docker build --pull --build-arg BUILD_COMMIT="$BUILD_COMMIT" --tag "$AUDIT_IMAGE" -f services/audit-svc/Dockerfile .
printf '\nPruebas automatizadas dentro de la imagen Linux:\n'
docker run --rm --network none --read-only --tmpfs /tmp "$AUDIT_IMAGE" python -m unittest discover -s tests -v
# El volumen persiste fuera de los contenedores. Se inicializa su propietario antes de usar un proceso no root.
docker volume create cna_nats_data >/dev/null
docker run --rm --network none --user 0 --entrypoint /bin/sh -v cna_nats_data:/data \
  nats:2.11.8-alpine -ec 'chown 10001:10001 /data'
printf '\nImagen lista en VM-2: %s\n' "$AUDIT_IMAGE"
printf 'Siguiente paso: desplegar el stack desde VM-1. No se publicaron puertos.\n'
