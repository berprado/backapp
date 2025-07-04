"""
Módulo para la gestión de impresión de facturas.

Este módulo contiene funciones para la impresión de facturas en impresoras térmicas 
y generación de documentos PDF.
"""

import os
import threading
from datetime import datetime
import logging
import traceback
import streamlit as st
from invoice_templates import generate_html_invoice
from siat_pdf import html_to_pdf
from thermal_printer import ThermalPrinter
from logger_config import get_printer_logger

printer_logger = get_printer_logger()

# Estructura de ``st.session_state['print_job']`` utilizada para controlar el
# proceso de impresión.  Cada clave se actualiza en diferentes etapas del flujo:
#
# ``cuf`` y ``numero_factura`` se establecen cuando una factura es validada.
# ``datos_impresion`` guarda la información necesaria para generar el HTML de la
# factura.
# ``html_content`` se asigna justo antes de iniciar la impresión.
# ``print_status`` proporciona retroalimentación a la UI durante todo el
# proceso.
# ``in_progress`` y ``finalizado`` indican el estado del hilo de impresión.
PRINT_JOB_DEFAULTS = {
    'cuf': None,
    'numero_factura': None,
    'html_content': None,
    'print_status': None,
    'datos_impresion': {},
    'in_progress': False,
    'finalizado': False,
}

def initialize_print_state():
    """Prepara ``st.session_state['print_job']`` con valores por defecto."""
    if 'print_job' not in st.session_state:
        st.session_state['print_job'] = PRINT_JOB_DEFAULTS.copy()

def reiniciar_estados():
    """Restablece los valores del trabajo de impresión."""
    st.session_state['print_job'] = PRINT_JOB_DEFAULTS.copy()
    if 'factura_validada' in st.session_state:
        del st.session_state['factura_validada']

def imprimir_en_hilo(html_content_orig, cuf, nit, numero_factura):
    """
    Crea un hilo para manejar la impresión de la factura y generación del PDF.
    Esta función incorpora toda la lógica de monitoreo del hilo.

    Args:
        html_content_orig (str): Contenido HTML original de la factura.
        cuf (str): Código Único de Facturación.
        nit (str): NIT del emisor.
        numero_factura (str): Número de factura.
    """
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
                    st.session_state['print_job']['print_status'] = "✅ Impresión completada exitosamente"
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
            st.session_state['print_job']['print_status'] = error_msg
        finally:
            st.session_state['print_job']['in_progress'] = False
            st.session_state['print_job']['finalizado'] = True
    
    # Evitar múltiples procesos de impresión simultáneos
    if st.session_state.get('print_job', {}).get('in_progress', False):
        printer_logger.warning("Se intentó iniciar una nueva impresión mientras otra está en progreso.")
        return
    
    # Verificar carpeta de destino PDF
    if not os.path.exists('pdfs'):
        os.makedirs('pdfs')
    
    # Verificar permisos de escritura
    if not os.access('pdfs', os.W_OK):
        printer_logger.error("No hay permisos de escritura en la carpeta pdfs")
        st.session_state['print_job']['print_status'] = "❌ No hay permisos de escritura en la carpeta de PDFs"
        return
    
    # Actualizar el estado e iniciar el hilo de impresión
    st.session_state['print_job'].update({
        'html_content': html_content_orig,
        'cuf': cuf,
        'numero_factura': numero_factura,
        'in_progress': True,
        'finalizado': False,
        'print_status': "⏱️ Impresión en progreso..."
    })
    
    # Iniciar hilo de impresión
    thread = threading.Thread(target=imprimir)
    thread.daemon = True
    thread.start()

    printer_logger.info(f"Hilo de impresión iniciado para la factura {numero_factura}")
    return True

def mostrar_mensaje_impresion_en_curso():
    """
    Muestra un mensaje de advertencia en la UI si la impresión está en curso.
    """
    if st.session_state.get('print_job', {}).get('in_progress', False):
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
