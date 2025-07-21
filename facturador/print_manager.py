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
from invoice_templates import generate_html_invoice as generate_html_for_pdf
from siat_pdf import html_to_pdf
from thermal_printer import ThermalPrinter
from logger_config import get_printer_logger
from facturador.data_models import FacturaProcesada

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

def imprimir_en_hilo(factura_obj: FacturaProcesada):
    """
    Crea un hilo para manejar la impresión de la factura y la generación del PDF.
    Esta función ahora acepta un objeto FacturaProcesada como única fuente de verdad.

    Args:
        factura_obj (FacturaProcesada): El objeto que contiene todos los datos de la factura.
    """
    def imprimir():
        """Función que se ejecuta en un hilo separado."""
        try:
            printer_logger.info(f"INICIO HILO: Procesando factura N° {factura_obj.numero_factura}")

            # directorios de salida
            base_dir = os.path.dirname(os.path.abspath(__file__))
            pdfs_dir = os.path.join(base_dir, "pdfs")
            os.makedirs(pdfs_dir, exist_ok=True)
            
            # --- 1. Generación de PDF ---
            try:
                printer_logger.info("Paso 1: Generando HTML para el PDF.")
                # Usamos los datos del objeto para generar un HTML específico para el PDF
                html_content_pdf = generate_html_for_pdf(factura_obj)
                
                output_pdf_path = os.path.join(pdfs_dir, f"factura_{factura_obj.numero_factura}.pdf")
                printer_logger.info(f"Generando PDF en: {output_pdf_path}")
                
                pdf_result = html_to_pdf(html_content_pdf, output_pdf_path)
                if not pdf_result:
                    raise Exception("La función html_to_pdf() retornó False.")
                
                printer_logger.info(f"PDF generado exitosamente: {output_pdf_path}")
                
            except Exception as e:
                printer_logger.error(f"Error crítico durante la generación del PDF: {str(e)}", exc_info=True)
                # Decidimos si el error de PDF debe detener la impresión térmica. 
                # Por ahora, lo registramos pero continuamos.
                st.session_state['print_status'] = f"⚠️ Error en PDF, intentando impresión térmica..."
            
            # --- 2. Impresión Térmica (REACTIVADA) ---
            try:
                printer_logger.info("Paso 2: Iniciando impresión térmica.")
                printer = ThermalPrinter()
                
                success = printer.print_invoice(factura_obj)

                if success:
                    printer_logger.info("Impresión térmica completada exitosamente.")
                    st.session_state['print_status'] = "✅ PDF generado e Impresión completada."
                else:
                    printer_logger.warning("Impresión térmica falló, pero el PDF podría haberse generado.")
                    st.session_state['print_status'] = "⚠️ PDF generado, pero la impresión térmica falló."

            except Exception as e:
                error_msg = f"Error en impresión térmica: {str(e)}"
                printer_logger.error(f"Error crítico durante la impresión térmica: {error_msg}", exc_info=True)
                st.session_state['print_status'] = f"⚠️ PDF generado, pero error en impresión: {error_msg}"

        except Exception as e:
            # Captura errores generales del proceso
            error_msg = f"❌ Error general en el hilo de impresión: {str(e)}"
            printer_logger.error(error_msg, exc_info=True)
            st.session_state['print_status'] = error_msg
        finally:
            printer_logger.info(f"FIN HILO: Limpiando estado para factura N° {factura_obj.numero_factura}")
            st.session_state['impresion_en_progreso'] = False
            st.session_state['impresion_finalizada'] = True
    
    # --- Lógica de control del hilo (se mantiene mayormente igual) ---
    if st.session_state.get('impresion_en_progreso', False):
        printer_logger.warning("Se intentó iniciar una nueva impresión mientras otra está en progreso.")
        return

    if not os.access('pdfs', os.W_OK):
        printer_logger.error("No hay permisos de escritura en la carpeta pdfs")
        st.session_state['print_status'] = "❌ No hay permisos de escritura en la carpeta de PDFs"
        return
    
    # Actualizar el estado e iniciar el hilo
    st.session_state['impresion_en_progreso'] = True
    st.session_state['impresion_finalizada'] = False
    st.session_state['print_status'] = "⏱️ Impresión en progreso..."
    
    thread = threading.Thread(target=imprimir, name=f"PrintThread_Factura_{factura_obj.numero_factura}")
    thread.daemon = True
    thread.start()

    printer_logger.info(f"Hilo de impresión iniciado para la factura {factura_obj.numero_factura}")
    return True

def mostrar_mensaje_impresion_en_curso():
    """
    Muestra un mensaje de advertencia en la UI si la impresión está en curso.
    """
    if st.session_state.get('impresion_en_progreso', False):
        st.warning("⚠️ La impresión está en curso. Por favor, espera a que finalice antes de iniciar una nueva impresión.")
