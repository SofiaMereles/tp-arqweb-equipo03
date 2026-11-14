#!/usr/bin/env bash
# Docker Engine y Compose desde el repositorio oficial; sin publicar puertos.
set -euo pipefail
[[ ${EUID} -eq 0 ]] || { echo 'Ejecutar con sudo bash.' >&2; exit 1; }
case $(hostnamectl --static) in
    cna-node1|arqwebserver) ;;
    *) echo 'Nodo inesperado: revisar antes de instalar.' >&2; exit 1 ;;
esac
. /etc/os-release
[[ "$ID" == ubuntu ]] || { echo 'Este procedimiento requiere Ubuntu.' >&2; exit 1; }
suite=${UBUNTU_CODENAME:-${VERSION_CODENAME:-}}
case "$suite" in
    jammy|noble|resolute|stonking) ;;
    *) echo "Revisar soporte oficial para suite: $suite" >&2; exit 1 ;;
esac
conflicts=()
for pkg in docker.io docker-compose docker-compose-v2 docker-doc docker-buildx podman-docker containerd runc; do
    if [[ $(dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null || true) == 'install ok installed' ]]; then
        conflicts+=("$pkg")
    fi
done
if (( ${#conflicts[@]} )); then
    printf 'Paquetes a revisar antes de instalar: %s\n' "${conflicts[*]}" >&2
    echo 'No se desinstala nada automaticamente.' >&2
    exit 1
fi
if [[ -e /etc/apt/sources.list.d/docker.sources || -e /etc/apt/sources.list.d/docker.list ]]; then
    echo 'Ya existe una fuente Docker. Revisar su contenido antes de repetir.' >&2
    exit 1
fi
printf 'Nodo: %s\nUbuntu: %s\nSuite: %s\n' "$(hostnamectl --static)" "$VERSION_ID" "$suite"
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl --connect-timeout 10 --max-time 60 -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
arch=$(dpkg --print-architecture)
cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $suite
Components: stable
Architectures: $arch
Signed-By: /etc/apt/keyrings/docker.asc
EOF
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
printf '\n--- Verificacion de instalacion ---\n'
hostnamectl --static
systemctl is-active docker
docker version
docker compose version
docker info --format 'Nombre={{.Name}}; Version={{.ServerVersion}}; Swarm={{.Swarm.LocalNodeState}}'
dpkg-query -W -f='${Package}=${Version}\n' docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
printf '\nEngine y Compose instalados; no se formo Swarm ni se publicaron puertos de contenedores.\n'
