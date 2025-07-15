---
applyTo: '**'
---
---

### **Fase de Refactorización Offline: Paso 1 de 3**

**Objetivo:** Modificar el punto de entrada de la aplicación (`main.py`) para que, en lugar de mostrar una UI de contingencia simple, llame a la interfaz de usuario principal (`ui_copy.py`), pasándole el contexto de que está en modo offline y la información del evento activo.

Esto unifica el flujo de la aplicación: `main.py` siempre delega la construcción de la UI a `ui_copy.py`, pero le proporciona el contexto necesario.

#### **Acciones a Realizar:**

1.  **Renombrar la función en `ui_copy.py` para mayor claridad.**
    *   Abre el archivo `ui_copy.py`.
    *   Busca la línea `def main(is_online=None, connectivity_info=None):`
    *   Cámbiale el nombre a algo más descriptivo, como `render_full_ui`. Y haz que acepte un parámetro más para el evento.
    *   **Antes:**
        ```python
        def main(is_online=None, connectivity_info=None):
        ```
    *   **Después:**
        ```python
        def render_full_ui(is_online: bool, connectivity_info: dict, evento_activo: dict = None):
        ```
        (El `evento_activo: dict = None` hace que el parámetro sea opcional, lo cual es útil).

2.  **Modificar la llamada en `main.py` para el modo ONLINE.**
    *   Abre el archivo `main.py`.
    *   Primero, cambia el import para reflejar el nuevo nombre.
    *   **Antes:**
        ```python
        from ui_copy import main as online_main
        ```
    *   **Después:**
        ```python
        from ui_copy import render_full_ui
        ```
    *   Luego, busca la línea donde se llama a la función en el bloque `if conectado:`.
    *   **Antes:**
        ```python
        online_main(is_online=conectado, connectivity_info=resultado_completo)
        ```
    *   **Después:**
        ```python
        render_full_ui(is_online=conectado, connectivity_info=resultado_completo)
        ```

3.  **Reemplazar la UI de contingencia simple en `main.py` con la nueva llamada.**
    *   En `main.py`, localiza el bloque `else:` que se ejecuta cuando no hay conexión.
    *   Actualmente, este bloque contiene un `st.form("form_factura_offline")` y toda la lógica para guardar un XML simple. **Vamos a reemplazar todo ese bloque.**
    *   **Antes (Lógica a reemplazar):**
        ```python
        # Este bloque entero, desde "else:" hasta el final de la función main()
        else:
            st.error("❌ No se pudo conectar al SIN. Se activará la contingencia.")
            # ...
            # ... toda la lógica del formulario y el botón de finalizar
            # ...
        ```
    *   **Después (El nuevo bloque `else:`):**
        ```python
        else:
            # La lógica para notificar y gestionar el evento se mantiene...
            st.error("❌ No se pudo conectar al SIN. Se activará la contingencia.")
            notificar_reconexion_si_aplica()

            eventos_activos = get_significant_events(limit=5, only_open=True)
            if eventos_activos:
                st.info("ℹ️ Ya existe un evento registrado en modo contingencia.")
                evento = eventos_activos[0]
            else:
                # ... (toda tu lógica existente para registrar un nuevo evento) ...
                # ... esto no cambia ...
                evento = ... # El diccionario del evento creado o None si falla

            # Aquí viene el cambio clave: si tenemos un evento, llamamos a la UI completa
            if evento:
                render_full_ui(is_online=False, connectivity_info=resultado_completo, evento_activo=evento)
            else:
                # Si no se pudo encontrar o crear un evento, mostramos el error
                st.error("❌ Error crítico: No se pudo obtener o registrar un evento de contingencia. La facturación está deshabilitada.")
        ```