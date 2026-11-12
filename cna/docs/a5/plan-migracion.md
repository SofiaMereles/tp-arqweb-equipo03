# A5 — Plan de migración y matriz de riesgos

Fecha: 12/11/2026. Estado: diseño de Fase 5; no se ejecutaron cambios en VM-1 ni migraciones de datos.

## Alcance y aceptación docente

Se revisaron las secciones 4.5 y 4.6 del PDF oficial y los criterios globales CA-1–CA-7. A5 exige orden justificado, criterio de hecho por paso, reversión planificada en menos de un minuto y riesgos con probabilidad × impacto y mitigación. Este plan desarrolla ADR-006–010 y respeta los contratos A3 y el modelo A4.

El producto de A5 es un **plan verificable**. Las pruebas de despliegue, rendimiento, recuperación y duración del rollback siguen pendientes de Fase 6/7. No se marca un criterio global como aprobado por estar descrito aquí.

## Principios de transición

1. BookStack, su código y MariaDB se conservan. Las capacidades nuevas se conectan por REST/Webhooks; no se modifica el esquema original ni se entregan credenciales de MariaDB a los servicios.
2. Habilitar una funcionalidad por vez. Preparar primero sus dependencias, procesar en paralelo sin tráfico nuevo de usuario y abrir su ruta solo cuando cumpla el criterio de hecho.
3. Desactivar el tráfico no implica borrar datos, vaciar colas o detener el broker. Mantener información suficiente para reconciliar y volver a habilitar.
4. No retirar la funcionalidad nativa de BookStack. Durante este TP el Strangler agrega entradas `/v2/*` sin eliminar las originales.
5. No reemplazar una implementación HTTP por otra con respuestas incompatibles. La vuelta al monolito se hace mediante acceso nativo explícito, no mediante redirecciones de POST ni respuestas 200 que simulen los esquemas de A3.

## Orden de extracción: de menor a mayor riesgo funcional

La valoración es relativa a esta instalación; no afirma que un servicio tenga menor riesgo en cualquier proyecto. Se priorizan cambios derivados y reversibles antes de introducir trabajos y referencias persistentes.

### M0 — Preparar plataforma y proteger la línea base (prerrequisito)

**Acción.** Verificar VM-1, memoria del anfitrión, red privada y presupuesto de VM-2 antes de crearla. Guardar backup consistente de MariaDB, uploads/adjuntos, configuración de BookStack/Nginx y secretos necesarios para restaurar, fuera de Git y con acceso restringido. Probar restauración aislada. Preparar Swarm, volúmenes, broker, puente y aislamiento de bases; incorporar Redis y MinIO cuando se habiliten S3/S4, evitando cargar procesos innecesarios desde el inicio.

Preparar logs y métricas mínimos desde la integración; completar la observabilidad de A4 antes de sus pruebas. Probar certificados con ambos dominios, conectividad privada y restricciones de puertos. Preparar las variantes de gateway y el acceso nativo del [runbook de reversión](reversion.md) antes de publicar cualquier ruta nueva.

**Hecho cuando:** backup y restauración aislada tienen evidencia; login, crear libro y editar página siguen funcionando; ambos nodos tienen conectividad; se conocen RAM/disco disponibles y límites; solo las entradas autorizadas son accesibles desde fuera; un webhook se persiste antes de 202 y se publica al volver NATS. La configuración de despliegue y secretos permite reproducir el entorno sin subir credenciales. No modificar el contenido original para probar un backup sobre producción.

**Responsable previsto:** rol de infraestructura; otro integrante revisa el resultado. **Estado:** pendiente de ejecución. **Relación:** CA-2, CA-4, CA-5 y CA-7; prepara B1/B3/B4/B5.

### M1 — S2 auditoría: registro paralelo sin intervenir la edición

**Justificación.** Consume hechos y agrega un registro propio; no cambia páginas ni decide la respuesta de búsqueda. Se puede contrastar con la actividad nativa y retirar su consulta sin alterar el contenido. Su durabilidad sigue siendo crítica: menor impacto funcional no significa que se tolere perder auditoría.

**Acción.** Crear `audit_db`/rol, consumidor durable independiente y deduplicación. Ejecutar en paralelo; contrastar actor, objeto, fecha y correlación de eventos aceptados. Solo después habilitar `/v2/audit` para consumidores autorizados.

