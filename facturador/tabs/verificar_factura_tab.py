"""
Módulo para la pestaña de verificación de facturas.
"""
import streamlit as st
from estado_factura import verificar_estado_factura
from ui_utils import show_message
from logger_config import get_logger

logger = get_logger()

def render():
    """
    Renderiza la pestaña de verificación de facturas.
    
    Esta pestaña permite consultas informativas del estado de facturas.
    Usa caché inteligente (30s) para mejorar performance en consultas repetidas.
    Incluye opción de "Refrescar" para forzar consulta en tiempo real al SIAT.
    
    Versión: 2.1.0 (Compatible con sistema de caché híbrido)
    """
    st.header("🔍 Verificar Factura")

    log_enabled = st.session_state.get("main_active_tab_name") == "Verificar Factura"

    if log_enabled:
        logger.info("Usuario accedió a la pestaña 'Verificar Factura'")
    
    # Información sobre el caché
    with st.expander("ℹ️ Acerca del caché de verificación"):
        st.markdown("""
        **Sistema de caché inteligente:**
        - Las consultas se cachean por 30 segundos para mejorar la velocidad
        - Si consultas la misma factura en < 30s, la respuesta será instantánea
        - Usa el botón "🔄 Refrescar" para forzar una consulta nueva al SIAT
        - El caché se renueva automáticamente después de 30 segundos
        """)
    
    numero_factura = st.text_input("Ingrese el número de la factura:")
    
    # Placeholder para mensajes
    message_placeholder = st.empty()

    # Botones en columnas para mejor UX
    col1, col2 = st.columns([3, 1])
    
    with col1:
        verificar_button = st.button("✅ Verificar Factura", use_container_width=True)
    
    with col2:
        refrescar_button = st.button("🔄 Refrescar", use_container_width=True, 
                                     help="Ignora el caché y consulta el SIAT en tiempo real")

    # Procesar la verificación
    if verificar_button or refrescar_button:
        # Limpiar cualquier mensaje previo
        message_placeholder.empty()

        if not numero_factura:
            show_message('warning', "Por favor, ingrese un número de factura.", message_placeholder)
            logger.warning("Intento de verificación sin número de factura")
        else:
            # Determinar si es una consulta forzada
            force_check = refrescar_button
            
            if force_check:
                logger.info(f"Verificación FORZADA de factura {numero_factura} (usuario presionó Refrescar)")
            else:
                logger.info(f"Verificando estado de factura {numero_factura} (caché permitido)")
            
            # Mostrar spinner durante la verificación
            with st.spinner("🔍 Consultando estado en SIAT..." if force_check else "Verificando..."):
                exito, mensaje = verificar_estado_factura(numero_factura, force_check=force_check)
            
            logger.info(f"[SIAT] Respuesta recibida: {mensaje}")
            
            if exito:
                show_message('success', mensaje, message_placeholder)
                logger.info(f"Verificación exitosa para factura {numero_factura}: {mensaje}")
            else:
                show_message('error', mensaje, message_placeholder)
                logger.error(f"Error en verificación de factura {numero_factura}: {mensaje}")
