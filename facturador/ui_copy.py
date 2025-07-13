import os
import sys
import logging
from datetime import datetime

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
def main(is_online=None, connectivity_info=None):
    """
    Renderiza la interfaz principal de la aplicación.
    
    Args:
        is_online: Booleano que indica si el sistema está online. Si es None, se verifica internamente.
        connectivity_info: Diccionario con información detallada de conectividad. Si es None, se obtiene internamente.
    """
    ui_logger.info("Renderizando la interfaz principal en modo online")
    
    # Si no se proporciona información de conectividad, obtenerla
    if connectivity_info is None:
        connectivity_info = get_connectivity_info()
        is_online = connectivity_info["client_available"]
        status = connectivity_info.get('status', 'Estado')
        status_message = connectivity_info.get('status_message', 'Estado desconocido')
    else:
        # Si usamos connectivity_info de communication_manager
        principal = connectivity_info.get("verificacion_principal", {})
        estado_general = connectivity_info.get("estado_general", "DESCONOCIDO")
        recomendacion = connectivity_info.get("recomendacion", "")
        status = estado_general
        status_message = recomendacion
    
    # Mostrar estado de conectividad en la parte superior
    col1, col2 = st.columns([4, 1])
    
    with col1:
        if is_online:
            st.success(f"{status} - {status_message}", icon="✅")
            ui_logger.info("Sistema conectado a servicios del SIN")
        else:
            st.error(f"{status} - {status_message}", icon="⚠️")
            ui_logger.warning("Sistema funcionando en modo offline")
    
    with col2:
        # Botón para intentar reconectar
        if not is_online:
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
    # Determinar la hora del último chequeo según la fuente de datos disponible
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # Usar el método get con valor por defecto para evitar KeyError
    if 'timestamp' in connectivity_info:
        # Formato de communication_manager (ISO)
        try:
            last_check = datetime.fromisoformat(connectivity_info.get('timestamp')).strftime("%H:%M:%S")
        except (ValueError, TypeError):
            last_check = current_time
    else:
        # Formato de get_connectivity_info
        last_check = connectivity_info.get('last_check', current_time)
    
    with st.expander(f"ℹ️ Detalles de conectividad (último chequeo: {last_check})", expanded=False):
        st.json(connectivity_info)
    
    # Separador visual
    st.divider()
    
    # Definir la configuración de pestañas - qué pestañas están disponibles en qué modo
    tabs_config = {
        "🧾Facturar": facturacion_tab.render,
        "🔍Ver Facturas": facturas_tab.render,
        "😏Clientes": clientes_tab.render,
        "✅Validar NIT": validar_nit_tab.render,
        "🔍Verificar Factura": verificar_factura_tab.render,
        "🔍Gestionar CUIS": cuis_tab.render,
        "❌Anular/Revertir": anular_factura_tab.render,
        "❌Revertir Anulacion": revertir_anulacion_tab.render,
        "🔧Diagnóstico": diagnostico_tab.render
    }

    online_only_tabs = [
        "✅Validar NIT", 
        "🔍Verificar Factura", 
        "🔍Gestionar CUIS", 
        "❌Anular/Revertir", 
        "❌Revertir Anulacion"
    ]
    
    # Construir dinámicamente la lista de pestañas a mostrar
    tabs_to_render = ["🧾Facturar", "🔍Ver Facturas", "😏Clientes"]
    
    if is_online:
        # Si estamos online, añadimos las pestañas que dependen de la conexión
        tabs_to_render.extend(online_only_tabs)
    
    # Siempre añadimos la pestaña de diagnóstico al final
    tabs_to_render.append("🔧Diagnóstico")

    # Renderizar las pestañas
    rendered_tabs = st.tabs(tabs_to_render)

    # Mapear cada pestaña creada a su contenido
    for tab, tab_name in zip(rendered_tabs, tabs_to_render):
        with tab:
            ui_logger.debug(f"Renderizando pestaña: {tab_name}")
            try:
                # Obtener la función de renderizado del diccionario y llamarla
                render_function = tabs_config[tab_name]
                render_function()
            except Exception as e:
                ui_logger.error(f"Error al renderizar pestaña {tab_name}: {str(e)}", exc_info=True)
                st.error(f"Error al cargar esta pestaña: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    try:
        initialize_print_state()
        main()
    except Exception as e:
        ui_logger.error(f"Error en la ejecución principal: {str(e)}", exc_info=True)
        st.error(f"Ha ocurrido un error: {str(e)}")