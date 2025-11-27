# ✅ Checklist de Pruebas - Fase 3

## 📋 Información General
**Módulo:** Sincronización SIAT  
**Archivo:** `facturador/pages/1_Sincronizar.py`  
**Versión Streamlit:** 1.49.0+  
**Fecha de implementación:** 2024  

---

## 🧪 Casos de Prueba

### TC-UI-001: Notificaciones Toast (Activadas)
**Objetivo:** Verificar que las notificaciones toast aparecen y los logs se escriben

**Pasos:**
1. Iniciar la aplicación Streamlit
2. Ir a la página "Sincronizar"
3. Hacer clic en cualquier botón que dispare una sincronización
4. Observar la esquina superior derecha de la pantalla

**Resultado esperado:**
- [ ] Aparece notificación toast con mensaje correspondiente
- [ ] El toast desaparece automáticamente después de ~3 segundos
- [ ] El mensaje se registra en `logs/sincronizacion_YYYY-MM-DD.log`
- [ ] El log contiene timestamp, nivel y mensaje correcto

**Verificación de logs:**
```powershell
cat facturador/logs/sincronizacion_*.log | Select-String "notificar" | Select-Object -Last 5
```

**Estado:** ⬜ No probado | ✅ Pasó | ❌ Falló

---

### TC-UI-002: Notificaciones Alert (Toast desactivado)
**Objetivo:** Verificar el fallback cuando toast no está disponible

**Pasos:**
1. En el código, localizar una llamada a `notificar()`
2. Cambiar temporalmente el parámetro a `usar_toast=False`
3. Ejecutar la función correspondiente
4. Observar el comportamiento

**Resultado esperado:**
- [ ] Aparece un `st.alert()` en lugar de toast
- [ ] El mensaje es visible en el flujo principal de la página
- [ ] El log se escribe correctamente

**Estado:** ⬜ No probado | ✅ Pasó | ❌ Falló

---

### TC-UI-003: Panel de Métricas CON Datos
**Objetivo:** Verificar que el panel superior muestra métricas cuando hay datos

**Pasos:**
1. Realizar al menos una sincronización completa exitosa
2. Recargar la página de sincronización
3. Observar el panel de métricas en la parte superior

**Resultado esperado:**
- [ ] Se muestran 4 métricas en columnas
- [ ] Métrica 1 (🌐): Muestra "Online" en verde
- [ ] Métrica 2 (⏱️): Muestra tiempo desde última sincronización
- [ ] Métrica 3 (📊): Muestra cantidad de servicios sincronizados
- [ ] Métrica 4 (⏰): Muestra diferencia horaria con clasificación
- [ ] Los deltas tienen colores apropiados (verde/rojo según caso)

**Estado:** ⬜ No probado | ✅ Pasó | ❌ Falló

---

### TC-UI-004: Panel de Métricas SIN Datos
**Objetivo:** Verificar que el panel muestra placeholders cuando no hay datos

**Pasos:**
1. Limpiar el estado de sesión (reiniciar navegador o borrar cache)
2. Ir a la página de sincronización SIN hacer ninguna sincronización
3. Observar el panel de métricas

**Resultado esperado:**
- [ ] Se muestran 4 métricas con placeholders
- [ ] Métrica 1: "Desconocido" en gris
- [ ] Métrica 2: "No disponible"
- [ ] Métrica 3: "0/17"
- [ ] Métrica 4: "No disponible"
- [ ] No hay errores en consola

**Estado:** ⬜ No probado | ✅ Pasó | ❌ Falló

---

### TC-UI-005: Detalles Expandibles de Sincronización
**Objetivo:** Verificar el contenedor `st.status()` con detalles

**Pasos:**
1. Realizar una sincronización de fecha y hora
2. Buscar el contenedor "🔍 Detalles de Sincronización"
3. Hacer clic para expandir
4. Observar el contenido
5. Hacer clic de nuevo para contraer

**Resultado esperado:**
- [ ] Contenedor aparece colapsado por defecto
- [ ] Al expandir, muestra 2 métricas (hora servidor, hora local)
- [ ] Muestra análisis de diferencia horaria con color apropiado
- [ ] Si diferencia > 5s, muestra advertencia
- [ ] Incluye expander "🔧 Detalles Técnicos"
- [ ] Al colapsar, todo el contenido se oculta
- [ ] Estado cambia a "✅ Detalles mostrados" cuando expandido

**Estado:** ⬜ No probado | ✅ Pasó | ❌ Falló

---

### TC-UI-006: Sincronización Completa con Barra de Progreso
**Objetivo:** Verificar la barra de progreso y métricas en tiempo real

**Pasos:**
1. Ir a Tab "🚀 Sincronización Rápida"
2. Hacer clic en "🚀 Sincronizar Todo Ahora"
3. Observar el proceso completo

**Resultado esperado:**
- [ ] Aparece barra de progreso iniciando en 0%
- [ ] Barra avanza gradualmente hasta 100%
- [ ] Texto de la barra indica servicio actual
- [ ] Aparecen 4 métricas en tiempo real:
  - Exitosos (incrementa con cada éxito)
  - Fallidos (se mantiene en 0 si todo bien)
  - Progreso (X/18)
  - Tiempo (segundos transcurridos + promedio)
- [ ] Las métricas se actualizan durante el proceso
- [ ] Al finalizar, barra muestra "✅ Sincronización completa!"

**Estado:** ⬜ No probado | ✅ Pasó | ❌ Falló

---

### TC-UI-007: Celebración con Globos (Sincronización Perfecta)
**Objetivo:** Verificar que aparecen globos si todo es exitoso

**Pasos:**
1. Asegurar conexión estable a Internet
2. Ejecutar "Sincronizar Todo"
3. Esperar a que termine sin errores

