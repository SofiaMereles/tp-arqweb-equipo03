# A5 — Respaldo documental y futuros ensayos

Fecha de elaboración: 12/11/2026. Estado: plan revisado; no se ejecutó rollback ni se midió su duración.

`revision-documental.txt` conserva la revisión local de productos de la matriz, compilación, páginas inspeccionadas y hashes de las fuentes. No es una prueba operativa.

La consigna asigna F5-E1–E7 a A1–A4 y no define F5-E8 ni una P nueva para A5. Se conservan sus entregables por nombre descriptivo, sin inventar identificadores oficiales:

- [Plan de migración](../../../a5/plan-migracion.md): M0–M5 y criterio de hecho por paso.
- [Runbook](../../../a5/reversion.md): reversión por selector y presupuesto menor de sesenta segundos.
- [Matriz CSV](../../../a5/matriz-riesgos.csv): trece riesgos, factores y mitigaciones.
- [Tabla LaTeX](../../../a5/matriz-riesgos.tex): generada desde el CSV y usada por el informe.

## Revisión documental realizada

- [x] Orden S2 → S1 → S3 → S4 justificado por impacto funcional y costo de reversión.
- [x] Preparación, criterios de hecho por paso, responsables por rol y trazabilidad con CA/pruebas futuras.
- [x] Estrategia por ruta, alternativa nativa y conservación de jobs/objetos.
- [x] Presupuesto temporal, precondiciones, fallos y comprobación funcional del rollback.
- [x] Cinco riesgos obligatorios más ocho complementarios; P×I, mitigación, activador, responsable y verificación.
- [x] Escalas y productos revisados mediante `generar-matriz.py`.
- [ ] Ejecución de M0–M5 y pruebas globales: Fase 6/7.
- [ ] Medición de reversión por selector: pendiente.

## Qué guardar al ensayar la reversión

Crear un registro descriptivo, por ejemplo `A5-reversion-search-FECHA.txt`, con usuario y hostname de VM-1, selector, versión/destino anterior y nuevo, fecha UTC, inicio/fin monotónicos, duración, resultado de `nginx -t`, reload, respuesta API y operación nativa autorizada. Capturar la terminal con el comando y el resultado, y la vista nativa pertinente. Ocultar tokens, cookies y contraseñas.

Registrar también rechazo de nuevas admisiones y conservación de un job o archivo previo cuando corresponda. Un reload correcto o login 200 no sustituyen la prueba funcional. El resultado solo será aprobado si el comportamiento es correcto y la duración real es menor que sesenta segundos.

No hay un tiempo de rollback obtenido ni una captura de ejecución en este directorio. El objetivo temporal es planificado.
