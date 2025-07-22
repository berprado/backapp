# print_manager.py
import os
import threading
import queue
import time
import streamlit as st
from siat_pdf import html_to_pdf
from thermal_printer import ThermalPrinter
from logger_config import get_printer_logger
from facturador.data_models import FacturaProcesada
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
    Hilo trabajador con conexión de impresora persistente.
    """
    printer_logger.info("WORKER: Hilo de impresión iniciado.")
    
    # Creamos una ÚNICA instancia de la impresora para este worker.
    printer = ThermalPrinter()
    
    while True:
        try:
            factura_obj = q.get()
            if factura_obj is None: break

            printer_logger.info(f"WORKER: Nuevo trabajo recibido para factura N° {factura_obj.numero_factura}")
            st.session_state['print_status'] = f"⏱️ Procesando factura N° {factura_obj.numero_factura}..."
            
            # --- Generación de PDF (sin cambios) ---
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

            # --- Impresión Térmica con Conexión Persistente ---
            try:
                # Conectamos solo si es necesario (la primera vez o si hubo un error)
                printer.connect()
                
                success = printer.print_invoice(factura_obj)
                if not success: raise Exception("print_invoice retornó False")
                
                printer_logger.info(f"WORKER: Impresión térmica para factura {factura_obj.numero_factura} completada.")
                st.session_state['print_status'] = f"✅ Factura N° {factura_obj.numero_factura} impresa exitosamente."
            except Exception as e:
                printer_logger.error(f"WORKER: Error de impresora para factura {factura_obj.numero_factura}: {e}", exc_info=True)
                st.session_state['print_status'] = f"⚠️ PDF de Factura {factura_obj.numero_factura} generado, pero la impresora falló."
                # Importante: Desconectamos para forzar un reintento de conexión en el próximo trabajo
                printer.disconnect()

            q.task_done()

        except Exception as e:
            printer_logger.critical(f"WORKER: ERROR CRÍTICO EN EL HILO TRABAJADOR: {e}", exc_info=True)
            st.session_state['print_status'] = "🚨 Error crítico en el servicio de impresión. Reinicie la aplicación."
            time.sleep(5)

    # Al salir del bucle (si alguna vez lo hace), nos aseguramos de desconectar
    printer.disconnect()
    printer_logger.info("WORKER: Hilo de impresión finalizado.")

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

def mostrar_mensaje_impresion_en_curso():
    """
    Función de compatibilidad. En el nuevo sistema, el estado se muestra directamente.
    """
    pass
