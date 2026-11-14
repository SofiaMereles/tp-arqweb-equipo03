#!/usr/bin/env bash
# Prueba solo la copia restaurada; conserva la instalacion original.
set -euo pipefail
umask 077
[[ ${EUID} -eq 0 && $(hostnamectl --static) == cna-node1 ]] || {
    echo 'Ejecutar con sudo solo en cna-node1.' >&2; exit 1;
}
[[ $(cat /sys/class/net/ens37/address) == 00:0c:29:7f:f2:1a ]] || {
    echo 'La MAC no coincide con VM-2 verificada.' >&2; exit 1;
}
app=/var/www/bookstack-b1-restore
[[ -d "$app" && ! -L "$app" && -f "$app/.env" && -f "$app/artisan" ]] || {
    echo 'Falta la copia restaurada en la ruta prevista.' >&2; exit 1;
}
for tool in php mariadb openssl runuser systemd-run curl ss; do
    command -v "$tool" >/dev/null || { echo "Falta $tool" >&2; exit 1; }
done
[[ $(mariadb --protocol=socket --batch --skip-column-names -e "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='bookstack_b1_restore' AND TABLE_TYPE='BASE TABLE';") == 41 ]] || {
    echo 'No se encuentran las 41 tablas restauradas.' >&2; exit 1;
}
if ss -H -lnt 'sport = :18080' | grep -q .; then
    echo 'El puerto local 18080 esta ocupado; revisar antes de continuar.' >&2; exit 1
fi
work=$(mktemp -d /var/backups/b1-restore-app.XXXXXX)
trap 'echo "Prueba incompleta; registros privados en $work. Revisar el error antes de repetir." >&2' ERR
cp -a "$app/.env" "$work/env.before"
dbuser="b1_restore_$(openssl rand -hex 4)"
dbpass=$(openssl rand -hex 24)
mariadb --protocol=socket > "$work/usuario.log" 2>&1 <<SQL
CREATE USER '$dbuser'@'localhost' IDENTIFIED BY '$dbpass';
GRANT ALL PRIVILEGES ON bookstack_b1_restore.* TO '$dbuser'@'localhost';
SQL
# Credenciales generadas solo en VM-2, nunca impresas ni guardadas en Git.
B1_DB_USER="$dbuser" B1_DB_PASS="$dbpass" php <<'PHP'
<?php
$path = '/var/www/bookstack-b1-restore/.env';
$text = file_get_contents($path);
$values = [
    'DB_HOST'=>'localhost', 'DB_PORT'=>'3306',
    'DB_DATABASE'=>'bookstack_b1_restore',
    'DB_USERNAME'=>getenv('B1_DB_USER'), 'DB_PASSWORD'=>getenv('B1_DB_PASS'),
    'DB_URL'=>'', 'DATABASE_URL'=>'',
    'APP_URL'=>'http://127.0.0.1:18080', 'APP_DEBUG'=>'false',
];
foreach ($values as $key=>$value) {
    $pattern = '/^'.preg_quote($key, '/').'=.*$/m';
    if (preg_match($pattern, $text)) $text = preg_replace($pattern, $key.'='.$value, $text);
    else $text .= "\n".$key.'='.$value."\n";
}
if (file_put_contents($path, $text) === false) exit(1);
PHP
unset dbpass
chown www-data:www-data "$app/.env"
chmod 640 "$app/.env"
if [[ -f "$app/bootstrap/cache/config.php" ]]; then
    mv "$app/bootstrap/cache/config.php" "$work/config-cache.before.php"
fi
cd "$app"
# Arrancar el framework real y verificar la conexion efectiva, no solo el .env.
runuser -u www-data -- php > "$work/framework.log" 2>&1 <<'PHP'
<?php
require '/var/www/bookstack-b1-restore/vendor/autoload.php';
$app = require '/var/www/bookstack-b1-restore/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();
$db = $app->make('db')->connection();
if ($db->getDatabaseName() !== 'bookstack_b1_restore') exit(2);
$row = $db->selectOne('SELECT COUNT(*) AS total FROM entities');
echo 'Framework inicializado; base efectiva: '.$db->getDatabaseName()."\n";
echo 'Entidades leidas por la aplicacion: '.$row->total."\n";
PHP
unit="b1-restore-test-$(openssl rand -hex 4)"
cleanup() { systemctl stop "$unit" >/dev/null 2>&1 || true; }
trap cleanup EXIT
systemd-run --quiet --collect --unit="$unit" \
    --property=User=www-data --property=Group=www-data \
    --property=RuntimeMaxSec=90 --working-directory="$app" \
    /usr/bin/php -S 127.0.0.1:18080 -t public public/index.php
status=$(curl --retry 4 --retry-connrefused --retry-delay 1 --max-time 5 \
    -sS -o "$work/login.html" -w '%{http_code}' http://127.0.0.1:18080/login)
[[ "$status" == 200 ]] || {
    echo "HTTP inesperado: $status. Logs privados en $work; no publicar su contenido sin revisar." >&2; exit 1;
}
[[ -s "$work/login.html" ]] || { echo 'Respuesta vacia.' >&2; exit 1; }
{
    date -Is
    printf 'Nodo: %s\nCopia: %s\n' "$(hostnamectl --static)" "$app"
    cat "$work/framework.log"
    printf 'GET /login de la copia restaurada: HTTP %s\n' "$status"
    printf 'APP_KEY original conservada; credencial de prueba restringida a la base restaurada.\n'
    printf 'Servidor temporal solo en 127.0.0.1:18080; se detiene al terminar.\n'
    printf 'Instalacion /var/www/bookstack y base bookstack_db sin reemplazar.\n'
    printf 'Prueba de arranque y lectura; no valida login autenticado, edicion ni TLS del gateway.\n'
    printf 'Registro privado: %s\n' "$work"
} | tee "$work/resumen.txt"
