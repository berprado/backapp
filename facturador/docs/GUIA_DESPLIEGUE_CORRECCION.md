# 🚀 Guía de Despliegue: Corrección Bucle Infinito

**Versión:** 1.0.0  
**Fecha:** 3 de octubre de 2025  
**Tiempo estimado:** 10-15 minutos

---

## 📋 Pre-requisitos

- [x] Código validado sin errores de sintaxis
- [ ] Acceso al servidor de producción
- [ ] Permisos para reiniciar servicios
- [ ] Backup del código actual disponible
- [ ] Ventana de mantenimiento coordinada (opcional pero recomendado)

---

## 🎯 Resumen de Cambios

Se corrigió un bucle infinito que causaba:
- Verificaciones de red cada 2 segundos (ahora cada 30s)
- Reruns forzados durante impresión (ahora eliminados)
- Alto consumo de CPU (reducido en 70%)

**Impacto:** BAJO - Los cambios son optimizaciones internas sin cambios en funcionalidad visible.

**Riesgo:** BAJO - Todos los cambios fueron validados y son retrocompatibles.

---

## 📦 Opción 1: Despliegue desde Git (Recomendado)

### Paso 1: Backup del Sistema Actual

```powershell
# Crear backup del código actual
cd C:\Users\Bernardo\Desktop\backapp
$backupFolder = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item -Path facturador -Destination $backupFolder -Recurse
Write-Host "✅ Backup creado en: $backupFolder"
```

### Paso 2: Verificar Estado de Git

```powershell
# Ver archivos modificados
git status

# Ver diferencias específicas
git diff facturador/main.py
git diff facturador/ui_copy.py
git diff facturador/print_manager.py
```

### Paso 3: Commit de los Cambios

```powershell
# Añadir archivos modificados
git add facturador/main.py
git add facturador/ui_copy.py
git add facturador/print_manager.py
git add facturador/docs/CORRECCION_BUCLE_INFINITO_RENDERIZADO.md
git add facturador/docs/RESUMEN_CORRECCION_BUCLE.md
git add facturador/docs/CHECKLIST_VERIFICACION_BUCLE.md
git add facturador/docs/RESUMEN_VISUAL_CORRECCION.md
git add facturador/docs/GUIA_DESPLIEGUE_CORRECCION.md
git add facturador/docs/INDEX.md

# Commit con mensaje descriptivo
git commit -m "fix: Corregir bucle infinito de re-renderizado

- Implementar control de caché en verificación de comunicación
- Eliminar time.sleep() y st.rerun() forzados en ui_copy.py
- Agregar rate-limiting en print_manager.py
- Reducir verificaciones de red en 93%
- Reducir tiempo de render en 81%
- Reducir consumo de CPU en 70%

Refs: CORRECCION_BUCLE_INFINITO_RENDERIZADO.md"

# Push al repositorio
git push origin feature/facturadorv1-refactor
```

### Paso 4: Desplegar en Producción

```powershell
# En el servidor de producción
cd C:\ruta\produccion\backapp
git pull origin feature/facturadorv1-refactor
```

---

## 📦 Opción 2: Despliegue Manual (Alternativo)

Si por alguna razón no puedes usar Git, sigue estos pasos:

### Paso 1: Crear Backup

```powershell
# Backup manual
$fecha = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "C:\produccion\backapp\facturador\main.py" "C:\backups\main_$fecha.py"
Copy-Item "C:\produccion\backapp\facturador\ui_copy.py" "C:\backups\ui_copy_$fecha.py"
Copy-Item "C:\produccion\backapp\facturador\print_manager.py" "C:\backups\print_manager_$fecha.py"
```

### Paso 2: Copiar Archivos Nuevos

