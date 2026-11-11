# A1 — Análisis verificado del monolito

## Procedencia y alcance

Recolección ejecutada por `arqweb` en `arqwebserver` el 11/11/2026 a las 13:33:13 UTC. El paquete `a1-relevamiento.eihlt8.tar.gz` contiene el catálogo de 41 tablas, columnas y claves del esquema `bookstack_db`, y 479 archivos PHP de `app/`. Se verificaron las cinco sumas de `SHA256SUMS`. Las salidas originales están en `evidencias/fase5/relevamiento/` y los fragmentos numerados en `codigo-verificado.txt` dentro de esa carpeta.

El análisis sigue los flujos de consulta, creación/edición de contenido, indexación, actividad, exportación, subida/limpieza de medios y administración de usuarios/permisos. Los accesos delegados se señalan para distinguirlos de las consultas del propio componente. Es análisis estático del código instalado junto con metadatos reales de MariaDB. Las pruebas de entrega de eventos, tolerancia a fallos y rendimiento corresponden a las fases de implementación y operación.

## F5-E1 / P26 — Módulos y persistencia real

| Módulo | Tablas principales verificadas | Operaciones y fuente |
|---|---|---|
| Contenido | `entities`, `entity_container_data`, `entity_page_data`, `page_revisions`, `bookshelves_books`, `tags` | `Entity::save()` separa atributos comunes y específicos y guarda ambos modelos. `PageRepo::update()` guarda página y revisión y registra actividad. `BookshelfRepo::updateBooks()` sincroniza el pivote. `TagRepo::saveTagsToEntity()` reemplaza etiquetas. R01–R03, R11. |
| Búsqueda | `search_terms`, `entities`, `entity_container_data`, `entity_page_data`, `tags` | `SearchIndex` obtiene nombre, descripción/HTML y etiquetas, elimina términos previos e inserta los nuevos. `SearchRunner` une el índice con entidades por ID y tipo. R04. |
| Actividad / auditoría | `activities`, `users`, `entities` y sus datos específicos; `joint_permissions` mediante filtro de visibilidad | `ActivityLogger::add()` persiste el registro. `ActivityQueries` carga usuario y entidad y filtra actividad. La relación de permisos utiliza ID y tipo. R05. |
| Exportación | Las tres tablas de contenido; `tags`, `images`, `attachments` para ZIP; permisos mediante consultas visibles | `ExportFormatter` recorre libro/capítulos/páginas para Markdown y PDF. `BookContents` recupera páginas y capítulos visibles. `ZipExportPage` obtiene etiquetas y adjuntos y `ZipExportFiles` recupera archivos por modelo. R06. |
| Imágenes / adjuntos | `images`, `attachments`, `entity_page_data`, `page_revisions`; entidades y permisos mediante consultas visibles | `ImageService` guarda y elimina el registro y archivo. `AttachmentService` crea/actualiza/elimina el adjunto asociado a `uploaded_to`. La limpieza de imágenes lee HTML actual e histórico. `Attachment::scopeVisible()` y `Image::scopeVisible()` delegan en `PermissionApplicator`. R07–R08. |
| Usuarios / permisos | `users`, `roles`, `role_user`, `role_permissions`, `permission_role`, `entity_permissions`, `joint_permissions`; referencias en contenido y medios | `User::permissions()` une tablas de autorización. `UserRepo` guarda usuarios, sincroniza roles y actualiza referencias al eliminar un usuario. `PermissionsRepo` administra roles y permisos. `PermissionsUpdater` cambia restricciones y propietario y `JointPermissionBuilder` reconstruye permisos efectivos. R09–R10. |

El inventario restante incluye soporte y funciones auxiliares. Esto permite conservar las 41 tablas sin forzar cada tabla dentro de los seis recorridos principales de extracción.

| Grupo funcional auxiliar | Tablas del catálogo |
|---|---|
| Conversación, seguimiento y navegación | `comments`, `favourites`, `mention_history`, `views`, `watches` |
| Referencias, historial y orden de contenido | `references`, `slug_history`, `sort_rules`, `deletions` |
| Integraciones y notificaciones | `webhooks`, `webhook_tracked_events` |
| Acceso e identidad | `api_tokens`, `email_confirmations`, `mfa_values`, `password_resets`, `sessions`, `social_accounts`, `user_invites` |
| Importación | `imports` |
| Plataforma y configuración | `cache`, `jobs`, `failed_jobs`, `migrations`, `settings` |

Las 17 tablas principales únicas de la primera tabla y las 24 auxiliares cubren las 41 entradas del catálogo. Esta clasificación funcional expresa responsabilidad principal; las referencias entre grupos siguen siendo compartidas. El catálogo registra 280 columnas y cuatro claves foráneas declaradas: `permission_role.permission_id → role_permissions.id`, `permission_role.role_id → roles.id`, `role_user.role_id → roles.id` y `role_user.user_id → users.id`. La consulta anterior solo abarcaba cinco tablas de contenido, búsqueda y actividad. Las uniones y relaciones ORM respaldan los demás acoplamientos incluso cuando no hay FK salientes declaradas.

