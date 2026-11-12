# Informe integrado hasta Fase 5 A4

El archivo raíz es `main.tex`. A1–A4 están en `fase5-a1.tex` a `fase5-a4.tex`, incorporados con `\input` antes de `\end{document}`. Se conservan los estilos y colores del preámbulo original; A4 añade `lscape` para las láminas horizontales de nivel 2. La Fase 5 continúa como sección 10 y usa numeración automática de figuras y tablas. El índice y las referencias usan `hyperref`.

La portada identifica TP I y II y la fecha de noviembre de 2026. La conclusión histórica lleva el título «Conclusión del TP Integrador I». A1 incluye los seis módulos, las 41 tablas del inventario, una matriz de 6 × 17 tablas principales, el análisis de acoplamientos y los mapas DDD actual y de integración. P26, P27 y P28 figuran completados.

## Imágenes incorporadas

Todas se cargan desde `../../../cna/docs/evidencias/fase5/`, relativo a esta carpeta. Los originales se conservan con sus nombres exactos.

| Archivo | Ubicación | Label |
|---|---|---|
| `BASE-01-bookstack-activo.png` | Alcance y línea base | `fig:f5-base` |
| `F5-E1-01-inventario-tablas.png` | Inventario del esquema | `fig:f5-e1-inventario` |
| `F5-E1-02-columnas.png` | Estructura de cinco tablas | `fig:f5-e1-columnas` |
| `F5-E1-03-claves-foraneas.png` | Consulta de claves foráneas salientes | `fig:f5-e1-fk` |
| `F5-E2-01-contenido-permisos.png` | Respaldo de la matriz, contenido y permisos | `fig:f5-e2-contenido` |
| `F5-E2-02-busqueda-auditoria.png` | Respaldo de la matriz, búsqueda y auditoría | `fig:f5-e2-busqueda` |
| `F5-E2-03-medios.png` | Respaldo de la matriz, medios | `fig:f5-e2-medios` |
| `F5-E2-04-exportacion-markdown-a.png` | Respaldo de la matriz, exportación (inicio) | `fig:f5-e2-exporta` |
| `F5-E2-04-exportacion-markdown-b.png` | Respaldo de la matriz, exportación (continuación) | `fig:f5-e2-exportb` |

También se incorporan las siguientes capturas de cierre.

- `F5-E1-04-recoleccion-esquema-codigo.png`
- `F5-E1-05-fk-usuarios-roles.png`
- `F5-E2-05-escritura-contenido.png`
- `F5-E2-06-escritura-indice.png`
- `F5-E2-07-adjuntos.png`
- `F5-E2-08-usuarios-roles.png`
- `F5-E2-09-borrado-usuario.png`
- `F5-E2-10-permisos-efectivos.png`
- `F5-E2-11-exportacion-archivos.png`

F5-E2 corresponde a las tablas de la matriz. Las capturas de código son sus respaldos. F5-E3 se dibuja en TikZ dentro del fuente y tiene el label `fig:f5-e3-contextos`.

## Editar y compilar en Windows

Usar VS Code con LaTeX Workshop y MiKTeX. MiKTeX proporciona `pdflatex` y puede instalar los paquetes faltantes al compilar. Configurar esa opción en MiKTeX Console y reiniciar VS Code después de instalar la distribución.

LaTeX Workshop permite compilar con `Ctrl+Alt+B` y elegir una receta desde la paleta. Para esta plantilla se puede elegir una receta de dos ejecuciones de pdfLaTeX. El comentario de raíz en `fase5-a1.tex` apunta a `main.tex`.

También se puede compilar desde PowerShell con los siguientes comandos, una vez disponible pdfLaTeX en PATH.

```powershell
Set-Location 'C:\Users\sofii\tp-arqweb\docs\informe\Informe Final'
pdflatex -interaction=nonstopmode -halt-on-error -synctex=1 -jobname=Informe_TP_I_II main.tex
pdflatex -interaction=nonstopmode -halt-on-error -synctex=1 -jobname=Informe_TP_I_II main.tex
```

El nombre de salida separado evita sobrescribir el PDF histórico. La segunda ejecución actualiza el índice y las referencias. Si el registro pide otra ejecución por cambios en etiquetas, repetirla. Como alternativa, `latexmk -pdf -synctex=1 -jobname=Informe_TP_I_II main.tex` administra las repeticiones cuando latexmk y su dependencia Perl están instalados.

Abrir el PDF y revisar tablas, flechas del mapa y legibilidad de las capturas al 100 %. Las capturas conservan su resolución original para consulta con zoom en el visor. Después de cada prueba del TP, guardar el resultado original y actualizar las figuras, captions y el estado de P26 en adelante.

Para compilar en otro equipo, conservar la estructura del repositorio completa, porque el documento referencia tanto las imágenes del TP I de esta carpeta como las del TP II en `cna/`.

## Verificación realizada

Se inspeccionaron las 18 imágenes incluidas, se comprobaron sus rutas y se compiló con pdfLaTeX de MiKTeX. Se revisaron visualmente las páginas de A1, sus tablas y los mapas y se verificaron las referencias enlazadas. El archivo resultante es `Informe_TP_I_II.pdf`.

Documentación oficial consultada

- [Compilación con LaTeX Workshop](https://github.com/James-Yu/LaTeX-Workshop/wiki/Compile)
- [Instalación de MiKTeX en Windows](https://miktex.org/howto/install-miktex)

## Cierre de A2

ADR-006 a ADR-010 están aceptados por el equipo para el diseño y documentados en `fase5-a2.tex`. Los originales Markdown están en `cna/docs/adr/`, con alternativas, consecuencias y fuentes. La memoria del anfitrión respalda el condicionante de habilitación de VM-2. Las pruebas operativas se realizarán durante Fase 6.

## Contratos A3

El archivo `fase5-a3.tex` incorpora los cinco OpenAPI 3.1, los seis canales AsyncAPI 3.0, el sobre, el versionado y la validación F5-E4 / P29. La ejecución guardada verificó 242 ejemplos y nueve rechazos esperados sin errores. Los resultados están en `cna/docs/evidencias/fase5/a3/`. La captura `F5-E4-validacion-contratos.png` se incluye automáticamente cuando se guarda en la carpeta de evidencias de Fase 5. El refinamiento de A3 agrega inbox/outbox del puente y su base lógica a ADR-007 y ADR-009.

## Modelo y secuencias A4

`fase5-a4.tex` incorpora contexto C4, nivel 2 en dos vistas complementarias y tres secuencias con alternativas de error. Edición y exportación tienen dos láminas cada una. Las fuentes y el script reproducible están en `cna/docs/diagramas/a4/`; los PNG, SVG y reportes con hashes, en `cna/docs/evidencias/fase5/a4/`. Los SVG son útiles para ampliar los diagramas densos. Se documenta la arquitectura objetivo y se mantiene la Figura 1 como línea base; no se declara desplegada la extensión CNA. Después de modificar un `.puml`, ejecutar `renderizar.ps1`, compilar el informe y revisar las páginas afectadas.
