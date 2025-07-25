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

# Importar verificador de session_state para diagnóstico de impresión
from verificador_session_state import ejecutar_diagnostico_completo

def mostrar_boton_diagnostico_rapido():
    """
    Muestra un botón de acceso rápido al diagnóstico de impresión.
    Esta función puede ser llamada desde cualquier pestaña cuando hay problemas de impresión.
    """
    impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)
    print_status = st.session_state.get('print_status', '')
    
    # Solo mostrar si hay indicios de problemas
    if impresion_en_progreso or (print_status and 'error' in print_status.lower()):
        st.warning("⚠️ Se detectaron posibles problemas de impresión")
        if st.button("🔧 Diagnóstico Rápido de Impresión", help="Abre el panel de diagnóstico completo", key="diagnostico_rapido_impresion"):
            # Abrir en un expander
            with st.expander("🔍 Diagnóstico de Sistema de Impresión", expanded=True):
                ejecutar_diagnostico_completo("automatico")

def verificar_estado_sistema():
    """
    Verifica el estado general del sistema y devuelve un resumen.
    
    Returns:
        dict: Estado del sistema con indicadores de problemas
    """
    estado = {
        'problemas_detectados': [],
        'nivel_alerta': 'normal',  # normal, warning, error
        'mensaje_estado': 'Sistema funcionando correctamente'
    }
    
    # Verificar estados de impresión
    impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)
    impresion_finalizada = st.session_state.get('impresion_finalizada', False)
    
    if impresion_en_progreso and not impresion_finalizada:
        estado['problemas_detectados'].append('Proceso de impresión fantasma')
        estado['nivel_alerta'] = 'error'
        estado['mensaje_estado'] = 'Proceso de impresión bloqueado'
    
    # Verificar archivos de señal acumulados
    try:
        import glob
        signal_files = glob.glob("debug/*.signal")
        if len(signal_files) > 5:
            estado['problemas_detectados'].append(f'{len(signal_files)} archivos de señal acumulados')
            if estado['nivel_alerta'] == 'normal':
                estado['nivel_alerta'] = 'warning'
                estado['mensaje_estado'] = 'Mantenimiento recomendado'
    except:
        pass  # Ignorar errores de acceso a archivos
    
    # Verificar hilos de impresión activos
    try:
        import threading
        hilos_impresion = [h for h in threading.enumerate() if 'print' in h.name.lower()]
        if len(hilos_impresion) > 0:
            estado['problemas_detectados'].append(f'{len(hilos_impresion)} hilo(s) de impresión activo(s)')
            if estado['nivel_alerta'] == 'normal':
                estado['nivel_alerta'] = 'warning'
                estado['mensaje_estado'] = 'Hilos de impresión activos detectados'
    except:
        pass  # Ignorar errores de threading
    
    return estado

# Importar cliente para verificar conectividad (solo para el botón de reconexión)
from api_clients import reset_soap_client

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
def render_full_ui(is_online: bool, connectivity_info: dict, evento_activo: dict = None, reconectar_callback=None):
    """
    Renderiza la interfaz principal. Ahora es una vista "pura" que no realiza verificaciones.
    
    Args:
        is_online: Booleano que indica si el sistema está online.
        connectivity_info: Diccionario con información detallada de conectividad.
        evento_activo: Diccionario con la información del evento de contingencia activo, si existe.
        reconectar_callback: Función de callback para el botón de reconexión.
    """
    ui_logger.info("Renderizando la interfaz principal...")

    # Usar la información de conectividad ya proporcionada (no verificar de nuevo)
    principal = connectivity_info.get("verificacion_principal", {})
    estado_general = connectivity_info.get("estado_general", "DESCONOCIDO")
    recomendacion = connectivity_info.get("recomendacion", "")
    status = estado_general
    status_message = recomendacion
    
    # Mostrar estado de conectividad en la parte superior
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        if is_online:
            st.success(f"{status} - {status_message}", icon="✅")
            ui_logger.info("Sistema conectado a servicios del SIN")
        else:
            st.error(f"{status} - {status_message}", icon="⚠️")
            ui_logger.warning("Sistema funcionando en modo offline")
    
    with col2:
        # Indicador de estado del sistema de impresión
        estado_sistema = verificar_estado_sistema()
        if estado_sistema['nivel_alerta'] == 'error':
            st.error(f"🖨️ {estado_sistema['mensaje_estado']}", icon="🚨")
        elif estado_sistema['nivel_alerta'] == 'warning':
            st.warning(f"🖨️ {estado_sistema['mensaje_estado']}", icon="⚠️")
        else:
            st.success("🖨️ Sistema OK", icon="✅")
    
    with col3:
        # El botón de reconexión ahora usa una función "callback" pasada desde main.py
        if not is_online and reconectar_callback:
            if st.button("🔄 Reconectar", help="Intentar reconectarse a los servicios del SIN"):
                reconectar_callback()
    
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
    
    # Mostrar diagnóstico rápido si hay problemas de impresión
    mostrar_boton_diagnostico_rapido()
    
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
        "🔧Diagnóstico": diagnostico_tab.render,
        "🔧Pruebas": lambda: ejecutar_diagnostico_completo("tab_pruebas")  # Herramienta de diagnóstico de impresión
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
    
    # Siempre añadimos las pestañas de diagnóstico al final
    tabs_to_render.extend(["🔧Diagnóstico", "🔧Pruebas"])

    # Diccionario que mapea pestañas a los argumentos que requieren
    tab_args = {
        "🧾Facturar": {"is_online": is_online, "evento_activo": evento_activo},
        "✅Validar NIT": {"is_online": is_online, "connectivity_info": connectivity_info},
        "🔍Gestionar CUIS": {"is_online": is_online, "connectivity_info": connectivity_info},
        # Agrega aquí otras pestañas si requieren argumentos especiales
    }

    rendered_tabs = st.tabs(tabs_to_render)

    for tab, tab_name in zip(rendered_tabs, tabs_to_render):
        with tab:
            ui_logger.debug(f"Renderizando pestaña: {tab_name}")
            try:
                render_function = tabs_config[tab_name]
                args = tab_args.get(tab_name, {})
                render_function(**args)
            except Exception as e:
                ui_logger.error(f"Error al renderizar pestaña {tab_name}: {str(e)}", exc_info=True)
                st.error(f"Error al cargar esta pestaña: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    """
    Ejecutor de respaldo. En el flujo normal, main.py es quien llama a render_full_ui.
    """
    try:
        initialize_print_state()
        # Modo de respaldo - funcionalidad básica sin verificación completa
        dummy_connectivity = {
            "estado_general": "RESPALDO",
            "recomendacion": "Ejecutando en modo de respaldo. Use main.py para funcionalidad completa.",
            "verificacion_principal": {"conectado": False}
        }
        render_full_ui(is_online=False, connectivity_info=dummy_connectivity)
    except Exception as e:
        ui_logger.error(f"Error en la ejecución principal: {str(e)}", exc_info=True)
        st.error(f"Ha ocurrido un error: {str(e)}")