"""
Módulo para la pestaña de validación de NIT.
"""
import streamlit as st
import verifica_stream
from logger_config import get_logger
from api_clients import is_soap_client_available

logger = get_logger()

def render():
    """Renderiza la pestaña de validación de NIT."""
    st.header("✅ Validar NIT")
    logger.info("Usuario accedió a la pestaña 'Validar NIT'")
    
    # Verificar si hay conectividad para la validación de NIT
    if not is_soap_client_available():
        st.warning("⚠️ **Función no disponible en modo offline**")
        st.info("La validación de NIT requiere conexión con los servicios del SIN. "
                "Por favor, verifica tu conexión a internet e intenta reconectar desde la barra superior.")
        return
    
    # Llamar a la funcionalidad principal de verificación de NIT
    verifica_stream.main()