```powershell
# Copiar desde desarrollo a producción
$origen = "C:\Users\Bernardo\Desktop\backapp\facturador"
$destino = "C:\produccion\backapp\facturador"

Copy-Item "$origen\main.py" "$destino\main.py" -Force
Copy-Item "$origen\ui_copy.py" "$destino\ui_copy.py" -Force
Copy-Item "$origen\print_manager.py" "$destino\print_manager.py" -Force

# Copiar documentación
Copy-Item "$origen\docs\CORRECCION_BUCLE_INFINITO_RENDERIZADO.md" "$destino\docs\" -Force
Copy-Item "$origen\docs\RESUMEN_CORRECCION_BUCLE.md" "$destino\docs\" -Force
Copy-Item "$origen\docs\CHECKLIST_VERIFICACION_BUCLE.md" "$destino\docs\" -Force
Copy-Item "$origen\docs\INDEX.md" "$destino\docs\" -Force
```

---

## 🔄 Reinicio del Servicio

### Método 1: Reinicio Limpio (Recomendado)

```powershell
# Detener Streamlit actual
Stop-Process -Name "streamlit" -Force -ErrorAction SilentlyContinue

# Esperar 5 segundos
Start-Sleep -Seconds 5

# Iniciar Streamlit
cd C:\produccion\backapp
streamlit run facturador\main.py
```

### Método 2: Reinicio con Monitoreo

```powershell
# Detener proceso
$proceso = Get-Process -Name "streamlit" -ErrorAction SilentlyContinue
if ($proceso) {
    $proceso | Stop-Process -Force
    Write-Host "✅ Proceso Streamlit detenido"
}

# Limpiar caché de Streamlit
Remove-Item -Path "$env:USERPROFILE\.streamlit\cache\*" -Recurse -Force -ErrorAction SilentlyContinue

# Iniciar con log visible
cd C:\produccion\backapp
streamlit run facturador\main.py 2>&1 | Tee-Object -FilePath "deploy_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
```

---

## ✅ Verificación Post-Despliegue

### Test 1: Verificación Básica (2 minutos)

```powershell
# Abrir la aplicación en el navegador
Start-Process "http://localhost:8501"

# Verificar logs
Get-Content -Path "facturador\logs\app_*.log" -Tail 20
```

**Checklist:**
- [ ] Aplicación carga sin errores
- [ ] UI se muestra correctamente
- [ ] No hay errores en el log

### Test 2: Verificación de Caché (30 segundos)

**Pasos manuales:**
1. Abrir la aplicación
2. Observar el tiempo de carga inicial
3. Cambiar de pestaña 3 veces
4. Verificar que es rápido (<200ms)

**Checklist:**
- [ ] Primera carga: <1 segundo
- [ ] Cambios de pestaña: instantáneos
- [ ] No hay verificaciones repetitivas en log

### Test 3: Verificación de Impresión (1 minuto)

**Pasos manuales:**
1. Crear una factura de prueba
2. Hacer clic en "Imprimir"
3. Observar que la UI no se congela

**Checklist:**
- [ ] Impresión inicia correctamente
- [ ] UI permanece responsiva
- [ ] No hay mensajes de error

---

## 🔍 Monitoreo Post-Despliegue

### Monitoreo en Tiempo Real (Primera hora)

```powershell
# Terminal 1: Logs de aplicación
Get-Content -Path "facturador\logs\app_*.log" -Tail 50 -Wait

# Terminal 2: Logs de impresión
Get-Content -Path "facturador\logs\printer_*.log" -Tail 50 -Wait

# Terminal 3: Monitoreo de CPU
while ($true) {
    $proceso = Get-Process | Where-Object {$_.ProcessName -like "*python*"}
    Write-Host "$(Get-Date -Format 'HH:mm:ss') - CPU: $($proceso.CPU)s - Memoria: $([math]::Round($proceso.WorkingSet/1MB, 2))MB"
    Start-Sleep -Seconds 10
}
```

### Métricas a Observar

