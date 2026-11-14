#!/usr/bin/env bash
# Preparación B4 necesaria para S1: comprobar lectura y guardar credencial en Swarm.
set -euo pipefail
set +x
umask 077
[[ $EUID -eq 0 && $(hostnamectl --static) == arqwebserver ]] || {
  echo 'Ejecutar con sudo solo en VM-1 arqwebserver.' >&2; exit 1;
}
[[ -t 0 ]] || { echo 'Ejecutar desde una terminal interactiva.' >&2; exit 1; }
[[ $(docker info --format '{{.Swarm.ControlAvailable}}') == true ]] || exit 1
cert=/etc/ssl/certs/bookstack.crt
secret=cna_bookstack_api_token
config=cna_bookstack_ca_v1
[[ -r $cert ]] || { echo 'Falta el certificado publico de BookStack.' >&2; exit 1; }
if docker secret inspect "$secret" >/dev/null 2>&1; then
  echo 'El secreto ya existe. No se reemplazo; revisar vigencia antes de rotarlo.' >&2
  exit 1
fi
body=$(mktemp /run/cna-bookstack-api.XXXXXX)
cleanup() {
  unset token_id token_secret
  rm -f -- "$body"
}
trap cleanup EXIT
read -r -s -p 'Token ID (entrada oculta): ' token_id
printf '\n'
read -r -s -p 'Token Secret (entrada oculta): ' token_secret
printf '\n'
[[ $token_id =~ ^[A-Za-z0-9._-]+$ && $token_secret =~ ^[A-Za-z0-9._-]+$ ]] || {
  echo 'Formato inesperado: copiar cada valor sin espacios ni comillas.' >&2; exit 1;
}
# La credencial viaja por stdin a curl; no se incluye en sus argumentos.
status=$(printf 'header = "Authorization: Token %s:%s"\n' "$token_id" "$token_secret" |
  curl --config - --cacert "$cert" --resolve bookstack.local:443:127.0.0.1 \
    --connect-timeout 5 --max-time 15 --silent --show-error \
    --output "$body" --write-out '%{http_code}' 'https://bookstack.local/api/pages?count=1&offset=0')
[[ $status == 200 ]] || {
  printf 'API BookStack: HTTP %s. No se guardo el token; revisar permiso API, expiracion y valores.\n' "$status" >&2
  exit 1
}
php -r '$v=json_decode(file_get_contents($argv[1]),true,512,JSON_THROW_ON_ERROR); if(!isset($v["data"],$v["total"]) || !is_array($v["data"]) || !is_int($v["total"])) {fwrite(STDERR,"Respuesta API inesperada.\n");exit(1);} printf("Lectura API: HTTP 200; paginas visibles: %d.\n",$v["total"]);' "$body"
if docker config inspect "$config" >/dev/null 2>&1; then
  expected=$(sha256sum "$cert" | cut -d ' ' -f 1)
  existing=$(docker config inspect "$config" --format '{{.Spec.Data}}' | base64 -d | sha256sum | cut -d ' ' -f 1)
  [[ $expected == "$existing" ]] || {
    echo 'El config del certificado no coincide: requiere otra version, no se guardo el token.' >&2; exit 1;
  }
else
  docker config create "$config" "$cert" >/dev/null
fi
printf '%s:%s' "$token_id" "$token_secret" | docker secret create "$secret" - >/dev/null
unset token_id token_secret
date -Is
printf 'Nodo: %s\n' "$(hostnamectl --static)"
printf 'PASS: lectura API verificada con TLS y credencial guardada como secreto Swarm.\n'
printf 'Secreto: %s\nCertificado publico (Docker config): %s\n' "$secret" "$config"
printf 'No se guardaron credenciales en el repositorio ni se modificaron paginas.\n'
printf 'Pendiente: acceso desde VM-2 y verificacion del alcance de permisos del rol.\n'
