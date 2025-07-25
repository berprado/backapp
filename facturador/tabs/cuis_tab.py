"""
Módulo para la pestaña de gestión de CUIS.
"""
import streamlit as st
import cuis
from logger_config import get_logger
from api_clients import is_soap_client_available

logger = get_logger()

def render(is_online: bool, connectivity_info: dict = None):
    """Renderiza la pestaña de gestión de CUIS con diagnóstico centralizado."""
    st.header("🔑 Gestionar CUIS")
    logger.info("Usuario accedió a la pestaña 'Gestionar CUIS'")

    st.markdown("""
    **CUIS (Código Único de Inicio de Sistemas)** es un código único que autoriza al sistema 
    de facturación para operar con el SIN. Es necesario tenerlo vigente para emitir facturas.
    """)


    if not is_online:
        st.warning("⚠️ **Funciones limitadas en modo offline**")
        st.info("💡 Puedes consultar el CUIS actual, pero para solicitar uno nuevo necesitas conexión con el SIN.")
        st.divider()
        return

    # Información sobre el CUIS actual
    st.subheader("📊 Estado actual del CUIS")

    # Llamar a la funcionalidad principal de CUIS
    cuis.main()
