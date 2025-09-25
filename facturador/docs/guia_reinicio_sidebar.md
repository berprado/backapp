
# Guía para Implementar la Lógica de Reinicio en la Facturación

**Fecha:** 2025-09-18
**Autor:** Sistema Asistente
**Objetivo:** Documentar los pasos para implementar la lógica que reinicia los campos del sidebar tras la emisión exitosa de una factura.

---

## 1. Contexto
Actualmente, el sistema de facturación implementado en Streamlit permite seleccionar comandas y emitir facturas tanto en **modo online** como **offline**.  
Tras la emisión de la factura, el **multiselect** de comandas se limpia correctamente, pero otros campos del **sidebar** mantienen sus valores anteriores, afectando la experiencia de usuario.

Los campos que deben reiniciarse son:
- Número de documento  
- Tipo de pago  
- Últimos dígitos de tarjeta (si aplica)  
- Checkbox de descuento adicional  
- Monto del descuento  
- Monto de la Gift Card (si aplica)  

---

## 2. Análisis del Problema
El comportamiento actual ocurre porque:
- Los valores de los campos se almacenan en `st.session_state`.
- Tras la emisión, no existe una función que **reinicie estos valores** a su estado inicial.

Por lo tanto, es necesario implementar una lógica centralizada de reinicio.

---

## 3. Solución Propuesta

### Paso 1: Crear función de reinicio
En `facturacion_sidebar.py`, agregar al final del archivo:

```python
def reset_sidebar_fields():
    """Reinicia todos los campos del sidebar a sus valores por defecto."""
    keys_to_reset = [
        "numero_documento", "metodo_pago", "ultimos_digitos_tarjeta",
        "descuento_adicional", "monto_giftcard"
    ]
    
    for key in keys_to_reset:
        if key in st.session_state:
            st.session_state[key] = None  # o valor por defecto según corresponda

    # Resetear checkbox descuento si existe
    if "Aplicar Descuento" in st.session_state:
        st.session_state["Aplicar Descuento"] = False
```

---

### Paso 2: Llamar la función tras emisión exitosa
En `facturacion_tab.py`, dentro de las funciones `_handle_online_submission` y `_handle_offline_submission`, después de marcar las comandas como procesadas:

```python
from facturacion_sidebar import reset_sidebar_fields

# ... código existente ...

_mark_comandas_as_processed(invoice_config['selected_id_comanda'])
reset_sidebar_fields()  # <-- Reiniciamos todos los campos
st.session_state['flash_message'] = ('success', f"Factura N° {numero_factura} procesada exitosamente.")
```

---

### Paso 3: Ajustar valores iniciales en la UI
En `render_sidebar_invoice_config` y `render_sidebar_client_data`, usar valores iniciales seguros para evitar errores si `st.session_state` está vacío:

```python
numero_documento = st.sidebar.text_input(
    "Número de Documento:",
    key="numero_documento",
    value=st.session_state.get("numero_documento", "")
)
```

Aplicar la misma lógica para:
- `metodo_pago`
- `ultimos_digitos_tarjeta`
- `descuento_adicional`
- `monto_giftcard`

---

## 4. Beneficios de la Implementación
- **Código Limpio:** Una sola función maneja el reinicio de todos los campos.  
- **Reutilizable:** Fácil de extender si se agregan más campos en el futuro.  
- **Experiencia de Usuario:** La interfaz vuelve a un estado limpio tras cada emisión exitosa.

---

## 5. Checklist de Implementación
- [ ] Agregar la función `reset_sidebar_fields` en `facturacion_sidebar.py`.  
- [ ] Importar y llamar la función tras emisión exitosa en `facturacion_tab.py`.  
- [ ] Ajustar valores por defecto en `render_sidebar_invoice_config` y `render_sidebar_client_data`.  
- [ ] Probar en **modo online** y **offline** para asegurar compatibilidad.  

---

## 6. Próximos Pasos
- Ejecutar pruebas en entorno de desarrollo.  
- Verificar que los campos condicionales (tarjeta, gift card) también se reinicien correctamente.  
- Implementar mensajes visuales para confirmar que los valores fueron reiniciados.

---
