# B2.1 — Servicio S1 de búsqueda

Estado: lectura REST real desde VM-2 comprobada. Código de S1 y 19 pruebas
locales preparados, con las 14 pruebas de auditoría también aprobadas.
Pendiente construir imagen Linux, desplegar y comprobar el índice real.
F6-E4 NO está aprobada: exige edición real, eventos y consulta vía gateway.

## Diseño implementado

- Base `search_db`, rol `search_owner` no administrador y esquema propio.
  Comparte la instancia PostgreSQL, sin permisos de conexión cruzada con S2.
- Carga inicial de TODOS los libros y páginas usando APIs paginadas y
  detalles de contenido. Si falla una llamada, la transacción conserva el índice previo.
- PostgreSQL FTS en español con índice GIN, pesos para títulos/cuerpo/libro,
  ranking, filtro por tipo y paginación. Resultados de libros y páginas conforme a A3.
- Resaltado: escapar el texto de origen antes de convertir marcadores internos
  en `<mark>`. Enlaces nativos restringidos al origen HTTPS de BookStack.
- Antes de devolver coincidencias se comprueba nuevamente su visibilidad
  mediante API. La clave de laboratorio autoriza el mismo alcance de la
  cuenta de lectura; no constituye autenticación de usuarios individuales.
  Revalidar todas las coincidencias agrega llamadas REST y costo con catálogos
  grandes; el laboratorio debe medir ese costo antes de atribuir capacidad.
- Consumidor durable `search-svc-pages-v1` independiente de auditoría.
  Eventos de páginas actualizan/borran la proyección; los ID procesados y el
  efecto se guardan juntos antes del ACK. Reloj de entidad para eventos antiguos.
- Reconciliación REST periódica (60 s por defecto) para libros y recuperación
  de discrepancias. No se presenta como prueba de actualización por evento
  menor que 5 s: esa prueba debe distinguir el evento de la reconciliación.
- Configuración por entorno/secretos, sin MariaDB. Sondas separadas, métricas,
  logs JSON y propagación de request_id. API no root y filesystem read-only.

## Secuencia de ejecución

1. Copiar y extraer `tmp/b2-busqueda.tar.gz` en `~/tp2-b2-s1` de VM-2.
2. VM-2: `sudo bash ~/tp2-b2-s1/cna/deploy/b2-search/preparar-worker.sh`.
3. Conservar la salida/captura `PRE-B2-VM2-S1-pruebas-Linux.png`.
4. Copiar y extraer el mismo paquete en `~/tp2-b2-s1` de VM-1.
5. VM-1: `sudo bash ~/tp2-b2-s1/cna/deploy/b2-search/desplegar-manager.sh`.
   El job administrativo crea la base y prueba aislamiento. Su contraseña
   administrativa no se entrega al servicio de búsqueda. No reinicia PostgreSQL.
6. Comprobar `docker stack services cna` y logs de `cna_search`.
7. VM-2: `sudo bash ~/tp2-b2-s1/cna/deploy/b2-search/evidencia-worker.sh 3`.
   El ID 3 corresponde a la página de control leída por la cuenta de servicio;
   ajustar si se utiliza otra página. Guardar `PRE-B2-VM2-S1-indice-inicial.png`.

El despliegue incremental agrega únicamente S1 y su base, sin actualizar la
imagen que ya ejecuta S2. Usa el secreto BookStack y el certificado públicos
preparados en B4, el secreto NATS existente y la red `cna_backend`.
No publica puertos; se conectará el gateway en B5. Límites adicionales:
192 MiB / 0,50 CPU para S1, más un job temporal de inicialización de 96 MiB.
El stack completo de B5 deberá integrar esta definición en un solo comando;
el procedimiento incremental no acredita por sí solo F6-E16.

## Pruebas

`python -m unittest discover -s tests -v` desde `cna/services/`, o dentro
de la imagen. Las pruebas no reemplazan las verificaciones con PostgreSQL,
NATS y BookStack reales. Se comprueba también que una carga REST fallida
no vacíe el índice anterior y que un evento antiguo no sobrescriba uno nuevo.

## Fuentes

- [PostgreSQL, control de búsqueda y límites de seguridad de ts_headline](https://www.postgresql.org/docs/17/textsearch-controls.html).
- [NATS, consumidores pull durables](https://docs.nats.io/learn/jetstream/pull-consumers).
