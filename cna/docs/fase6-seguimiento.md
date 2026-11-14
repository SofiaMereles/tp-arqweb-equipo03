# Fase 6 — Seguimiento de implementación y evidencias

Inicio: 12/11/2026. Consigna revisada: secciones 5.1–5.6 y matriz P33–P48. El diseño A1–A5 está documentado; ninguna prueba de Fase 6 se aprueba por estar planificada.

## Resumen vigente para continuar

Este resumen prevalece sobre los pendientes históricos conservados más abajo.

| Ítem del PDF | Estado comprobado | Pendiente para cerrarlo |
|---|---|---|
| Fase 5 A1–A5 | Diseño documentado | Sin pendientes registrados de esta fase |
| Fase 6 B1 | Dos nodos Swarm, identidad/recursos, UFW, hosts y doble SAN documentados | Mantener las restricciones efectivas al incorporar los nuevos servicios |
| B2.1 búsqueda S1 | Carga inicial, libros/páginas, resaltado, enlace, sondas, métricas, correlación y pruebas; F6-E4 y CA-3 verificados con cota conservadora de 4 s | Comprobar eliminación del índice ante `page.deleted` con una página temporal; completar revisión de requisitos comunes |
| B2.2 auditoría S2 | F6-E5: duplicados producen un registro; persistencia tras recreación, filtros, sondas, métricas y logs | Verificar también la recepción del evento real de BookStack dentro de la integración B4 |
| B2.3 exportación S3 | Contrato y diseño de Fase 5 | Implementar API y worker separado, estados del job, MinIO y URL prefirmada; F6-E6/F6-E7 |
| B2.4 medios S4 | Contrato y diseño de Fase 5 | Implementar subida, miniatura y evento; F6-E8 por gateway |
| B3 imágenes | Dockerfiles y límites presentes para lo implementado | Revisión y evidencias F6-E9/F6-E10 de todos los servicios, incluido el presupuesto agregado final |
| B4 integración | Usuario API y secreto, Webhooks configurados, puente desplegado, actualización real de S1 por JetStream | Completar F6-E11/F6-E12 según el formato docente, forzar DLQ F6-E13 y comprobar ausencia de conexiones a MariaDB durante carga |
| B5 gateway | Búsqueda autenticada, TLS 1.3, cabeceras y configuración inicial | Rutas de servicios restantes, 429 real, 503 uniforme comprobado y despliegue completo desde repositorio limpio con un comando; F6-E14–E16 |
| Fase 7 | No iniciada | Experimentos y mediciones requieren los servicios de Fase 6; no se declaran logros anticipados |

Última operación confirmada: `RECONCILE_SECONDS=60` restaurado en S1,
con `Service cna_search converged`. Siguiente paso: crear una página
temporal en el libro Pruebas CNA y comprobar su eliminación del índice.
La página original 3 con beta se conserva. Aún no se recibió confirmación
de creación de esa página temporal ni de su borrado.

El informe compilado incluye B1, pruebas de S2 y F6-E4/CA-3 de S1
(página 104, Figura 75). B2–B5 permanecen abiertos donde se indica.

## Método de trabajo

Alcance confirmado nuevamente por el equipo: guiarse estrictamente por
el PDF de consignas, sin agregar funcionalidades o requisitos propios.
Cada siguiente paso debe indicar su sección/criterio y evidencia esperada.
Separar los requisitos docentes de las elecciones de implementación de los
ADR/contratos (motor, nombres de puertos, scripts, inbox/outbox, frecuencia
de reconciliación y cantidad de pruebas superior al mínimo).
Estas elecciones no se presentan como obligaciones literales del PDF.
No sumar pruebas opcionales ni declarar logros sin sus resultados.
Paso vigente: B2.1, eliminación del índice ante `page.deleted`.
F6-E4/P36 y CA-3 ya se verificaron con edición real por gateway.
El puente y el gateway se implementaron anticipadamente como dependencias
de esa interacción (3.2, 3.4, B4 y B5); no cuentan como servicios extraídos
adicionales ni implican cerrar íntegramente B4/B5.

