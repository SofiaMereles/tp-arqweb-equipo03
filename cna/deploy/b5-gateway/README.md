# Gateway incremental para la prueba real de S1

Estado: fuentes preparadas. Pendiente aplicar en VM-1 y verificar la ruta
autenticada; no se declara B5 completado ni F6-E4 aprobado.

## Ejecutar desde VM-1

Copiar esta carpeta y ejecutar `sudo bash ~/b5-gateway/instalar-gateway-vm1.sh`.
Requiere el certificado doble SAN de B1 y búsqueda disponible en VM-2:8081.
El script conserva una copia de la configuración previa de su propio archivo,
valida Nginx y recarga; revierte si falla la validación o sus comprobaciones.
No modifica el server block nativo de BookStack ni la clave privada.

## Alcance

- Server blocks para api.bookstack.local; HTTP redirige a HTTPS.
- Certificado local existente, TLS 1.3 configurado y comprobado con curl.
- Cabeceras de seguridad del archivo TP1 `config/nginx-bookstack.conf`.
- `/v2/search` hacia 192.168.145.130:8081, con timeouts explícitos.
- Clave API suministrada por el cliente y conservada por el proxy; no se
  incorpora ninguna credencial al archivo Nginx.
- X-Request-ID generado por Nginx y reenviado; evita duplicar la cabecera
  que devuelve la API. Se conserva traceparent si el cliente lo envía.
- Límite de 10 peticiones/s por origen con burst 20 y rechazo JSON 429.
- 503 JSON uniforme ante errores de servicio 502/503/504.
- Logs JSON con URI sin query, sin claves API ni token Webhook.

La instalación comprueba 401 sin credencial y login nativo HTTP 200, con CA
explícita, sin curl -k. Las consultas autenticadas, rate limit efectivo,
503 por caída y rutas de S2/S3/S4 deben completarse en las pruebas de B5.
No se promete que otro navegador confíe automáticamente en el certificado.

## Referencias

## Ensayo F6-E4 / P36 y CA-3

Conservar la consulta anterior a la edición. Para distinguir eventos de
reconciliación, establecer temporalmente en VM-1:
`docker service update --env-add RECONCILE_SECONDS=3600 --detach=false cna_search`.
Es un control del ensayo, no un requisito adicional del docente.
Después ejecutar en VM-2 `f6e4-edicion-worker.sh 3` con su archivo Python
en la misma carpeta. Esperar su aviso y editar por navegador alfa -> beta.
El observador no publica eventos ni modifica páginas. Comprueba consulta
por gateway, evento nuevo en JetStream, procesamiento en search_events y
ausencia de reconciliación REST durante el ensayo.

La cota de tiempo usa updated_at de BookStack y Date de Nginx, ambos de
VM-1. Suma un segundo por la resolución de Date, conservadoramente, y
exige una cota menor de 5 s. No compara relojes de VM distintas ni supone
una zona horaria ausente. Guardar los resultados reales; no aprobar CA-3
si falta evento, cambia reconciled_at o la cota alcanza 5 segundos.

Al terminar restaurar en VM-1:
`docker service update --env-add RECONCILE_SECONDS=60 --detach=false cna_search`.
Una falla del Webhook requiere revisar su entrega, sin presentar una
actualización por reconciliación como interacción asíncrona aprobada.

## Referencias

- [Proxy y errores Nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).
- [Limitación de solicitudes](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html).
