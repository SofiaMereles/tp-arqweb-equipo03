# ADR-006 — Estrategia de migración e integración con el monolito

## Estatus

Aceptado para el diseño por el equipo.

## Contexto

BookStack debe continuar atendiendo la gestión documental durante la extracción de búsqueda, auditoría, exportación y medios. La consigna establece integración por API REST y Webhooks y exige conservar el código fuente del monolito.

En A1 se verificó que el guardado de entidades persiste atributos comunes y específicos, invoca la indexación y registra actividad. La visibilidad de contenido y archivos depende de usuarios y permisos efectivos. Estos acoplamientos hacen necesario definir una frontera de integración que mantenga la autorización y permita incorporar los servicios gradualmente.

## Decisión

Aplicar Strangler Fig incorporando los servicios alrededor de BookStack. El Nginx de VM-1 expondrá las rutas `/v2/` de los servicios mediante el dominio `api.bookstack.local`. BookStack mantendrá la gestión documental y su dominio actual.

Los servicios que necesitan contenido lo obtendrán mediante la API REST, con una cuenta de servicio y los permisos necesarios para cada operación. Los cambios de páginas se recibirán por Webhooks en `event-bridge`, que adaptará los mensajes a los contratos de eventos y los publicará para sus consumidores. Cada adaptador HTTP o de eventos funcionará como capa anticorrupción entre los modelos del monolito y los contratos de los servicios.

La habilitación de las nuevas funcionalidades será gradual. El gateway permitirá desactivar una ruta del servicio y devolver el acceso a la funcionalidad equivalente del monolito conforme al procedimiento de reversión que se documentará en A5.

## Alternativas descartadas

- **Reemplazar BookStack en una sola entrega.** Concentra el riesgo de migración de contenido, usuarios y permisos en una única intervención y dificulta conservar la operación durante la transición.
- **Integrar los servicios mediante consultas directas a MariaDB.** Acopla los servicios a las tablas compartidas observadas en A1 y puede omitir los filtros de autorización de BookStack. Además, incumple la restricción docente de acceso a MariaDB desde los microservicios.
- **Modificar BookStack para invocar los nuevos servicios.** Obliga a mantener cambios propios sobre el código del monolito y contradice la vía de integración exigida por la consigna.

## Consecuencias

### Favorables

- Permite incorporar y verificar una funcionalidad por vez manteniendo la gestión documental disponible.
- Usa las interfaces del monolito como frontera de integración y conserva sus controles de acceso en las lecturas de API.
- Facilita desactivar una ruta externa ante fallos del servicio extraído.
- Los contratos propios permiten evolucionar los servicios con persistencia independiente.

### Costos y limitaciones

- La API de BookStack pasa a ser una dependencia de los servicios de búsqueda y exportación, con latencia adicional y necesidad de timeouts y tratamiento de errores.
- El índice y la auditoría externa se actualizarán de forma asíncrona, por lo que habrá un intervalo de consistencia eventual.
- La integración necesita operación adicional de gateway, adaptadores, broker y credenciales, además de observabilidad entre componentes.
- La lectura con un token de servicio exige definir el alcance de visibilidad de los resultados del servicio, especialmente en búsqueda y exportación.
- La recolección inicial y la recuperación ante eventos fallidos requieren procedimientos explícitos. Su entrega, deduplicación y reintento se especificarán en ADR-007 y ADR-010.

## Respaldo y validación prevista

El inventario, la matriz y los mapas de A1 respaldan el contexto de esta decisión. En Fase 6 se verificará la lectura mediante API, el recorrido edición → Webhook → evento → reindexación y el acceso mediante gateway. La implementación se contrastará con esos resultados antes de considerar validado el diseño.
