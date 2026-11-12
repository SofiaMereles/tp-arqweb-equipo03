# A5 — Runbook de reversión por funcionalidad

**Estado: plan. No instalado ni ejecutado en VM-1.** Las rutas de configuración siguientes se prepararán y probarán en Fase 6. No copiar estos comandos en el servidor actual como si esos archivos ya existieran.

## Qué significa volver al monolito

El monolito permanece operativo durante la migración. Revertir significa cerrar la entrada nueva afectada y usar su función nativa, sin restaurar toda la base ni detener BookStack.

Los contratos `/v2/*` no son iguales a los endpoints nativos. No redirigir un POST con 301/302/307/308 a una ruta de BookStack ni devolver HTML como si fuese la respuesta JSON de A3. Los clientes de API recibirán el error 503 JSON previsto y un enlace alternativo; el usuario continuará por la interfaz nativa autorizada. La vuelta funcional es explícita, no una compatibilidad HTTP inexistente.

| Selector | Entrada que se desactiva | Vuelta funcional | Qué se conserva |
|---|---|---|---|
| `audit` | Consultas `/v2/audit` afectadas | Panel nativo de actividad/auditoría, con permisos de la sesión | Consumidor, base CNA y eventos propios de servicios. La actividad nativa no contiene necesariamente toda la auditoría CNA. |
| `search` | `GET /v2/search` | Búsqueda nativa `/search?term=...`; codificar el término en el cliente | Consumidor e índice para corregir y reconciliar. |
| `exports` | Nuevos `POST /v2/exports` | Exportación nativa desde la página o libro seleccionados | GET de jobs, workers recuperables y `/objects/exports/*` para trabajos ya aceptados. |
| `media` | Nuevos `POST /v2/media` | Carga de imágenes/adjuntos en el editor nativo | GET de metadatos, originales y miniaturas y objetos ya referenciados. |

Un servicio o VM-2 caídos pueden impedir temporalmente conservar accesibles esos GET, aunque se mantengan sus rutas y datos. Revertir admisiones no devuelve disponibilidad a un volumen caído ni traslada objetos a BookStack. La recuperación de datos se mide por separado.

## Preparación obligatoria antes de habilitar la primera ruta

1. En VM-1, incluir una sola variante por selector dentro del server block de API. Ejemplo de organización prevista:
   - `/etc/nginx/cna/available/search.cna.conf` y `search.native.conf`;
   - `/etc/nginx/cna/active/search.conf`, enlace a la variante activa;
   - igual estructura para `audit`, `exports` y `media`.
   El include recoge solo `active/*.conf`, no archivos temporales. Los snippets forman parte de `cna/deploy/` al implementarlos; todavía no existen.
2. Cada variante nativa produce 503 JSON con `error.code`, `message`, `request_id`, `Content-Type: application/json`, `X-Request-ID` y un `Link` alternativo a BookStack. Para S3/S4 bloquea solo admisiones nuevas y deja rutas de lectura/descarga. El resto del server block no cambia.
3. Validar ambas variantes con la configuración completa y las credenciales de prueba. No usar un snippet aislado fuera de contexto como prueba de validez del sitio.
4. Preparar acceso SSH, privilegios y sesión nativa autorizada, más probes por ruta sin secretos en argumentos, logs ni repositorio. Verificar confianza del certificado; no usar `curl -k` para dar por validado TLS.
5. Conservar último archivo conocido válido, destino previo del enlace y un bloqueo exclusivo que evite cambios concurrentes. Preparar enlaces temporales en el mismo directorio/filesystem para renombrado atómico.
6. Ensayar previamente el cambio y su recuperación. Sin archivos preparados, probes y acceso nativo, no prometer menos de un minuto.

## Activadores

- Fallo de autorización o filtración: cerrar admisiones/lecturas afectadas inmediatamente, preservar registros y revocar la credencial comprometida.
- Búsqueda: retraso que incumple los cinco segundos en el ensayo, índice incoherente o 5xx persistentes.
- Exportación/medios: jobs sin progreso recuperable, objetos inválidos, error sostenido de almacenamiento o riesgo de pérdida.
- RAM: OOM, presión sostenida o incumplimiento del presupuesto que afecte a BookStack.
- Si el gateway o VM-1 completos están caídos, esta reversión no es ejecutable. Aplicar recuperación del nodo/configuración; no atribuirle el objetivo de sesenta segundos.

