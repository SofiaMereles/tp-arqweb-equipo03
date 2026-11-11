# F5-E4 / P29 — Validación de contratos

## Respaldo real guardado

- `validation-report.json` contiene versiones de herramientas, nodo y usuario, diagnósticos, resultados y SHA-256 de cada contrato.
- `validation-summary.txt` contiene el resumen legible de la misma ejecución.
- `webhook-source.txt` conserva los dos archivos fuente que respaldan el formato real de Webhook y el ajuste de durabilidad del puente.

La validación abarca los cinco OpenAPI 3.1, el AsyncAPI 3.0, los seis canales, el sobre común, los ejemplos y entradas negativas. Los resultados se regeneran con el comando de validación; se deben guardar juntos con los contratos de esa revisión.

## Captura de terminal pendiente de incorporar

Ejecutar en PowerShell de Windows, donde están los contratos y las herramientas instaladas:

```powershell
Set-Location 'C:\Users\sofii\tp-arqweb\cna\contracts'
& 'C:\Users\sofii\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' validate.mjs
```

Al terminar, capturar el comando y las líneas PASS de los seis archivos, el resumen de ejemplos y errores y la identificación de usuario y nodo impresa al comienzo. Guardar la imagen en `cna/docs/evidencias/fase5/F5-E4-validacion-contratos.png`. Si hace falta, ampliar la ventana o usar dos tomas consecutivas. La evidencia se genera en el anfitrión Windows; el propio validador identifica ese equipo.

No sustituir la ejecución por un dibujo de terminal. El resumen de texto y JSON ya respaldan la validación; la captura completa el registro visual usado en el informe.