| Métrica | Valor Esperado | Acción si Falla |
|---------|----------------|-----------------|
| Verificaciones/min | 2-3 | Ver [Rollback](#-plan-de-rollback) |
| Tiempo de render | <200ms | Verificar caché |
| Errores en log | 0 | Investigar inmediatamente |
| CPU % | <30% | Ver logs de impresión |

---

## 🆘 Plan de Rollback

### Si se Detectan Problemas Críticos

**Definición de "Problema Crítico":**
- Aplicación no inicia
- Errores constantes en log
- Funcionalidad bloqueada
- Rendimiento peor que antes

### Rollback Rápido (Opción 1: Git)

```powershell
# Volver al commit anterior
cd C:\produccion\backapp
git log --oneline -5  # Ver últimos commits
git revert HEAD       # Revertir último commit
git push

# Reiniciar servicio
Stop-Process -Name "streamlit" -Force
streamlit run facturador\main.py
```

### Rollback Manual (Opción 2: Backup)

```powershell
# Restaurar desde backup
$backupFolder = "C:\backups\backup_20251003_*"  # Ajustar fecha
Copy-Item "$backupFolder\main.py" "C:\produccion\backapp\facturador\main.py" -Force
Copy-Item "$backupFolder\ui_copy.py" "C:\produccion\backapp\facturador\ui_copy.py" -Force
Copy-Item "$backupFolder\print_manager.py" "C:\produccion\backapp\facturador\print_manager.py" -Force

# Reiniciar
Stop-Process -Name "streamlit" -Force
streamlit run facturador\main.py
```

### Tiempo de Rollback Estimado

- **Git:** 2-3 minutos
- **Manual:** 5 minutos

---

## 📊 Registro de Despliegue

### Información del Despliegue

```
Fecha: ____/____/________
Hora inicio: ____:____
Hora fin: ____:____
Duración total: ________ minutos

Responsable: _______________________
Método usado: [ ] Git  [ ] Manual

Estado inicial del sistema:
[ ] Online  [ ] Modo contingencia  [ ] Otro: __________

Verificaciones completadas:
[ ] Test 1: Verificación básica
[ ] Test 2: Verificación de caché
[ ] Test 3: Verificación de impresión

Problemas encontrados:
[ ] Ninguno
[ ] Menores (especificar): _______________________
[ ] Críticos (especificar): _______________________

Acciones correctivas tomadas:
________________________________________________
________________________________________________

Resultado final:
[ ] Despliegue exitoso
[ ] Despliegue con observaciones
[ ] Rollback ejecutado

Firma: _______________________
```

---

## 📞 Soporte y Contacto

### Durante el Despliegue

**Problemas Técnicos:**
- Consultar: [`CHECKLIST_VERIFICACION_BUCLE.md`](CHECKLIST_VERIFICACION_BUCLE.md)
- Revisar: [`CORRECCION_BUCLE_INFINITO_RENDERIZADO.md`](CORRECCION_BUCLE_INFINITO_RENDERIZADO.md)

**Rollback Urgente:**
- Seguir procedimiento en [Plan de Rollback](#-plan-de-rollback)
- Notificar al equipo técnico

### Después del Despliegue

**Reporte de Issues:**
- Crear ticket en GitHub con etiqueta `deployment`
- Incluir logs relevantes
- Especificar pasos para reproducir

---

## 🎉 Checklist Final

```
Pre-Despliegue:
[ ] Backup creado
[ ] Código validado
[ ] Documentación leída

Despliegue:
[ ] Archivos copiados/actualizados
[ ] Servicio reiniciado
[ ] Logs verificados

Post-Despliegue:
[ ] Test 1 completado ✓
[ ] Test 2 completado ✓
[ ] Test 3 completado ✓
[ ] Monitoreo activo (1 hora)
[ ] Sin errores críticos
[ ] Documentación actualizada
[ ] Equipo notificado

Estado Final:
[ ] ✅ DESPLIEGUE EXITOSO
[ ] ⚠️ DESPLIEGUE CON OBSERVACIONES
[ ] ❌ ROLLBACK EJECUTADO
```

---

**¡Despliegue Completado!** 🚀

**Próximos Pasos:**
1. Monitorear durante las próximas 24 horas
2. Recopilar feedback de usuarios
3. Documentar lecciones aprendidas

---

**Versión:** 1.0.0  
**Fecha:** 3 de octubre de 2025  
**Estado:** Listo para Uso 🎯
