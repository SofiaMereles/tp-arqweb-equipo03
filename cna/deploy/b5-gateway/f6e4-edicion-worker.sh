#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 && $(hostnamectl --static) == cna-node1 ]] || {
  echo 'Ejecutar con sudo solo en VM-2 cna-node1.' >&2; exit 1;
}
cd "$(dirname "$(readlink -f "$0")")"
container=$(docker ps --filter label=com.docker.swarm.service.name=cna_search -q)
[[ -n $container && $container != *$'\n'* ]] || exit 1
printf 'Nodo: %s\n' "$(hostnamectl --static)"
docker exec -i "$container" python -u - "${1:-3}" < f6e4-edicion.py
