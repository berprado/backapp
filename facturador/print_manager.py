"""
Módulo para la gestión de impresión de facturas.

Este módulo contiene funciones para la impresión de facturas en impresoras térmicas 
y generación de documentos PDF.
"""

import os
import threading
import queue
from datetime import datetime
import logging
import traceback
import streamlit as st
from invoice_templates import generate_html_invoice
from siat_pdf import html_to_pdf
from thermal_printer import ThermalPrinter
from logger_config import get_printer_logger

printer_logger = get_printer_logger()

def initialize_print_state():
    """
    Inicializa el estado de impresión en la sesión de Streamlit.
    
    Esta función establece los valores predeterminados para el estado
    de impresión en la sesión de Streamlit.
    """
    keys_defaults = {
        'print_status': None,
        'datos_impresion': {},
        'cuf': None,
        'ultima_factura': None,
        'impresion_en_progreso': False,
        'impresion_finalizada': False
    }
    for key, default in keys_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

def reiniciar_estados():
    """
    Reinicia los estados de impresión en la sesión de Streamlit.
    
    Esta función elimina las claves relacionadas con la impresión
    de la sesión de Streamlit.
    """
    keys_to_reset = [
        'factura_validada', 'print_status', 'datos_impresion', 
        'cuf', 'ultima_factura', 'impresion_en_progreso', 
        'impresion_finalizada'
    ]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

def imprimir_en_hilo(html_content_orig, cuf, nit, numero_factura):
    """
    Crea un hilo para manejar la impresión de la factura y generación del PDF.
    El hilo escribe los resultados en una cola para que la interfaz
    principal actualice ``st.session_state`` de forma segura.

    Args:
        html_content_orig (str): Contenido HTML original de la factura.
        cuf (str): Código Único de Facturación.
        nit (str): NIT del emisor.
        numero_factura (str): Número de factura.
    """
    result_queue = queue.Queue()

    def imprimir():
        try:
            printer_logger.info(f"Iniciando proceso de impresión para factura {numero_factura}")

            # Actualizar HTML con CUF
            html_content = html_content_orig.replace("{cuf}", cuf)

            # Guardar HTML para debug y referencia
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_dir = os.path.dirname(os.path.abspath(__file__))
            debug_dir = os.path.join(base_dir, "debug")
            pdfs_dir = os.path.join(base_dir, "pdfs")
            os.makedirs(debug_dir, exist_ok=True)
            os.makedirs(pdfs_dir, exist_ok=True)
            debug_path = os.path.join(debug_dir, f"factura_{numero_factura}_{timestamp}.html")
            
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                f.flush()
                os.fsync(f.fileno())  # Asegurar escritura al disco
            printer_logger.info(f"HTML guardado en {debug_path}")

            # Intentar generar el PDF
            try:
                output_pdf_path = os.path.join(pdfs_dir, f"factura_{numero_factura}_{nit}_{cuf[-8:]}.pdf")
                html_to_pdf(html_content, output_pdf_path)
                printer_logger.info(f"PDF generado exitosamente: {output_pdf_path}")
            except Exception as e:
                raise Exception(f"Error al generar PDF: {str(e)}")

            # Proceder con la impresión térmica
            try:
                printer = ThermalPrinter()
                success = printer.print_invoice(html_content, nit, cuf, numero_factura)
                if success:
                    result_queue.put(("success", "✅ Impresión completada exitosamente"))
                else:
                    raise Exception("Error durante la impresión térmica")
            except Exception as e:
                raise Exception(f"Error en impresión térmica: {str(e)}")

            # Crear un archivo de señalización para indicar que la impresión ha terminado
            signal_file = f"debug/print_complete_{numero_factura}.signal"
            with open(signal_file, "w") as f:
                f.write(f"Impresión completada: {datetime.now().isoformat()}")
                f.flush()
                os.fsync(f.fileno())  # Asegurar escritura al disco
            printer_logger.info(f"Señal de finalización creada: {signal_file}")

        except Exception as e:
            error_msg = f"❌ Error de impresión: {str(e)}"
            printer_logger.error(error_msg)
            printer_logger.error(traceback.format_exc())
            result_queue.put(("error", error_msg))
        finally:
            result_queue.put(("done", None))
    
    # Evitar múltiples procesos de impresión simultáneos
    if st.session_state.get('impresion_en_progreso', False):
        printer_logger.warning("Se intentó iniciar una nueva impresión mientras otra está en progreso.")
        return
    
    # Verificar carpeta de destino PDF
    if not os.path.exists('pdfs'):
        os.makedirs('pdfs')
    
    # Verificar permisos de escritura
    if not os.access('pdfs', os.W_OK):
        printer_logger.error("No hay permisos de escritura en la carpeta pdfs")
        st.session_state['print_status'] = "❌ No hay permisos de escritura en la carpeta de PDFs"
        return
    
    # Actualizar el estado e iniciar el hilo de impresión
    st.session_state['impresion_en_progreso'] = True
    st.session_state['impresion_finalizada'] = False
    st.session_state['print_status'] = "⏱️ Impresión en progreso..."
    
    # Iniciar hilo de impresión
    thread = threading.Thread(target=imprimir, name=f"print_{numero_factura}")
    thread.daemon = True
    thread.start()

    printer_logger.info(f"Hilo de impresión iniciado para la factura {numero_factura}")
    return thread, result_queue

def mostrar_mensaje_impresion_en_curso():
    """
    Muestra un mensaje de advertencia en la UI si la impresión está en curso.
    """
    if st.session_state.get('impresion_en_progreso', False):
        st.warning("⚠️ La impresión está en curso. Por favor, espera a que finalice antes de iniciar una nueva impresión.")

def process_invoice(subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura, nit, cuf):
    """
    Centraliza la generación de HTML, PDF e impresión de la factura.

    Args:
        subtotal (float): Subtotal de la factura.
        descuento_adicional (float): Descuento adicional aplicado.
        monto_giftcard (float): Monto de giftcard aplicado.
        lineas_productos (list): Lista de productos en la factura.
        nombre_cliente (str): Nombre del cliente.
        fecha_emision (str): Fecha de emisión de la factura.
        numero_factura (str): Número de la factura.
        nit (str): NIT del emisor.
        cuf (str): Código Único de Facturación.

    Returns:
        bool: True si el proceso fue exitoso, False en caso de error.
    """
    try:
        # Generar HTML
        html_content = generate_html_invoice(
            subtotal=subtotal,
            descuento_adicional=descuento_adicional,
            monto_giftcard=monto_giftcard,
            lineas_productos=lineas_productos,
            nombre_cliente=nombre_cliente,
            fecha_emision=fecha_emision,
            numero_factura=numero_factura
        )

        # Guardar HTML para depuración
        debug_dir = os.path.join(os.getcwd(), "debug")
        os.makedirs(debug_dir, exist_ok=True)
        debug_path = os.path.join(debug_dir, f"factura_{numero_factura}.html")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Generar PDF
        pdf_dir = os.path.join(os.getcwd(), "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, f"factura_{numero_factura}_{nit}_{cuf[-8:]}.pdf")
        html_to_pdf(html_content, pdf_path)

        # Imprimir factura
        printer = ThermalPrinter()
        printer.process_and_print_invoice(html_content, nit, cuf, numero_factura)

        return True
    except Exception as e:
        printer_logger.error(f"Error en el proceso de factura: {str(e)}")
        return False
