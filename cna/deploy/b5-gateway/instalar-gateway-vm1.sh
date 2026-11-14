#!/usr/bin/env bash
set -euo pipefail
umask 077
[[ $EUID -eq 0 && $(hostnamectl --static) == arqwebserver ]] || {
  echo 'Ejecutar con sudo solo en VM-1 arqwebserver.' >&2; exit 1;
}
cd "$(dirname "$(readlink -f "$0")")"
source=cna-api.conf
target=/etc/nginx/conf.d/cna-api.conf
cert=/etc/ssl/certs/bookstack.crt
[[ -f $source && -f $cert && -f /etc/ssl/private/bookstack.key ]] || exit 1
nginx -t
openssl x509 -in "$cert" -noout -checkhost api.bookstack.local
curl --silent --show-error --connect-timeout 3 --max-time 10 --fail \
  http://192.168.145.130:8081/readyz >/dev/null
backup=$(mktemp -d /var/backups/cna-gateway.XXXXXX)
old=false
if [[ -f $target ]]; then
  cp -a "$target" "$backup/cna-api-anterior.conf"
  old=true
fi
rollback() {
  if [[ $old == true ]]; then
    cp -a "$backup/cna-api-anterior.conf" "$target"
  else
    rm -f -- /etc/nginx/conf.d/cna-api.conf
  fi
  nginx -t && systemctl reload nginx
  echo 'Se restauro la configuracion anterior del gateway.' >&2
}
install -o root -g root -m 644 "$source" "$target"
if ! nginx -t; then
  rollback
  exit 1
fi
if ! systemctl reload nginx; then
  rollback
  exit 1
fi
# Esperar a los nuevos workers de Nginx antes de comprobar la ruta nueva.
status=000
for ((attempt=0; attempt<10; attempt++)); do
  status=$(curl --cacert "$cert" --resolve api.bookstack.local:443:127.0.0.1 \
    --tlsv1.3 --tls-max 1.3 --connect-timeout 3 --max-time 5 -sS \
    -o "$backup/api-sin-credencial.json" -w '%{http_code}' 'https://api.bookstack.local/v2/search?q=alfa') || status=000
  [[ $status == 401 ]] && break
  sleep 0.3
done
if [[ $status != 401 ]]; then
  echo "La ruta API devolvio HTTP $status; se esperaba 401 sin clave." >&2
  rollback
  exit 1
fi
native=$(curl --cacert "$cert" --resolve bookstack.local:443:127.0.0.1 \
  --connect-timeout 3 --max-time 10 -sS -o /dev/null -w '%{http_code}' https://bookstack.local/login) || native=000
if [[ $native != 200 ]]; then
  echo "El login nativo devolvio HTTP $native." >&2
  rollback
  exit 1
fi
date -Is
printf 'Nodo: %s\n' "$(hostnamectl --static)"
printf 'Gateway API: TLS 1.3 verificado y ruta /v2/search responde HTTP 401 sin clave, como corresponde.\n'
printf 'BookStack nativo /login: HTTP 200 con certificado verificado.\n'
printf 'Configuracion: %s\nRespaldo y comprobacion: %s\n' "$target" "$backup"
printf 'Pendiente: consulta autenticada y edicion real F6-E4. B5 completo aun no se declara aprobado.\n'
