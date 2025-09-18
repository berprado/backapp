
# Informe de Inconsistencias y Solución Propuesta  
**Fecha:** 2025-09-18  
**Autor:** Sistema Asistente  
**Objetivo:** Documentar las inconsistencias identificadas en el reinicio del campo **Número de Documento** en el sidebar y proveer instrucciones detalladas para su corrección.

---

## 1. Inconsistencia Identificada

Tras la emisión exitosa de una factura, se espera que todos los campos del sidebar, incluyendo **Número de Documento**, retomen sus valores por defecto.  
Sin embargo, observamos que **este campo mantiene su valor anterior** después del reinicio.  

### Motivo principal:
- El campo **sí se borra** del `st.session_state` en la función `reset_sidebar_fields()`.  
- **Pero la lógica de carga del cliente** vuelve a rellenar el valor desde la base de datos si existe un cliente con ese número de documento, provocando que visualmente el campo aparezca como no reiniciado.

---

## 2. Impacto en la Aplicación

- El usuario percibe que el campo **no se reinicia correctamente**, aunque internamente sí se elimina del `session_state`.  
- Puede generar confusión y errores en la emisión de facturas si el usuario no nota que los datos cargados provienen de la BD y no de la sesión previa.

---

## 3. Solución Propuesta

### Paso 1: Controlar el Reinicio Explícitamente
En `reset_sidebar_fields()`, agregar un flag especial para indicar que el cliente debe reiniciarse:  

```python
def reset_sidebar_fields():
    keys_to_clear = [
        'numero_documento',
        'metodo_pago',
        'ultimos_digitos_tarjeta',
        'aplicar_descuento',
        'descuento_adicional',
        'monto_giftcard'
    ]
    
    for key in keys_to_clear:
        st.session_state.pop(key, None)
    
    # Flag especial para controlar reinicio del cliente
    st.session_state["reset_cliente"] = True
```

---

### Paso 2: Ajustar la Lógica de Carga del Cliente
En `render_sidebar_client_data()`, modificar la lógica para verificar si el flag `reset_cliente` está activo antes de cargar datos desde la BD:

```python
if "reset_cliente" in st.session_state and st.session_state["reset_cliente"]:
    numero_documento = st.sidebar.text_input("Número de Documento:", key="numero_documento")
    st.session_state["reset_cliente"] = False
else:
    # Lógica actual que rellena el cliente desde BD
    numero_documento = st.sidebar.text_input(
        "Número de Documento:", 
        key="numero_documento", 
        value=st.session_state.get("numero_documento", "")
    )
    # Aquí continuar con la lógica para cargar cliente si existe
```

---

### Paso 3: Integración con el Flujo de Facturación
Verificar en `facturacion_tab.py` que **`reset_sidebar_fields()`** se llame después de una emisión exitosa para activar el flag:

```python
_mark_comandas_as_processed(payload.get('comandas', []))
reset_sidebar_fields()
st.session_state['flash_message'] = ('success', payload.get('message', 'Factura procesada exitosamente.'))
```

---

## 4. Beneficios de la Solución

- El campo **Número de Documento** quedará visualmente vacío tras una emisión exitosa.  
- Se evita que la lógica de carga del cliente sobrescriba el reinicio.  
- La experiencia del usuario será consistente con el resto de los campos del sidebar.

---

## 5. Checklist de Implementación

- [ ] Agregar el flag `reset_cliente` en `reset_sidebar_fields()`.  
- [ ] Modificar `render_sidebar_client_data()` para respetar el flag.  
- [ ] Verificar el correcto reinicio tras emitir una factura.  
- [ ] Probar en **modo online** y **offline** para confirmar compatibilidad.

---

## 6. Próximos Pasos

- Ejecutar pruebas unitarias para verificar que el campo queda vacío tras el reinicio.  
- Asegurar que otros campos condicionales (tarjeta, gift card, descuento) también respeten este enfoque si se requiere.  
- Documentar la lógica final para futuros mantenimientos.

---
