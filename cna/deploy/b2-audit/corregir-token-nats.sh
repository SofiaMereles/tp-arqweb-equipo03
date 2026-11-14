#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 && $(hostnamectl --static) == arqwebserver ]] || {
  echo 'Ejecutar con sudo solo en VM-1 arqwebserver.' >&2; exit 1;
}
cd "$(dirname "$(readlink -f "$0")")"
[[ -f nats-start.sh ]] || { echo 'Falta copiar nats-start.sh junto a este script.' >&2; exit 1; }
# Se monta un script para evitar las distintas capas de interpretación de --args.
config=cna_nats_start_v2
if ! docker config inspect "$config" >/dev/null 2>&1; then
  docker config create "$config" nats-start.sh >/dev/null
fi
options=()
if ! docker service inspect cna_nats --format '{{range .Spec.TaskTemplate.ContainerSpec.Configs}}{{println .ConfigName}}{{end}}' | grep -Fxq "$config"; then
  options+=(--config-add "source=$config,target=/etc/nats/start.sh,mode=0555")
fi
docker service update --detach=true --entrypoint /bin/sh --args /etc/nats/start.sh "${options[@]}" cna_nats
printf '\nSe actualizo solo el arranque de NATS; secretos y volumen se conservaron.\n'
docker stack services cna
