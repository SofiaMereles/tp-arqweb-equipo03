# Evidencias de la Fase 5

A4 conserva las evidencias de diseño F5-E5/P30, F5-E6/P31 y F5-E7/P32 en [a4/](a4/README.md). Incluye contexto C4, dos láminas complementarias del nivel 2 y tres secuencias con sus errores. Las fuentes y el script de generación están en [diagramas/a4/](../../diagramas/a4/README.md). Se distinguen los componentes existentes de la arquitectura objetivo; el renderizado no demuestra despliegue.

La validación de A3 (F5-E4 / P29) está guardada en [a3/](a3/README.md), con resultados reales, versiones y hashes. Los contratos incluyen S1–S4, el puente y seis canales. La captura de terminal se guarda como `F5-E4-validacion-contratos.png` en esta carpeta y se incorpora automáticamente al compilar el informe.

El relevamiento completo del 11/11/2026 está respaldado en `relevamiento/` y en `a1-relevamiento.eihlt8.tar.gz`. Se verificaron las sumas SHA-256 del paquete. El [análisis ampliado](../../fase5-a1-analisis-verificado.md), la [trazabilidad](../../fase5-a1-trazabilidad.md) y las [capturas adicionales de cierre](capturas-cierre-a1.md) continúan las evidencias iniciales de esta lista. La captura de recolección está guardada como `F5-E1-04-recoleccion-esquema-codigo.png`.

Guardar las capturas en esta carpeta. Incluir el comando, su resultado y el prompt `arqweb@arqwebserver` cuando la evidencia provenga de la VM. Evitar capturar cookies, tokens y credenciales.

| Evidencia | Archivo sugerido | Qué debe mostrar | Estado |
|---|---|---|---|
| F5-E1 / P26 | `F5-E1-01-inventario-tablas.png` | Consulta a `information_schema.TABLES` y listado de las 41 tablas | Resultado anotado; captura pendiente |
| F5-E1 / P26 | `F5-E1-02-columnas.png` | `SHOW COLUMNS` de las tablas analizadas; dividir en varias capturas si hace falta | Primer grupo consultado; captura pendiente |
| F5-E1 / P26 | `F5-E1-03-claves-foraneas.png` | Consulta a `KEY_COLUMN_USAGE` y regreso al prompt sin filas para las cinco tablas examinadas | Captura guardada |
| F5-E2 / P27 | `F5-E2-01-contenido-permisos.png` | Código que une `entities.id` con `entity_page_data.page_id` y usa `draft` | Hallazgo anotado; captura pendiente |
| F5-E2 / P27 | `F5-E2-02-busqueda-auditoria.png` | Unión de búsqueda y guardado de actividad; se pueden guardar por separado | Hallazgo anotado; captura pendiente |
| F5-E2 / P27 | `F5-E2-03-medios.png` | Lectura de HTML de páginas y revisiones en `ImageService` | Hallazgo anotado; captura pendiente |
| F5-E2 / P27 | `F5-E2-04-exportacion-markdown.png` | Uniones de `EntityScope` y recorrido de `ExportFormatter` | Hallazgo anotado; captura pendiente |
| F5-E2 / P27 | Matriz del informe | Matriz módulo × tabla con L/E y referencias a los fragmentos de código | [Borrador de A1](../../fase5-a1-inventario.md) |
| F5-E3 / P28 | Mapa de contextos | Contextos de BookStack y sus relaciones | Pendiente |

Para reproducir el inventario desde SSH:

```bash
sudo mariadb --table bookstack_db -e "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'bookstack_db' ORDER BY TABLE_NAME;"
```

Los resultados y rutas de código ya registrados están en el borrador de A1. Las capturas de código respaldan las celdas de la matriz y se pueden guardar a medida que se verifica cada acceso.

## Comandos para recuperar las capturas pendientes

Ejecutar cada línea por separado desde la sesión SSH. Para capturas de varias pantallas, agregar sufijos `-a`, `-b`, etc.

**F5-E1-02 · Columnas**

```bash
sudo mariadb --table bookstack_db -e 'SHOW COLUMNS FROM entities; SHOW COLUMNS FROM entity_container_data; SHOW COLUMNS FROM entity_page_data; SHOW COLUMNS FROM search_terms; SHOW COLUMNS FROM activities;'
```

**F5-E2-01 · Contenido y permisos**

```bash
sudo sed -n '77,92p' /var/www/bookstack/app/Entities/Queries/EntityQueries.php
sudo sed -n '192,208p' /var/www/bookstack/app/Permissions/PermissionApplicator.php
```

**F5-E2-02 · Búsqueda y auditoría**

```bash
sudo sed -n '155,187p' /var/www/bookstack/app/Search/SearchRunner.php
sudo sed -n '24,73p' /var/www/bookstack/app/Activity/Tools/ActivityLogger.php
```

**F5-E2-03 · Medios**

```bash
sudo sed -n '170,209p' /var/www/bookstack/app/Uploads/ImageService.php
```

**F5-E2-04 · Exportación Markdown**

```bash
sudo sed -n '14,35p' /var/www/bookstack/app/Entities/Models/EntityScope.php
sudo sed -n '295,365p' /var/www/bookstack/app/Exports/ExportFormatter.php
```

**Comprobación de partida · BookStack activo** (respaldo adicional, sin número propio en la consigna)

```bash
systemctl is-active nginx php8.5-fpm mariadb
curl -k -sS -I --resolve bookstack.local:443:127.0.0.1 https://bookstack.local/login | head -n 1
```

Nombre sugerido: `BASE-01-bookstack-activo.png`. La salida de `curl` se limita al estado HTTP para dejar fuera las cookies.
