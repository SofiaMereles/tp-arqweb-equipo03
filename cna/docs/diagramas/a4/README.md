# A4: C4 y secuencias de BookStack CNA

## Cómo leerlos

- **C4 nivel 1:** una caja representa toda la plataforma; las personas alrededor son quienes la utilizan. El alcance incluye BookStack y los servicios nuevos, por eso BookStack no se presenta como un sistema externo.
- **C4 nivel 2:** abre esa caja para mostrar las unidades que ejecutan código y guardan datos. Un contenedor C4 no equivale necesariamente a Docker: BookStack/PHP-FPM y MariaDB también son contenedores del modelo. Las agrupaciones por VM añaden la información de despliegue que pide la consigna.
- **Secuencias:** leer de arriba hacia abajo. Cada columna es un participante; las flechas son mensajes. `alt` muestra alternativas, incluidos errores; `par` muestra consumidores independientes que pueden trabajar en paralelo. `newpage` divide una secuencia larga en láminas, sin convertirla en otra interacción.

## Estado y criterios de aceptación

Se revisaron las secciones 3.2–3.4, 4.4, 4.6 y la matriz de evidencias del PDF oficial. Este apartado representa la **arquitectura objetivo** de Fase 5. BookStack en VM-1 y el acceso SSH por `ens37` están verificados; VM-2, Swarm, servicios y telemetría nuevos siguen pendientes de implementación. La coherencia con el despliegue real se deberá revisar al terminar Fase 6. No se certifica ese despliegue con dibujos.

| Prueba / evidencia | Fuentes `.puml` | Láminas generadas |
|---|---|---|
| P30 / F5-E5 | `F5-E5-c4-contexto.puml` | Contexto completo: actores, plataforma y accesos. |
| P31 / F5-E6 | `F5-E6-01-c4-contenedores.puml`, `F5-E6-02-c4-operacion.puml` | Un modelo de nivel 2 en dos vistas: aplicaciones/datos y operación/telemetría. |
| P32 / F5-E7, interacción 1 | `F5-E7-01-edicion-indexacion.puml` | Principal y errores (`_001`): webhook, persistencia, broker, S1, S2, reentrega y DLQ. |
| P32 / F5-E7, interacción 2 | `F5-E7-02-busqueda.puml` | Búsqueda síncrona; errores de entrada, acceso, gateway y base. |
| P32 / F5-E7, interacción 3 | `F5-E7-03-exportacion.puml` | Principal y errores (`_001`): 202/job, Redis, worker, API, MinIO, consulta, recuperación y fallo. |

Las imágenes están en [`../../evidencias/fase5/a4/`](../../evidencias/fase5/a4/). **PNG** sirve para visualizar e incluir en LaTeX; **SVG** conserva el texto y las líneas al ampliar y permite revisar las láminas densas. No hace falta capturar una terminal para sustituir estos diagramas: son las evidencias de diseño solicitadas. El registro de compilación y hashes acompaña sus fuentes.

## Decisiones reflejadas

- ADR-006–010 y contratos A3: REST/Webhooks sin acceso directo de los servicios a MariaDB; NATS JetStream; Swarm; bases y roles separados; jobs en Redis; objetos en MinIO.
- VM-1 conserva BookStack y Nginx. Manager Swarm en `drain` previsto; VM-2 aloja tareas y volúmenes locales. Un manager y un broker no son alta disponibilidad.
- La IP observada de VM-1 en Solo host es `192.168.145.129`. La IP física de `ens33` usa DHCP y cambia; la IP interna de VM-2 se asignará antes del despliegue. No se inventa una IP desplegada para ese nodo.
- El nivel 1 muestra personas y sistema; el nivel 2 agrega nodos, puertos y protocolos sin confundir el contexto con un diagrama de red.
- La observabilidad contempla Prometheus, Grafana, Loki, Collector y Jaeger. Los exporters y el agente de VM-1 son tareas previstas; el Nginx existente no se supone capaz de emitir OTLP por sí solo. La propagación del contexto HTTP de BookStack requiere instrumentación compatible sin modificar su código y prueba real.
- El puente guarda inbox/outbox antes de 202 y espera PubAck antes de marcar enviado. S1/S2 confirman después de sus transacciones y deduplican por `event_id`. La DLQ requiere transferencia explícita confirmada.
- Redis es la cola ejecutable de S3. Los eventos de exportación en NATS alimentan la auditoría y no disparan otra ejecución del job.
- La descarga de objetos atraviesa el gateway; ruta y Host deben ser coherentes con la firma S3. La URL de A3 es ilustrativa, no una firma funcional.

## Puertos del diseño

Son asignaciones propuestas, no resultados de `ss` ni reglas de firewall ya aplicadas. Confirmar ausencia de conflictos y actualizar esta tabla, diagramas y despliegue juntos en Fase 6.