## Operación prevista: presupuesto total menor que 60 s

El operador elige **una funcionalidad**, toma el bloqueo y registra `t0` con reloj monotónico y fecha UTC. El tiempo de detección previo se informa aparte. No usar operaciones de aprovisionamiento, instalación, backup completo ni arranque de VM dentro de esta ventana.

| Ventana objetivo | Acción |
|---|---|
| 0–10 s | Guardar destino anterior del selector y cambiar atómicamente al snippet nativo preparado. |
| 10–20 s | Ejecutar `nginx -t` sobre la configuración efectiva. Si falla, restaurar el enlace anterior, no recargar y registrar fallo. |
| 20–30 s | Recargar Nginx sin detenerlo. Confirmar por solicitudes nuevas que el comportamiento activo cambió; enviar la señal no basta. |
| 30–55 s | Probar la ruta afectada y el funcionamiento nativo autorizado; comprobar conservación de GET/jobs/objetos que corresponda. Registrar `t1`. |
| 55–59 s | Margen operativo. Si no termina en menos de 60 s, el objetivo no se cumplió, aunque luego se recupere. |

Los intervalos son un presupuesto de diseño, no tiempos obtenidos. La restauración del enlace o recuperación tras una falla pueden excederlo y se registrarán como ensayo fallido.

### Secuencia de comandos que se implementará y ensayará

Ejemplo de diseño para `search`, una vez creados y validados los snippets; ejecutarlo bajo el bloqueo de cambios. El procedimiento completo deberá capturar el destino anterior, gestionar cada código de salida y restaurarlo si falla la validación o recarga:

```bash
# NO ejecutar ahora: los archivos son una organización prevista de Fase 6.
sudo ln -s /etc/nginx/cna/available/search.native.conf /etc/nginx/cna/active/.search.next
sudo mv -Tf /etc/nginx/cna/active/.search.next /etc/nginx/cna/active/search.conf
sudo nginx -t
# Solo si nginx -t termina correctamente:
sudo systemctl reload nginx
```

No encadenar la recarga si la prueba falla. No emplear `systemctl stop` ni `restart` como mecanismo de reversión. Si falla el reload o las solicitudes siguen mostrando la variante anterior, restaurar el selector conocido válido, validar y recargar de nuevo; informar el resultado real, sin asumir que la señal aplicó la nueva configuración.

## Comprobaciones de salida

- Una conexión HTTP nueva a la ruta retirada recibe 503 JSON y el `request_id` esperado, sin proxy al servicio retirado. No basta el exit code de `systemctl reload`.
- La sesión nativa autorizada realiza la función equivalente: buscar un término conocido, consultar actividad, exportar una página de prueba o cargar una imagen de prueba. Login 200 por sí solo no prueba esa funcionalidad.
- Los otros servicios y el monolito no cambian por retirar una ruta.
- En S3, nuevos POST se rechazan, pero un job previo conserva estado y archivo; en S4, una imagen previa mantiene su referencia cuando el almacén está disponible.
- `elapsed_s = t1 - t0 < 60`. Guardar duración por selector y resultado de cada probe. Repetir hasta contar con un ensayo exitoso por funcionalidad antes de atribuir el objetivo al procedimiento.

La vuelta al servicio nuevo requiere diagnóstico, reconciliación y sus criterios de hecho completos. Cambiar el selector a `cna` usa el mismo control, prueba y reload. No reabrir una ruta solo porque el contenedor figure como running.

## Datos y efectos en curso

No revertir MariaDB ni borrar volúmenes, streams, buckets, jobs o eventos como parte de este procedimiento. S2/S1 pueden seguir consumiendo para conservar auditoría y reducir atraso. S3 deja de admitir trabajos nuevos y conserva reservas, outbox y resultados de los anteriores. S4 mantiene objetos referenciados; migrarlos o retirarlos exige otro plan y prueba de restauración.

## Evidencia del ensayo futuro

Conservar usuario/hostname de VM-1, selector, variante previa/nueva, tiempos UTC y monotónicos, `nginx -t`, resultado del reload, probes HTTP sanitizados y comprobación nativa. Ocultar cookies/tokens. Guardar los resultados en `cna/docs/evidencias/fase5/a5/` con estado real. En este momento no existe una medición de rollback.