1. Completar un bloque pequeño, conservar salida y captura real con usuario/hostname y verificar su resultado.
2. Mantener BookStack operativo y sus datos protegidos. Confirmar identidad del nodo antes de modificar hostname, red, firewall, paquetes o servicios.
3. Al cerrar un ítem B, revisar todos sus requisitos y evidencias antes de incorporarlo al LaTeX como completado. No agregar resultados futuros como obtenidos.
4. Guardar secretos fuera del repositorio. Redactar tokens, cookies, contraseñas y comandos de unión al clúster en evidencias públicas.
5. Conservar fuentes reproducibles en `cna/deploy/` y `cna/services/` cuando se construyan. La guía de esta etapa no implica que ya existan.

## B1 — Infraestructura: primer ítem

### Estado actual: infraestructura documentada y lista para B2

Se revisaron visualmente las capturas F6-E1–E3: dos nodos Ready,
UFW final de ambos nodos, hosts y doble SAN. BookStack responde HTTP 200
con validación del certificado y TLS 1.3. Se incorporó `fase6-b1.tex`
al informe, con recursos, procedimientos y trazabilidad.
El VMX de VM-2 se releyó al cerrar la documentación: `numvcpus = "2"`
y `memsize = "2048"`. La captura inicial de creación muestra 4096 MiB;
el informe explica la reducción posterior.

El presupuesto agregado de los futuros contenedores y el filtrado efectivo
de sus puertos publicados se comprobarán con B3/B5. No son pruebas ya
ejecutadas. Los pendientes de restauración funcional adicional y de dos VM
de 4 GB que aparecen en el registro histórico siguiente no bloquean B2;
se conserva el historial sin declararlos resueltos. Próximo ítem: B2,
comenzando por S2 auditoría según A5.

### Registro de preparación

Alcance aclarado con el equipo: el primer punto docente (clon enlazado, hostname/IP propios y recursos documentados) está cubierto. El ensayo adicional de arranque de la aplicación restaurada queda diferido y no bloquea instalar Docker. No se declara completado dicho ensayo ni se confunde con un requisito explícito de B1. Próximo paso: salida NAT de VM-2, Docker/Compose y formación del clúster, seguidos de firewall y certificado.

- [x] Identificar VM-1 y el origen para VM-2: `Clon de Ubuntu Server TP ARQWEB`, confirmado por hostname y MAC en el invitado.
- [ ] Medir recursos del anfitrión y confirmar margen para dos VM de 4 GB antes de iniciarlas juntas.
- [ ] Backup consistente y restauración aislada conforme a A5 antes de cambios de infraestructura.
  - Restauración SQL de prueba en VM-2 completada en `bookstack_b1_restore`: 41 tablas y recuentos coincidentes (1 entidad, 2 usuarios, 2 actividades), sin reemplazar `bookstack_db`. Archivos recuperados en `/var/www/bookstack-b1-restore`, 224 MB, con artisan presente. Falta probar arranque y conexion efectiva de esta copia a la base restaurada. [SQL](evidencias/fase6/preparacion/vm2-restauracion-sql-confirmada.txt) y [archivos](evidencias/fase6/preparacion/vm2-archivos-restaurados.txt).
  - Respaldo privado creado en VM-1: `/var/backups/bookstack-b1.KX0e0T`, 73 MB, 41 tablas InnoDB y verificaciones gzip/tar/SHA-256 correctas según salida aportada. Copiado fuera del repositorio a Windows; el integrante confirma hashes coincidentes. `PRE-B1-VM2-backup-integridad.png` confirma extracción en VM-2 y SHA256SUMS: origen, SQL, aplicación y configuración dan OK. Restauración funcional pendiente. [Creación](evidencias/fase6/preparacion/vm1-backup-2026-11-12.txt) y [copia externa](evidencias/fase6/preparacion/backup-copia-externa-confirmacion.txt).
