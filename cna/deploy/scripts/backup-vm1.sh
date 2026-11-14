#!/usr/bin/env bash
# Preparacion B1. Backup privado; no modifica configuracion ni detiene servicios.
# Ejecutar sin ediciones, subidas ni cambios de esquema concurrentes.
set -euo pipefail
umask 077
if [[ ${EUID} -ne 0 ]]; then
    echo 'Ejecutar con sudo bash backup-vm1.sh' >&2
    exit 1
fi
app=/var/www/bookstack
db=bookstack_db
for tool in mariadb mariadb-dump tar gzip sha256sum du df awk mktemp; do
    command -v "$tool" >/dev/null || { echo "Falta herramienta: $tool" >&2; exit 1; }
done
[[ -d "$app" && -f "$app/.env" && ! -L "$app" ]] || {
    echo 'Revisar ruta de BookStack y .env antes de continuar.' >&2; exit 1;
}
tables=$(mariadb --batch --skip-column-names -e "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='$db' AND TABLE_TYPE='BASE TABLE';")
other_engines=$(mariadb --batch --skip-column-names -e "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='$db' AND TABLE_TYPE='BASE TABLE' AND (ENGINE IS NULL OR ENGINE <> 'InnoDB');")
[[ "$tables" =~ ^[0-9]+$ && "$tables" -gt 0 && "$other_engines" == 0 ]] || {
    echo 'Se requiere base existente con tablas InnoDB para este procedimiento.' >&2; exit 1;
}
db_bytes=$(mariadb --batch --skip-column-names -e "SELECT CAST(COALESCE(SUM(DATA_LENGTH+INDEX_LENGTH),0) AS UNSIGNED) FROM information_schema.TABLES WHERE TABLE_SCHEMA='$db';")
app_bytes=$(du -sb "$app" | awk '{print $1}')
config_paths=()
for path in etc/nginx etc/php etc/mysql etc/mariadb etc/my.cnf etc/my.cnf.d etc/ssl etc/ufw; do
    [[ -e "/$path" ]] && config_paths+=("$path")
done
[[ ${#config_paths[@]} -gt 0 ]] || { echo 'No se encontraron configuraciones previstas.' >&2; exit 1; }
config_bytes=0
for path in "${config_paths[@]}"; do
    current_bytes=$(du -sb "/$path" | awk '{print $1}')
    config_bytes=$((config_bytes + current_bytes))
done
mkdir -p /var/backups
available=$(df -PB1 /var/backups | awk 'NR==2 {print $4}')
# Estimacion conservadora, no garantia: comprimir suele reducir el tamano.
required=$((2 * (db_bytes + app_bytes + config_bytes) + 536870912))
if (( available < required )); then
    echo "Espacio insuficiente segun estimacion: disponibles=$available, previstos=$required bytes." >&2
    exit 1
fi
backup_dir=$(mktemp -d /var/backups/bookstack-b1.XXXXXX)
trap 'echo "Backup incompleto; conservar para revisar: $backup_dir" >&2' ERR
{
    date -Is
    printf 'Hostname: %s\nOperador: %s\n' "$(hostname)" "${SUDO_USER:-root}"
    printf 'Base: %s\nTablas InnoDB: %s\n' "$db" "$tables"
    mariadb --batch -e "SHOW VARIABLES LIKE 'datadir';"
    printf 'Precondicion: sin cambios concurrentes en contenido, archivos o esquema.\n'
} > "$backup_dir/origen.txt"
mariadb-dump --single-transaction --quick --skip-lock-tables \
    --routines --events --triggers "$db" | gzip > "$backup_dir/bookstack_db.sql.gz"
tar -czf "$backup_dir/bookstack-app.tar.gz" -C /var/www bookstack
tar -czf "$backup_dir/configuracion.tar.gz" -C / "${config_paths[@]}"
gzip -t "$backup_dir/bookstack_db.sql.gz"
tar -tzf "$backup_dir/bookstack-app.tar.gz" >/dev/null
tar -tzf "$backup_dir/configuracion.tar.gz" >/dev/null
(
    cd "$backup_dir"
    sha256sum origen.txt bookstack_db.sql.gz bookstack-app.tar.gz configuracion.tar.gz > SHA256SUMS
    sha256sum -c SHA256SUMS > verificacion.txt
)
{
    printf 'Backup B1 creado en: %s\n' "$backup_dir"
    printf 'Nodo: %s\nTablas InnoDB: %s\n' "$(hostname)" "$tables"
    printf 'gzip/tar legibles y SHA-256 verificados.\n'
    du -sh "$backup_dir"
    printf 'Contiene datos y secretos: no copiar al repositorio ni publicar.\n'
    printf 'Pendiente: copia fuera de VM-1 y restauracion aislada.\n'
} | tee "$backup_dir/resumen.txt"
