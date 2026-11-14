# Puente B4 necesario para cerrar la interacción real de S1

Estado: 13 pruebas locales del puente aprobadas; 46 pruebas locales totales
de los servicios existentes aprobadas. Pendiente construir imagen Linux,
aplicar filtro privado, desplegar y configurar Webhooks reales.
No se declara completado B4 ni la prueba de edición F6-E4.

## Propiedades

- `event-bridge` recibe POST `/internal/webhooks/bookstack?token=...`.
  Valida el secreto antes del cuerpo y devuelve 401 si no coincide.
- Valida el Webhook con el OpenAPI de A3; normaliza los tres eventos de
  páginas al sobre AsyncAPI con UUID, version, occurred_at, request_id y payload.
- Guarda inbox y outbox en la misma transacción de `bridge_db`, rol
  `bridge_owner` no administrativo. Devuelve 202 después del commit;
  cuerpo repetido por webhook_id/JSON canónico devuelve 200 y el UUID original.
- Deduplicación conservada sin borrado automático (supera el mínimo de 7 días).
- Publicador con lease recuperable en outbox; marca enviado después de PubAck.
  Ante caída del broker, el POST puede persistir y responder 202. Ready verifica
  las dependencias necesarias para aceptar durablemente (PostgreSQL), no exige
  que NATS esté disponible en ese instante. El publicador sigue reintentando.
- Health/ready separados, contador/histograma Prometheus, logs JSON stdout.
  El token en la query no se registra; uvicorn access log está desactivado.
- No se modifica código BookStack ni se accede a MariaDB desde los servicios.

## Orden de ejecución

1. Construir en VM-2 usando `preparar-worker.sh` dentro del paquete extraído.
   Ejecuta solo las 13 pruebas del puente dentro de su imagen.
2. Antes de publicar puertos, ejecutar en VM-2 `proteger-puertos-worker.sh`.
   Agrega UFW privado y filtrado DOCKER-USER/conntrack para 8081 y 8085,
   permitiendo VM-1 192.168.145.129 por ens37 y denegando otros orígenes.
   Conserva SSH, Swarm, PostgreSQL y NATS. Instala aplicación de reglas al
   arranque antes de Docker; no deshabilita la gestión de firewall de Docker.
3. Copiar/extraer el mismo paquete en VM-1 y ejecutar `desplegar-manager.sh`.
   El job de inicialización exige el marcador de filtro en VM-2 y prueba
   aislamiento de bridge_db respecto de search_db/audit_db.
4. Verificar todas las tareas y probar desde VM-1 el acceso a 8081/8085.
   Comprobar desde Windows que esos puertos estén bloqueados. El marcador
   de preparación no sustituye estas pruebas efectivas.
5. Configurar Webhooks desde el administrador de BookStack y después gateway.
   Si la versión instalada bloquea el destino privado, revisar ALLOWED_SSR_HOSTS;
   no habilitar globalmente ALLOW_UNTRUSTED_SERVER_FETCHING sin necesidad.

El token del Webhook se genera y guarda como secreto de Swarm. Su copia y
la URL que necesita el administrador quedan en `/home/arqweb/.cna-private/`,
fuera del repositorio, con directorio 0700 y archivos 0600.
No incluir la URL completa en capturas, logs públicos o mensajes de chat.

## Puertos y presupuesto incremental

S1 se publica en 8081 y el puente en 8085, ambos en modo host y protegidos
por origen antes de publicarse. No se publica el routing mesh en VM-1.
El gateway de VM-1 expondrá las rutas externas mediante TLS/443.
Puente: 128 MiB y 0,25 CPU; los componentes actuales suman límites de
896 MiB. El job temporal requiere 96 MiB. Quedan pendientes medir consumo
bajo carga y presupuestar exportación/medios/observabilidad.

Las fuentes incrementales se consolidarán en el despliegue de un comando
de B5. Estos scripts parciales no acreditan F6-E16.

## Referencias

- [Docker y DOCKER-USER después de DNAT](https://docs.docker.com/engine/network/firewall-iptables).
- [Seguridad de peticiones salientes de BookStack](https://www.bookstackapp.com/docs/admin/security/).
- [Webhooks de BookStack](https://www.bookstackapp.com/docs/admin/email-webhooks/).
