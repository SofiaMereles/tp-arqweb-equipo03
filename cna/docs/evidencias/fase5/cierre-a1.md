# Criterios de cierre de A1

## F5-E1 / P26 — Inventario por módulo

- [x] Consultar el catálogo real de tablas.
- [x] Inspeccionar columnas y claves de las cinco tablas iniciales.
- [x] Inspeccionar el esquema restante y confirmar el mapeo ORM de cada tabla relevante.
- [x] Documentar los seis módulos: contenido, búsqueda, actividad, exportación, imágenes/adjuntos y usuarios/permisos.
- [x] Vincular las tablas a los accesos de código con archivo y método verificables.

## F5-E2 / P27 — Matriz de acoplamiento

- [x] Identificar lecturas compartidas de contenido, permisos, búsqueda, medios y exportación Markdown.
- [x] Confirmar persistencia de actividad.
- [x] Revisar escrituras de contenido e índice y el ciclo de vida de imágenes y adjuntos.
- [x] Completar usuarios, roles y permisos, y revisar las dependencias de exportación relevantes al alcance elegido.
- [x] Sustituir las celdas PV por accesos respaldados o por un alcance explícito cuando corresponda. Un resultado de búsqueda vacío por sí solo no prueba ausencia de acceso.
- [x] Resaltar tablas compartidas y explicar el efecto sobre la extracción de cada módulo.

## F5-E3 / P28 — Mapa de contextos

- [x] Preparar propuesta en TikZ dentro del informe.
- [x] Revisar los límites con el inventario completo.
- [x] Explicitar relaciones cliente/proveedor, autorización y capa anticorrupción, distinguiendo situación actual y diseño propuesto.
- [x] Guardar el mapa final y su fuente versionable y comprobar su legibilidad.

## Respaldo y cierre documental

- [x] Guardar salidas originales de las consultas y fragmentos de código adicionales.
- [x] Guardar capturas con comando, resultado, usuario y hostname de cada hallazgo nuevo.
- [x] Presentar el esquema verificado con una descripción técnica de sus tablas y relaciones.
- [x] Integrar nuevas evidencias y actualizar matriz, mapa y estados de P26–P28.
- [x] Compilar y revisar las páginas del informe antes de declarar A1 completo.

El script `recolectar-a1.sh` guarda esquema y código para realizar el análisis local con menos consultas manuales. Los archivos de código son un respaldo para inspección. Las capturas deben provenir de ejecuciones reales en la terminal del nodo.

Cierre de A1 integrado en `docs/informe/Informe Final/fase5-a1.tex`. La versión PDF se compila con MiKTeX y conserva referencias enlazadas.