## F5-E2 / P27 — Matriz módulo × tabla

L = lectura, E = inserción/actualización/eliminación. `D(L)` o `D(E)` = operación delegada a otro módulo en el recorrido revisado. `—` = operación no atribuida en ese recorrido; no certifica ausencia global de acceso. Cada celda afirmativa tiene respaldo en las referencias R01–R11. Se separa el soporte transversal de los accesos principales para que no se confunda propietario funcional con acceso exclusivo. El CSV tiene los mismos seis módulos como filas.

| Módulo | entities | entity_container_data | entity_page_data | page_revisions | search_terms | tags | bookshelves_books |
|---|---|---|---|---|---|---|---|
| Contenido | L/E | L/E | L/E | L/E | D(E) | L/E | L/E |
| Búsqueda | L | L | L | — | L/E | L | — |
| Actividad / auditoría | L | L | L | — | — | — | — |
| Exportación | L | L | L | — | — | L (ZIP) | — |
| Imágenes / adjuntos | D(L) | — | L | L | — | — | — |
| Usuarios / permisos | L/E | L | L | E | — | — | — |

| Módulo | activities | users | roles | role_user | role_permissions | permission_role | entity_permissions | joint_permissions | images | attachments |
|---|---|---|---|---|---|---|---|---|---|---|
| Contenido | D(E) | — | — | — | — | — | — | D(E) | — | — |
| Búsqueda | — | — | — | — | — | — | — | D(L) | — | — |
| Actividad / auditoría | L/E | L | — | — | — | — | — | D(L) | L (avatar) | — |
| Exportación | — | — | — | — | — | — | — | D(L) | L (ZIP) | L (ZIP) |
| Imágenes / adjuntos | — | — | — | — | — | — | — | D(L) | L/E | L/E |
| Usuarios / permisos | D(E) | L/E | L/E | L/E | L | L/E | L/E | L/E | E | E |

Los roles y permisos también se consultan cuando un flujo aplica autorización. La matriz muestra ese soporte como dependencia del módulo usuarios/permisos y destaca `joint_permissions`, que participa en la visibilidad de resultados. Las escrituras de usuarios sobre imágenes, adjuntos y revisiones corresponden a la anulación de autoría durante la eliminación de una cuenta. Esa ruta queda identificada explícitamente y no implica que usuarios gestione el contenido de los archivos.

### Acoplamientos que condicionan la extracción

1. **Contenido y búsqueda.** `BaseRepo::update()` llama a `indexForSearch()` después de guardar. Separar físicamente las tablas rompería esta actualización síncrona. La extracción debe reconstruir el índice propio por API y eventos, con idempotencia y tratamiento de borrado.
2. **Contenido y permisos.** Las consultas visibles dependen de borradores, propietario y permisos efectivos. El índice externo debe conservar las restricciones de acceso; la lectura por un token de servicio necesita un alcance de permisos definido. Diseñar esa autorización queda como decisión de las fases de contratos e implementación.
3. **Contenido y auditoría.** La edición de página invoca `Activity::add()`; el logger persiste y solicita emisión de Webhooks. Auditoría externa necesita identidad de actor, objeto y momento en el evento, y una copia durable en su almacén.
4. **Contenido, medios y revisiones.** La limpieza de imágenes lee HTML actual e histórico. Una extracción de medios necesita conservar referencias y evitar eliminar archivos que aún se usan. `uploaded_to` vincula adjuntos e imágenes con la página y su visibilidad.
5. **Contenido y exportación.** Markdown/PDF recorren entidades visibles y ZIP carga además etiquetas y archivos. El servicio de exportación delegará la lectura autorizada en la API del monolito y mantendrá sus trabajos y artefactos propios.
6. **Usuarios y otros módulos.** El borrado de usuario actualiza autoría y propiedad de contenido, medios y revisiones. La migración debe definir cómo representa las referencias de un actor eliminado sin replicar el esquema compartido.

## F5-E3 / P28 — Mapa de contextos

Los fuentes `fase5-a1-contextos.mmd` y `fase5-a1-contextos-propuesto.mmd` contienen dos vistas. La primera describe los seis contextos lógicos dentro del monolito y sus dependencias observadas. La segunda propone límites para la extracción, con relaciones proveedor → consumidor y capas anticorrupción por API y por Webhooks. El mapa propuesto es un artefacto de diseño de A1. Las decisiones de broker, almacenes y orquestador se justifican en A2.

Usuarios/permisos es proveedor de autorización; contenido provee datos a búsqueda y exportación; medios provee archivos referenciados por contenido; actividad recibe las acciones producidas por contenido y administración. Las ACL adaptan los contratos externos sin trasladar las tablas compartidas a los nuevos servicios. Se preservan las restricciones docentes de integración por API REST y Webhooks.

## Integración en el informe

El informe integrado incorpora el inventario, la matriz, los dos mapas DDD y las 18 capturas disponibles, con referencias y estados P26–P28 completados. Las nuevas capturas cubren claves foráneas, escrituras de contenido e índice, adjuntos, roles, eliminación de usuarios, permisos efectivos y archivos de exportación.
