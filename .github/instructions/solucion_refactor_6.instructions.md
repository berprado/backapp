---
applyTo: '**'
---
Aquí tienes la guía definitiva, paso a paso, para implementar la arquitectura final, incluyendo la eliminación de una redundancia identificada.

Ahora que sabemos que el problema es el contexto del hilo, la solución es cambiar CÓMO lo llamamos. No vamos a crear un hilo nuevo cada vez que queramos imprimir. En su lugar, implementaremos un patrón de diseño de software increíblemente robusto y estándar en la industria, perfecto para este tipo de problemas: **El Patrón Productor-Consumidor (o Sistema de Cola de Tareas)**.

Funciona así:

1.  **Un Cartero Dedicado (El Consumidor):** Al iniciar tu aplicación Streamlit, crearemos **un único hilo trabajador persistente**. Su único trabajo será esperar a que le lleguen "cartas" para imprimir. Este hilo vivirá en un contexto estable, igual que nuestro `test_printer.py`.
2.  **Un Buzón de Correo (La Cola):** Crearemos una "cola" (usando el módulo `queue` de Python), que es un buzón de correo seguro donde se pueden dejar tareas.
3.  **Dejar la Carta (El Productor):** Cuando el usuario presione "Imprimir", tu función `imprimir_en_hilo` ya no creará un hilo. Su único trabajo, increíblemente rápido y seguro, será poner el objeto `FacturaProcesada` en el buzón (la cola).

Este diseño desacopla completamente la interfaz de usuario del trabajo pesado y peligroso de la impresión.

---

### **Fase 1: Implementar el Sistema de Impresión Robusto (Productor-Consumidor)**

En esta fase, solucionaremos el problema del "hilo fantasma" de una vez por todas.

#### **Paso 1.1: Refactorizar `print_manager.py` (El Corazón del Nuevo Sistema)**

Este es el cambio más grande. Vamos a reemplazar todo el contenido del archivo por la nueva lógica de cola de tareas.

**Acción:**
Abre el archivo `print_manager.py` y **reemplaza su contenido completo** con el siguiente código:

