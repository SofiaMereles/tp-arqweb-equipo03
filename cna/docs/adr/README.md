# A2 — Registro de decisiones de arquitectura

Cada ADR conserva Estatus, Contexto, Decisión y Consecuencias, y documenta alternativas descartadas y costos. Los recuadros docentes fijan el tema y las restricciones. El equipo debe justificar su elección sobre el entorno real.

| ADR | Tema | Estado |
|---|---|---|
| [ADR-006](ADR-006-migracion-integracion.md) | Migración e integración | Aceptado para diseño |
| [ADR-007](ADR-007-broker-mensajes.md) | NATS JetStream, consumidores durables y confirmaciones | Aceptado para diseño |
| [ADR-008](ADR-008-orquestacion.md) | Swarm de dos VM, condicionado al presupuesto de recursos | Aceptado para diseño |
| [ADR-009](ADR-009-persistencia-servicios.md) | Almacenes propios y aislamiento lógico por servicio | Aceptado para diseño |
| [ADR-010](ADR-010-consistencia-idempotencia.md) | Consistencia eventual, idempotencia y DLQ | Aceptado para diseño |

En A2 el artefacto principal es el documento de decisión versionado. La consigna no asigna una nueva evidencia F5 exclusiva a cada ADR. Las comparaciones y mediciones usadas para decidir deben conservarse como respaldo y distinguirse de resultados aún por ejecutar en Fase 6.

A2 completado con ADR-006 a ADR-010 aceptados por el equipo e integrados en el informe. La validación operativa de las decisiones corresponde a Fase 6. La condición de recursos de ADR-008 se conserva para ejecutar la topología elegida.
