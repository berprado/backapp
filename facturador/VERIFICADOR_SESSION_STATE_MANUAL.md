# Verificador de Session State - Manual de Uso

## 🔍 Qué es el Verificador

El Verificador de Session State es una herramienta de diagnóstico integrada en el sistema de facturación que ayuda a identificar y resolver problemas relacionados con el sistema de impresión.

## 🚀 Cómo Acceder

### Método 1: Pestaña Pruebas
1. Ve a la pestaña **🔧Pruebas** en la interfaz principal
2. Se abrirá automáticamente el panel de diagnóstico completo

### Método 2: Diagnóstico Rápido
1. Cuando hay problemas de impresión detectados, aparece un botón **🔧 Diagnóstico Rápido de Impresión**
2. Haz clic en el botón para abrir el diagnóstico en un expander

## 📊 Pestañas del Diagnóstico

### 👻 Estado Fantasma
- **Propósito**: Detecta procesos de impresión que no terminaron correctamente
- **Cuándo usar**: Si las impresiones se quedan "colgadas"
- **Acciones disponibles**:
  - 🔧 Forzar Limpieza de Estado
  - 📊 Verificar Hilos
  - 🗂️ Ver Logs Recientes

### 🧵 Hilos
- **Propósito**: Monitorea hilos de Python activos
- **Qué muestra**: 
  - Total de hilos activos
  - Hilos de impresión específicos
  - Hilos daemon y normales
- **Indicadores**:
  - ✅ Estado normal (< 5 hilos)
  - ⚠️ Muchos hilos activos
  - 🚨 Hilos de impresión detectados

### 📁 Archivos Señal
- **Propósito**: Verifica archivos de señalización que pueden causar problemas
- **Qué hace**: 
  - Lista archivos `.signal` en la carpeta `debug/`
  - Permite limpiar archivos acumulados
- **Cuándo limpiar**: Si hay más de 5 archivos de señal

### 🔄 Recargas
- **Propósito**: Verifica problemas de persistencia entre recargas de Streamlit
- **Métricas**:
  - Contador de sesión
  - Tiempo de sesión
  - Persistencia de estados críticos
- **Problema común**: Estados que persisten cuando no deberían

### 📊 Resumen
- **Propósito**: Vista consolidada de todos los diagnósticos
- **Recomendaciones automáticas**: Basadas en problemas detectados
- **Métricas del sistema**: Vista general del estado

## 🎯 Problemas Comunes y Soluciones

### Problema: "Impresión en progreso" permanente
**Síntomas**: El botón de impresión no funciona, estado shows "impresión en progreso"
**Solución**: 
1. Ve a **👻 Estado Fantasma**
2. Usa **🔧 Forzar Limpieza de Estado**

### Problema: Múltiples hilos de impresión
**Síntomas**: La aplicación va lenta, impresiones duplicadas
**Solución**:
1. Ve a **🧵 Hilos**
2. Si hay hilos de impresión activos, reinicia la aplicación Streamlit

### Problema: Archivos de señal acumulados
**Síntomas**: Errores extraños, comportamiento inconsistente
**Solución**:
1. Ve a **📁 Archivos Señal**
2. Usa **🗑️ Limpiar Archivos de Señal**

### Problema: Estados que no se limpian
**Síntomas**: Problemas persisten después de recargar la página
**Solución**:
1. Ve a **🔄 Recargas**
2. Verifica la persistencia de estados
3. Usa **🧹 Limpiar Session State** si es necesario

## 🔧 Funciones de Emergencia

### Limpieza Total del Sistema
Si todos los métodos anteriores fallan:

1. **🧹 Limpiar Session State** (pestaña Estado Fantasma)
2. **🗑️ Limpiar Archivos de Señal** (pestaña Archivos Señal)
3. **Reiniciar aplicación Streamlit** (ctrl+c en terminal y volver a ejecutar)

### Interpretación de Estados
- `impresion_en_progreso: True` + `impresion_finalizada: False` = 🚨 Proceso fantasma
- `impresion_en_progreso: True` + `impresion_finalizada: True` = ⚠️ Estado inconsistente
- `impresion_en_progreso: False` + `impresion_finalizada: True` = ✅ Normal (listo para nueva impresión)

## 📝 Logs y Debug

El verificador genera logs en la consola que muestran:
- Estado de todas las claves del session_state
- Verificación de tipos de datos
- Estado de archivos relacionados con la última factura
- Recomendaciones específicas

## 🚨 Cuándo Contactar Soporte

Contacta soporte técnico si:
1. El diagnóstico muestra "ESTRUCTURA VÁLIDA" pero los problemas persisten
2. Las acciones de limpieza no resuelven el problema
3. Aparecen errores no contemplados en este manual
4. Los hilos de impresión no se pueden eliminar reiniciando

## 💡 Consejos de Prevención

1. **No cierres la aplicación** durante una impresión
2. **Espera** a que termine cada impresión antes de iniciar otra
3. **Limpia archivos de señal** periódicamente si usas mucho el sistema
4. **Reinicia la aplicación** una vez al día si hay uso intensivo

---
*Este verificador fue diseñado para ser una herramienta de autodiagnóstico que permite resolver la mayoría de problemas de impresión sin intervención técnica.*
