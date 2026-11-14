#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 && $(hostnamectl --static) == cna-node1 ]] || exit 1
container=$(docker ps --filter label=com.docker.swarm.service.name=cna_audit --format '{{.ID}}')
[[ -n $container && $container != *$'\n'* ]] || {
  echo 'Se necesita una tarea cna_audit ejecutandose; revisar docker ps.' >&2; exit 1;
}
printf 'Nodo: %s\n' "$(hostnamectl --static)"
docker exec "$container" python -m tools.evidence_audit
printf '\nPersistencia de los datos de auditoria fuera del contenedor: PostgreSQL con volumen.\n'
printf 'Esta prueba no sustituye la integracion de Webhooks reales (B4).\n'
