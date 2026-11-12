param(
    [string]$PlantUmlJar = '',
    [string]$Java = 'java'
)
$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
if (-not $PlantUmlJar) { $PlantUmlJar = Join-Path $repoRoot 'tmp/plantuml-1.2025.10.jar' }
$jarHash = '4a01ea09b317180fb8e7eef712dfdca725409d2ee1919e4b5adfe9d8362b6fe5'
if (-not (Test-Path -LiteralPath $PlantUmlJar)) {
    throw 'Falta PlantUML 1.2025.10. Consultar README.md para descargar el JAR oficial.'
}
if ((Get-FileHash -LiteralPath $PlantUmlJar -Algorithm SHA256).Hash.ToLower() -ne $jarHash) {
    throw 'El SHA-256 del JAR no coincide con la version revisada.'
}
$sources = @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.puml' | Sort-Object Name)
if ($sources.Count -ne 6) { throw 'Se esperan seis fuentes: L1, dos laminas L2 y tres secuencias.' }
$evidenceDir = Join-Path $repoRoot 'cna/docs/evidencias/fase5/a4'
New-Item -ItemType Directory -Force $evidenceDir | Out-Null
$javaArgs = @('-Djava.awt.headless=true', '-DPLANTUML_LIMIT_SIZE=12000', '-jar', $PlantUmlJar, '-charset', 'UTF-8')
$version = (& $Java @javaArgs -version | Out-String).Trim()
& $Java @javaArgs -checkonly @($sources.FullName)
if ($LASTEXITCODE -ne 0) { throw 'PlantUML detecto un error de sintaxis.' }
foreach ($format in @('png', 'svg')) {
    & $Java @javaArgs "-t$format" '-Sdpi=180' -o $evidenceDir @($sources.FullName)
    if ($LASTEXITCODE -ne 0) { throw "Fallo el renderizado $format." }
}
$expected = @(
    'F5-E5-c4-contexto',
    'F5-E6-01-c4-contenedores', 'F5-E6-02-c4-operacion',
    'F5-E7-01-edicion-indexacion', 'F5-E7-01-edicion-indexacion_001',
    'F5-E7-02-busqueda',
    'F5-E7-03-exportacion', 'F5-E7-03-exportacion_001'
)
$outputs = @()
foreach ($stem in $expected) {
    foreach ($extension in @('png', 'svg')) {
        $path = Join-Path $evidenceDir "$stem.$extension"
        if (-not (Test-Path -LiteralPath $path)) { throw "Falta $path" }
        if ($extension -eq 'svg') {
            $svgText = [System.IO.File]::ReadAllText($path)
            [xml]$svg = $svgText
            if ($svg.DocumentElement.LocalName -ne 'svg' -or $svgText -match 'Syntax Error|An error has occured') {
                throw "SVG invalido: $path"
            }
        }
        $outputs += [ordered]@{file="$stem.$extension";sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower()}
    }
}
$report = [ordered]@{
    evidence = @('F5-E5/P30', 'F5-E6/P31', 'F5-E7/P32')
    generated_at = [DateTime]::UtcNow.ToString('o')
    host = [Environment]::MachineName
    status = 'PASS'
    scope = 'Sintaxis, renderizado y archivos de diseno; no verifica servicios desplegados.'
    plantuml = '1.2025.10'
    plantuml_jar_sha256 = $jarHash
    runtime = $version
    source_count = $sources.Count
    rendered_sheets = $expected.Count
    sources = @($sources | ForEach-Object { [ordered]@{file=$_.Name;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()} })
    outputs = $outputs
}
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $evidenceDir 'render-report.json') -Encoding utf8
$summary = @(
    'A4 - F5-E5/P30, F5-E6/P31, F5-E7/P32: PASS',
    "Fecha UTC: $($report.generated_at)", "Nodo: $($report.host)",
    'PlantUML 1.2025.10; C4-PlantUML incluido en el JAR.',
    '6 fuentes; 8 laminas PNG y 8 SVG; sintaxis correcta y SVG parseables.',
    'L1: contexto. L2: aplicaciones/datos y operacion. Secuencias: edicion, busqueda, exportacion.',
    'Diseno objetivo: la validacion no constituye una prueba de despliegue ni de ejecucion de los flujos.'
)
$summary | Set-Content -LiteralPath (Join-Path $evidenceDir 'render-summary.txt') -Encoding utf8
$summary
