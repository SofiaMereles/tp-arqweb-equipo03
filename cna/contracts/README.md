# A3 — Contratos HTTP y eventos

## Alcance docente

La consigna, sección 4.3, exige OpenAPI 3.1 por servicio, AsyncAPI 3.0 con seis canales, sobre común, versionado y validación sin errores. Se incluyen S1–S4 para cubrir la funcionalidad de medios y el contrato interno de `event-bridge` para cerrar la integración. Son contratos de diseño de la Fase 5. Las implementaciones y pruebas en vivo corresponden a Fase 6.

| Archivo | Operaciones funcionales |
|---|---|
| `search-svc.openapi.yaml` | `GET /v2/search?q=`; resultados de libros y páginas, con resaltado y enlaces a BookStack |
| `audit-svc.openapi.yaml` | `GET /v2/audit?entity=&id=&from=&to=`, `GET /v2/audit/{event_id}` |
| `export-svc.openapi.yaml` | `POST /v2/exports` → 202 + `job_id`; `GET /v2/exports/{job_id}` → queued/running/done/failed |
| `media-svc.openapi.yaml` | `POST /v2/media`, metadatos y descarga de original/miniatura |
| `event-bridge.openapi.yaml` | `POST /internal/webhooks/bookstack?token=…` sobre la red privada |
| `bookstack.asyncapi.yaml` | Los seis canales de eventos requeridos y sus productores y consumidores |

Cada servicio documenta también `/healthz`, `/readyz` y `/metrics` sobre su servidor interno. Los endpoints operativos se separan del gateway público mediante `servers` por operación.

La carga inicial de búsqueda recorre `/api/pages` y `/api/books` con paginación. La respuesta distingue `entity_type` y `entity_id`, y el filtro opcional `entity_type` limita los resultados a libros o páginas. Los eventos de páginas actualizan su proyección y la revisión del catálogo de libros se complementa mediante la API.

## Qué significan las respuestas

- **200** entrega un resultado de consulta, imagen terminada o reconocimiento de Webhook duplicado.
- **202** acepta trabajo asíncrono de exportación o guarda de forma durable un Webhook. La finalización se consulta por `job_id` o se observa en los consumidores.
- **400** indica entrada inválida, UUID mal formado o filtros incompatibles.
- **404** identifica un recurso inexistente o no visible cuando el endpoint recibe un identificador. Una búsqueda sin coincidencias devuelve 200 y una lista vacía.
- **503** usa el mismo esquema JSON `Error` cuando un servicio o dependencia requerida no está disponible.
- **401/403** describen credenciales y autorización. **409** protege claves de idempotencia. **413/415** limitan las subidas. **429** expresa el límite del gateway.

Los códigos se aplican según la semántica de cada operación. Un GET de búsqueda no acepta un trabajo y por eso no devuelve 202. El conjunto de contratos cubre 200, 202, 400, 404 y 503 exigidos por la consigna. Los ejemplos están validados contra sus esquemas.

## Seguridad y alcance de visibilidad

Las APIs `/v2/` requieren `X-API-Key`, una credencial del consumidor del laboratorio configurada por secreto. El token interno de BookStack se utiliza exclusivamente desde los servicios hacia su API. La clave del cliente debe mapearse a un alcance autorizado antes de devolver contenido o archivos.

La primera implementación se limita al conjunto de contenido compartido autorizado para la cuenta de servicio y los consumidores del laboratorio. Para admitir permisos distintos por usuario se necesita una proyección o verificación de autorización por consumidor. No se puede asumir que ocultar la URL de BookStack protege el texto ya devuelto por el índice. Este alcance se verificará durante la implementación y cualquier ampliación requerirá actualizar contratos y pruebas de autorización.

El puente usa el token en query requerido por B4 y valida antes de persistir. La query debe redactarse en los logs del puente y del proxy. Los ejemplos y los contratos no incluyen credenciales reales.

## Sobre común y canales

`EventEnvelope` exige `event_id` (UUID), `type`, `version`, `occurred_at` (date-time ISO 8601 con zona), `request_id` y `payload`. `traceparent` es opcional para instrumentación distribuida.

| Canal | Productor | Consumidores de diseño |
|---|---|---|
| `bookstack.page.created` | event-bridge | search-svc y audit-svc, consumidores durables separados |
| `bookstack.page.updated` | event-bridge | search-svc y audit-svc, consumidores durables separados |
| `bookstack.page.deleted` | event-bridge | search-svc y audit-svc; búsqueda elimina la proyección |
| `export.requested` | API/outbox de export-svc | audit-svc |
| `export.completed` | worker/outbox de export-svc | audit-svc |
| `media.uploaded` | media-svc | audit-svc |

El job ejecutable se reserva en Redis conforme a ADR-009. `export.requested` en NATS documenta el hecho y permite auditoría; no es una segunda cola ejecutable que duplique el trabajo. La escritura del job y del outbox de publicación debe ser atómica. La publicación pendiente se recupera después de una caída.

Los consumidores confirman después de guardar sus efectos, deduplican por `event_id` y aplican el tratamiento de reintentos y DLQ de ADR-010. La deduplicación del broker es complementaria. Los mensajes de ejemplo tienen UUID distintos para hechos distintos.

## Normalización de los Webhooks reales

Se contrastó el formato con `app/Activity/Tools/WebhookFormatter.php` y el envío con `app/Activity/DispatchWebhookJob.php` del paquete relevado en A1.

