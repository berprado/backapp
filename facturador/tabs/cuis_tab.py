"""
Módulo para la pestaña de gestión de CUIS.
"""
import streamlit as st
import cuis
from logger_config import get_logger
from api_clients import is_soap_client_available

logger = get_logger()

def render():
    """Renderiza la pestaña de gestión de CUIS."""
    st.header("🔑 Gestionar CUIS")
    logger.info("Usuario accedió a la pestaña 'Gestionar CUIS'")
    
    st.markdown("""
    **CUIS (Código Único de Inicio de Sistemas)** es un código único que autoriza al sistema 
    de facturación para operar con el SIN. Es necesario tenerlo vigente para emitir facturas.
    """)
    
    # Verificar conectividad para operaciones con CUIS
    if not is_soap_client_available():
        st.warning("⚠️ **Funciones limitadas en modo offline**")
        st.info("💡 Puedes consultar el CUIS actual, pero para solicitar uno nuevo necesitas conexión con el SIN.")
        st.divider()
    
    # Información sobre el CUIS actual
    st.subheader("📊 Estado actual del CUIS")
    
    # Llamar a la funcionalidad principal de CUIS
    cuis.main()
