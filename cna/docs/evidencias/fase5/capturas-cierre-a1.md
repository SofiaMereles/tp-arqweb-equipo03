# Capturas adicionales para el cierre de A1

Ejecutar directamente cada comando en la sesión SSH para que la captura muestre la consulta o el archivo examinado y su resultado. Incluir el prompt con usuario y hostname. Si la salida ocupa varias pantallas, dividir con sufijos `-a` y `-b`.

Las consultas de esquema y los fragmentos numerados ya están respaldados en `relevamiento/`. Estas capturas complementan ese respaldo con la ejecución visible en el nodo.

## 1. Claves foráneas del esquema completo

Guardar como `F5-E1-05-fk-usuarios-roles.png`.

```bash
sudo mariadb --table bookstack_db -e "SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA = 'bookstack_db' AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY TABLE_NAME, COLUMN_NAME;"
```

## 2. Escritura de contenido

Guardar como `F5-E2-05-escritura-contenido.png`.

```bash
sudo sed -n '110,134p' /var/www/bookstack/app/Entities/Models/Entity.php
```

## 3. Escritura del índice

Guardar como `F5-E2-06-escritura-indice.png`.

```bash
sudo sed -n '100,115p' /var/www/bookstack/app/Search/SearchIndex.php
sudo sed -n '274,292p' /var/www/bookstack/app/Search/SearchIndex.php
```

## 4. Alta y baja de adjuntos

Guardar como `F5-E2-07-adjuntos.png`.

```bash
sudo sed -n '39,57p' /var/www/bookstack/app/Uploads/AttachmentService.php
sudo sed -n '143,150p' /var/www/bookstack/app/Uploads/AttachmentService.php
```

## 5. Usuarios y roles

Guardar como `F5-E2-08-usuarios-roles.png`.

```bash
sudo sed -n '164,181p' /var/www/bookstack/app/Users/Models/User.php
sudo sed -n '300,311p' /var/www/bookstack/app/Users/UserRepo.php
```

## 6. Referencias al borrar un usuario

Guardar como `F5-E2-09-borrado-usuario.png`.

```bash
sudo sed -n '220,239p' /var/www/bookstack/app/Users/UserRepo.php
sudo sed -n '259,265p' /var/www/bookstack/app/Users/UserRepo.php
```

## 7. Restricciones y permisos efectivos

Guardar como `F5-E2-10-permisos-efectivos.png`.

```bash
sudo sed -n '22,40p' /var/www/bookstack/app/Entities/Tools/PermissionsUpdater.php
sudo sed -n '217,232p' /var/www/bookstack/app/Permissions/JointPermissionBuilder.php
```

## 8. Archivos para exportación ZIP

Guardar como `F5-E2-11-exportacion-archivos.png`.

```bash
sudo sed -n '82,107p' /var/www/bookstack/app/Exports/ZipExports/ZipExportFiles.php
```
