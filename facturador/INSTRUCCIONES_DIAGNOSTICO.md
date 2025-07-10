# 🔍 Guía de Diagnóstico del Sistema de Impresión

## 📋 Plan de Acción Implementado

Se han creado varios módulos de diagnóstico para identificar exactamente por qué no funciona la impresión de facturas:

### 🆕 Archivos Creados

1. **`diagnostico_impresion.py`** - Módulo principal de diagnóstico
2. **`verificar_imports.py`** - Script independiente para verificar importaciones  
3. **`ejecutar_diagnostico.ps1`** - Script de PowerShell para ejecutar todo
4. **`main_enhanced_demo.py`** - Modificado con modos de debug adicionales

## 🚀 Cómo Usar el Sistema de Diagnóstico

### Opción 1: Ejecutar Script Completo (Recomendado)
```powershell
# En PowerShell, navegar al directorio del proyecto y ejecutar:
./ejecutar_diagnostico.ps1
```

### Opción 2: Ejecutar Verificaciones Individuales

#### 2.1 Verificar Importaciones
```powershell
python verificar_imports.py
```

#### 2.2 Ejecutar Sistema con Debug
```powershell
streamlit run main_enhanced_demo.py
```
Luego seleccionar **"🐛 Debug Impresión"** o **"🔍 Diagnóstico Completo"** en el menú.

## 🔧 Modos de Diagnóstico Disponibles

### 🐛 **Debug Impresión**
- Simula el proceso completo paso a paso
- Muestra exactamente dónde falla el proceso
- Permite probar la generación de HTML
- Opción de ejecutar impresión real

### 🔍 **Diagnóstico Completo**  
- Analiza el estado completo del session_state
- Verifica permisos de carpetas
- Prueba la generación de HTML con datos de ejemplo
- Verifica todas las importaciones necesarias
- Guarda reportes detallados

## 📊 Qué Buscar en los Resultados

### ✅ **Si todo está bien:**
- Todos los módulos se importan correctamente
- Se genera HTML sin errores
- Las carpetas tienen permisos correctos
- El session_state contiene todos los datos necesarios

### ❌ **Problemas comunes y soluciones:**

#### **Error de Importación**
```
❌ invoice_templates - ImportError: No module named 'invoice_templates'
```
**Solución:** Verificar que el archivo existe y está en el directorio correcto.

#### **Datos Faltantes**
```
❌ Faltan claves requeridas: datos_impresion, cuf
```
**Solución:** Primero completar una facturación exitosa antes de intentar imprimir.

#### **HTML Vacío**
```
❌ HTML generado está vacío o es None
```
**Solución:** Verificar los datos de entrada en `datos_impresion`.

#### **Permisos de Carpetas**
```
❌ pdfs/ - Existe pero SIN permisos de escritura
```
**Solución:** Ejecutar como administrador o cambiar permisos de la carpeta.

## 📁 Archivos de Salida

El sistema genera varios archivos de diagnóstico:

- `debug/session_state_debug_YYYYMMDD_HHMMSS.json` - Estado completo del sistema
- `debug/test_html_YYYYMMDD_HHMMSS.html` - HTML de prueba generado
- `debug/diagnostico_sistema_YYYYMMDD_HHMMSS.txt` - Reporte completo del sistema

## 🎯 Próximos Pasos

1. **Ejecutar el diagnóstico completo**
2. **Identificar exactamente dónde falla el proceso**
3. **Revisar los archivos de log generados**
4. **Corregir los problemas específicos encontrados**

## 💡 Funciones de Prueba

### Simular Datos de Factura
El diagnóstico incluye una función para simular datos completos de una factura, útil para probar sin necesidad de completar todo el proceso de facturación.

### Probar Generación HTML
Permite probar la función `generate_compact_html_invoice` con datos conocidos para verificar que funciona correctamente.

### Verificar Hardware de Impresión
Verifica la conexión con la impresora térmica (si está conectada).

---

## 🚨 **Importante**

Este sistema de diagnóstico es **no invasivo** - no modifica el funcionamiento normal del sistema, solo agrega capacidades de debugging. Puedes seguir usando el sistema normal seleccionando los modos "Mejorado" u "Original".

---

## 📞 **Siguientes Pasos Recomendados**

1. Ejecutar `./ejecutar_diagnostico.ps1`
2. Revisar la salida de `verificar_imports.py`
3. Usar el modo "🔍 Diagnóstico Completo" en Streamlit
4. Analizar los archivos generados en `debug/`
5. Reportar los resultados específicos encontrados
