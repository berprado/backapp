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
from invoice_templates import generate_html_invoice, generate_html_invoice_legacy
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

def imprimir_en_hilo(factura_obj):
    """
    Crea un hilo para manejar la impresión de la factura y generación del PDF.
    Esta función incorpora toda la lógica de monitoreo del hilo.

    Args:
        factura_obj (FacturaProcesada): Objeto con todos los datos de la factura.
    """
    def imprimir():
        try:
            printer_logger.info(f"Iniciando proceso de impresión para factura {factura_obj.numero_factura}")

            # Generar HTML a partir del objeto factura_obj
            html_content = generate_html_invoice(factura_obj)
            
            # Extraer datos del objeto factura para consistencia con el resto del código
            numero_factura = factura_obj.numero_factura
            cuf = factura_obj.cuf
            nit = factura_obj.nit_emisor

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
                printer_logger.info(f"Iniciando generación de PDF en: {output_pdf_path}")
                
                pdf_result = html_to_pdf(html_content, output_pdf_path)
                if pdf_result:
                    printer_logger.info(f"PDF generado exitosamente: {output_pdf_path}")
                    
                    # Verificar que el archivo realmente existe
                    if os.path.exists(output_pdf_path):
                        file_size = os.path.getsize(output_pdf_path)
                        printer_logger.info(f"PDF verificado: {file_size} bytes")
                    else:
                        raise Exception("PDF reportado como exitoso pero archivo no existe")
                else:
                    raise Exception("html_to_pdf retornó False")
                    
            except Exception as e:
                printer_logger.error(f"Error detallado en generación PDF: {str(e)}")
                raise Exception(f"Error al generar PDF: {str(e)}")

            # Proceder con la impresión térmica
            try:
                printer_logger.info("Iniciando impresión térmica...")
                printer = ThermalPrinter()
                success = printer.print_invoice(html_content, nit, cuf, numero_factura)
                if success:
                    printer_logger.info("Impresión térmica completada exitosamente")
                    st.session_state['print_status'] = "✅ Impresión completada exitosamente"
                else:
                    printer_logger.warning("Impresión térmica falló, pero PDF fue generado")
                    st.session_state['print_status'] = "⚠️ PDF generado, pero impresión térmica falló"
            except Exception as e:
                printer_logger.error(f"Error en impresión térmica: {str(e)}")
                # No lanzar excepción aquí para que se complete el proceso
                st.session_state['print_status'] = f"⚠️ PDF generado, error en impresión térmica: {str(e)}"

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
            st.session_state['print_status'] = error_msg
        finally:
            st.session_state['impresion_en_progreso'] = False
            st.session_state['impresion_finalizada'] = True
    
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
    thread = threading.Thread(target=imprimir)
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

def process_invoice(factura_obj=None, subtotal=None, descuento_adicional=None, monto_giftcard=None, lineas_productos=None, nombre_cliente=None, fecha_emision=None, numero_factura=None, nit=None, cuf=None):
    """
    Centraliza la generación de HTML, PDF e impresión de la factura.
    
    Se puede llamar de dos formas:
    1. Con un objeto FacturaProcesada (método preferido)
    2. Con los parámetros individuales (método legacy)

    Args:
        factura_obj (FacturaProcesada, optional): Objeto con todos los datos de la factura.
        subtotal (float, optional): Subtotal de la factura (legacy).
        descuento_adicional (float, optional): Descuento adicional aplicado (legacy).
        monto_giftcard (float, optional): Monto de giftcard aplicado (legacy).
        lineas_productos (list, optional): Lista de productos en la factura (legacy).
        nombre_cliente (str, optional): Nombre del cliente (legacy).
        fecha_emision (str, optional): Fecha de emisión de la factura (legacy).
        numero_factura (str, optional): Número de la factura (legacy).
        nit (str, optional): NIT del emisor (legacy).
        cuf (str, optional): Código Único de Facturación (legacy).

    Returns:
        bool: True si el proceso fue exitoso, False en caso de error.
    """
    try:
        # Generar HTML según el tipo de entrada
        if factura_obj and isinstance(factura_obj, FacturaProcesada):
            html_content = generate_html_invoice(factura_obj)
            numero_factura = factura_obj.numero_factura
            nit = factura_obj.nit_emisor
            cuf = factura_obj.cuf
        else:
            # Para compatibilidad con código legacy
            html_content = generate_html_invoice_legacy(
                subtotal=subtotal,
                descuento_adicional=descuento_adicional,
                monto_giftcard=monto_giftcard,
                lineas_productos=lineas_productos,
                nombre_cliente=nombre_cliente,
                fecha_emision=fecha_emision,
                numero_factura=numero_factura,
                nit=nit,
                cuf=cuf
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
