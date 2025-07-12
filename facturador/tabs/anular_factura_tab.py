"""
Módulo para la pestaña de anulación de facturas.
"""
import streamlit as st
from anulacion import anular_factura
from data_access import obtener_motivos_anulacion
from ui_utils import show_message
from logger_config import get_logger

logger = get_logger()

def render():
    """Renderiza la pestaña de anulación de facturas."""
    st.header("Anular Factura")
    logger.info("Usuario accedió a la pestaña 'Anular Factura'")
    
    # Placeholder para mensajes
    message_placeholder = st.empty()
    
    # Entrada para el número de factura
    numero_factura_anular = st.text_input("Ingrese el número de la factura a anular:")
    
    # Obtener las opciones de motivos desde la base de datos
    opciones_motivos = obtener_motivos_anulacion()
    
    # Verificar si hay motivos de anulación disponibles
    if opciones_motivos:
        descripcion_motivo = st.selectbox("Seleccione el motivo de la anulación", opciones_motivos)
    else:
        st.error("No se encontraron motivos de anulación disponibles.")
        logger.error("No se encontraron motivos de anulación en la base de datos")
        descripcion_motivo = None

    # Botón para iniciar la anulación de la factura
    if st.button("Anular Factura"):
        # Limpiar cualquier mensaje previo
        message_placeholder.empty()

        if not numero_factura_anular or not descripcion_motivo:
            show_message('warning', "Por favor, ingrese todos los datos requeridos.", message_placeholder)
            logger.warning(f"Intento de anulación incompleto - Factura: {numero_factura_anular}, Motivo: {descripcion_motivo}")
        else:
            logger.info(f"Iniciando anulación de factura {numero_factura_anular} con motivo: {descripcion_motivo}")
            # Llamar a la función anular_factura
            exito, mensaje = anular_factura(numero_factura_anular, descripcion_motivo)
            
            if exito:
                show_message('success', mensaje, message_placeholder)
                logger.info(f"Anulación exitosa para factura {numero_factura_anular}: {mensaje}")
            else:
                show_message('error', mensaje, message_placeholder)
                logger.error(f"Error en anulación de factura {numero_factura_anular}: {mensaje}")
