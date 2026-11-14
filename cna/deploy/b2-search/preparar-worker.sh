#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 && $(hostnamectl --static) == cna-node1 ]] || {
  echo 'Ejecutar con sudo solo en VM-2 cna-node1.' >&2; exit 1;
}
cd "$(dirname "$(readlink -f "$0")")/../.."
source deploy/b2-search/build.env
docker build --pull --build-arg BUILD_COMMIT="$BUILD_COMMIT" --tag "$SEARCH_IMAGE" -f services/search-svc/Dockerfile .
docker run --rm --network none --read-only --tmpfs /tmp "$SEARCH_IMAGE" python -m unittest discover -s tests -v
printf '\nImagen S1 lista en VM-2: %s\n' "$SEARCH_IMAGE"
printf 'Pruebas Linux completadas; pendiente despliegue desde VM-1.\n'
