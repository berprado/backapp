"""
Módulo para la pestaña de validación de NIT.
"""
import streamlit as st
import verifica_stream
from logger_config import get_logger
from api_clients import is_soap_client_available

logger = get_logger()

def render(is_online: bool, connectivity_info: dict = None):
    """Renderiza la pestaña de validación de NIT con diagnóstico centralizado."""
    st.header("✅ Validar NIT")

    log_enabled = st.session_state.get("main_active_tab_name") == "Validar NIT"

    if log_enabled:
        logger.info("Usuario accedió a la pestaña 'Validar NIT'")

    if not is_online:
        logger.warning("Función de validación de NIT no disponible: el sistema asume modo offline.")
        st.warning("⚠️ **Función no disponible en modo offline**")
        st.info("La validación de NIT requiere conexión con los servicios del SIN. "
                "Por favor, verifica tu conexión a internet e intenta reconectar desde la barra superior.")
        return

    if log_enabled:
        logger.info("Conectividad con el SIN verificada correctamente. Mostrando interfaz de validación de NIT.")
    # Llamar a la funcionalidad principal de verificación de NIT
    verifica_stream.main()
