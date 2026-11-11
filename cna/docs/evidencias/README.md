# Registro de evidencias del TP II

Con cada actividad, guardar el respaldo cuando se obtenga el resultado. Registrar el identificador oficial, la prueba P correspondiente, el nodo, el comando o escenario, el resultado esperado y observado, y el archivo que irá citado en el informe. Si hay que repetir una prueba, conservar el resultado previo cuando ayude a explicar una corrección.

| Fase | Identificadores | Qué guardar |
|---|---|---|
| 5 · Diseño | F5-E1 a E7 / P26 a P32 | Consultas de esquema, matriz, mapa de contextos, salida de validación de contratos y fuentes de los diagramas C4 y de secuencia. [Lista hasta el punto actual](fase5/README.md) |
| 6 · Despliegue | F6-E1 a E16 / P33 a P48 | Salidas de nodos, firewall y certificado; interacciones de los servicios; inspección de imágenes; broker, DLQ y pruebas del gateway; salida del despliegue en un comando. Guardar en `fase6/`. |
| 7 · Operación | F7-E1 a E14 / P49 a P62 | Capturas con hora en experimentos de fallos, resultados de carga y escalado, métricas, logs, trazas, alertas, escaneo, SBOM y prueba de rotación. Guardar en `fase7/`. |

Usar el prefijo de la evidencia en el nombre del archivo, por ejemplo `F6-E15-429-gateway.png`. Para terminal, incluir el prompt con usuario y hostname, el comando y su salida. Para Grafana, MinIO u otra interfaz, mostrar la vista pertinente y acompañarla con una referencia al nodo o escenario. Conservar salidas extensas como texto o JSON y los diagramas y tableros en su formato fuente. Usar capturas para mostrar el resultado que se citará en el informe. Ocultar credenciales, cookies y tokens antes de guardar o publicar.