**Hecho cuando:** filtros y consulta individual cumplen A3; el mismo `event_id` produce un registro; detener S2 dos minutos durante veinte ediciones deja veinte eventos publicados pendientes y se recuperan exactamente una vez como efecto; un evento inválido se conserva en DLQ con causa; BookStack sigue operativo. Retención debe cubrir el ensayo. La prueba distingue eventos que llegaron al puente de webhooks que nunca llegaron: no atribuye a CA-6 una garantía de origen que todavía no existe.

**Responsable:** integración/eventos. **Estado:** pendiente. **Relación:** CA-5/CA-6; F6-E5/P37 y F7-E2/P50. **Reversión:** consulta nativa de actividad para las acciones de BookStack; no se afirma que contenga eventos exclusivos de S3/S4. Conservar la auditoría CNA y su consumidor.

### M2 — S1 búsqueda: proyección reconstruible, con autorización y reconciliación

**Justificación.** El índice es derivado y reconstruible por API. Aumenta el riesgo respecto de S2: entrega contenido al usuario y puede mostrar resultados obsoletos o no autorizados.

**Acción.** Crear `search_db`/rol. Establecer consumidor/cursor durable antes de la carga paginada de páginas y libros; conservar y reproducir cambios concurrentes, serializar por entidad y verificar revisiones y borrados. Comparar búsquedas en paralelo antes de abrir `/v2/search`.

**Hecho cuando:** diez ediciones controladas se reflejan cada una en menos de cinco segundos desde guardado hasta resultado; creación, actualización y borrado mantienen coherencia; una carga inicial con edición concurrente no pierde cambios; resultados, filtros y resaltado cumplen A3; una consulta sin coincidencias entrega 200 vacío. Un consumidor sin alcance autorizado no recibe contenido, ni siquiera texto del índice. S1 caído genera 503 JSON por el gateway mientras login/edición de BookStack siguen disponibles.

Las diez ediciones son el ensayo propuesto del equipo, no un umbral adicional de la consigna. Se registrará cada tiempo, no solo el promedio. Comparar carga c=10/c=50 y latencia con la línea base corresponde a Fase 7.

**Responsable:** servicio de búsqueda. **Estado:** pendiente. **Relación:** CA-3/CA-5; F6-E4/P36, F7-E1/P49, F7-E5/P53 y F7-E6/P54. **Reversión:** búsqueda nativa `/search?term=...`; mantener consumidor para no acumular divergencia.

### M3 — S3 exportación: trabajos recuperables antes de abrir nuevas solicitudes

**Justificación.** Introduce estado de jobs, concurrencia de workers, archivos y aceptación asíncrona. Un rollback debe conservar trabajos ya aceptados: tiene más efectos que retirar una consulta.

**Acción.** Preparar Redis persistente, bucket `exports`, políticas, worker y outbox. Validar sin tráfico de usuario las combinaciones página/libro × PDF/Markdown. Habilitar POST solo después de probar seguimiento y descarga; comenzar con un worker y escalar en el ensayo previsto.

**Hecho cuando:** POST devuelve 202 y un `job_id` consultable; los estados cumplen A3; cada archivo existe, tiene contenido válido y URL firmada accesible por HTTPS del gateway. Repetir clave/cuerpo conserva job; otro cuerpo devuelve 409. Redis inaccesible antes de aceptar devuelve 503 sin anunciar aceptación. Matar un worker permite recuperar el mismo job sin `running` indefinido. Una falla permanente queda `failed` con causa. Estado y outbox son atómicos; NATS caído no pierde la publicación pendiente. Ensayar política AOF y recuperación del volumen antes de atribuir durabilidad.

**Responsable:** exportación/persistencia. **Estado:** pendiente. **Relación:** CA-1/CA-5/CA-7; F6-E6/P38, F6-E7/P39 y F7-E3/P51. Escalado 1→3: F7-E7/P55. **Reversión:** bloquear nuevas solicitudes, conservar GET/descargas y drenar o recuperar jobs; nuevas exportaciones desde la página/libro nativos.

### M4 — S4 medios: archivos y referencias de mayor costo de reversión

**Justificación.** Crea objetos que podrían quedar referenciados en contenido duradero. Desactivar una subida no recupera ni mueve automáticamente esos archivos; por eso se incorpora al final, aunque sea necesario para el máximo del apartado B2.

