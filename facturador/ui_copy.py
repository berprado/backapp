import os
import sys
import logging

# Agregar la ruta del directorio padre al path de Python
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Streamlit
import streamlit as st

# Librerías externas
from dotenv import load_dotenv

# Módulos de impresión
from print_manager import initialize_print_state

# Configuración de loggers
from logger_config import get_logger

# Importar módulos de pestañas
from tabs import (
    facturacion_tab, 
    facturas_tab, 
    validar_nit_tab, 
    clientes_tab,
    verificar_factura_tab,
    cuis_tab,
    anular_factura_tab,
    revertir_anulacion_tab,
    diagnostico_tab
)

# Importar cliente para verificar conectividad
from api_clients import is_soap_client_available, get_connectivity_info, reset_soap_client

# Configurar loggers
ui_logger = get_logger('ui')  # Logger específico para la interfaz de usuario

load_dotenv()

# Crear directorio de PDFs si no existe
if not os.path.exists('pdfs'):
    os.makedirs('pdfs')
    
# Verificar permisos de escritura
try:
    if not os.access('pdfs', os.W_OK):
        ui_logger.error("No hay permisos de escritura en la carpeta pdfs")
        raise PermissionError("No hay permisos de escritura en la carpeta pdfs")
except Exception as e:
    ui_logger.error(f"Error al verificar permisos: {str(e)}", exc_info=True)

# La inicialización del cliente SOAP se ha movido a api_clients.py
# para mantener la separación de responsabilidades

# Gestión de pestañas con logs
def main():
    ui_logger.info("Iniciando la interfaz principal")
    
    # Obtener información detallada de conectividad
    connectivity_info = get_connectivity_info()
    
    # Mostrar estado de conectividad en la parte superior
    col1, col2 = st.columns([4, 1])
    
    with col1:
        if connectivity_info["client_available"]:
            st.success(f"{connectivity_info['status']} - {connectivity_info['status_message']}", icon="✅")
            ui_logger.info("Sistema conectado a servicios del SIN")
        else:
            st.error(f"{connectivity_info['status']} - {connectivity_info['status_message']}", icon="⚠️")
            ui_logger.warning("Sistema funcionando en modo offline")
    
    with col2:
        # Botón para intentar reconectar
        if not connectivity_info["client_available"]:
            if st.button("🔄 Reconectar", help="Intentar reconectarse a los servicios del SIN"):
                with st.spinner("Intentando reconectar..."):
                    client = reset_soap_client()
                    if client is not None:
                        st.success("✅ Reconexión exitosa")
                        st.rerun()  # Refrescar la página para mostrar el nuevo estado
                    else:
                        st.error("❌ No se pudo reconectar")
                        st.rerun() # Actualizar la UI para mostrar el estado de error
    
    # Información adicional en un expander colapsable
    with st.expander(f"ℹ️ Detalles de conectividad (último chequeo: {connectivity_info['last_check']})", expanded=False):
        st.json(connectivity_info)
    
    # Separador visual
    st.divider()
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "🧾Facturar", "🔍Ver Facturas", "✅Validar NIT", "😏Clientes", 
        "🔍Verificar Factura", "🔍Gestionar CUIS", "❌Anular/Revertir", "❌Revertir Anulacion", "🔧Diagnóstico"
    ])

    # Pestaña 1: Facturación
    with tab1:
        facturacion_tab.render()

    # Pestaña 2: Ver Facturas Generadas
    with tab2:
        facturas_tab.render()
    
    # Pestaña 3: Validar NIT
    with tab3:
        validar_nit_tab.render()
        
    # Pestaña 4: Lista de Clientes
    with tab4:
        clientes_tab.render()

    # Pestaña 5: Verificar Factura
    with tab5:
        verificar_factura_tab.render()

    # Pestaña 6: Gestionar CUIS
    with tab6:
        cuis_tab.render()

    # Pestaña 7: Anular Factura
    with tab7:
        anular_factura_tab.render()

    # Pestaña 8: Revertir Anulación de Factura
    with tab8:
        revertir_anulacion_tab.render()
    # Pestaña 9: Diagnóstico Avanzado
    with tab9:
        diagnostico_tab.render()

if __name__ == "__main__":
    try:
        initialize_print_state()
        main()
    except Exception as e:
        ui_logger.error(f"Error en la ejecución principal: {str(e)}", exc_info=True)
        st.error(f"Ha ocurrido un error: {str(e)}")