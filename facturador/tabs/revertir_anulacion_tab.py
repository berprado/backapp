"""
Módulo para la pestaña de reversión de anulación de facturas.
"""
import streamlit as st
from reversion import enviar_solicitud_reversion, procesar_respuesta_reversion
from data_access import obtener_cuf_por_numero_factura
from ui_utils import show_message
from logger_config import get_logger

logger = get_logger()

def render():
    """Renderiza la pestaña de reversión de anulación de facturas."""
    st.header("Revertir Anulación de Factura")

    log_enabled = st.session_state.get("main_active_tab_name") == "Revertir Anulacion"
    if log_enabled:
        logger.info("Usuario accedió a la pestaña 'Revertir Anulación'")
    
    # Placeholder para mensajes
    message_placeholder = st.empty()
    
    # Entrada para el número de factura
    numero_factura_revertir = st.text_input("Ingrese el número de la factura a revertir la anulación:")

    # Botón para iniciar la reversión de la anulación
    if st.button("Revertir Anulación"):
        # Limpiar cualquier mensaje previo
        message_placeholder.empty()

        if not numero_factura_revertir:
            show_message('warning', "Por favor, ingrese el número de la factura.", message_placeholder)
            logger.warning("Intento de reversión sin número de factura")
        else:
            logger.info(f"Iniciando reversión de anulación para factura {numero_factura_revertir}")
            
            cuf, factura = obtener_cuf_por_numero_factura(numero_factura_revertir)
            if not cuf:
                show_message('error', "No se encontró la factura especificada.", message_placeholder)
                logger.error(f"No se encontró CUF para la factura {numero_factura_revertir}")
            else:
                logger.info(f"CUF encontrado para factura {numero_factura_revertir}: {cuf}")
                exito, respuesta_siat = enviar_solicitud_reversion(cuf)
                logger.info(f"[SIAT] Respuesta recibida: {respuesta_siat}")
                if exito:
                    exito_reversion, mensaje_reversion = procesar_respuesta_reversion(respuesta_siat, factura)
                    if exito_reversion:
                        show_message('success', mensaje_reversion, message_placeholder)
                        logger.info(f"Reversión exitosa para factura {numero_factura_revertir}: {mensaje_reversion}")
                    else:
                        show_message('error', mensaje_reversion, message_placeholder)
                        logger.error(f"Error al procesar reversión de factura {numero_factura_revertir}: {mensaje_reversion}")
                else:
                    show_message('error', respuesta_siat, message_placeholder)
                    logger.error(f"Error en solicitud de reversión para factura {numero_factura_revertir}: {respuesta_siat}")
