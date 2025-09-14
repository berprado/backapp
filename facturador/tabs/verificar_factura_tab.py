"""
Módulo para la pestaña de verificación de facturas.
"""
import streamlit as st
import logging
import os
from estado_factura import verificar_estado_factura
from ui_utils import show_message
from logger_config import get_logger
def get_verificacion_logger():
    log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'verificacion.log')
    logger = logging.getLogger('verificacion')
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    console_handler = logging.StreamHandler()
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger

logger = get_logger()
verificacion_logger = get_verificacion_logger()

def render():
    """Renderiza la pestaña de verificación de facturas."""
    st.header("Verificar Factura")
    verificacion_logger.info("Usuario accedió a la pestaña 'Verificar Factura'")
    
    numero_factura = st.text_input("Ingrese el número de la factura:")
    
    # Placeholder para mensajes
    message_placeholder = st.empty()

    if st.button("Verificar Factura"):
        # Limpiar cualquier mensaje previo
        message_placeholder.empty()

        if not numero_factura:
            show_message('warning', "Por favor, ingrese un número de factura.", message_placeholder)
            verificacion_logger.warning("Intento de verificación sin número de factura")
        else:
            verificacion_logger.info(f"Verificando estado de la factura: {numero_factura}")
            exito, mensaje = verificar_estado_factura(numero_factura)
            verificacion_logger.info(f"[SIAT] Respuesta recibida: {mensaje}")
            if exito:
                show_message('success', mensaje, message_placeholder)
                verificacion_logger.info(f"Verificación exitosa para factura {numero_factura}: {mensaje}")
            else:
                show_message('error', mensaje, message_placeholder)
                verificacion_logger.error(f"Error en verificación de factura {numero_factura}: {mensaje}")
