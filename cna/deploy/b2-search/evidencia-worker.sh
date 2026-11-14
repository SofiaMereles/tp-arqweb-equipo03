#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 && $(hostnamectl --static) == cna-node1 ]] || exit 1
container=$(docker ps --filter label=com.docker.swarm.service.name=cna_search -q)
[[ -n $container && $container != *$'\n'* ]] || {
  echo 'Se necesita una tarea cna_search ejecutandose.' >&2; exit 1;
}
printf 'Nodo: %s\n' "$(hostnamectl --static)"
docker exec "$container" python -m tools.evidence_search_initial "${1:-3}"
