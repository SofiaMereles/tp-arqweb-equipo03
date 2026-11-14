#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 && $(hostnamectl --static) == cna-node1 ]] || {
  echo 'Ejecutar con sudo solo en VM-2 cna-node1.' >&2; exit 1;
}
cd "$(dirname "$(readlink -f "$0")")/../.."
source deploy/b4-integration/build.env
docker build --pull --build-arg BUILD_COMMIT="$BUILD_COMMIT" --tag "$BRIDGE_IMAGE" -f services/event-bridge/Dockerfile .
docker run --rm --network none --read-only --tmpfs /tmp "$BRIDGE_IMAGE" python -m unittest discover -s tests -v
printf '\nImagen del puente lista en VM-2: %s\n' "$BRIDGE_IMAGE"
printf 'Pendiente: filtro de puertos, despliegue y Webhooks reales.\n'
