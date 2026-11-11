# Fase 5: relevamiento inicial

## 1. Conectarse a la VM desde PowerShell

La captura actual muestra `192.168.100.30` en ens33 y `192.168.145.129` en ens37. El informe anterior usaba `192.168.100.23`; no reutilizar esa dirección sin verificarla.

```powershell
ssh arqweb@192.168.100.30
```

Si esa interfaz no es accesible desde el anfitrión, probar la otra IP. Confirmar los modos de ambos adaptadores en VMware.

## 2. Relevar sistema y servicios dentro de Ubuntu

Ejecutar los bloques por separado. Son consultas; no instalan paquetes ni cambian configuraciones.

```bash
date -Is
whoami
hostnamectl
cat /etc/os-release
ip -br addr
ip route
free -h
lscpu | head -n 20
df -h /
```

```bash
nginx -v
php -v
mariadb --version
systemctl --no-pager --full status nginx mariadb
systemctl list-units --type=service --all 'php*-fpm.service'
sudo ss -lntup
sudo ufw status verbose
curl -k -I --resolve bookstack.local:443:127.0.0.1 https://bookstack.local
```

`-k` se usa aquí para consultar el servicio con certificado local autofirmado; no valida la confianza del certificado. La respuesta HTTP debe interpretarse junto con el login y la edición desde el navegador.

Anotar también la RAM total del anfitrión Windows y la RAM asignada a la VM en VMware. La RAM libre dentro de Ubuntu no permite decidir por sí sola si se puede crear una segunda o tercera VM.

## 3. Identificar la base de datos sin revelar secretos

En la instalación documentada, el código está en `/var/www/bookstack`. Consultar únicamente nombre y prefijo de tablas:

```bash
sudo grep -E '^(DB_DATABASE|DB_PREFIX)=' /var/www/bookstack/.env
sudo mariadb -e 'SHOW DATABASES;'
```

No compartir el `.env` completo, contraseñas, APP_KEY ni tokens. En las consultas siguientes, sustituir `NOMBRE_BASE_REAL` por el nombre obtenido, conservando las comillas simples.

## 4. Inspeccionar el esquema real (base para F5-E1 / P26)

```bash
sudo mariadb --table -e "SELECT TABLE_NAME, TABLE_TYPE FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'NOMBRE_BASE_REAL' ORDER BY TABLE_NAME;"
```

```bash
sudo mariadb --table -e "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'NOMBRE_BASE_REAL' ORDER BY TABLE_NAME, ORDINAL_POSITION;"
```

```bash
sudo mariadb --table -e "SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA = 'NOMBRE_BASE_REAL' AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY TABLE_NAME, COLUMN_NAME;"
```

Estas consultas no leen contenido de páginas ni datos personales. Las claves foráneas muestran relaciones declaradas; su ausencia no demuestra que dos módulos estén desacoplados. El inventario debe contrastarse con el código de la versión instalada y su comportamiento.

## 5. Construir A1 con los resultados

| Módulo | Tablas reales | Acceso de lectura/escritura | Tablas compartidas | Evidencia del uso |
|---|---|---|---|---|
| Contenido | Pendiente | Pendiente | Pendiente | Pendiente |
| Búsqueda | Pendiente | Pendiente | Pendiente | Pendiente |
| Actividad / auditoría | Pendiente | Pendiente | Pendiente | Pendiente |
| Exportación | Pendiente | Pendiente | Pendiente | Pendiente |
| Imágenes / adjuntos | Pendiente | Pendiente | Pendiente | Pendiente |
| Usuarios / permisos | Pendiente | Pendiente | Pendiente | Pendiente |

Después de verificar el uso, convertir el inventario en una matriz con módulos en filas y tablas en columnas, marcando L (lectura), E (escritura), L/E o sin acceso. Identificar las columnas compartidas y explicar por qué impiden una extracción directa. Completar un mapa de contextos con las relaciones y la capa de integración por API/eventos.

Para F5-E1, conservar consultas y resultados que respalden las tablas por módulo. Para F5-E2, guardar la matriz; para F5-E3, el mapa de contextos. Las capturas deben incluir el prompt con usuario y hostname. Una lista de tablas aislada no completa A1.

## Pendientes antes de cerrar el diseño

- Confirmar IP y rol de cada adaptador de VM-1.
- Confirmar recursos del anfitrión y de cada futura VM.
- Confirmar versión real de BookStack y disponibilidad de API y Webhooks.
- Verificar login, creación de libro y edición de página de la instalación actual.
- Completar A1 antes de fijar contratos y decisiones de infraestructura.