| Campo del Webhook | Campo normalizado |
|---|---|
| `page_create`, `page_update`, `page_delete` | `type` bookstack.page.created/updated/deleted |
| `triggered_at` | `occurred_at` |
| `triggered_by.id` y `.name` | `payload.actor` |
| `related_item.id` | `payload.page_id` |
| `related_item.book_id`, si existe | `payload.book_id` |
| `related_item.current_revision.revision_number` o `revision_count`, si existe | `payload.source_revision`, versión monotónica del contenido por página |
| UUID asignado al aceptar por primera vez | `event_id` |
| Cabecera recibida o identificador generado al ingresar al puente | `request_id` |

El puente acepta los campos adicionales que BookStack ya emite y solo copia al sobre los datos definidos por el contrato. La deduplicación de entrada conserva durante al menos siete días la huella SHA-256 del JSON canónico del cuerpo por Webhook y su UUID normalizado. Un reintento idéntico conserva su `event_id`. Dos acciones distintas con el mismo cuerpo original son indistinguibles sin un identificador fuente adicional; se validará el comportamiento con revisiones reales antes de atribuir deduplicación perfecta a la entrada.

### Ajuste de durabilidad identificado al revisar el código

En la versión relevada, `DispatchWebhookJob::handle()` registra el error HTTP o de conexión y termina el método. Esa ruta no programa un nuevo intento del mismo envío. Por eso `event-bridge` guardará inbox y outbox en una transacción local **antes de responder 202**. El publicador del outbox podrá esperar a que NATS vuelva sin perder la entrada ya aceptada. Esto agrega `bridge_db` y un rol exclusivo en PostgreSQL, con el mismo aislamiento lógico de ADR-009.

La confirmación 202 cubre eventos persistidos en el puente. Una caída que impida que el Webhook llegue al puente requiere un procedimiento de recuperación de origen. La reconciliación por API recupera el índice, pero por sí sola no reconstruye toda la auditoría de las acciones perdidas. El alcance de la prueba CA-6 se verificará expresamente con consumidores detenidos y entradas aceptadas.

### Correlación

El gateway genera `X-Request-ID` y los servicios lo conservan en llamadas, respuestas, eventos y logs. El Webhook observado no incorpora automáticamente la cabecera de la edición original. El puente inicia su correlación si la recibe ausente. Antes de la prueba de trazas de Fase 7 se deberá incorporar y verificar instrumentación que propague el contexto del envío HTTP de BookStack; el contrato no certifica que esa propagación ya esté implementada.

## Versionado

Las versiones de ruta HTTP y de evento son independientes.

1. La API actual usa `/v2/`. `info.version: 1.0.0` identifica la revisión del contrato de esa API, no cambia su ruta.
2. Las estructuras actuales son estrictas. Las correcciones de redacción o nuevos ejemplos que no alteren el mensaje pueden publicarse como parche del contrato.
3. Un cambio incompatible crea rutas `/v3/` con contratos separados. El gateway mantiene `/v2/` operativo durante la migración y publica un calendario de retiro. Los consumidores existentes continúan con sus esquemas.
4. Los eventos actuales tienen `version: '1.0'` y se publican en los seis subjects definidos. Sus campos y significado se conservan mientras existan consumidores de esa versión.
5. Un cambio incompatible de eventos usa `version: '2.0'` y subjects separados, por ejemplo `v2.bookstack.page.updated`, con contratos y consumidores propios. Se publica a ambas versiones desde el mismo hecho durante la transición. Los consumidores antiguos solo se suscriben a sus subjects compatibles.
6. Los dos mensajes de versiones de un mismo hecho conservan el identificador lógico y el `request_id`. Cada proyección deduplica en su propio almacén. Una proyección no debe consumir simultáneamente ambas representaciones sin una estrategia explícita.
7. Agregar campos al sobre o al payload estricto requiere versionar el esquema y planificar su migración; no se presenta como un cambio transparente para validadores antiguos.

## Validar y guardar F5-E4 / P29

Requisitos locales: Node.js 22 o superior y pnpm. Las dependencias de herramientas están fijadas por `pnpm-lock.yaml`; sus scripts de instalación se deshabilitan porque no son necesarios para los validadores. El paquete de telemetría Scarf queda expresamente deshabilitado.

Desde `cna/contracts`:

```bash
pnpm install --frozen-lockfile --ignore-scripts
pnpm run validate
```

`validate.mjs` ejecuta Spectral para cada OpenAPI, el parser oficial de AsyncAPI para el documento de eventos y AJV para los ejemplos. Comprueba también las versiones, los seis canales y los campos obligatorios del sobre. Un fallo termina con código distinto de cero.

Los resultados reales y los SHA-256 de los seis contratos se guardan en:

- `cna/docs/evidencias/fase5/a3/validation-report.json`
- `cna/docs/evidencias/fase5/a3/validation-summary.txt`

El parser puede emitir una recomendación informativa para actualizar AsyncAPI a 3.1. Se conserva 3.0 porque es la versión exigida por la consigna. Errores y advertencias hacen fallar la validación; las recomendaciones informativas se conservan en el informe de resultados.

Para la captura `F5-E4-validacion-contratos.png`, ejecutar en terminal el comando de validación y mostrar su resumen, con usuario y hostname del equipo donde se ejecuta. En Windows se puede mostrar `whoami` y `hostname` antes del comando. Guardar también el log completo, no solo la captura.

## Referencias

- [OpenAPI 3.1.0](https://spec.openapis.org/oas/v3.1.0.html)
- [AsyncAPI 3.0.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0)
- [Spectral](https://github.com/stoplightio/spectral)
- [Parser oficial de AsyncAPI](https://github.com/asyncapi/parser-js)