- [x] Crear o verificar VM-2 como clon enlazado, con hostname/IP propios y recursos registrados: `cna-node1`, 192.168.145.130/24 por Solo host, 2 vCPU y 2048 MiB temporales.
  - Clon enlazado `cna-node1` creado y verificado mediante descriptor VMDK en `C:\Maquina Virtual Clon\`; 2 vCPU y 2048 MiB temporales. Nombre, machine-id y MAC propios verificados; claves SSH regeneradas y acceso desde Windows confirmado. Después del arranque aislado se conectó Solo host y obtuvo 192.168.145.130/24. Los 2048 MiB son de preparación, no prueba del presupuesto final de ADR-008. [Creación](evidencias/fase6/preparacion/vm2-clon-enlazado-verificacion.txt) y [procedimiento de identidad](b1-vm2-identidad.md).
- [x] Revisar identidad de clon, direcciones, MAC, identificadores y claves SSH antes de incorporarlo como nodo independiente: valores propios y regeneración de claves documentados, acceso SSH confirmado.
  - Captura `PRE-B1-VM2-identidad-nueva.png`: nombre `cna-node1`, machine-id distinto de VM-1 y MAC propias. Captura SSH posterior: regeneración de claves, configuración sin errores, servicio `active` y huella pública ED25519. `PRE-B1-VM2-red-solo-host.png` confirma `ens37` UP con 192.168.145.130/24 y `ens33` DOWN; no hay ruta por defecto. El integrante confirmó acceso desde Windows con hostname `cna-node1` y usuario `arqweb`. Falta documentar la comparación de huellas con VM-1.
- [ ] Mantener red privada entre nodos y comprobar salida a Internet para las instalaciones, sin exponer servicios.
  - VM-2: NAT por ens33, 192.168.147.128/24 y default via 192.168.147.2; Solo host por ens37, 192.168.145.130/24. Captura de curl al repositorio Docker devuelve HTTP/2 200 sin omitir validación TLS. Falta prueba entre ambos nodos activos.
- [x] Instalar Docker Engine y plugin Compose, usando procedimiento compatible con la versión real de Ubuntu.
  - VM-1 completada según captura `PRE-B1-VM1-Docker-Compose.png`: Engine 29.9.3 y Compose v5.7.1. La instalación en ambos nodos está verificada.
  - VM-2 completada: Engine 29.9.3, Compose v5.7.1, paquetes oficiales para resolute; daemon responde y Swarm inactive. Captura `PRE-B1-VM2-Docker-Compose.png`. VM-1 pendiente. Con solo VM-2 encendida se observaron 2,36 GiB libres en Windows: preparar VM-1 por separado y revisar margen antes del clúster simultáneo.
- [x] Formar Swarm de dos nodos; VM-1 manager en drain conforme a ADR-008; VM-2 worker. Salida aportada confirma arqwebserver Ready/Drain/Leader y cna-node1 Ready/Active, ambos Engine 29.9.3; F6-E1/P33.
  - Incorporacion del worker completada; `docker node ls` muestra ambos nodos Ready. Puertos internos del manager y worker configurados por el integrante. Confirmacion documental final de firewall y certificado pendientes.
- [ ] UFW y reglas efectivas de Docker restringen los puertos por origen; verificar también el acceso desde un origen no autorizado.
  - Manager VM-1: UFW active; deny incoming; reglas Swarm 2377/tcp, 7946/tcp+udp y 4789/udp solo ens37, origen VM-2 192.168.145.130 y destino VM-1 192.168.145.129. SSH/HTTP/HTTPS previos conservados. Worker y pruebas efectivas pendientes.
  - Worker: salida final aportada confirma UFW active y deny incoming/routed. Solo permite SSH desde Windows 192.168.145.1 y VM-1 192.168.145.129, y Swarm 7946/tcp+udp y 4789/udp desde VM-1, todo en ens37 hacia 192.168.145.130. Ya no aparecen reglas Anywhere para 22/80/443. [Salida final](evidencias/fase6/preparacion/PRE-B2-VM2-ufw-vm2.txt). Los futuros puertos publicados por Docker requieren verificación propia al desplegarse.
- [x] Actualizar hosts de Windows para ambos dominios y emitir certificado con SAN `bookstack.local` y `api.bookstack.local`.
  - Hosts apunta ambos nombres a 192.168.145.129. Salida aportada confirma doble SAN, TLS 1.3 con verificación correcta para bookstack.local y login HTTP 200 usando --cacert. El integrante confirmó la comprobación posterior de api.bookstack.local. [Registro](evidencias/fase6/preparacion/vm1-certificado-validado.txt). Falta revisar las capturas finales de UFW antes de cerrar B1 e incorporarlo al informe.
- [ ] Comprobar que BookStack sigue funcionando tras los cambios y revisar P33–P35.

El `192.168.100.23` del PDF es histórico. Se usarán las IP privadas efectivas verificadas, sin copiar una dirección de otra red. `ens37=192.168.145.129` corresponde al último acceso comprobado; se confirma de nuevo al encender la VM.

### Hallazgos iniciales del anfitrión (solo lectura)

VMware registra dos VM de nombres similares:

| Nombre registrado | Recursos en VMX | MAC del adaptador Solo host |
|---|---|---|
| Ubuntu Server TP ARQWEB | 2 vCPU / 4096 MiB | `00:0c:29:d6:43:d9` |
| Clon de Ubuntu Server TP ARQWEB | 2 vCPU / 4096 MiB | `00:0c:29:fa:eb:d7` |

El segundo coincide con la MAC de `ens37` de los relevamientos de BookStack. Su invitado se confirmó el 12/11 como `arqwebserver`, con Nginx, PHP-FPM y MariaDB activos. Se conserva como VM-1. La otra VM sigue sin inspeccionarse en esta etapa. Los discos consultados tienen `parentCID=ffffffff` y formato `monolithicSparse`, sin referencia a disco padre: el clon existente es completo. B1 pide crear VM-2 como clon enlazado; esa creacion sigue pendiente, sin eliminar las VM actuales.

La sesion actual muestra `ens33=192.168.100.30` y `ens37=192.168.145.129`, con 658 MiB usados y 2,6 GiB disponibles dentro del invitado. Son datos en reposo, no prueba de capacidad bajo carga. [Salida aportada por el integrante](evidencias/fase6/preparacion/vm1-identificacion-2026-11-12.txt). Se comprobo [HTTP 200 en /login](evidencias/fase6/preparacion/vm1-http-2026-11-12.txt) mediante resolucion local y `curl -k`; la confianza del certificado y las operaciones autenticadas se verificaran aparte. Falta proteger la linea base y probar restauracion antes de clonar.

El primer relevamiento del 12/11 encontró 15,31 GiB físicos y unos 4,76 GiB libres, sin VM en ejecución según `vmrun list`. La RAM libre cambia: repetir tras cerrar aplicaciones y antes de arrancar nodos. Dos asignaciones de 4 GB necesitan margen adicional para Windows y VMware; no se considera suficiente el valor libre inicial para iniciar ambas juntas.

## Ítems posteriores: criterios de cierre

### Estado actual S2, posterior a los registros históricos siguientes

Avance S1 posterior: lectura desde VM-2 PASS el 2026-11-13T21:09:20Z.
Actualización funcional S1: el integrante confirmó cna_search 1/1 y tarea
3cap7heesyxr0k97dhk60yzqx Running en cna-node1. La consulta inicial aprobó
readyz=200, coincidencia completa con REST (una página y dos libros), búsqueda
alfa con una coincidencia de página ID 3, resaltado, enlace nativo, búsqueda
de libros, métricas y X-Request-ID. Registro en
`evidencias/fase6/preparacion/PRE-B2-VM2-S1-indice-inicial.txt`.
Para cerrar F6-E4 faltan la edición real y actualización por evento mediante
event-bridge (B4), y la consulta vía gateway (B5). No se declara S1 cerrado.
Se preparó el código del puente durable en `services/event_bridge/`, con
13 pruebas propias aprobadas y 46 pruebas locales totales aprobadas. El
paquete B4 incluye preparación de filtro privado para publicar 8081/8085,
alta de bridge_db y despliegue del puente. No se ejecutó todavía en las VM;
filtro efectivo, Webhooks reales y gateway siguen pendientes.
Actualización posterior: el integrante confirmó construcción en VM-2 de
`cna-event-bridge-svc:1.0.0-87c76ad-7135bd137bad` y 13 pruebas Linux OK
en 2,810 s. Se guardó `evidencias/fase6/preparacion/PRE-B4-VM2-puente-pruebas-Linux.txt`.
Siguiente: preparar filtro UFW/DOCKER-USER de los puertos 8081/8085 y
después ordenar el despliegue desde VM-1. No hay prueba efectiva del filtro todavía.
Actualización posterior del filtro: el integrante ejecutó el script en VM-2;
se habilitó cna-port-filter.service, se agregaron dos reglas UFW privadas y
se confirmaron ACCEPT desde 192.168.145.129 por ens37 y DROP del resto para
8081/8085 usando conntrack/puerto original. Registro
`evidencias/fase6/preparacion/PRE-B4-VM2-filtro-puertos.txt`.
Falta desplegar el puente y comprobar accesos efectivos permitido/denegado.
Actualización posterior: alta de bridge_db y rol bridge_owner PASS, con
rechazo de CONNECT a audit_db. El integrante confirmó cinco servicios 1/1,
incluido cna_bridge, y publicación privada de búsqueda/puente. Registro
`evidencias/fase6/preparacion/PRE-B4-VM1-despliegue.txt`.
Pendiente: readiness por HTTP desde VM-1, rechazo de Webhook sin token,
acceso denegado desde Windows, Webhooks reales y gateway.
Actualización posterior HTTP: VM-1 recibió 200/ready de S1 en 8081 y del
puente en 8085; POST sin token recibió 401 con error JSON correlacionado.
Registro `evidencias/fase6/preparacion/PRE-B4-VM1-acceso-interno.txt`.
Siguiente comprobación: TCP 8081/8085 bloqueado desde Windows. Después,
configurar Webhooks reales y gateway para completar F6-E4.
El integrante confirmó luego la creación del Webhook. Se conserva la
confirmación en `evidencias/fase6/preparacion/PRE-B4-VM1-webhook-creado.txt`,
sin token ni presunción de entrega efectiva. Se prepararon las fuentes de
gateway incremental en `deploy/b5-gateway/`, con ruta S1, TLS, cabeceras,
timeouts, request_id, rate limit y 503 JSON. Aplicación en VM-1 y pruebas
autenticadas todavía pendientes; no se cierra B5 por esta configuración parcial.
Actualización gateway: el integrante ejecutó el instalador en VM-1;
Nginx válido, SAN API coincidente, TLS 1.3 y 401 sin clave comprobados,
login nativo HTTP 200 conservado. Registro
`evidencias/fase6/preparacion/PRE-B5-VM1-gateway-inicial.txt`.
Falta consulta autenticada por gateway y edición real antes/después F6-E4.
Consulta autenticada anterior a edición confirmada posteriormente:
2026-11-13T23:49:55Z, HTTP 200, TLS 1.3, cabeceras y request_id presentes,
pagina ID 3 con alfa resaltado. Registro
`evidencias/fase6/preparacion/PRE-B2-VM2-S1-gateway-antes.txt`.
Se preparó observador F6-E4/CA-3: control temporal de reconciliación,
edición humana, evento real en JetStream, ID aplicado por S1 y cota temporal
con relojes de VM-1 (updated_at y Date del gateway). Todavía no ejecutado.
Se debe restaurar RECONCILE_SECONDS=60 después del ensayo.
Actualización de construcción posterior: el integrante confirmó la imagen
`cna-search-svc:1.0.0-87c76ad-277ad9eb91f4` construida en VM-2 y 33 pruebas
Linux OK en 2,029 s. Registro `evidencias/fase6/preparacion/PRE-B2-VM2-S1-pruebas-Linux.txt`.
Pendiente siguiente: despliegue desde VM-1, alta aislada de search_db y
comprobación de carga inicial y consultas contra el índice real.
Primer intento de despliegue S1 detenido: el job cna_search_db_init terminó
con OperationalError sin detalle; S2, NATS y PostgreSQL permanecieron 1/1.
Se corrigió un defecto del verificador que solo aceptaba SQLSTATE 42501:
la negativa de CONNECT durante conexión libpq también puede llegar sin
SQLSTATE. Ahora acepta únicamente el rechazo explícito de audit_db, verifica
antes la conexión válida a search_db y muestra etapa/error con secretos
redactados. Cuatro pruebas locales del ajuste OK. La causa exacta del primer
fallo aún no está confirmada; falta ejecutar la versión corregida en VM-1.
Cuenta ve una página (ID 3, book_id 2), libro Pruebas CNA y frase
integrador nube alfa; GET administrativo /api/users devuelve 403. Registro
`evidencias/fase6/preparacion/PRE-B2-VM2-lectura-bookstack.txt`.
Se implementó código inicial de búsqueda y despliegue incremental; 33
pruebas locales OK (19 de S1 y 14 de S2). Pendiente construir y ejecutar
S1 en Linux. No se declara aprobada F6-E4 ni se añade el servicio al informe
como operativo antes de comprobar sus resultados reales.

Actualización preparación S1/B4, 2026-11-13T20:59:40Z según VM-1: el
script de token devolvió HTTP 200 y total=0 páginas visibles. Se crearon
`cna_bookstack_api_token` (secreto Swarm) y `cna_bookstack_ca_v1` (config
con certificado público). Registro: `evidencias/fase6/preparacion/PRE-B4-VM1-secreto-api.txt`.
Todavía no se acredita conexión desde VM-2 ni lectura de contenido concreto;
se necesita preparar una página y comprobar su visibilidad para S1.

Preparación de S1/B4: el integrante confirmó creación del rol de lectura
API, usuario Servicio CNA y token guardado privadamente. Se preparó
`deploy/scripts/guardar-token-bookstack-vm1.sh` para validar GET /api/pages
con TLS y guardar id:secret mediante stdin en un Docker secret. Todavía
no se recibió salida de ejecución ni se verificó acceso desde VM-2.

Reemplazo de la tarea confirmado: ua2izsnx8k8i -> 0nriqr2z2q25 en VM-2.
Consulta posterior en contenedor 7b140879bca3 a las 2026-11-13T04:00:22Z:
el evento 38213507-ee9d-4c9b-8ed8-e901cd1b62e6 conserva total=1 y recorded_at
original sin republicación. Healthz/readyz=200, filtros inclusivos/exclusivos,
métricas y X-Request-ID comprobados; logs JSON correlacionados.
Evidencias: `preparacion/PRE-B2-VM2-recreacion-tarea.*` y
`preparacion/PRE-B2-VM2-persistencia.*`, dentro de evidencias/fase6.
Se incorporó `fase6-b2.tex` para documentar S2 sin declarar completados los
otros servicios ni la integración real B4. El equipo confirmó que aún falta
crear el usuario y token de servicio de BookStack para continuar con S1.

Resultado funcional posterior de S2: F6-E5/P37 PASS el
2026-11-13T03:48:28Z según salida aportada. El evento controlado
38213507-ee9d-4c9b-8ed8-e901cd1b62e6 se publicó dos veces (secuencias
JetStream 1 y 2) y la consulta devuelve total=1 para page/1320391391.
Se conservaron captura y texto en `evidencias/fase6/preparacion/PRE-B2-VM2-evento-duplicado.*`.
El diagnóstico previo también confirmó readyz=200, PostgreSQL con rol
audit_owner y tabla audit_records, autenticación NATS, tres streams y
ambos consumidores durables disponibles. Causa de los timeouts transitorios
no determinada; no se declaran resueltos por un cambio de DNS no realizado.
Pendiente inmediato: recrear solo la tarea de auditoría y consultar el mismo
registro sin volver a publicarlo, como verificación de ausencia de estado local.

### Inicio B2: auditoría en construcción

Se agregó código de `cna/services/audit_svc/`, pruebas, Dockerfile y stack
inicial en `cna/deploy/b2-audit/`. Se ejecutaron 14 pruebas locales con
resultado OK; registro en `evidencias/fase6/preparacion/B2-audit-pruebas-locales.txt`.
El integrante ejecutó después la construcción en VM-2: imagen
`cna-audit-svc:1.0.0-87c76ad-db4af96523a3` y 14 pruebas Linux OK en 1,184 s.
Captura y salida: `evidencias/fase6/preparacion/PRE-B2-VM2-pruebas-Linux.png` y `.txt`.
Todavía falta desplegar el stack y ejecutar F6-E5 con dependencias reales.
Actualización posterior: el integrante confirmó cna_audit, cna_nats y
cna_postgres en 1/1 tras corregir el arranque de NATS mediante el config
nats-start.sh. Registro: `evidencias/fase6/preparacion/PRE-B2-VM2-stack-servicios.txt`.
Falta ejecutar la herramienta de evidencia F6-E5 y comprobar persistencia
al recrear la tarea de auditoría; no se declara todavía cerrado B2.2.
Las dependencias se instalaron en un entorno local aislado y se fijaron
en `cna/services/requirements.lock`. No se ejecutó todavía el despliegue
en las VM ni la prueba real F6-E5. B2 permanece abierto; búsqueda,
exportación y medios aún no están implementados. La implementación
parcial no se incorporó al informe como resultado logrado.

| Ítem | Qué debe quedar comprobado | Evidencias |
|---|---|---|
| B1 | Dos nodos, recursos, Docker/Swarm, UFW por origen, hosts y certificado con doble SAN | F6-E1–E3 / P33–P35 |
| B2 | S1–S4 con contratos, health/ready, métricas, logs JSON, correlación, persistencia externa y al menos tres pruebas por servicio; funciones específicas de cada uno | F6-E4–E8 / P36–P40 |
| B3 | Imágenes multi-stage, usuario no root, etiquetas sin latest, límites, healthcheck y solo lectura donde corresponda | F6-E9–E10 / P41–P42 |
| B4 | Cuenta de API con permisos mínimos, Webhooks autenticados, normalización, durabilidad/ack/DLQ y ausencia de conexiones de servicios a MariaDB | F6-E11–E13 / P43–P45 |
| B5 | Gateway TLS 1.3, cabeceras, timeouts, request_id, rate limit, 503 JSON y despliegue completo con un comando | F6-E14–E16 / P46–P48 |

B2 se implementará en el orden de A5: auditoría, búsqueda, exportación y medios. B3/B4 se construyen junto a los servicios y se cierran con verificación propia. El permiso de exportación que requiera la API de BookStack se verificará con privilegios mínimos; no se asumirá suficiente el rol de lectura para una operación que demande otro permiso.

Registro y archivos: [evidencias de Fase 6](evidencias/fase6/README.md).

### F6-E4 y CA-3 verificados mediante edición real

El equipo repitió el ensayo con la imagen S1 corregida `021cea696896`.
La edición alfa a beta en página 3, libro 2, generó el evento real
`d8521090-bb3d-4d65-a4b7-728fec445414`, persistido por S1. La consulta
por gateway encontró beta y dejó de encontrar alfa. La cota conservadora
fue 4,0 s, menor que 5 s, sin reconciliación REST durante el ensayo.
Salida y captura: `evidencias/fase6/preparacion/F6-E4-busqueda-edicion-real.txt`
y `.png`. F6-E4/P36 y CA-3 verificados para esta edición.
El equipo restauró `RECONCILE_SECONDS=60` desde VM-1 y Swarm confirmó
`Service cna_search converged`; registro:
`evidencias/fase6/preparacion/PRE-B2-VM1-S1-intervalo-restaurado.txt`.
B2 no se declara completo:
faltan, entre otros requisitos, borrado en S1, exportación S3 y medios S4.

### Corrección de espera de eventos S1 antes de repetir F6-E4

La salida aportada desde VM-2 confirma `RECONCILE_SECONDS=3600` y una
secuencia repetida `consumer_reconnecting` con `TimeoutError`, seguida de
`initial_index_complete`. Se conserva en
`evidencias/fase6/preparacion/PRE-B2-VM2-S1-diagnostico-reconexion.txt`.
El código del cliente NATS instalado puede lanzar `asyncio.TimeoutError`
al agotar una espera de fetch sin mensajes; el consumidor solo capturaba
su subclase `nats.errors.TimeoutError`. Se amplió la captura de ese fetch
a `asyncio.TimeoutError`, sin ocultar fallos de conexión en otras operaciones.
Dos pruebas de regresión verifican que ambos tipos permiten procesar el
siguiente mensaje sin reconectar ni repetir la carga inicial. Las 21 pruebas
locales de búsqueda pasaron. Paquete preparado con imagen
`cna-search-svc:1.0.0-87c76ad-021cea696896`; construcción Linux y actualización
del servicio aún pendientes. No se actualizó el servidor desde esta sesión.
F6-E4 y CA-3 continúan pendientes de repetición con edición real. Mantener
temporalmente el intervalo de 3600 s durante la medición y restaurar 60 s al terminar.
