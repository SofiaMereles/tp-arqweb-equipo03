# ADR-009 — Base de datos por servicio

## Estatus

Aceptado para el diseño por el equipo. Versiones de imágenes, cuotas y permisos se verificarán durante la implementación.

## Contexto

A1 mostró tablas compartidas de contenido, índice, actividad y autorización. Los nuevos servicios necesitan persistencia propia, reemplazo de contenedores sin pérdida de datos e independencia respecto del esquema de BookStack. MariaDB debe permanecer accesible localmente en VM-1 y los microservicios deben integrarse por API y eventos.

## Decisión

Usar persistencia lógica independiente por servicio, con credenciales y permisos específicos, migraciones propias y almacenamiento fuera de la capa escribible del contenedor.

| Servicio | Almacén propuesto | Propiedad de datos |
|---|---|---|
| S1 búsqueda | PostgreSQL, base `search_db`, rol propio | Proyección del contenido, índice de texto completo y eventos aplicados. El índice se reconstruye por API y eventos. |
| S2 auditoría | PostgreSQL, base `audit_db`, rol propio | Registros de eventos, actor, objeto, fecha y `request_id`; unicidad de `event_id`. |
| S3 exportación | Redis para trabajos; bucket `exports` en MinIO | Estados y cola de jobs, resultados y archivos con URLs prefirmadas temporales. API y workers de S3 comparten esos datos porque pertenecen al mismo servicio. |
| S4 medios | Bucket `media` en MinIO, credencial y política propias | Originales y miniaturas identificados por claves de objetos y metadatos. |
| event-bridge (plataforma) | PostgreSQL, base `bridge_db`, rol propio | Inbox de Webhooks aceptados, deduplicación y outbox de publicación. |

El contrato A3 incorpora la persistencia del puente después de comprobar que la ruta de envío de Webhooks instalada registra errores sin programar un reintento del mismo envío. La confirmación HTTP se emite después de guardar la entrada y su publicación pendiente en la misma transacción.

Inicialmente `search_db` y `audit_db` podrán residir en una sola instancia PostgreSQL para limitar procesos en la VM. Cada rol tendrá `CONNECT` y permisos únicamente sobre su base. Se revocarán privilegios públicos que permitan acceso cruzado y se probará el rechazo entre roles. Ningún servicio dispondrá de un usuario superadministrador ni consultará las tablas del otro.

Los buckets compartirán una instancia MinIO con políticas separadas. Redis se dedicará a S3 y se configurará con persistencia AOF y volumen. Su política de sincronización y la recuperación de jobs se probarán antes de aceptar la durabilidad del flujo. La URL prefirmada deberá ser accesible desde el cliente a través del gateway y mantener la firma válida.

La clave y la contraseña de MariaDB no se entregarán a los servicios. La API de BookStack proveerá el contenido autorizado que necesiten. Los volúmenes persistentes se ubicarán y respaldarán conforme al ADR-008.

## Alternativas descartadas

- **Compartir tablas o credenciales de MariaDB.** Conserva el acoplamiento analizado y evita la frontera de autorización y contratos establecida para los servicios.
- **Una única base con tablas y usuario compartidos para todos los servicios.** Permite consultas y cambios cruzados que comprometen la autonomía y la propiedad de datos.
- **Una instancia PostgreSQL por servicio desde el inicio.** Refuerza el aislamiento físico, pero agrega procesos y consumo fijo. Se empieza con bases y roles aislados en una instancia y se conserva la posibilidad de separarlos físicamente.
- **Meilisearch para S1.** Es una alternativa especializada válida. Se propone PostgreSQL FTS para combinar proyección, índice y deduplicación en transacciones del servicio y reutilizar operación de un solo motor relacional. La latencia de búsqueda se medirá; la elección no implica superioridad de rendimiento.
- **Archivos dentro del contenedor.** La recreación del contenedor comprometería su conservación. Se usan volúmenes del almacén y almacenamiento de objetos.

## Consecuencias

### Favorables

- Cada servicio evoluciona su esquema y solo expone datos mediante contratos.
- El índice y la auditoría pueden registrar el procesamiento del evento junto con su resultado en su propia transacción.
- La recreación de APIs y workers conserva los datos administrados por los almacenes.

### Costos y limitaciones

- La instancia PostgreSQL compartida conserva un dominio de falla y competencia de recursos comunes, aunque las bases estén aisladas lógicamente.
- MinIO compartido también concentra disponibilidad y disco. Las políticas deben impedir acceso de S4 al bucket de S3 y viceversa.
- Redis, PostgreSQL y MinIO requieren volúmenes, cuotas, backup y pruebas de restauración.
- Los datos replicados por eventos tienen consistencia eventual y necesitan procedimientos de recuperación.
- AOF, volúmenes y confirmaciones no sustituyen la prueba de durabilidad frente al tipo de falla elegido.

## Respaldo y validación prevista

Guardar el inventario de almacenes, permisos por rol/bucket, pruebas negativas de acceso cruzado, recreación de contenedores y recuperación de datos. Verificar en VM-1 que ningún servicio abra conexiones a MariaDB. Registrar la persistencia de trabajos de exportación y la descarga de archivos por el gateway.

## Fuentes

- [Privilegios de PostgreSQL](https://www.postgresql.org/docs/current/ddl-priv.html)
- [Persistencia de Redis](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)
