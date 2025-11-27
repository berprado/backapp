# 🔧 Guía de Comandos Git - Fase 2

**Proyecto:** Sistema de Facturación Electrónica  
**Branch:** `feature/facturadorv1-refactor`  
**Fecha:** 9 de Octubre de 2025

---

## 📋 Pre-commit Checklist

Antes de hacer commit, asegúrate de:

- [ ] ✅ Todos los test cases de `CHECKLIST_FASE2_TESTING.md` están aprobados
- [ ] ✅ Code review completado y aprobado
- [ ] ✅ No hay código comentado o debug statements
- [ ] ✅ Logs funcionan correctamente
- [ ] ✅ La aplicación corre sin errores

---

## 🗂️ Archivos Modificados

### Código
```bash
facturador/pages/1_Sincronizar.py
```

### Documentación
```bash
facturador/docs/FASE2_REFACTORIZACION_COMPLETA.md
facturador/docs/CHECKLIST_FASE2_TESTING.md
facturador/docs/RESUMEN_FASE2_REFACTORIZACION.md
facturador/docs/GIT_COMMIT_FASE2.md
facturador/docs/INDEX.md
```

---

## 📝 Comandos Git

### Paso 1: Ver el Estado Actual
```powershell
git status
```

### Paso 2: Revisar los Cambios (Diff)
```powershell
# Ver cambios en el código
git diff facturador/pages/1_Sincronizar.py

# Ver resumen de cambios
git diff --stat
```

### Paso 3: Agregar Archivos al Staging
```powershell
# Opción A: Agregar todos los archivos modificados
git add -A

# Opción B: Agregar archivos específicos
git add facturador/pages/1_Sincronizar.py
git add facturador/docs/FASE2_REFACTORIZACION_COMPLETA.md
git add facturador/docs/CHECKLIST_FASE2_TESTING.md
git add facturador/docs/RESUMEN_FASE2_REFACTORIZACION.md
git add facturador/docs/GIT_COMMIT_FASE2.md
git add facturador/docs/INDEX.md
```

### Paso 4: Verificar Staging Area
```powershell
git status
```

Deberías ver algo como:
```
Changes to be committed:
  modified:   facturador/pages/1_Sincronizar.py
  new file:   facturador/docs/FASE2_REFACTORIZACION_COMPLETA.md
  new file:   facturador/docs/CHECKLIST_FASE2_TESTING.md
  new file:   facturador/docs/RESUMEN_FASE2_REFACTORIZACION.md
  new file:   facturador/docs/GIT_COMMIT_FASE2.md
  modified:   facturador/docs/INDEX.md
```

### Paso 5: Hacer Commit
```powershell
git commit -m "refactor(sync): Fase 2 - Eliminar variables globales y refactorizar funciones

- Refactorizar sincronizar_fecha_hora() para usar actualizar_estado_sync()
- Refactorizar mostrar_informacion_sincronizacion() para usar obtener_estado_sync()
- Mejorar main() con indicadores visuales de última sincronización
- Eliminar todas las declaraciones 'global' del código
- Eliminar lógica duplicada de formateo de diferencias horarias
- Añadir docstrings a todas las funciones refactorizadas

BREAKING CHANGE: Elimina completamente las variables globales remote_time, 
local_time y time_difference. Todo el estado ahora se gestiona mediante 
st.session_state.

Métricas de mejora:
- Variables globales: 3 → 0 (100% eliminadas)
- Declaraciones 'global': 2 → 0 (100% eliminadas)
- Funciones documentadas: 0/3 → 3/3 (100%)

Refs: #SYNC-FASE2
Docs: facturador/docs/FASE2_REFACTORIZACION_COMPLETA.md"
```

---

## 🏷️ Alternativa: Commit Detallado (Multilinea)

Si prefieres un commit más detallado con múltiples líneas:

```powershell
git commit
```

Esto abrirá tu editor de texto. Escribe:

