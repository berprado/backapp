"""
Módulo para la pestaña de visualización de facturas.
"""
import streamlit as st
from invoice_manager import mostrar_lista_facturas
from logger_config import get_logger

logger = get_logger()

def render():
    """Renderiza la pestaña de facturas generadas."""
    st.header("Facturas Generadas")
    logger.info("Usuario accedió a la pestaña 'Ver Facturas'")
    
    facturas_tabs = st.tabs(["Todas", "Pendientes", "Validadas", "Anuladas"])
    
    with facturas_tabs[0]:
        logger.info("Mostrando todas las facturas")
        mostrar_lista_facturas("TODAS")
    
    with facturas_tabs[1]:
        logger.info("Mostrando facturas pendientes")
        mostrar_lista_facturas("PENDIENTE")
        
    with facturas_tabs[2]:
        logger.info("Mostrando facturas validadas")
        mostrar_lista_facturas("VALIDADA")
        
    with facturas_tabs[3]:
        logger.info("Mostrando facturas anuladas")
        mostrar_lista_facturas("ANULADA")
