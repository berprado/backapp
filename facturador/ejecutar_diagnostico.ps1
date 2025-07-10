# Script de PowerShell para ejecutar el diagnóstico del sistema de impresión
# Uso: ./ejecutar_diagnostico.ps1

Write-Host "🚀 DIAGNÓSTICO DEL SISTEMA DE IMPRESIÓN BACKINVOICE" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Verificar si estamos en el directorio correcto
$currentDir = Get-Location
Write-Host "📍 Directorio actual: $currentDir" -ForegroundColor Yellow

# Verificar si Python está disponible
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no encontrado. Instale Python antes de continuar." -ForegroundColor Red
    exit 1
}

# Ejecutar verificación de importaciones
Write-Host "`n🔍 Ejecutando verificación de importaciones..." -ForegroundColor Cyan
try {
    python verificar_imports.py
    $importResult = $LASTEXITCODE
    
    if ($importResult -eq 0) {
        Write-Host "✅ Verificación de importaciones completada exitosamente" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Se encontraron problemas en las importaciones" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error ejecutando verificar_imports.py: $_" -ForegroundColor Red
}

# Ejecutar el sistema principal con modo diagnóstico
Write-Host "`n🖥️ Iniciando sistema principal en modo diagnóstico..." -ForegroundColor Cyan
Write-Host "💡 Selecciona 'Diagnóstico Completo' en el menú para ver el análisis detallado" -ForegroundColor Yellow

try {
    streamlit run main_enhanced_demo.py
} catch {
    Write-Host "❌ Error ejecutando el sistema principal: $_" -ForegroundColor Red
    Write-Host "💡 Asegúrate de que Streamlit esté instalado: pip install streamlit" -ForegroundColor Yellow
}

Write-Host "`n✅ Diagnóstico completado. Revisa los archivos en la carpeta debug/ para más detalles." -ForegroundColor Green
