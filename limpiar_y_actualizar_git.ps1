# Archivo: limpiar_y_actualizar_git.ps1

$gitignorePath = ".gitignore"
Write-Host "Generando nuevo archivo .gitignore..."

$contenidoGitignore = @"
# Archivos de entorno
.env

# Archivos de certificados y claves privadas
*.pem

# Archivos comprimidos
*.gz

# Archivos de texto temporales o de respaldo
*.txt

# Directorios de entornos virtuales
venv/
env/
.virtualenv/
backapp/

# Archivos de base de datos MySQL (backups y dumps)
*.sql
*.sql.gz
dump_*.sql
*.mwb

# Directorios de facturas generadas y temporales
/xmls/
facturador/xmls/
facturador/offline/
facturador/debug/
facturador/offline_archivos/

# Archivos PDF generados automáticamente
*.pdf

# Archivos de respaldo, copia y scripts temporales
*-Copy.py
*-Backup.py
*_temp.py
*.bak
*.swp
*.swo
*.ps1

# Archivos de log
*.log

# Archivos de caché y compilación
__pycache__/
*.pyc
*.pyo

# Archivos temporales de editores
.idea/
.vscode/
.DS_Store

# Directorios específicos de caché o logs
facturador/__pycache__/
facturador/logs/
facturador/pages/__pycache__/

# Archivos de subida temporales
.tmp.driveupload/

# Archivos de documentación o estructura local
estructura.md
static/*.md

# Directorios innecesarios o pruebas
facturador/off/

# Datos de contenedores Docker (MySQL, etc.)
mysql_data/

# Ignorar scripts SQL de estructuras o pruebas
facturador/sql/
sql/
"@

Set-Content -Path $gitignorePath -Value $contenidoGitignore -Encoding UTF8
Write-Host ".gitignore actualizado correctamente."

# Verifica que estás en un repo Git
if (-not (Test-Path ".git")) {
    Write-Error "No estás en un repositorio Git válido."
    exit 1
}

# Most