```
refactor(sync): Fase 2 - Eliminar variables globales y refactorizar funciones

Completa la migración del sistema de gestión de estado eliminando todas las
referencias a variables globales y refactorizando las funciones existentes.

## Cambios en el Código

### sincronizar_fecha_hora()
- Elimina declaración 'global remote_time, local_time, time_difference'
- Usa actualizar_estado_sync() para guardar valores calculados
- Mejora manejo de errores con logging detallado
- Añade docstring completo

### mostrar_informacion_sincronizacion()
- Usa obtener_estado_sync() para leer valores del estado
- Reutiliza obtener_diferencia_horaria_formateada() eliminando duplicación
- Añade docstring completo

### main()
- Añade inicializar_estado_sincronizacion() al inicio
- Implementa indicadores visuales de última sincronización:
  * Verde: < 1 hora
  * Azul: 1-24 horas
  * Amarillo: > 24 horas con recomendación
- Añade docstring completo

## Métricas

- Variables globales: 3 → 0 (100% eliminadas)
- Declaraciones 'global': 2 → 0 (100% eliminadas)
- Funciones documentadas: 0/3 → 3/3 (100%)
- Líneas refactorizadas: ~85

## Testing

Checklist de 10 test cases creado en:
docs/CHECKLIST_FASE2_TESTING.md

## Documentación

- FASE2_REFACTORIZACION_COMPLETA.md: Documentación técnica detallada
- RESUMEN_FASE2_REFACTORIZACION.md: Resumen ejecutivo
- INDEX.md: Actualizado con documentación Fase 2

BREAKING CHANGE: Elimina completamente las variables globales remote_time,
local_time y time_difference. Cualquier código externo que dependiera de
estas variables debe migrar a usar las funciones de acceso.

Refs: #SYNC-FASE2
Docs: facturador/docs/FASE2_REFACTORIZACION_COMPLETA.md
```

---

## 🔍 Verificar el Commit

Después de hacer commit:

```powershell
# Ver el último commit
git log -1

# Ver los cambios del último commit
git show

# Ver estadísticas del último commit
git show --stat
```

---

## 🚀 Push al Repositorio

```powershell
# Push a la rama actual
git push origin feature/facturadorv1-refactor

# Si es tu primer push en esta rama
git push -u origin feature/facturadorv1-refactor
```

---

## 🔄 Si Necesitas Hacer Cambios Después del Commit

### Modificar el Último Commit (Antes de Push)
```powershell
# Hacer cambios en los archivos...
git add <archivos-modificados>
git commit --amend
```

### Deshacer el Último Commit (Antes de Push)
```powershell
# Mantener los cambios en el working directory
git reset --soft HEAD~1

# Descartar completamente el commit y los cambios
git reset --hard HEAD~1
```

---

## 📊 Ver Historial de Commits

```powershell
# Ver últimos 5 commits
git log --oneline -5

# Ver commits con cambios de archivos
git log --stat

# Ver commits con gráfico
git log --graph --oneline --all
```

---

## ✅ Resumen de Comandos Rápidos

```powershell
# Workflow completo
git status                                    # Ver estado
git add -A                                    # Agregar todos
git status                                    # Verificar staging
git commit -m "mensaje"                       # Commit
git log -1                                    # Ver último commit
git push origin feature/facturadorv1-refactor # Push
```

---

## 🔖 Convención de Mensajes de Commit

Este proyecto sigue **Conventional Commits**:

```
<tipo>(<alcance>): <descripción>

[cuerpo opcional]

[notas al pie opcionales]
```

### Tipos Comunes
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `refactor`: Refactorización de código
- `docs`: Cambios en documentación
- `test`: Añadir o modificar tests
- `chore`: Tareas de mantenimiento

### Ejemplo para Fase 2
```
refactor(sync): Fase 2 - Eliminar variables globales

BREAKING CHANGE: ...
```

---

## 📞 Ayuda

Si tienes dudas:
1. Revisa `GIT_COMMIT_FASE1.md` para ejemplos similares
2. Consulta la documentación de Conventional Commits
3. Pregunta al equipo antes de hacer push

---

**Última actualización:** 9 de Octubre de 2025
