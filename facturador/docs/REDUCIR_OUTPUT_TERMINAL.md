# 🔇 Guía para Reducir Output Verboso en Terminal

## ✅ **SOLUCIÓN IMPLEMENTADA**

He añadido configuraciones en dos lugares para reducir los logs verbosos de `fontTools`:

### **1. En `main.py` (Líneas 9-18):**
```python
# 🔧 CONFIGURACIÓN PARA REDUCIR OUTPUT VERBOSO EN TERMINAL
# Suprimir logs DEBUG de librerías externas que generan ruido
logging.getLogger('fontTools').setLevel(logging.WARNING)
logging.getLogger('fontTools.ttLib').setLevel(logging.WARNING)
logging.getLogger('fontTools.subset').setLevel(logging.WARNING)
logging.getLogger('fontTools.ttLib.ttFont').setLevel(logging.WARNING)
logging.getLogger('fontTools.subset.timer').setLevel(logging.WARNING)
```

### **2. En `logger_config.py` (Función global):**
```python
def suppress_verbose_external_logs():
    """Configura los loggers para mostrar solo mensajes importantes."""
    # Se ejecuta automáticamente al importar el módulo
```

---

## 🚀 **MÉTODOS ADICIONALES**

### **Opción A: Comando Streamlit con Logging Reducido**
```powershell
streamlit run main.py --logger.level=warning
```

### **Opción B: Variable de Entorno**
```powershell
$env:STREAMLIT_LOGGER_LEVEL="WARNING"
streamlit run main.py
```

### **Opción C: Filtrar Output en PowerShell**
```powershell
# Excluir líneas que contengan 'fontTools'
streamlit run main.py 2>&1 | Select-String -Pattern 'fontTools' -NotMatch

# O excluir múltiples patrones
streamlit run main.py 2>&1 | Select-String -Pattern 'DEBUG.*fontTools|INFO.*fontTools' -NotMatch
```

### **Opción D: Redirigir a Archivo**
```powershell
# Guardar todo el output en un archivo
streamlit run main.py > app_output.log 2>&1

# Solo mostrar errores importantes
streamlit run main.py 2>&1 | Select-String -Pattern 'ERROR|CRITICAL|WARNING'
```

---

## 🔧 **CONFIGURACIÓN PERMANENTE**

### **En archivo `.streamlit/config.toml`:**
```toml
[logger]
level = "warning"
messageFormat = "%(asctime)s %(message)s"
```

### **Variables de Entorno en `run_app.bat`:**
```batch
@echo off
set STREAMLIT_LOGGER_LEVEL=WARNING
streamlit run facturador/main.py
```

---

## 🎯 **RESULTADO ESPERADO**

Después de estos cambios, deberías ver:

**ANTES:**
```
DEBUG:fontTools.ttLib.ttFont:Reading 'maxp' table from disk
DEBUG:fontTools.subset.timer:Took 0.001s to load 'maxp'
INFO:fontTools.subset:maxp pruned
```

**DESPUÉS:**
```
(Sin logs de fontTools, solo mensajes importantes de tu aplicación)
```

---

## ⚡ **APLICAR CAMBIOS INMEDIATAMENTE**

Para que los cambios tomen efecto, reinicia tu aplicación:

```powershell
# Detener streamlit (Ctrl+C) y ejecutar:
cd facturador
streamlit run main.py
```

Los cambios en `main.py` y `logger_config.py` se aplicarán automáticamente.