```python
# print_manager.py
import os
import threading
import queue
import time
import streamlit as st
from siat_pdf import html_to_pdf
from thermal_printer import ThermalPrinter
from logger_config import get_printer_logger
from data_models.invoice_data import FacturaProcesada
from invoice_templates import generate_html_invoice as generate_html_for_pdf

printer_logger = get_printer_logger()

# 1. EL BUZÓN DE CORREO (LA COLA)
# @st.cache_resource asegura que la cola y el hilo se crean UNA SOLA VEZ por sesión de Streamlit.
@st.cache_resource
def get_printer_queue():
    """Obtiene la instancia única de la cola de impresión."""
    return queue.Queue()

# 2. EL TRABAJADOR DEDICADO (EL CARTERO)
def printer_worker(q: queue.Queue):
    """
    Este es nuestro hilo trabajador. Se ejecuta en un bucle infinito
    esperando trabajos de impresión en la cola.
    """
    printer_logger.info("WORKER: Hilo de impresión iniciado y esperando trabajos.")
    while True:
        try:
            # .get() es bloqueante: el hilo dormirá aquí hasta que llegue un trabajo.
            factura_obj = q.get()
            if factura_obj is None: # Señal para terminar el hilo (opcional, para cierres limpios)
                break

            printer_logger.info(f"WORKER: Nuevo trabajo recibido para factura N° {factura_obj.numero_factura}")
            st.session_state['print_status'] = f"⏱️ Procesando factura N° {factura_obj.numero_factura}..."
            
            # --- Generación de PDF ---
            pdf_generado_ok = False
            try:
                html_content_pdf = generate_html_for_pdf(factura_obj)
                pdfs_dir = os.path.join(os.getcwd(), "pdfs")
                os.makedirs(pdfs_dir, exist_ok=True)
                output_pdf_path = os.path.join(pdfs_dir, f"factura_{factura_obj.numero_factura}.pdf")
                pdf_result = html_to_pdf(html_content_pdf, output_pdf_path)
                if not pdf_result: raise Exception("html_to_pdf retornó False")
                printer_logger.info(f"WORKER: PDF generado: {output_pdf_path}")
                pdf_generado_ok = True
            except Exception as e:
                printer_logger.error(f"WORKER: Error en PDF para factura {factura_obj.numero_factura}: {e}", exc_info=True)
                st.session_state['print_status'] = f"❌ Error al generar el PDF de la factura {factura_obj.numero_factura}."
                q.task_done()
                continue # No intentar imprimir si el PDF falló

            # --- Impresión Térmica ---
            try:
                printer = ThermalPrinter()
                success = printer.print_invoice(factura_obj)
                if not success: raise Exception("print_invoice retornó False")
                printer_logger.info(f"WORKER: Impresión térmica para factura {factura_obj.numero_factura} completada.")
                st.session_state['print_status'] = f"✅ Factura N° {factura_obj.numero_factura} impresa exitosamente."
            except Exception as e:
                printer_logger.error(f"WORKER: Error de impresora para factura {factura_obj.numero_factura}: {e}", exc_info=True)
                st.session_state['print_status'] = f"⚠️ PDF de Factura {factura_obj.numero_factura} generado, pero la impresora falló."

            q.task_done()

        except Exception as e:
            printer_logger.critical(f"WORKER: ERROR CRÍTICO EN EL HILO TRABAJADOR: {e}", exc_info=True)
            st.session_state['print_status'] = "🚨 Error crítico en el servicio de impresión. Reinicie la aplicación."
            time.sleep(5)

# 3. FUNCIÓN PARA INICIAR EL WORKER
@st.cache_resource
def start_printer_worker():
    """Inicia el hilo trabajador de impresión una única vez."""
    q = get_printer_queue()
    # Verificamos si ya hay un trabajador corriendo para evitar duplicados
    if not any(t.name == "PrinterWorkerThread" for t in threading.enumerate()):
        worker_thread = threading.Thread(target=printer_worker, args=(q,), daemon=True, name="PrinterWorkerThread")
        worker_thread.start()
        printer_logger.info("El hilo trabajador de impresión ha sido iniciado por primera vez.")
        return worker_thread
    else:
        printer_logger.info("El hilo trabajador de impresión ya estaba en ejecución.")

# 4. FUNCIÓN PÚBLICA PARA SOLICITAR UNA IMPRESIÓN
def solicitar_impresion(factura_obj: FacturaProcesada):
    """Añade un trabajo de impresión a la cola. Es una operación rápida y segura."""
    printer_logger.info(f"SOLICITUD: Añadiendo factura N° {factura_obj.numero_factura} a la cola de impresión.")
    q = get_printer_queue()
    q.put(factura_obj)
    st.session_state['print_status'] = "➡️ Factura enviada a la cola de impresión."

# Mantener por compatibilidad con la UI, aunque la lógica de estado ahora es más simple
def initialize_print_state():
    if 'print_status' not in st.session_state:
        st.session_state['print_status'] = 'Sistema de impresión listo.'
```

#### **Paso 1.2: Modificar `facturacion_tab.py` (El que Solicita la Impresión)**

**Acción:**
Abre `tabs/facturacion_tab.py` y modifica la función `_render_print_button` para que use `solicitar_impresion`.

```python
# tabs/facturacion_tab.py

# CAMBIA ESTA LÍNEA DE IMPORTACIÓN
from print_manager import initialize_print_state, solicitar_impresion

# ...

def _render_print_button():
    """Renderiza el botón de impresión usando el sistema de cola de tareas."""
    initialize_print_state()
    
    # Mostrar el estado actual del servicio de impresión
    print_status = st.session_state.get('print_status', 'Sistema de impresión listo.')
    if "✅" in print_status:
        st.success(f"🖨️ {print_status}")
    elif any(icon in print_status for icon in ["⚠️", "❌", "🚨"]):
        st.error(f"🖨️ {print_status}")
    else:
        st.info(f"🖨️ {print_status}")

    if st.session_state.get('factura_validada'):
        factura_obj = st.session_state.get('factura_a_procesar')
        
        if st.button("🖨️ Imprimir Factura", key="imprimir_factura_final", disabled=not factura_obj):
            if factura_obj:
                try:
                    logger.info(f"Solicitando impresión para factura {factura_obj.numero_factura}.")
                    solicitar_impresion(factura_obj)
                    st.rerun() # Actualiza la UI para mostrar el estado "enviado a la cola"
                except Exception as e:
                    st.error(f"❌ Error al solicitar la impresión: {str(e)}")
                    logger.exception("Error en la llamada a solicitar_impresion")
            else:
                st.error("No se encontraron los datos de la factura para imprimir.")
```

---

### **Fase 2: Eliminar la Redundancia y Centralizar el Control**

