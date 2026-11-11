# ADR-008 — Plataforma de orquestación

## Estatus

Aceptado para el diseño por el equipo. La habilitación de VM-2 está condicionada a verificar memoria disponible y consumo conjunto del laboratorio.

## Contexto

El TP requiere despliegue reproducible, recuperación de servicios y escalado de workers, con el monolito operativo ante la caída de servicios o VM-2. El equipo utiliza VMware y tiene una VM base con 2 vCPU y 4 GB asignados. Ubuntu reportó 3,3 GiB de RAM visible y 2,6 GiB disponibles en el relevamiento inicial.

El anfitrión Windows reportó 16.442.781.696 bytes de RAM física, 12 procesadores lógicos y 16.057.404 KiB de memoria visible. En la consulta de A2 tenía 2.249.404 KiB libres, aproximadamente 2,1 GiB. El total físico y la memoria visible miden cosas distintas y los valores libres corresponden a un instante. El respaldo se guarda en `recursos-a2.txt`.

La memoria libre observada requiere liberar aplicaciones o cargas antes de agregar una VM de 4 GB. Los recursos del anfitrión y de las VM deben verificarse de nuevo antes de instalar la plataforma y antes de las pruebas de carga.

## Decisión

Adoptar Docker Swarm como orquestador del diseño, con dos VM en el laboratorio inicial.

| Nodo | Rol previsto | Asignación y criterio |
|---|---|---|
| VM-1, `arqwebserver` | Monolito, gateway y manager de Swarm | Conservar 2 vCPU y 4 GB de la VM base. Excluir las tareas de los nuevos servicios mediante disponibilidad `drain`, conservando la función de manager. |
| VM-2, `cna-node1` | Worker de Swarm, servicios y persistencia | Prever 2 vCPU y 4 GB, con límites por contenedor. Confirmar que el anfitrión sostenga ambas VM antes de crearla. |

El manager mantendrá el estado deseado y las réplicas de los servicios. Los export-workers podrán escalar de una a tres réplicas. Las imágenes se construirán y estarán disponibles antes de `docker stack deploy`; el stack no realiza la construcción de Dockerfiles.

Los almacenes con volúmenes locales se fijarán a VM-2 mediante restricciones de ubicación. Una caída de VM-2 detendrá esos componentes hasta recuperar el nodo y sus discos, mientras BookStack continuará en VM-1. El regreso del nodo debe permitir reconciliar los servicios automáticamente.

Los endpoints de servicio se publicarán de forma restringida sobre el nodo de servicios, sin abrir el routing mesh sobre todas las interfaces externas. UFW y las reglas efectivas de Docker se verificarán juntos. El tráfico entre nodos usará la red interna y los puertos de clúster necesarios, limitados por origen. El acceso externo de aplicación seguirá el gateway de VM-1.

## Alternativas descartadas

- **Docker Compose sobre VM-2.** Es una base válida y de menor complejidad para un solo host. Se elige Swarm por su estado deseado, reemplazo de tareas y manejo de réplicas, útiles para los experimentos de caída y escalado. Compose queda como alternativa si las mediciones obligan a revisar este ADR, con su impacto en las pruebas y rúbrica documentado.
- **k3s.** Ofrece el modelo Kubernetes, pero agrega aprendizaje y operación de su plano de control. Sus mínimos oficiales excluyen la carga de aplicaciones. En el presupuesto inicial se prioriza una plataforma más acotada al objetivo del TP.
- **Tres VM desde el inicio.** Con la memoria libre observada, una tercera VM necesita primero demostrar capacidad del anfitrión. La observabilidad se presupuestará inicialmente en VM-2 y se trasladará solo si las mediciones justifican otro nodo.

## Consecuencias

### Favorables

- Permite declarar réplicas y mantener el estado deseado de servicios.
- Proporciona un mecanismo de despliegue por stack y acceso a secretos por servicio.
- Separa el ciclo de vida de servicios y monolito en dos VM.

### Costos y limitaciones

- Un solo manager es un punto único de falla del plano de control. Dos nodos con un manager no constituyen alta disponibilidad.
- Los volúmenes locales fijan los servicios con estado a VM-2 y requieren respaldo y recuperación del mismo almacenamiento.
- El uso de Swarm añade puertos internos, restricciones de ubicación y reglas de publicación que deben verificarse.
- La planificación de 4 GB por VM no garantiza que todos los servicios y observabilidad entren. Los límites deben sumar menos que la memoria visible del nodo, dejando margen al SO y Docker; CPU, swap, disco y latencia se medirán bajo carga.
- El snapshot de memoria del anfitrión exige preparar el entorno antes de ejecutar dos VM simultáneamente.

## Respaldo y validación prevista

Conservar mediciones de Windows y Ubuntu, listado de nodos, límites de contenedores y consumo en reposo/carga. Probar reemplazo de una tarea, escalado 1 → 3 de workers y recuperación tras apagar/encender VM-2. Medir BookStack mientras se ejecutan los servicios. Si no hay margen, revisar este ADR y el presupuesto antes del despliegue final.

## Fuentes

- [Docker Swarm, managers y workers](https://docs.docker.com/engine/swarm/how-swarm-mode-works/nodes/)
- [Servicios, réplicas, ubicación y publicación de puertos](https://docs.docker.com/engine/swarm/services/)
- [Docker Compose en producción](https://docs.docker.com/compose/how-tos/production/)
- [Requisitos de k3s](https://docs.k3s.io/installation/requirements)