| Comunicación | Protocolo y puerto | Exposición |
|---|---|---|
| Cliente → Nginx VM-1 | HTTPS/TCP 443; HTTP/TCP 80 solo redirección | Entrada web; dominios `bookstack.local` y `api.bookstack.local`. |
| Operador → nodos | SSH/TCP 22 | Red privada; VM-1 verificada, VM-2 prevista. |
| Nginx → BookStack | FastCGI por socket Unix local | Sin publicación de PHP-FPM. Ruta exacta a verificar en configuración efectiva. |
| BookStack → MariaDB | Socket local o TCP 3306 local | Transporte efectivo a verificar; nunca accesible desde servicios. |
| Gateway → S1/S2/S3/S4 | HTTP/TCP 8081/8082/8083/8084 → 8000 | Publicación Swarm `mode=host` restringida a la red privada. |
| BookStack → puente | HTTP/TCP 8085 → 8000 + token | Red privada; token redactado en logs. |
| Servicios → PostgreSQL | SQL/TCP 5432 | Overlay interna; `search_db`, `audit_db`, `bridge_db`, roles exclusivos. |
| S3 → Redis | RESP/TCP 6379 | Overlay interna; AOF y volumen. |
| Productores/consumidores → NATS | NATS/TCP 4222 | Overlay interna; consumidores durables y autenticación. |
| Exporter → NATS | HTTP/TCP 8222 | Monitoreo interno; exporter Prometheus en 7777. |
| Worker, medios, gateway → MinIO | S3 HTTP/TCP 9000 | Overlay o ruta privada VM-1→VM-2; no publicación pública directa. |
| Prometheus → servicios/exporters | HTTP/TCP 8000, 9113 y 7777 | Interno; Nginx `stub_status` privado previsto en 8080. |
| Grafana → Prometheus/Loki | HTTP/TCP 9090 y 3100 | Interno. |
| Operador → Grafana/Jaeger | HTTP/TCP 3000 y 16686 | Red privada; sin exposición pública. |
| Instrumentación → Collector | OTLP HTTP/TCP 4318 o gRPC/TCP 4317 | Interno; solo 4318 privado para el agente de VM-1. |
| Collector → Loki/Jaeger | OTLP HTTP/TCP 3100 y gRPC/TCP 4317 | Interno. |
| Swarm entre nodos | TCP 2377; TCP/UDP 7946; UDP 4789 | Solo entre IP privadas; overlay cifrada requerirá permitir ESP (IP 50), si se habilita. |

Los puertos internos iguales pertenecen a contenedores distintos y no implican publicaciones del mismo puerto en el host. Las aperturas para MinIO, Collector, métricas y paneles deben limitarse al origen requerido. Los límites de RAM y las versiones concretas se medirán/fijarán al desplegar; 4 GB asignados a VM-2 no garantizan capacidad para toda la plataforma.

## Caminos de error y límites reconocidos

1. **Edición:** 400/401 de entrada, 503 si no se persiste, outbox pendiente con broker caído, reintentos limitados, DLQ confirmada y deduplicación de auditoría al recuperar un consumidor. Si el webhook nunca llega, el envío instalado no lo reprograma; hay que resolver recuperación de origen. La reconciliación de búsqueda no equivale a reconstruir toda la auditoría. La correlación de la edición original tampoco está implementada todavía.
2. **Búsqueda:** 429 del gateway, 401/403, 400, S1 caído o base inaccesible → 503 JSON uniforme. Cero coincidencias → 200 con lista vacía. El índice respeta el alcance compartido autorizado del laboratorio.
3. **Exportación:** clave duplicada con mismo cuerpo devuelve el mismo job; otro cuerpo → 409; Redis caído antes de aceptar → 503 sin 202. Timeouts/API/MinIO disparan reintentos y finalmente `failed`; caída de worker permite recuperar la reserva. Consultar un job fallido conocido devuelve 200 con su estado. La durabilidad real de AOF y el comportamiento ante caídas se probarán después.

## Ver y regenerar en Windows

Abrir los PNG directamente en VS Code o el visor de imágenes. Para ampliar, abrir los SVG en un navegador. Editar los `.puml` cambia la fuente; regenerar actualiza las imágenes.

Requisitos: Java disponible como `java` y PlantUML **1.2025.10**, que incluye C4-PlantUML. El JAR es una herramienta local y se mantiene en `tmp/`, fuera de Git. Descargar desde la raíz del repositorio:

```powershell
New-Item -ItemType Directory -Force tmp | Out-Null
Invoke-WebRequest 'https://github.com/plantuml/plantuml/releases/download/v1.2025.10/plantuml-1.2025.10.jar' -OutFile tmp/plantuml-1.2025.10.jar
& ./cna/docs/diagramas/a4/renderizar.ps1
```

Si `java` no está en PATH, pasar su ruta con `-Java 'RUTA/java.exe'`. El script verifica el SHA-256 del JAR, comprueba sintaxis y genera ocho láminas en PNG/SVG y un reporte con hashes. Una validación técnica correcta no sustituye la inspección visual ni las pruebas de ejecución de Fase 6.

El informe usa imágenes de esta carpeta de evidencias. Después de regenerar, compilar `main.tex` con el nombre de salida `Informe_TP_I_II` y revisar las páginas nuevas. El PDF conserva la Figura 1 como línea base histórica; A4 documenta su evolución objetivo y la referencia expresamente.

## Referencias

- Consigna local: `cna/TP_Integrador_II_BookStack_Cloud_Native.pdf`, secciones 3.4 y 4.4; P30–P32.
- [Modelo C4 oficial](https://c4model.com/diagrams) y [contexto](https://c4model.com/diagrams/system-context).
- [C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML).
- [PlantUML: secuencias](https://plantuml.com/sequence-diagram) y [línea de comandos](https://plantuml.com/command-line).
