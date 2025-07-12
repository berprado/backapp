"""
Módulo para la pestaña de verificación de facturas.
"""
import streamlit as st
from estado_factura import verificar_estado_factura
from ui_utils import show_message
from logger_config import get_logger

logger = get_logger()

def render():
    """Renderiza la pestaña de verificación de facturas."""
    st.header("Verificar Factura")
    logger.info("Usuario accedió a la pestaña 'Verificar Factura'")
    
    numero_factura = st.text_input("Ingrese el número de la factura:")
    
    # Placeholder para mensajes
    message_placeholder = st.empty()

    if st.button("Verificar Factura"):
        # Limpiar cualquier mensaje previo
        message_placeholder.empty()

        if not numero_factura:
            show_message('warning', "Por favor, ingrese un número de factura.", message_placeholder)
            logger.warning("Intento de verificación sin número de factura")
        else:
            logger.info(f"Verificando estado de la factura: {numero_factura}")
            exito, mensaje = verificar_estado_factura(numero_factura)
            if exito:
                show_message('success', mensaje, message_placeholder)
                logger.info(f"Verificación exitosa para factura {numero_factura}: {mensaje}")
            else:
                show_message('error', mensaje, message_placeholder)
                logger.error(f"Error en verificación de factura {numero_factura}: {mensaje}")
