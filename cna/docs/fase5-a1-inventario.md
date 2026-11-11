# Fase 5 · A1 — Inventario de BookStack

Este archivo conserva el relevamiento inicial. La revisión ampliada del paquete de la VM, con matriz de los seis módulos y accesos verificados, está en [el análisis actualizado](fase5-a1-analisis-verificado.md). Sus referencias de código están en [la trazabilidad](fase5-a1-trazabilidad.md).

Relevamiento aportado desde `arqwebserver` (Ubuntu 26.04.1 LTS sobre VMware). La VM reportó 3,3 GiB de RAM, 2,6 GiB disponibles y sin swap. La ruta predeterminada sale por `ens33` (`192.168.100.30/24`), vía `192.168.100.1`. `ens37` tiene `192.168.145.129/24`. Los modos de los adaptadores quedan por confirmar en VMware.

## Verificación local del monolito (10/11/2026)

`systemctl is-active nginx php8.5-fpm mariadb` devolvió `active` para los tres servicios. La consulta HTTPS a `https://bookstack.local/login`, resolviendo el dominio a `127.0.0.1` desde la VM, devolvió `HTTP/1.1 200 OK`. Se usó `curl -k` para el certificado local. Quedan por comprobar el acceso desde Windows, el inicio de sesión, la creación de un libro y la edición de una página.

## Inventario observado en MariaDB

La consulta a `information_schema.TABLES` para `bookstack_db` devolvió 41 nombres. La lista incluye `entities`, `entity_container_data` y `entity_page_data`. En ese esquema no aparecieron tablas llamadas `books` o `pages`.

```text
activities
api_tokens
attachments
bookshelves_books
cache
comments
deletions
email_confirmations
entities
entity_container_data
entity_page_data
entity_permissions
failed_jobs
favourites
images
imports
jobs
joint_permissions
mention_history
mfa_values
migrations
page_revisions
password_resets
permission_role
references
roles
role_permissions
role_user
search_terms
sessions
settings
slug_history
social_accounts
sort_rules
tags
users
user_invites
views
watches
webhooks
webhook_tracked_events
```

## Primer grupo para inspeccionar

```bash
sudo mariadb bookstack_db -e 'SHOW COLUMNS FROM entities; SHOW COLUMNS FROM entity_container_data; SHOW COLUMNS FROM entity_page_data; SHOW COLUMNS FROM search_terms; SHOW COLUMNS FROM activities;'
```

El objetivo es ubicar los campos que podrían relacionar el contenido con el índice de búsqueda y con los registros de actividad. Los nombres de campos permiten proponer relaciones. Para distinguir claves foráneas de referencias mantenidas por la aplicación, revisar `information_schema.KEY_COLUMN_USAGE` y contrastar el uso con el código instalado.

## Matriz preliminar de acoplamiento (F5-E2 / P27)

| Módulo | `entities` | `entity_container_data` | `entity_page_data` | `search_terms` | `activities` | `users` |
|---|---|---|---|---|---|---|
| Contenido | Principal | Principal | Principal | Por verificar | Por verificar | Referencia candidata |
| Búsqueda | Referencia candidata | Por verificar | Fuente de texto candidata | Principal | Por verificar | Por verificar |
| Exportación Markdown | L: páginas, libros y capítulos | L: datos de libros y capítulos | L: Markdown o HTML de páginas | Por verificar | Por verificar | Por verificar |
| Actividad / auditoría | Referencia candidata para eventos de contenido | Por verificar | Por verificar | Por verificar | Principal | Referencia candidata |

«Principal» indica la responsabilidad sugerida por la estructura observada. La matriz todavía requiere confirmar los accesos de lectura y escritura en el código instalado.

- `entities`: clave primaria compuesta por `id` y `type`; tiene `book_id` y `chapter_id`.
- `entity_container_data`: clave primaria compuesta por `entity_id` y `entity_type`, par compatible con `entities.(id, type)`.
- `entity_page_data`: clave primaria `page_id`; almacena `html`, `text` y `markdown`. Posible relación con `entities.id` para el tipo página.
- `search_terms`: almacena `term`, `score` y el par `entity_id` / `entity_type`. Ese par sugiere que el índice apunta a entidades de contenido.
- `activities`: contiene `user_id`, `type`, `created_at` y el par opcional `loggable_id` / `loggable_type`. El par puede identificar distintos tipos de objetos, por lo que su destino queda por verificar.

La consulta a `information_schema.KEY_COLUMN_USAGE` filtrada por las cinco tablas y `REFERENCED_TABLE_NAME IS NOT NULL` devolvió cero filas. Esto confirma que ninguna de esas tablas declara claves foráneas salientes en el esquema observado. El siguiente paso es identificar en el código de BookStack dónde se leen o escriben los campos que sugieren relaciones.

