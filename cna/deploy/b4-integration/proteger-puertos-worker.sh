#!/usr/bin/env bash
# Filtro adicional a UFW para los puertos publicados por Docker.
set -euo pipefail
[[ $EUID -eq 0 && $(hostnamectl --static) == cna-node1 ]] || {
  echo 'Ejecutar con sudo solo en VM-2 cna-node1.' >&2; exit 1;
}
if [[ ${1:-} != --apply ]]; then
  [[ $(docker network inspect cna_backend --format '{{.EnableIPv6}}') == false ]] || {
    echo 'La red tiene IPv6: revisar su filtrado antes de publicar servicios.' >&2; exit 1;
  }
  iptables -S DOCKER-USER >/dev/null || {
    echo 'No existe DOCKER-USER; revisar el backend de firewall de Docker antes de continuar.' >&2; exit 1;
  }
  install -m 755 "$(readlink -f "$0")" /usr/local/sbin/cna-port-filter
  cat > /etc/systemd/system/cna-port-filter.service <<'UNIT'
[Unit]
Description=Filtrado privado de puertos CNA publicados por Docker
Wants=network-online.target
After=network-online.target ufw.service
Before=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/cna-port-filter --apply
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
UNIT
  systemctl daemon-reload
  systemctl enable cna-port-filter.service >/dev/null
  ufw allow in on ens37 from 192.168.145.129 to 192.168.145.130 port 8081 proto tcp
  ufw allow in on ens37 from 192.168.145.129 to 192.168.145.130 port 8085 proto tcp
fi
for chain in DOCKER-USER CNA-PORTS; do
  if ! iptables -S "$chain" >/dev/null 2>&1; then
    iptables -N "$chain"
  fi
done
for port in 8081 8085; do
  allow=(-i ens37 -s 192.168.145.129 -p tcp -m conntrack --ctdir ORIGINAL --ctorigdstport "$port" -j ACCEPT)
  deny=(-p tcp -m conntrack --ctdir ORIGINAL --ctorigdstport "$port" -j DROP)
  iptables -C CNA-PORTS "${allow[@]}" 2>/dev/null || iptables -A CNA-PORTS "${allow[@]}"
  iptables -C CNA-PORTS "${deny[@]}" 2>/dev/null || iptables -A CNA-PORTS "${deny[@]}"
done
iptables -C DOCKER-USER -j CNA-PORTS 2>/dev/null || iptables -I DOCKER-USER 1 -j CNA-PORTS
install -d -m 755 /var/lib/cna-port-filter
printf '{"node":"cna-node1","source":"192.168.145.129","ports":[8081,8085]}\n' > /var/lib/cna-port-filter/ready.json
chmod 644 /var/lib/cna-port-filter/ready.json
printf '\nFiltro configurado: puertos 8081/8085 solo desde VM-1 por ens37.\n'
iptables -S CNA-PORTS
printf 'La efectividad se comprobara despues de publicar los servicios.\n'