**Acción.** Preparar bucket y credenciales de medios, límites, metadatos y miniaturas; probar retención/restauración antes de permitir referencias nuevas. Mantener las cargas nativas de BookStack y sus archivos originales. No sustituir URLs antiguas de manera masiva.

**Hecho cuando:** imagen admitida genera original y miniatura proporcional, con metadatos y evento `media.uploaded`; se validan PNG/JPEG/WebP, tamaños, píxeles y acceso según A3; el exceso de tamaño o formato se rechaza; las URLs siguen accesibles tras reiniciar el servicio con su volumen; se prueba restauración aislada y se comprueba publicación recuperable. La caída del servicio no afecta cargas nativas ni lectura del monolito.

**Responsable:** medios/almacenamiento. **Estado:** pendiente. **Relación:** F6-E8/P40 y CA-2/CA-5. **Reversión:** bloquear POST nuevo, volver al editor nativo y mantener GET de objetos existentes, metadatos y miniaturas. No borrar buckets durante la reversión.

### M5 — Consolidar y preparar la entrega

**Hecho cuando:** se han demostrado CA-1–CA-7, incluido el mínimo de tres servicios y la conservación de BookStack; se ejecutan los experimentos y evidencias exigidos de Fases 6/7, se contrastan diagramas con el despliegue y se mide reversión por ruta en menos de sesenta segundos. La recuperación de todos los jobs o del índice puede tardar más y se registra aparte. El repositorio limpio reproduce el despliegue con la configuración y secretos externos documentados.

No crear la etiqueta final `v2.0.0` ni marcar el TP completo antes de esas verificaciones. La Fase 5 cierra el diseño, no la implementación de Fases 6/7.

## Puertas de avance y detención

- Si un paso falla, no habilitar la siguiente funcionalidad. Registrar causa, conservar evidencias y volver a su entrada nativa conforme al runbook; corregir en paralelo.
- Si se pierde autorización, hay corrupción, un volumen no se restaura o la RAM provoca OOM, detener nuevas admisiones inmediatamente. Priorizar la disponibilidad del monolito y preservar datos.
- Si el origen de webhooks no permite recuperar todas las acciones necesarias, no declarar auditoría completa extremo a extremo. Documentar el límite y validar un mecanismo de recuperación de origen sin alterar código de BookStack antes de atribuir esa garantía.
- Todo cambio de broker, topología, semántica de eventos o almacenes actualiza ADR, contrato, A4 y este plan; no se cambia solo la implementación.

## Matriz de riesgos

La fuente editable es [`matriz-riesgos.csv`](matriz-riesgos.csv). Probabilidad (P) e impacto (I) usan escala 1–3: bajo, medio y alto. Puntaje = P×I: 1–2 bajo; 3–4 medio; 6–9 alto. Son estimaciones del equipo para priorizar, no estadísticas medidas. No asignamos porcentajes ficticios.

Cada riesgo tiene mitigación, señal de activación, responsable por rol, verificación y puntaje residual estimado. El residual supone aplicar y comprobar las medidas; no equivale al riesgo actual. R07 mantiene 6 hasta validar recuperación del origen; R05 conserva impacto alto porque no se incorpora alta disponibilidad del gateway.

`generar-matriz.py` comprueba IDs, escalas y productos y genera `matriz-riesgos.tex`, que incorpora el informe. La evaluación operativa de los riesgos queda pendiente.

## Trazabilidad y evidencias

La consigna no asigna F5-E8 ni una P específica a A5: no se inventan esos identificadores. El plan, runbook, CSV y LaTeX constituyen sus entregables documentales. Los resultados de una futura prueba de rollback se guardarán con nombre descriptivo y referencia a A5, sin presentarlos como una prueba oficial numerada nueva.

La [lista de evidencias A5](../evidencias/fase5/a5/README.md) indica qué conservar al ensayar. Todas las mediciones de duración figuran **pendientes** hasta ejecutar el procedimiento real.

## Referencias

- Consigna local: `cna/TP_Integrador_II_BookStack_Cloud_Native.pdf`, secciones 2, 4.5, 4.6 y 7.2–7.4.
- ADR-006–010, contratos A3 y diagramas A4 de este repositorio.
- [NGINX: prueba de configuración](https://nginx.org/en/docs/switches.html).
- [NGINX: control y recarga](https://nginx.org/en/docs/control.html).
