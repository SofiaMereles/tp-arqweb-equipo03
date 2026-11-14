# Evidencias de Fase 6

Estado actual: B1 documentado; auditoría S2 con F6-E5 y persistencia verificadas; búsqueda S1 con edición real F6-E4 y CA-3 verificados (cota conservadora de 4 s). Se conservan las capturas y salidas originales. B2 continúa abierto: resta comprobar borrado en S1, implementar exportación S3 y medios S4, y revisar el conjunto de requisitos comunes. B3–B5 no se declaran completos. El [resumen vigente](../../fase6-seguimiento.md) identifica los pendientes frente a los registros históricos.

Preparación de VM-2: [`PRE-B1-VM2-primer-arranque-aislado.png`](preparacion/PRE-B1-VM2-primer-arranque-aislado.png) muestra el primer arranque aportado por el integrante: hostname `arqwebserver`, `machine-id` heredado y ambas interfaces sin enlace (`DOWN` / `NO-CARRIER`). Las MAC mostradas ya difieren de VM-1. Quedan pendientes cambiar el hostname y separar los identificadores del invitado. La captura de consola no demuestra por sí sola la asignación de RAM ni sustituye la captura de configuración de VMware.

| Prueba | Evidencia | Archivo sugerido | Estado |
|---|---|---|---|
| P33 | F6-E1 | `preparacion/F6-E1-nodos-swarm.png` y `preparacion/PRE-B2-VM2-nodos-swarm.txt` | Captura revisada: dos nodos Ready, manager Drain y worker Active |
| P34 | F6-E2 | `preparacion/PRE-B1-VM1-ufw-Swarm.png`, `preparacion/F6-E2-ufw-vm2.png`, `preparacion/PRE-B2-VM2-ufw-vm2.txt` | UFW de ambos nodos revisado; filtrado de futuros puertos Docker se comprobará al desplegarlos |
| P35 | F6-E3 | `preparacion/F6-E3-certificado-doble-san.png` y `preparacion/PRE-B1-hosts-dos-dominios.png` | Doble SAN, TLS 1.3 verificado y login HTTP 200; captura revisada |
| P36 | F6-E4 | `preparacion/F6-E4-busqueda-edicion-real.png` y `.txt`; salida previa en `preparacion/PRE-B2-VM2-S1-gateway-antes.txt` | Verificado: alfa → beta por evento real y gateway; cota conservadora 4,0 s, sin reconciliación REST durante el ensayo (CA-3) |
| P37 | F6-E5 | `preparacion/PRE-B2-VM2-evento-duplicado.png` y `.txt`; `PRE-B2-VM2-persistencia.png` y `.txt` | PASS: dos entregas, un registro; mismo evento conservado tras reemplazo; sondas, filtros, métricas y correlación verificados. Webhooks reales B4 pendientes |
| P38 | F6-E6 | `F6-E6-ciclo-job.png` y estados obtenidos | Pendiente |
| P39 | F6-E7 | `F6-E7-objeto-minio.png` | Pendiente |
| P40 | F6-E8 | `F6-E8-subida-miniatura.png` | Pendiente |
| P41 | F6-E9 | `F6-E9-imagenes.png` y tabla de etiquetas/tamaños | Pendiente |
| P42 | F6-E10 | `F6-E10-inspect-SERVICIO.png` y extracto sin secretos | Pendiente |
| P43 | F6-E11 | `F6-E11-webhooks.png`, con token oculto | Pendiente |
| P44 | F6-E12 | `F6-E12-evento-broker.png` | Pendiente |
| P45 | F6-E13 | `F6-E13-dlq.png` y causa/intentos (sin secretos) | Pendiente |
| P46 | F6-E14 | `F6-E14-gateway.png` y `nginx -t` | Pendiente |
| P47 | F6-E15 | `F6-E15-rate-limit-429.png` | Pendiente |
| P48 | F6-E16 | `F6-E16-despliegue.png` y servicios healthy | Pendiente |

En terminal, capturar usuario/hostname, comando y resultado real. Acompañar capturas extensas con texto/JSON. No guardar claves privadas, secretos, cookies, tokens de API ni el token de unión a Swarm. `docker inspect` completo puede contener variables sensibles: guardar solo los campos necesarios.

El informe LaTeX incorpora B1 en `fase6-b1.tex`, con las capturas revisadas y las limitaciones observadas. No se confunde el cierre de infraestructura con la verificación del despliegue completo. Los ítems B2–B5 se incorporarán al completarse.
