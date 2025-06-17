# Activar entorno virtual "backapp" si existe
$venvPath = ".\backapp\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Output "Activando entorno virtual en .\backapp..."
    & $venvPath
} else {
    Write-Warning "No se encontró el entorno virtual en .\backapp\Scripts\Activate.ps1"
}

# Verificar que Graphviz (dot) esté instalado
try {
    $version = dot -V
    Write-Output "Graphviz detectado: $version"
} catch {
    Write-Error "Graphviz no está disponible. Asegúrate de haberlo instalado correctamente y agregado al PATH."
    exit 1
}

# Archivo a analizar (puedes cambiar esta línea según lo necesites)
$archivo = "facturador\main.py"

Write-Output "Generando grafo de dependencias para $archivo..."

# Corregido: quitamos --show y dejamos que se genere la imagen (abre automáticamente el visor si está habilitado)
pydeps $archivo --max-bacon=2 --show-deps --nodot

Write-Output "Grafo generado correctamente."
