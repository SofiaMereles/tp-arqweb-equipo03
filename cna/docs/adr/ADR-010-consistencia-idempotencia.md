# ADR-010 — Consistencia eventual, idempotencia y mensajes fallidos

## Estatus

Aceptado para el diseño por el equipo. Las garantías se verificarán con pruebas de duplicación, reentrega, caída y recuperación.

## Contexto

La búsqueda y la auditoría se actualizan de forma asíncrona. Un mensaje puede entregarse nuevamente si el consumidor guarda el resultado y falla antes de confirmar. También puede fallar de forma transitoria o permanente, llegar fuera de orden o agotar su ventana de conservación. La edición de una página debe reflejarse en el índice en menos de cinco segundos según los criterios del TP.

## Decisión

Adoptar consistencia eventual y entrega al menos una vez, con efectos idempotentes por consumidor. El identificador `event_id` pertenece al evento lógico y se mantiene en sus reintentos y reenvíos a DLQ. El sobre incluye además `type`, `version`, `occurred_at`, `request_id` y `payload`, que se definirán en AsyncAPI durante A3.

### Persistencia y confirmación

1. Validar el sobre y la versión antes de aplicar el evento.
2. En auditoría, usar una restricción única por `event_id`. La inserción y cualquier marca de procesamiento se confirman en una misma transacción local.
3. En búsqueda, mantener el registro del evento aplicado y la actualización de la proyección en una misma transacción de `search_db`. La consulta a la API ocurre con timeout y tratamiento de errores; el guardado se serializa por entidad y respeta versiones de contenido cuando estén disponibles.
4. Confirmar el mensaje al broker después de completar la transacción. Si el evento ya está aplicado, reconocerlo sin repetir el efecto.
5. Ante una falla previa al commit, permitir la reentrega. Si el commit se completó pero se perdió el ack, la restricción de idempotencia evita el efecto duplicado.

El registro de deduplicación debe conservarse como mínimo durante la retención y la ventana de replay de los eventos. Cada consumidor tiene su registro propio, por lo que S1 y S2 pueden procesar legítimamente el mismo `event_id` una vez cada uno.

### Orden y reconciliación

S1 consultará el estado actual de la página y serializará sus actualizaciones por entidad. Se documentará el criterio de versión o reconciliación para evitar que una respuesta antigua sobrescriba una nueva. Un borrado conserva una marca de eliminación o un criterio equivalente para evitar resurrección por eventos atrasados. Un error de autorización o un timeout no se interpretará como prueba de borrado.

La indexación inicial y la reconciliación por API complementan los Webhooks. El orden de creación del consumidor y de la carga inicial, junto con el replay, debe cubrir las ediciones concurrentes con esa carga. Las condiciones exactas se formalizarán en los contratos y pruebas de S1.

### Reintentos y DLQ

Se propone un máximo de cinco intentos por consumidor, con esperas crecientes y jitter, y timeouts explícitos hacia BookStack. Los errores permanentes de esquema o versión se envían a DLQ con su causa, mientras los transitorios usan reintentos acotados.

La DLQ conservará el sobre original, el consumidor, la causa, los intentos y las marcas temporales. El traslado espera confirmación de persistencia en el destino antes de reconocer o terminar el original. Si ocurre una caída entre esos pasos, la duplicación en la DLQ se controla con la clave `(consumer, event_id)`.

JetStream requiere implementar esa transferencia. Se supervisarán también los avisos de entrega agotada para recuperar mensajes que lleguen al límite después de la caída de un consumidor. Los mensajes agotados deben quedar recuperables en el stream hasta confirmar su traslado. El monitoreo alertará por DLQ y por mensajes agotados pendientes de transferencia.

El replay conserva el `event_id`. Un evento que nunca se aplicó podrá procesarse tras corregir su causa. Una reparación que busque cambiar un efecto ya aplicado requerirá una operación explícita de reconciliación o compensación, con un nuevo identificador y relación con el original.

### Trabajos de exportación

La idempotencia de una solicitud HTTP se tratará mediante una clave de solicitud y su `job_id`, separada del `event_id` de sus eventos. La creación del estado y la inserción en la cola de Redis deben ser atómicas. El worker tendrá un mecanismo de reserva recuperable y actualizará estado y resultado de forma idempotente. Una caída no debe dejar un job en `running` indefinidamente. El objeto tendrá una clave estable por job para permitir reintentos sin multiplicar resultados.

## Alternativas descartadas

- **Confirmar antes de guardar.** Una caída entre ack y persistencia puede perder el efecto de un mensaje ya reconocido.
- **Suponer entrega exactamente una vez para toda la operación.** La transacción del almacén y el ack del broker son pasos diferentes. Las capacidades de deduplicación del broker no sustituyen la idempotencia del efecto de negocio.
- **Reintentar indefinidamente.** Un mensaje inválido puede consumir capacidad y ocultar una falla permanente.
- **Deduplicar solo en memoria.** El reinicio del proceso pierde el registro de eventos aplicados.
- **Descartar al agotar intentos.** Impide diagnosticar y recuperar el evento, contrario al objetivo de entrega confiable del TP.

## Consecuencias

### Favorables

- Permite recuperar eventos tras una caída y evitar efectos duplicados verificables.
- Los fallos permanentes quedan disponibles para diagnóstico y replay controlado.
- Las restricciones locales y el ack posterior mantienen consistente la proyección de cada servicio frente a reentregas.

### Costos y limitaciones

- El usuario puede observar temporalmente datos anteriores en búsqueda mientras se procesa un evento.
- Se requieren tablas de eventos procesados, versiones o serialización por entidad, cuotas y limpieza compatible con el replay.
- La DLQ y su transferencia agregan código y operación y necesitan pruebas de caída en sus puntos intermedios.
- El umbral de cinco segundos depende de carga, disponibilidad y reintentos. Su cumplimiento se medirá desde la edición hasta la consulta del índice.
- La durabilidad comienza en la aceptación persistente de cada tramo. Se deberá comprobar también la recuperación del tramo BookStack → event-bridge.

## Respaldo y validación prevista

Enviar el mismo evento dos veces y verificar un solo efecto por consumidor. Detener auditoría mientras se editan 20 páginas y comprobar su recuperación. Forzar un error permanente y observar la DLQ. Interrumpir el consumidor después del commit y antes del ack. Probar orden invertido de actualización/borrado y caída de un worker durante un job. Conservar logs, IDs y tiempos de cada experimento.

## Fuentes

- [Persistencia y entrega de JetStream](https://docs.nats.io/concepts/jetstream)
- [Consumidores y confirmaciones](https://docs.nats.io/learn/jetstream/pull-consumers)
- [Redis Streams y grupos de consumidores](https://redis.io/docs/latest/develop/data-types/streams/)
