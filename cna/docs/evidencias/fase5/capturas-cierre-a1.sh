#!/usr/bin/env bash
# Respaldo de A1. Muestra esquema o codigo; no invoca funciones PHP.
set -euo pipefail
cd /var/www/bookstack
case "${1:-}" in
  1)
    sudo mariadb --table bookstack_db -e "SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA = 'bookstack_db' AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY TABLE_NAME, COLUMN_NAME;"
    ;;
  2)
    sudo sed -n '110,134p' app/Entities/Models/Entity.php
    ;;
  3)
    sudo sed -n '100,115p' app/Search/SearchIndex.php
    sudo sed -n '274,292p' app/Search/SearchIndex.php
    ;;
  4)
    sudo sed -n '39,57p' app/Uploads/AttachmentService.php
    sudo sed -n '143,150p' app/Uploads/AttachmentService.php
    ;;
  5)
    sudo sed -n '164,181p' app/Users/Models/User.php
    sudo sed -n '300,311p' app/Users/UserRepo.php
    ;;
  6)
    sudo sed -n '220,239p' app/Users/UserRepo.php
    sudo sed -n '259,265p' app/Users/UserRepo.php
    ;;
  7)
    sudo sed -n '22,40p' app/Entities/Tools/PermissionsUpdater.php
    sudo sed -n '217,232p' app/Permissions/JointPermissionBuilder.php
    ;;
  8)
    sudo sed -n '82,107p' app/Exports/ZipExports/ZipExportFiles.php
    ;;
  *)
    printf 'Uso: bash capturas-cierre-a1.sh NUMERO\nOpciones: 1 FK, 2 escritura contenido, 3 indexacion, 4 adjuntos, 5 roles, 6 borrado usuario, 7 permisos efectivos, 8 archivos ZIP.\n'
    exit 2
    ;;
esac
