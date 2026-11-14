#!/usr/bin/env bash
# Restaura el SQL en una base de prueba nueva. No reemplaza la base existente.
set -euo pipefail
umask 077
[[ ${EUID} -eq 0 ]] || { echo 'Ejecutar con sudo bash.' >&2; exit 1; }
[[ $(hostnamectl --static) == cna-node1 ]] || {
    echo 'Solo se permite en VM-2, hostname cna-node1.' >&2; exit 1;
}
[[ $(cat /sys/class/net/ens37/address) == 00:0c:29:7f:f2:1a ]] || {
    echo 'La MAC no coincide con VM-2 verificada. Revisar identidad.' >&2; exit 1;
}
backup=/home/arqweb/restauracion-b1/bookstack-b1.KX0e0T
[[ -f "$backup/SHA256SUMS" && -f "$backup/bookstack_db.sql.gz" ]] || {
    echo 'No se encontro el respaldo verificado en la ruta prevista.' >&2; exit 1;
}
(
    cd "$backup"
    sha256sum -c SHA256SUMS >/dev/null
)
work=$(mktemp -d /var/backups/b1-restore-db.XXXXXX)
trap 'echo "Prueba incompleta; registro privado: $work" >&2' ERR
gzip -dc "$backup/bookstack_db.sql.gz" > "$work/backup.sql"
# No aceptar un dump que cambie el esquema de destino o use referencias
# explicitas a la base original. No reescribir el SQL silenciosamente.
if grep -Ei '^[[:space:]]*(USE|CREATE[[:space:]]+DATABASE|DROP[[:space:]]+DATABASE)[[:space:]]' "$work/backup.sql" >/dev/null ||
   grep -F '`bookstack_db`.' "$work/backup.sql" >/dev/null; then
    echo 'El dump contiene seleccion de base o referencias calificadas; revisar antes de importar.' >&2
    exit 1
fi
db_bytes=$(mariadb --protocol=socket --batch --skip-column-names -e "SELECT CAST(COALESCE(SUM(DATA_LENGTH+INDEX_LENGTH),0) AS UNSIGNED) FROM information_schema.TABLES WHERE TABLE_SCHEMA='bookstack_db';")
free_bytes=$(df -PB1 /var/lib/mariadb | awk 'NR==2 {print $4}')
(( free_bytes > 2 * db_bytes + 536870912 )) || {
    echo 'No hay margen suficiente para la base temporal.' >&2; exit 1;
}
# Sin IF NOT EXISTS: rechazar una base de prueba previa en vez de mezclar datos.
mariadb --protocol=socket -e 'CREATE DATABASE bookstack_b1_restore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'
mariadb --protocol=socket bookstack_b1_restore < "$work/backup.sql" > "$work/importacion.log" 2>&1
count=$(mariadb --protocol=socket --batch --skip-column-names -e "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='bookstack_b1_restore' AND TABLE_TYPE='BASE TABLE';")
[[ "$count" == 41 ]] || { echo "Se esperaban 41 tablas; se encontraron $count." >&2; exit 1; }
{
    date -Is
    printf 'Nodo: %s\nRestauracion SQL completada en: bookstack_b1_restore\nTablas: %s\n' "$(hostnamectl --static)" "$count"
    mariadb --protocol=socket --table -e "SELECT 'bookstack_db' AS base, (SELECT COUNT(*) FROM bookstack_db.entities) AS entidades, (SELECT COUNT(*) FROM bookstack_db.users) AS usuarios, (SELECT COUNT(*) FROM bookstack_db.activities) AS actividades UNION ALL SELECT 'bookstack_b1_restore', (SELECT COUNT(*) FROM bookstack_b1_restore.entities), (SELECT COUNT(*) FROM bookstack_b1_restore.users), (SELECT COUNT(*) FROM bookstack_b1_restore.activities);"
    printf 'La base original no se reemplazo. Aplicacion y archivos aun pendientes de prueba de restauracion.\n'
    printf 'Registro privado: %s\n' "$work"
} | tee "$work/resumen.txt"