**Resultado esperado:**
- [ ] Si 0 fallidos, aparece mensaje: "🎉 ¡Sincronización perfecta!"
- [ ] Aparece animación de `st.balloons()`
- [ ] Panel de métricas superior se actualiza automáticamente
- [ ] Logs registran: "Sincronización completa exitosa: X/18"

**Estado:** ⬜ No probado | ✅ Pasó | ❌ Falló

---

### TC-UI-008: Indicador de Sidebar + Botón de Verificación
**Objetivo:** Verificar el indicador compacto y su interactividad

**Pasos:**
1. Observar el sidebar (panel izquierdo)
2. Localizar la sección del indicador de estado
3. Hacer clic en "🔄 Verificar Conexión"
4. Observar la actualización

**Resultado esperado:**
- [ ] Indicador muestra estado de conexión con emoji y color
- [ ] Muestra resumen de última sincronización
- [ ] Botón "🔄 Verificar Conexión" es visible
- [ ] Al hacer clic, indicador se actualiza
- [ ] Logs registran: "Usuario solicitó verificación rápida desde sidebar"
- [ ] Si conexión exitosa, indicador cambia a verde

**Estado:** ⬜ No probado | ✅ Pasó | ❌ Falló

---

### TC-UI-009: Navegación entre Tabs
**Objetivo:** Verificar que las tabs funcionan correctamente

**Pasos:**
1. Ir a la página de sincronización
2. Observar las 2 tabs: "🚀 Sincronización Rápida" y "🔧 Sincronización Manual"
3. Hacer clic en cada tab alternadamente
4. Verificar que el contenido cambia

**Resultado esperado:**
- [ ] Tab 1 (Rápida) muestra:
  - Descripción de la sincronización completa
  - Tiempo estimado
  - Botón grande "Sincronizar Todo Ahora"
- [ ] Tab 2 (Manual) muestra:
  - Descripción de sincronización selectiva
  - Selector de servicios con descripciones amigables
  - Botón "Sincronizar Servicio Seleccionado"
  - Botón de refrescar (🔄)
- [ ] El cambio entre tabs es instantáneo
- [ ] El panel de métricas superior permanece visible al cambiar tabs

**Estado:** ⬜ No probado | ✅ Pasó | ❌ Falló

---

### TC-UI-010: Verificación de Logging Centralizado
**Objetivo:** Confirmar que el logging centralizado se preservó 100%

**Pasos:**
1. Ejecutar varias acciones:
   - Sincronización completa
   - Sincronización manual de 2 servicios
   - Verificación de conexión desde sidebar
   - Expandir detalles de sincronización
2. Revisar archivo de logs

**Resultado esperado:**
- [ ] Archivo `logs/sincronizacion_YYYY-MM-DD.log` existe
- [ ] Contiene entradas con formato correcto:
  ```
  YYYY-MM-DD HH:MM:SS,mmm - sincronizacion - LEVEL - Mensaje
  ```
- [ ] Todas las funciones nuevas generan logs apropiados
- [ ] Niveles de log son correctos (INFO/WARNING/ERROR/DEBUG)
- [ ] No hay logs duplicados innecesariamente

**Comandos de verificación:**
```powershell
# Ver últimas 20 líneas del log más reciente
cat facturador/logs/sincronizacion_*.log | Select-Object -Last 20

# Contar entradas por nivel
(cat facturador/logs/sincronizacion_*.log | Select-String "INFO").Count
(cat facturador/logs/sincronizacion_*.log | Select-String "WARNING").Count
(cat facturador/logs/sincronizacion_*.log | Select-String "ERROR").Count

# Buscar entradas de funciones nuevas
cat facturador/logs/sincronizacion_*.log | Select-String "notificar|panel_metricas|sidebar|expandible|progreso"
```

**Estado:** ⬜ No probado | ✅ Pasó | ❌ Falló

---

## 📊 Resumen de Pruebas

| Test | Estado | Notas |
|------|--------|-------|
| TC-UI-001 | ⬜ |  |
| TC-UI-002 | ⬜ |  |
| TC-UI-003 | ⬜ |  |
| TC-UI-004 | ⬜ |  |
| TC-UI-005 | ⬜ |  |
| TC-UI-006 | ⬜ |  |
| TC-UI-007 | ⬜ |  |
| TC-UI-008 | ⬜ |  |
| TC-UI-009 | ⬜ |  |
| TC-UI-010 | ⬜ |  |

**Total:** 0/10 probados

---

## 🐛 Registro de Bugs Encontrados

### Bug #1
**Test:** TC-UI-XXX  
**Descripción:**  
**Severidad:** 🔴 Alta | 🟡 Media | 🟢 Baja  
**Reproducción:**  
**Estado:** ⬜ Abierto | ✅ Resuelto  

---

## 📝 Notas Adicionales

### Entorno de Prueba
- **SO:** Windows  
- **Python:** 3.x  
- **Streamlit:** 1.49.0+  
- **Navegador:**  
- **Fecha de prueba:**  

### Observaciones Generales
(Añadir cualquier observación relevante durante las pruebas)

---

## ✅ Criterios de Aceptación

La Fase 3 se considera **ACEPTADA** cuando:
- [ ] Todos los tests (TC-UI-001 a TC-UI-010) pasan exitosamente
- [ ] No hay errores críticos en logs
- [ ] No hay errores de sintaxis o runtime
- [ ] La funcionalidad existente no se rompió
- [ ] El logging centralizado funciona correctamente
- [ ] La experiencia de usuario es fluida y sin bugs visuales

---

**Preparado por:** GitHub Copilot  
**Última actualización:** 2024  
**Versión del documento:** 1.0  
