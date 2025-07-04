# printer_utils.py
from escpos.printer import Usb
import streamlit as st
import logging


# Configuración del logger
printer_logger = logging.getLogger('printer_utils')
printer_logger.setLevel(logging.DEBUG)

if not printer_logger.handlers:
    # Crear manejadores
    file_handler = logging.FileHandler('printer_debug.log')
    console_handler = logging.StreamHandler()

    # Crear formato
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Agregar manejadores al logger
    printer_logger.addHandler(file_handler)
    printer_logger.addHandler(console_handler)

def verificar_impresora():
    """
    Verifica la conexión con la impresora térmica
    Returns:
        bool: True si la impresora está conectada y lista
    """
    try:
        printer = Usb(0x04B8, 0x0E15, 0, out_ep=0x01)
        printer_logger.info("Impresora verificada y conectada correctamente")
        return True
    except Exception as e:
        error_msg = f"Error al conectar con la impresora: {str(e)}"
        printer_logger.error(error_msg)
        st.error(error_msg)
        return False

def guardar_factura_actual(html_content, cuf, nit, numero_factura):
    """
    Guarda los datos de la factura actual en el session_state
    """
    st.session_state['factura_actual'] = {
        'html_content': html_content,
        'cuf': cuf,
        'nit': nit,
        'numero_factura': numero_factura,
        'impresa': False
    }
    printer_logger.info(f"Factura {numero_factura} guardada en session_state")

def obtener_factura_actual():
    """
    Obtiene los datos de la factura actual del session_state
    Returns:
        dict: Datos de la factura o None si no hay factura
    """
    return st.session_state.get('factura_actual')

def marcar_factura_impresa():
    """
    Marca la factura actual como impresa en el session_state
    """
    if 'factura_actual' in st.session_state:
        st.session_state['factura_actual']['impresa'] = True
        printer_logger.info(f"Factura {st.session_state['factura_actual']['numero_factura']} marcada como impresa")
