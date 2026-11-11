# ADR-007 — Selección del broker de mensajes

## Estatus

Aceptado para el diseño por el equipo. Validación operativa prevista en Fase 6.

## Contexto

Una edición de BookStack debe actualizar búsqueda y auditoría mediante el mismo evento. Los consumidores necesitan posiciones independientes y recuperación de mensajes publicados mientras están detenidos. Se requieren persistencia, confirmación manual, reintentos limitados y mensajes fallidos conservados para diagnóstico. El laboratorio tiene recursos de memoria acotados.

## Decisión

Usar NATS con JetStream habilitado como broker de eventos. Configurar un stream de páginas con almacenamiento en archivo sobre un volumen persistente y consumidores pull durables independientes para búsqueda y auditoría. Cada consumidor tendrá confirmación explícita después de persistir su resultado. Los trabajos de exportación conservarán su mecanismo de cola propio conforme a ADR-009.

El refinamiento de A3 establece que `event-bridge` guardará inbox y outbox de forma atómica antes de devolver 202 al Webhook. El publicador espera la confirmación de JetStream antes de marcar la salida como enviada. Esta separación permite recuperar la publicación si el broker está temporalmente caído. Mantendrá el mismo `event_id` al reintentar un evento ya normalizado. Si BookStack entrega de nuevo un Webhook sin identificador estable, el adaptador debe reconocer esa repetición conforme al contrato de entrada; la idempotencia por `event_id` del consumidor no resuelve por sí sola dos IDs diferentes para la misma acción.

El diseño inicial utiliza un broker con una réplica de almacenamiento. Esto cubre reinicios del proceso y del nodo con el mismo disco disponible. La réplica única concentra la disponibilidad del broker en ese nodo y no protege frente a pérdida del volumen.

Se usarán límites explícitos de memoria, disco y retención. La capacidad y el período de conservación deben cubrir las pruebas de caída de consumidores y medirse antes del despliegue final. La recuperación a DLQ se implementará explícitamente conforme a ADR-010. Alcanzar `MaxDeliver` en JetStream no equivale a mover automáticamente el mensaje a una DLQ.

## Alternativas descartadas

| Alternativa | Qué ofrece | Motivo de descarte para este diseño |
|---|---|---|
| RabbitMQ | Acknowledgements, publisher confirms, enrutamiento y dead-lettering configurable. | Es válido para el TP, pero requeriría adoptar su modelo de exchanges, colas y políticas. Se prefiere el modelo de stream con consumidores independientes para los eventos de páginas. El consumo relativo de RAM entre productos no se considera medido. |
| Redis Streams como broker general | Streams, grupos de consumidores, pendientes y recuperación de trabajo. | Redis se reserva para los trabajos de exportación. Separar el broker de eventos permite administrar su retención y consumidores sin compartir el ciclo de vida de los jobs. Redis Streams también necesitaría políticas explícitas de persistencia y mensajes fallidos. |
| Core NATS sin JetStream | Pub/sub entre procesos conectados. | La persistencia y recuperación de eventos durante la caída de consumidores requieren JetStream. |

## Consecuencias

### Favorables

- Un mismo evento de página puede ser procesado por búsqueda y auditoría con cursores separados.
- El consumidor puede recuperar mensajes pendientes después de un reinicio.
- Los ack explícitos permiten confirmar después de guardar el efecto del evento.
- Stream y consumidores forman una frontera de integración independiente de las tablas de BookStack.

### Costos y limitaciones

- Hay que operar el volumen, los límites de retención, el monitoreo de pendientes y el procedimiento de DLQ.
- La entrega al menos una vez permite duplicados, por lo que exige idempotencia en cada servicio.
- Una instancia inicial es un punto único de falla. La indisponibilidad del broker necesita reintentos del productor y visibilidad de los fallos de Webhooks.
- Una confirmación del broker no demuestra que los consumidores ya hayan procesado el evento.
- La elección por modelo operativo debe contrastarse con consumo real. No se atribuyen cifras de ahorro de RAM sin una medición.

## Respaldo y validación prevista

Guardar configuración de streams y consumidores, prueba de publicación confirmada, reinicio del consumidor y prueba de DLQ. Medir memoria y disco con la carga de laboratorio. La aceptación de Webhooks durante una caída del broker debe probarse desde BookStack; si no ofrece reintentos suficientes, habrá que agregar almacenamiento durable de entrada en `event-bridge` antes de reconocer el evento.

## Fuentes

- [JetStream y su modelo de persistencia y consumidores](https://docs.nats.io/concepts/jetstream)
- [Consumidores pull y confirmaciones](https://docs.nats.io/learn/jetstream/pull-consumers)
- [RabbitMQ, acknowledgements y publisher confirms](https://www.rabbitmq.com/docs/confirms)
- [Redis Streams](https://redis.io/docs/latest/develop/data-types/streams/)
