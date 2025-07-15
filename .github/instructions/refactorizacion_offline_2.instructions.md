---
applyTo: '**'
---
### **Fase de Refactorización Offline: Paso 2 de 3**

**Objetivo:** Modificar `facturacion_tab.py` para que sea consciente del contexto (online/offline) y adapte tanto su interfaz como su lógica de acción.

#### **Acciones a Realizar:**

1.  **Pasar el Contexto a `facturacion_tab.py`:**
    *   Abre el archivo `ui_copy.py`.
    *   Busca el bucle `for tab, tab_name in zip(rendered_tabs, tabs_to_render):`.
    *   Dentro del bucle, vamos a hacer un caso especial para la pestaña de facturación, para pasarle los parámetros que necesita.
    *   **Código a modificar en `ui_copy.py`:**
        ```python
        # Dentro del bucle for en render_full_ui
        # ...
        render_function = tabs_config[tab_name]
        
        if tab_name == "🧾Facturar":
            # Caso especial: pasar el contexto a la pestaña de facturación
            render_function(is_online=is_online, evento_activo=evento_activo)
        else:
            # Las otras pestañas no necesitan el contexto (por ahora)
            render_function()
        ```

2.  **Adaptar `facturacion_tab.py` para Recibir el Contexto:**
    *   Abre el archivo `tabs/facturacion_tab.py`.
    *   Modifica la firma de su función principal `render()` para que acepte los nuevos parámetros.
    *   **Antes:**
        ```python
        def render():
        ```
    *   **Después:**
        ```python
        def render(is_online: bool, evento_activo: dict = None):
        ```

3.  **Mostrar el Banner de Modo Contingencia:**
    *   Dentro de la función `render()` de `facturacion_tab.py`, justo al principio, añade el banner informativo si estamos en modo offline.
    *   **Código a añadir en `facturacion_tab.py`:**
        ```python
        def render(is_online: bool, evento_activo: dict = None):
            logger.info(f"Renderizando pestaña de facturación en modo {'ONLINE' if is_online else 'OFFLINE'}")

            if not is_online:
                if evento_activo:
                    st.warning(
                        f"""
                        ⚠️ **MODO DE CONTINGENCIA ACTIVADO** ⚠️\n
                        **Evento:** {evento_activo.get('descripcion', 'N/A')} (ID: {evento_activo.get('id')})\n
                        **CUFD del Evento:** `{evento_activo.get('cufd')}`\n
                        *Las facturas se generarán y guardarán localmente para su envío posterior.*
                        """,
                        icon="📡"
                    )
                else:
                    # Este caso no debería ocurrir si main.py funciona bien, pero es una buena salvaguarda
                    st.error("Error crítico: Modo offline pero no se encontró un evento de contingencia activo.")
                    return # Detener la renderización de la pestaña si no hay evento
            
            # ... el resto de la función render() continúa aquí ...
        ```

4.  **Adaptar el Botón "Facturar":**
    *   Busca la función `_render_facturar_button` y pásale el parámetro `is_online`.
    *   Dentro de `_render_facturar_button`, cambia el texto y el `help` del botón dinámicamente como propusimos.
    *   **Código de ejemplo en `facturacion_tab.py`:**
        ```python
        def _render_facturar_button(is_online: bool, ...otros_params...):
            button_label = "Facturar y Enviar al SIN" if is_online else "Generar y Guardar Factura Offline"
            button_help = "Se conectará con el SIN para validar la factura." if is_online else "Guardará la factura localmente. NO se enviará al SIN."

            if st.button(button_label, help=button_help, ...):
                # Por ahora, solo vamos a verificar que la bifurcación funciona
                if is_online:
                    st.info("DEBUG: Se ejecutaría la lógica ONLINE.")
                    # Aquí iría la llamada a _handle_online_submission(...)
                else:
                    st.info("DEBUG: Se ejecutaría la lógica OFFLINE.")
                    # Aquí iría la llamada a _handle_offline_submission(...)
        ```
    *   **Importante:** Por ahora, no implementes la lógica completa de `_handle_offline_submission`. Solo asegúrate de que, al estar en modo offline y presionar el botón, veas el mensaje "DEBUG: Se ejecutaría la lógica OFFLINE.".