## Accesos observados en el código instalado

### Exportación: trazabilidad de la consulta

Los controladores de exportación llaman a `findVisibleByIdOrFail()`. En `Entities/Queries/PageQueries.php`, ese método delega a `findVisibleById()`, que ejecuta `Page::query()` con el alcance `visible`. En `Entities/Queries/BookQueries.php`, el método ejecuta `Book::query()` con el mismo alcance. Se confirma lectura de contenido vía los modelos `Page` y `Book`, sujeta a visibilidad. La consulta de listado de páginas usa `entities as books` y `type = 'book'` para recuperar el slug del libro. Esa subconsulta pertenece al listado y no demuestra que se ejecute durante la exportación.

`Entity.php:84` identifica `entities` como tabla base. `EntityScope::apply()` filtra por tipo y une los datos de páginas por ID o los de contenedores por ID y tipo. `ExportFormatter::bookToMarkdown()` obtiene el árbol con `BookContents::getTree(false, true)`, agrega la descripción del libro y delega cada elemento a `chapterToMarkdown()` o `pageToMarkdown()`. El formateador de capítulos agrega la descripción y recorre las páginas visibles. El de páginas usa el Markdown guardado o convierte el HTML. El recorrido respalda marcar lectura de `entities`, `entity_container_data` y `entity_page_data` para exportar libros a Markdown.

Rutas relativas a `/var/www/bookstack/app`. L indica lectura confirmada por el fragmento de código. La salida de búsqueda identifica líneas de interés y deja pendientes las operaciones que necesitan más contexto.

| Módulo | Tabla | Acceso observado | Referencia |
|---|---|---|---|
| Contenido | `entities`, `entity_page_data` | L: une `entities.id` con `entity_page_data.page_id` y filtra borradores | `Entities/Queries/EntityQueries.php:81–88` |
| Usuarios / permisos | `entities`, `entity_page_data` | L: une ambas tablas y usa el indicador de borrador | `Permissions/PermissionApplicator.php:198–204` |
| Imágenes / adjuntos | `entity_page_data`, `page_revisions` | L: busca el nombre del archivo en el HTML actual y, opcionalmente, en las revisiones antes de considerar una imagen para limpieza | `Uploads/ImageService.php`, `deleteUnusedImages()` |
| Búsqueda | `search_terms`, `entities` | L: agrupa los términos por tipo e ID, enlaza con `entities` mediante ambos campos y ordena por puntaje | `Search/SearchRunner.php`, `applyTermSearch()` |
| Actividad / auditoría | `activities` | L/E: aplica restricciones por objeto, persiste actividades con `save()` y desvincula la entidad cuando se elimina | `Activity/ActivityQueries.php:31,87`; `Activity/Tools/ActivityLogger.php`, `add()` y `removeEntity()` |
| Actividad / auditoría | `joint_permissions` | La consulta compara `activities.loggable_type` con `joint_permissions.entity_type`; falta revisar la condición completa | `Activity/Models/Activity.php:52` |

`ActivityLogger::add()` guarda el ID del usuario actual y, si el objeto es una entidad, su ID y tipo polimórfico. Después de `save()` llama a `dispatchWebhooks()`, que selecciona webhooks activos suscritos al tipo de evento o a `all`. Esto identifica un punto de integración para auditoría, pendiente de comprobar con eventos reales.

`entity_page_data` es una tabla compartida entre contenido, permisos y medios. La limpieza de medios depende de que las referencias a los archivos sigan siendo identificables en el HTML. Para el TP II, el nuevo servicio de búsqueda debe obtener contenido mediante la API de BookStack y mantener su propio índice. La auditoría debe recibir eventos y persistirlos en su almacén.

Los controladores `Exports/Controllers/PageExportApiController.php` y `Exports/Controllers/BookExportApiController.php` aplican el permiso `ContentExport`. Ambos consultan contenido visible por ID mediante `PageQueries` o `BookQueries` y delegan la conversión a `ExportFormatter` (PDF, HTML, texto o Markdown) o `ZipExportBuilder` (ZIP). Para la matriz queda seguir esas consultas y el formateador hasta las tablas. Para S3, verificar en una prueba de API que la cuenta de servicio tenga acceso al contenido y permiso de exportación antes de depender de estos endpoints.

Estado de las evidencias: F5-E1/P26 y F5-E2/P27 en curso. Faltan accesos de escritura, exportación y partes de medios y usuarios. F5-E3/P28 (mapa de contextos) pendiente.
