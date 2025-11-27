# Actualización del flujo de reinicio de facturación

## Objetivo
Dejar documentados los ajustes realizados para que, tras una emisión exitosa de factura, la barra lateral se restablezca por completo —incluido el campo *Número de Documento*— y las comandas procesadas dejen de mostrarse para su reutilización.

---

## Cambios principales

### `facturador/facturacion_sidebar.py`
- Se añadió el flag `reset_cliente` dentro de `reset_sidebar_fields()`. Cada vez que se limpia el estado (comandas procesadas, método de pago, etc.) se activa esta bandera para indicar que el formulario de cliente debe reiniciarse.
- `render_sidebar_client_data()` ahora revisa `reset_cliente` antes de renderizar el `text_input` del número de documento:
  - Si la bandera está activa, el campo se pinta vacío y la bandera se desactiva inmediatamente.
  - En caso contrario, se respeta el valor de `st.session_state['numero_documento']` (útil cuando el usuario escribe manualmente o recupera un cliente).
- Con esto se evita que, tras el reinicio, el cliente se recargue desde la base y vuelva a mostrar el mismo documento.

### `facturador/tabs/facturacion_tab.py`
- Se incorporó un helper `_mark_comandas_as_processed` que se reutiliza para garantizar que las comandas facturadas desaparezcan del multiselect.
- El botón *Facturar* (`_render_facturar_button`) ahora controla el resultado mediante `st.session_state['last_submission_success']`:
  - Ejecuta el handler correspondiente (online u offline).
  - Si hay éxito, marca comandas, resetea el sidebar (activando `reset_cliente`) y lanza `st.rerun()` para refrescar la UI.
- Los handlers `_handle_online_submission` y `_handle_offline_submission`:
  - Devuelven valores booleanos y encapsulan `return False` en cualquier rama de error.
  - Guardan en `last_submission_success` la lista de comandas utilizadas y el mensaje de confirmación.
  - Registra `flash_message` para mostrar la confirmación tras el rerun.

---

## Flujo resultante
1. El usuario emite la factura (online u offline).
2. El handler correspondiente valida, persiste, marca la emisión como exitosa y llena `last_submission_success`.
3. `_render_facturar_button` detecta el payload, llama a `_mark_comandas_as_processed`, ejecuta `reset_sidebar_fields()` (que activa `reset_cliente`) y dispara `st.rerun()`.
4. En el nuevo render:
   - Se muestra el `flash_message` con el resumen de la factura generada.
  - El multiselect excluye las comandas procesadas.
  - El número de documento aparece vacío porque `reset_cliente` fuerza el reinicio del formulario.

---

## Notas finales
- El flujo mantiene compatibilidad tanto en modo online como offline.
- `py_compile` sobre `facturacion_sidebar.py` y `facturacion_tab.py` se ejecutó sin errores tras la refactorización.
- Si en el futuro se añaden campos condicionados al formulario de cliente, basta con consultar `reset_cliente` para garantizar un reinicio homogéneo.
