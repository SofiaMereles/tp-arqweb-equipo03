# Fase 5: relevamiento inicial

## 1. Conectarse a la VM desde PowerShell

La VM tiene dos adaptadores de red configurados en VMware:

| Interfaz | Modo | Comportamiento de la IP |
|---|---|---|
| `ens33` | En puente (automático) | Recibe una IP por DHCP de la red física a la que está conectado el anfitrión. Puede cambiar al pasar a otra red Wi-Fi o Ethernet, o al renovarse la concesión. |
| `ens37` | Solo host (Host-only) | Pertenece a una red virtual privada entre el anfitrión y las VM conectadas a ella. No depende del Wi-Fi: en los relevamientos conservó `192.168.145.129` al cambiar la red física. Si usa DHCP, esa dirección no está garantizada como fija; puede cambiar si se reasigna la concesión o se reconfigura la red virtual de VMware. |

Las direcciones son valores observados, no constantes del proyecto. En un relevamiento, `ens33` tenía `192.168.100.30`; en otro, `10.145.148.231`. Antes de conectarse, comprobar las direcciones vigentes desde la consola de Ubuntu:

```bash
ip -br addr
```

Desde PowerShell, usar la IP vigente de una interfaz accesible. Por ejemplo, para el adaptador en puente, si conserva la dirección observada en el segundo relevamiento:

```powershell
ssh arqweb@10.145.148.231
```

Para el adaptador Solo host, si conserva su dirección:

```powershell
ssh arqweb@192.168.145.129
```

En las pruebas realizadas, SSH funcionó por `ens33`; la conectividad por `ens37` queda pendiente de verificar. El modo Solo host permite comunicación con el anfitrión, pero no garantiza que SSH sea accesible: también deben estar configurados el adaptador virtual de Windows, las rutas, el servicio y el firewall. Tener una IP asignada no demuestra por sí solo que la conexión funcione.

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
