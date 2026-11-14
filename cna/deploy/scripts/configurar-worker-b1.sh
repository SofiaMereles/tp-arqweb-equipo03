#!/usr/bin/env bash
# B1: UFW del worker; no inicia servicios ni cambia datos de BookStack.
set -euo pipefail
export LC_ALL=C
[[ ${EUID} -eq 0 && $(hostnamectl --static) == cna-node1 ]] || {
    echo 'Ejecutar con sudo solo en cna-node1.' >&2; exit 1;
}
[[ $(cat /sys/class/net/ens37/address) == 00:0c:29:7f:f2:1a ]] || {
    echo 'MAC inesperada; revisar identidad antes de cambiar firewall.' >&2; exit 1;
}
ip -4 -o addr show dev ens37 | grep -q '192.168.145.130/24' || {
    echo 'No coincide la IP privada prevista del worker.' >&2; exit 1;
}
command -v ufw >/dev/null
[[ $(docker info --format '{{.Name}}') == cna-node1 ]] || exit 1
# Permitir administracion antes de retirar las aperturas heredadas.
ufw allow in on ens37 from 192.168.145.1 to 192.168.145.130 port 22 proto tcp
ufw allow in on ens37 from 192.168.145.129 to 192.168.145.130 port 22 proto tcp
ufw allow in on ens37 from 192.168.145.129 to 192.168.145.130 port 7946 proto tcp
ufw allow in on ens37 from 192.168.145.129 to 192.168.145.130 port 7946 proto udp
ufw allow in on ens37 from 192.168.145.129 to 192.168.145.130 port 4789 proto udp
for port in 22 80 443; do
    if ufw status verbose | grep -Eq "^${port}/tcp[[:space:]].*ALLOW IN[[:space:]]+Anywhere"; then
        ufw --force delete allow "$port/tcp"
    fi
done
ufw default deny incoming
ufw default allow outgoing
ufw --force enable
install -d -m 700 -o arqweb -g "$(id -gn arqweb)" /home/arqweb/.cna-private
printf '\nNodo: %s\n' "$(hostnamectl --static)"
ufw status verbose
printf '\nSSH permitido desde Windows 192.168.145.1 y VM-1 192.168.145.129.\n'
printf 'Swarm permitido solo desde VM-1; worker aun no unido al cluster.\n'
printf 'Reglas de puertos publicados por Docker se verificaran con el despliegue.\n'