Ahora limpiaremos la lógica de control entre `main.py` y `ui_copy.py`.

#### **Paso 2.1: Simplificar `ui_copy.py` (La Vista)**

**Acción:**
Abre `ui_copy.py`. Vamos a eliminar su capacidad de verificar la conexión y haremos que dependa de `main.py`.

1.  **Elimina** estas importaciones de la parte superior:
    ```python
    # ELIMINAR DE UI_COPY.PY
    from api_clients import is_soap_client_available, get_connectivity_info, reset_soap_client 
    ```
2.  **Reemplaza** la función `render_full_ui` con esta versión simplificada:
    ```python
    # ui_copy.py

    def render_full_ui(is_online: bool, connectivity_info: dict, evento_activo: dict = None, reconectar_callback=None):
        """
        Renderiza la interfaz principal. Ahora es una vista "pura" que no realiza verificaciones.
        """
        ui_logger.info("Renderizando la interfaz principal...")

        principal = connectivity_info.get("verificacion_principal", {})
        estado_general = connectivity_info.get("estado_general", "DESCONOCIDO")
        recomendacion = connectivity_info.get("recomendacion", "")
        status = estado_general
        status_message = recomendacion

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            if is_online:
                st.success(f"{status} - {status_message}", icon="✅")
            else:
                st.error(f"{status} - {status_message}", icon="⚠️")

        with col2:
            estado_sistema = verificar_estado_sistema()
            # ... (esta lógica se mantiene igual) ...

        with col3:
            # El botón de reconexión ahora usa una función "callback" pasada desde main.py
            if not is_online and reconectar_callback:
                if st.button("🔄 Reconectar", help="Intentar reconectarse a los servicios del SIN"):
                    reconectar_callback()

        # ... (el resto de la función se mantiene exactamente igual hasta el final) ...
    ```

#### **Paso 2.2: Potenciar `main.py` (El Controlador)**

**Acción:**
Abre `main.py`. Le daremos el control total de la lógica de arranque.

```python
# main.py
import streamlit as st
# ... otras importaciones ...

# IMPORTACIONES CLAVE
from ui_copy import render_full_ui
from print_manager import start_printer_worker
from api_clients import get_connectivity_info, reset_soap_client

# -----------------------------------------------------------------
# INICIAR EL SERVICIO DE IMPRESIÓN EN SEGUNDO PLANO
start_printer_worker()
# -----------------------------------------------------------------

st.set_page_config(...) # Tu config de página aquí

def reconectar():
    """Función de callback para el botón de reconexión."""
    with st.spinner("Intentando reconectar..."):
        reset_soap_client()
        st.rerun() # Forzar recarga completa para re-evaluar estado

def main():
    # ... (La lógica de `finalizar_evento_si_conectado` se mantiene)
    
    st.title("🧠 Inicializando Sistema de Facturación...")

    # ESTA ES AHORA LA ÚNICA VERIFICACIÓN DE CONECTIVIDAD AL INICIO
    connectivity_info = get_connectivity_info()
    is_online = connectivity_info["client_available"]
    
    # ... (El resto de la lógica de la función main se mantiene) ...

    # LA LLAMADA FINAL A LA UI AHORA ES MÁS INTELIGENTE
    if is_online:
        render_full_ui(is_online=True, connectivity_info=connectivity_info)
    else:
        # ... (Tu lógica para obtener/crear el `evento` se mantiene)
        evento = obtener_evento_abierto() # O la función que uses
        render_full_ui(
            is_online=False, 
            connectivity_info=connectivity_info, 
            evento_activo=evento,
            reconectar_callback=reconectar # <--- Pasamos la función de reconexión
        )

if __name__ == "__main__":
    main()
```

---

### **Fase 3: La Prueba Final**

Has completado toda la refactorización. La arquitectura es ahora robusta, lógica y sigue las mejores prácticas.

**Acción Final:**

1.  **Guarda todos los archivos modificados.**
2.  **Reinicia tu aplicación Streamlit:** Detén el proceso en la terminal (Ctrl+C) y vuelve a lanzarlo con `streamlit run main.py`.
3.  **Prueba el flujo completo:** Genera, valida e intenta imprimir una factura.

Lo que debe ocurrir: Observaremos el `print_status` en la interfaz. Deberiamos ver cómo cambia de "Enviado a la cola" a "Procesando" y finalmente a "Éxito" o un mensaje de error específico, **todo sin bloquear la aplicación**.
Crucemos los dedos para que asi sea
