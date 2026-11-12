# TP Integrador II: evolución de BookStack

Continuación del TP I. Estado: diseño de Fase 5 A1–A5 documentado, con contratos validados y evidencias de diseño guardadas. La implementación y las pruebas de Fases 6/7 siguen pendientes; todavía no hay servicios implementados ni despliegue reproducible.

## Orden de trabajo

1. Relevar la VM y el esquema real siguiendo [la guía de relevamiento](docs/fase5-relevamiento.md).
2. Completar el inventario de módulos, la matriz módulo × tabla y el mapa de contextos (A1).
3. Documentar ADR-006 a ADR-010 con alternativas y consecuencias negativas (A2).
4. Definir y validar OpenAPI 3.1 por servicio y AsyncAPI 3.0 para eventos (A3).
5. Crear C4 de contexto y contenedores y tres secuencias con caminos de error (A4).
6. Definir orden de extracción, reversión en menos de un minuto y riesgos con mitigaciones (A5).

La Fase 5 produce diseño verificable antes de construir contenedores. Los ADR de A2 registran las decisiones de broker, almacenes y orquestación, junto con sus alternativas y condiciones de despliegue.

## Alcance previsto

- S1 `search-svc`: búsqueda e indexación por eventos.
- S2 `audit-svc`: auditoría durable e idempotente.
- S3 `export-svc`: API de trabajos y workers separados; archivos en almacenamiento de objetos.
- S4 `media-svc`: subida de imágenes y miniaturas, necesario para el máximo de B2.
- Plataforma: Nginx existente como gateway, event-bridge, broker y observabilidad. Estos componentes no cuentan como funcionalidades extraídas.

BookStack conserva su código fuente y su MariaDB local. Los nuevos servicios se integrarán por API REST y Webhooks.

## Evidencias y entregables

Continuar ADR desde ADR-006, pruebas desde P26 y evidencias desde F5-E1. No marcar pruebas como aprobadas sin ejecución y resultados reales.

Consultar el [registro de evidencias](docs/evidencias/README.md) para guardar capturas y resultados durante cada fase.

## Contratos de A3

Los contratos OpenAPI 3.1 de S1–S4 y del puente y el AsyncAPI 3.0 están en [contracts/](contracts/README.md). Desde esa carpeta, `pnpm install --frozen-lockfile --ignore-scripts` instala los validadores y `pnpm run validate` verifica especificaciones, ejemplos y reglas de aceptación. El resumen y los hashes quedan guardados como F5-E4 / P29.

## Diagramas de A4

El [modelo C4 y las tres secuencias](docs/diagramas/a4/README.md) tienen fuentes PlantUML editables, PNG para el informe y SVG para ampliar. Se incluyen nodos, puertos y caminos de error, distinguiendo lo existente del diseño objetivo. Las evidencias F5-E5–F5-E7 y su registro de renderizado están en `docs/evidencias/fase5/a4/`. La coherencia con el despliegue efectivo se revisará en Fase 6.

## Migración y riesgos de A5

El [plan de migración](docs/a5/plan-migracion.md) ordena S2 → S1 → S3 → S4 y define criterios de hecho por paso. El [runbook](docs/a5/reversion.md) planifica reversión por ruta en menos de un minuto conservando jobs y objetos; todavía no se ha ejecutado ni cronometrado. La matriz de trece riesgos se edita en `docs/a5/matriz-riesgos.csv` y se regenera para LaTeX con `python cna/docs/a5/generar-matriz.py` desde la raíz del repositorio. El [registro A5](docs/evidencias/fase5/a5/README.md) distingue revisión documental de ensayos pendientes.

Al implementar se incorporarán `services/`, `deploy/` y `observability/`. Los contratos ya están en `contracts/`; los diagramas, decisiones y análisis se conservan en `docs/`.
