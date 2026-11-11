#!/usr/bin/env bash
# Recolecta estructura y código de BookStack. No exporta filas ni el .env.
set -euo pipefail
umask 077
app_dir=/var/www/bookstack
task_dir=$(mktemp -d "$HOME/a1-relevamiento.XXXXXX")
archive_path="$task_dir.tar.gz"
test -d "$app_dir/app"
sudo -v
{
    date -Is
    printf 'Usuario: %s\nNodo: %s\n' "$(whoami)" "$(hostname)"
    printf 'Aplicacion: %s\n' "$app_dir"
} > "$task_dir/origen.txt"
sudo mariadb --batch --raw -e "SELECT TABLE_NAME, TABLE_TYPE FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'bookstack_db' ORDER BY TABLE_NAME;" > "$task_dir/tablas.tsv"
sudo mariadb --batch --raw -e "SELECT TABLE_NAME, ORDINAL_POSITION, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'bookstack_db' ORDER BY TABLE_NAME, ORDINAL_POSITION;" > "$task_dir/columnas.tsv"
sudo mariadb --batch --raw -e "SELECT TABLE_NAME, CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA = 'bookstack_db' ORDER BY TABLE_NAME, CONSTRAINT_NAME, ORDINAL_POSITION;" > "$task_dir/claves.tsv"
sudo tar -czf "$task_dir/codigo-app.tar.gz" -C "$app_dir" app
sudo chown "$(id -u):$(id -g)" "$task_dir/codigo-app.tar.gz"
(
    cd "$task_dir"
    sha256sum origen.txt tablas.tsv columnas.tsv claves.tsv codigo-app.tar.gz > SHA256SUMS
)
tar -czf "$archive_path" -C "$task_dir" .
printf '\nRelevamiento terminado. Archivo para copiar a Windows:\n%s\n' "$archive_path"
