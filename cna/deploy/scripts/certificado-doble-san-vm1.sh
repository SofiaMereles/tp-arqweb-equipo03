#!/usr/bin/env bash
# B1: reemitir certificado local conservando la clave y el sitio existente.
set -euo pipefail
umask 077
[[ ${EUID} -eq 0 && $(hostnamectl --static) == arqwebserver ]] || {
    echo 'Ejecutar con sudo solo en VM-1 arqwebserver.' >&2; exit 1;
}
[[ $(cat /sys/class/net/ens37/address) == 00:0c:29:fa:eb:d7 ]] || exit 1
cert=/etc/ssl/certs/bookstack.crt
key=/etc/ssl/private/bookstack.key
[[ -f "$cert" && -f "$key" ]] || { echo 'No coinciden las rutas previstas.' >&2; exit 1; }
nginx -t
subject=$(openssl x509 -in "$cert" -noout -subject -nameopt RFC2253)
issuer=$(openssl x509 -in "$cert" -noout -issuer -nameopt RFC2253)
[[ ${subject#subject=} == "${issuer#issuer=}" ]] || {
    echo 'El certificado no es autofirmado: renovar con su CA, no sustituir automaticamente.' >&2; exit 1;
}
openssl pkey -in "$key" -passin pass: -noout >/dev/null
work=$(mktemp -d /var/backups/b1-certificado.XXXXXX)
cp -a "$cert" "$work/bookstack-anterior.crt"
openssl req -x509 -new -sha256 -days 365 -key "$key" -passin pass: \
    -subj '/CN=bookstack.local' \
    -addext 'subjectAltName=DNS:bookstack.local,DNS:api.bookstack.local' \
    -addext 'basicConstraints=critical,CA:FALSE' \
    -addext 'extendedKeyUsage=serverAuth' -out "$work/bookstack-nuevo.crt"
for name in bookstack.local api.bookstack.local; do
    openssl verify -CAfile "$work/bookstack-nuevo.crt" -verify_hostname "$name" "$work/bookstack-nuevo.crt"
done
install -o root -g root -m 644 "$work/bookstack-nuevo.crt" "$cert"
if ! nginx -t; then
    cp -a "$work/bookstack-anterior.crt" "$cert"
    echo 'Se restauro el certificado anterior; no se recargo Nginx.' >&2
    exit 1
fi
if ! systemctl reload nginx; then
    cp -a "$work/bookstack-anterior.crt" "$cert"
    nginx -t && systemctl reload nginx
    echo 'Fallo la recarga nueva; se restauro el certificado anterior.' >&2
    exit 1
fi
for name in bookstack.local api.bookstack.local; do
    openssl s_client -connect 127.0.0.1:443 -servername "$name" \
        -tls1_3 -verify_hostname "$name" -verify_return_error -CAfile "$cert" \
        </dev/null > "$work/tls-$name.log" 2>&1
done
status=$(curl --cacert "$cert" --resolve bookstack.local:443:127.0.0.1 \
    --connect-timeout 5 --max-time 15 -sS -o /dev/null -w '%{http_code}' https://bookstack.local/login)
[[ "$status" == 200 ]] || { echo "Login devolvio HTTP $status; revisar antes de continuar." >&2; exit 1; }
{
    date -Is
    printf 'Nodo: %s\n' "$(hostnamectl --static)"
    openssl x509 -in "$cert" -noout -subject -issuer -dates -ext subjectAltName -fingerprint -sha256
    printf 'TLS 1.3 y nombre de certificado verificados para ambos dominios.\n'
    printf 'Login nativo: HTTP %s, verificado sin curl -k.\n' "$status"
    printf 'Certificado publico: %s\nRespaldo privado: %s\n' "$cert" "$work"
    printf 'api.bookstack.local aun no implica rutas /v2/ implementadas (B5).\n'
} | tee "$work/resumen.txt"
