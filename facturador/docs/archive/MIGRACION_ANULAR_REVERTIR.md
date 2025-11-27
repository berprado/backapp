# 🚀 Guía Rápida de Migración - Pestaña Unificada Anular/Revertir

## ⚡ Cambios Necesarios en `main.py`

### Paso 1: Actualizar Importaciones

**ANTES:**
```python
from tabs import (
    facturacion_tab,
    anular_factura_tab,        # ← REMOVER
    revertir_anulacion_tab,    # ← REMOVER
    # ... otros tabs
)
```

**DESPUÉS:**
```python
from tabs import (
    facturacion_tab,
    anular_revertir_tab,       # ← NUEVO: Módulo unificado
    # ... otros tabs
)
```

---

### Paso 2: Actualizar Definición de Pestañas

**ANTES:**
```python
tabs = st.tabs([
    "📝 Facturación",
    "🚫 Anular Factura",       # ← REMOVER
    "🔄 Revertir Anulación",   # ← REMOVER
    # ... otras pestañas
])
```

**DESPUÉS:**
```python
tabs = st.tabs([
    "📝 Facturación",
    "🔧 Anular o Revertir",    # ← NUEVO: Pestaña unificada
    # ... otras pestañas
])
```

---

### Paso 3: Actualizar Renderizado de Pestañas

**ANTES:**
```python
with tabs[0]:
    facturacion_tab.render()

with tabs[1]:
    anular_factura_tab.render()    # ← REMOVER

with tabs[2]:
    revertir_anulacion_tab.render() # ← REMOVER

# ... otras pestañas
```

**DESPUÉS:**
```python
with tabs[0]:
    facturacion_tab.render()

with tabs[1]:
    anular_revertir_tab.render()    # ← NUEVO: Una sola llamada

# ... otras pestañas (ajustar índices si es necesario)
```

---

## 🔍 Ejemplo Completo de `main.py`

```python
import streamlit as st
from tabs import (
    facturacion_tab,
    anular_revertir_tab,  # ← Módulo unificado
    consulta_tab,
    reportes_tab
)

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Facturación",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("📊 Sistema de Facturación Electrónica")

# Definir pestañas
tabs = st.tabs([
    "📝 Facturación",
    "🔧 Anular o Revertir",  # ← Pestaña unificada
    "🔍 Consultas",
    "📈 Reportes"
])

# Renderizar contenido de cada pestaña
with tabs[0]:
    # Guardar nombre de pestaña activa para logging condicional
    st.session_state['main_active_tab_name'] = "Facturación"
    facturacion_tab.render()

with tabs[1]:
    # Guardar nombre de pestaña activa
    st.session_state['main_active_tab_name'] = "Anular o Revertir"
    anular_revertir_tab.render()  # ← Nueva implementación

with tabs[2]:
    st.session_state['main_active_tab_name'] = "Consultas"
    consulta_tab.render()

with tabs[3]:
    st.session_state['main_active_tab_name'] = "Reportes"
    reportes_tab.render()
```

---

## ✅ Checklist de Migración

### Pre-Migración
- [ ] Hacer backup de `main.py` actual
- [ ] Verificar que exista `facturador/tabs/anular_revertir_tab.py`
- [ ] Leer documentación completa (`REFACTOR_ANULAR_REVERTIR.md`)

### Durante Migración
- [ ] Actualizar importaciones en `main.py`
- [ ] Actualizar definición de pestañas
- [ ] Actualizar renderizado de pestañas
- [ ] Ajustar índices de pestañas si es necesario
- [ ] Verificar que `st.session_state['main_active_tab_name']` se actualice correctamente

### Post-Migración
- [ ] Ejecutar aplicación: `streamlit run main.py`
- [ ] Verificar que la pestaña "Anular o Revertir" aparezca
- [ ] Probar cambio entre "Anular Factura" y "Revertir Anulación"
- [ ] Verificar que logs se generen correctamente
- [ ] Probar flujo completo de anulación
- [ ] Probar flujo completo de reversión

### Rollback (Si es necesario)
- [ ] Restaurar backup de `main.py`
- [ ] Reiniciar aplicación
- [ ] Reportar problemas encontrados

---

## 🧪 Pruebas Básicas Post-Migración

### Prueba 1: Navegación
1. Iniciar aplicación
2. Hacer clic en pestaña "Anular o Revertir"
3. ✅ Verificar que se muestre el segmented control
4. ✅ Verificar que aparezca información contextual

### Prueba 2: Cambio de Operación
1. Seleccionar "Anular Factura"
2. ✅ Verificar que aparezca campo "Motivo"
3. Seleccionar "Revertir Anulación"
4. ✅ Verificar que desaparezca campo "Motivo"
5. ✅ Verificar que aparezca advertencia sobre "una sola vez"

### Prueba 3: Validación en Tiempo Real
1. Ingresar número de factura válida
2. ✅ Verificar que se muestren datos de la factura
3. ✅ Verificar que se muestre estado (VÁLIDA/ANULADA)

### Prueba 4: Flujo Completo
1. Intentar anular una factura válida
2. ✅ Verificar que proceso complete exitosamente
3. Intentar revertir la factura anulada
4. ✅ Verificar que proceso complete exitosamente

---

## 🐛 Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'anular_revertir_tab'"

**Solución:**
```bash
# Verificar que el archivo exista
ls facturador/tabs/anular_revertir_tab.py

# Si no existe, el archivo no se creó correctamente
# Copiar el contenido desde el archivo de documentación
```

### Problema: "AttributeError: module 'streamlit' has no attribute 'segmented_control'"

**Causa:** Versión de Streamlit < 1.37.0

**Solución:**
```bash
# Actualizar Streamlit
pip install --upgrade streamlit

# Verificar versión
streamlit --version
# Debe ser >= 1.37.0
```

### Problema: Los logs no se generan correctamente

**Solución:**
```python
# Verificar que st.session_state se actualice:
with tabs[1]:
    st.session_state['main_active_tab_name'] = "Anular o Revertir"
    anular_revertir_tab.render()
```

### Problema: La pestaña se ve mal o no responde

**Solución:**
```bash
# Limpiar caché de Streamlit
streamlit cache clear

# Reiniciar aplicación
```

---

## 📊 Comparación Visual

### Antes (2 pestañas)
```
[Facturación] [Anular Factura] [Revertir Anulación] [Consultas]
     ↑              ↑                  ↑
   Tab 0         Tab 1              Tab 2
```

### Después (1 pestaña unificada)
```
[Facturación] [Anular o Revertir] [Consultas]
     ↑               ↑
   Tab 0          Tab 1
                    ↓
        [Anular Factura | Revertir Anulación]
               (segmented control)
```

---

## 🎯 Beneficios Inmediatos

✅ **Menos pestañas:** Interfaz más limpia  
✅ **Menos clics:** Cambio de operación más rápido  
✅ **Validación en tiempo real:** Feedback instantáneo  
✅ **Mensajes contextuales:** Ayuda específica según operación  
✅ **Código DRY:** Sin duplicación entre módulos

---

## 📞 Soporte

Si encuentras problemas durante la migración:

1. **Revisar logs:** `logs/app_YYYYMMDD.log`
2. **Consultar documentación completa:** `REFACTOR_ANULAR_REVERTIR.md`
3. **Verificar código fuente:** `facturador/tabs/anular_revertir_tab.py`
4. **Hacer rollback si es crítico:** Restaurar backup de `main.py`

---

**¡Buena suerte con la migración! 🚀**
