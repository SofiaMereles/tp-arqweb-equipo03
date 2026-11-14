# B2.2 — Primer despliegue de auditoría

Estado actual: imagen construida, 14 pruebas Linux OK, stack con tres servicios 1/1 y F6-E5/P37 PASS. La recreación de la tarea conservó el registro original, con sondas, filtros, métricas y correlación verificados. Se incorporó el resultado al informe. B2 sigue abierto para los otros servicios y la integración real con BookStack se configura en B4.

Componentes: PostgreSQL (base `audit_db`, rol `audit_owner` no superusuario), NATS JetStream con volumen y API/consumidor `audit-svc`. Total de límites de esta etapa: 576 MiB y 1,25 CPU. Las tareas se fijan a `cna-node1`; VM-1 conserva su estado Drain. No se publican puertos: la primera comprobación se ejecuta dentro de la tarea, y el gateway se conectará en B5.

## Qué se implementó

- GET `/v2/audit`, con X-API-Key, paginación, entidad/ID y fechas con zona.
- `/healthz`, `/readyz` separado (PostgreSQL y consumidor/JetStream), `/metrics` con contador por código e histograma.
- Logs JSON a stdout y propagación de X-Request-ID/event.request_id.
- Validación de eventos usando el AsyncAPI existente; INSERT con unicidad por event_id y ACK después del commit.
- Consumidores durables independientes de páginas y eventos de plataforma. Reintentos con demora y DLQ después de cinco fallos; la publicación en DLQ espera PubAck antes de terminar el original.
- Configuración por entorno y secretos Swarm; ninguna credencial de MariaDB.
- Imagen multi-stage no root y filesystem read-only para auditoría.

La clave de API de esta etapa autoriza la consulta de auditoría del laboratorio. No representa permisos individuales de usuarios de BookStack. Los eventos creados por la herramienta de evidencia son sintéticos y están identificados como pruebas.

## Ejecución guiada

1. Extraer el paquete en `~/tp2-b2` de VM-2.
2. En VM-2: `sudo bash ~/tp2-b2/cna/deploy/b2-audit/preparar-worker.sh`.
3. Guardar `B2-S2-pruebas-Linux.png` mostrando el resultado de las pruebas.
4. Extraer el mismo paquete en `~/tp2-b2` de VM-1.
5. En VM-1: `sudo bash ~/tp2-b2/cna/deploy/b2-audit/desplegar-manager.sh`.
6. Esperar `1/1` en las tres filas de `sudo docker stack services cna`.
7. En VM-2: `sudo bash ~/tp2-b2/cna/deploy/b2-audit/evidencia-worker.sh`.
8. Guardar el resultado como `F6-E5-evento-duplicado.png` y conservar la salida en texto.

El helper F6-E5 exige dos secuencias diferentes de JetStream y espera el ACK de ambas entregas antes de verificar un solo registro en PostgreSQL. Así evita confundir deduplicación del broker con idempotencia del consumidor.

Los secretos se generan en el manager sin mostrarlos en pantalla y se conservan al repetir el despliegue. Los volúmenes persisten al recrear tareas. No ejecutar `docker volume rm`, cambiar credenciales de una base inicializada ni borrar la cadena de discos del clon. El script SQL de inicialización solo se ejecuta cuando el volumen de PostgreSQL está vacío.

## Pruebas con un comando

Dentro de la imagen: `python -m unittest discover -s tests -v`.
En desarrollo, instalar `cna/services/requirements.lock` en un entorno aislado y ejecutar el mismo comando desde `cna/services/`.

Se prueban contratos, autenticación, filtros inválidos, correlación, métricas, liveness frente a readiness, errores sin fuga de secretos, ACK después de commit, fallo de transacción, fallo de publicación en DLQ y pérdida de ACK después del commit. La idempotencia SQL con dependencias reales se acredita al ejecutar F6-E5, no mediante mocks.

## Resultados comprobados y pendientes de integración

- Construcción y 14 pruebas Linux: OK; stack real y consumidores listos.
- F6-E5: dos mensajes confirmados (secuencias 1 y 2) y un registro con event_id 38213507-ee9d-4c9b-8ed8-e901cd1b62e6.
- Recreación: tarea ua2izsnx8k8i reemplazada por 0nriqr2z2q25; consulta posterior conserva el mismo event_id y recorded_at sin republicación. Healthz/readyz=200; filtros, métricas y X-Request-ID verificados.
- Evidencias originales: `cna/docs/evidencias/fase6/preparacion/PRE-B2-VM2-*`.
- LaTeX: `docs/informe/Informe Final/fase6-b2.tex`.
- Pendiente: integración con eventos reales del monolito y prueba de DLQ en el despliegue (B4), y gateway (B5).

## Referencias de implementación

Corrección de arranque: NATS interpreta las variables de entorno como valores
de configuración. Un token hexadecimal que comienza con un número debe
entregarse al parser como cadena entre comillas. `corregir-token-nats.sh`
actualiza únicamente los argumentos del servicio ya desplegado, conservando
el secreto original y los volúmenes. El `stack.yaml` también incorpora esta
corrección para los despliegues siguientes. No agregar comillas al archivo
del secreto que usan los clientes.

La primera corrección inline no resolvió el fallo observado. La revisión
posterior usa `nats-start.sh` montado como Docker config `cna_nats_start_v2`;
el servicio ejecuta una ruta de archivo, sin pasar un comando de shell
anidado a `docker service update --args`. El script agrega comillas literales
solo a la variable de entorno que analiza NATS. Se verificó con un secreto
ficticio y un ejecutable simulado; el arranque real aún debe confirmarse en VM-2.

- [Variables y cadenas en la configuración NATS](https://docs.nats.io/reference/config/).

- [Transacciones Psycopg](https://www.psycopg.org/psycopg3/docs/basic/transactions.html).
- [Consumidores JetStream](https://docs.nats.io/nats-concepts/jetstream/consumers).
- [Lifespan y pruebas FastAPI](https://fastapi.tiangolo.com/advanced/testing-events/).
