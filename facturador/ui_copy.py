# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime
import time

# Streamlit
import streamlit as st

# Asegurar que la salida estándar use UTF-8 para mostrar correctamente acentos y emojis
try:
    # Disponible en Python 3.7+; puede fallar en entornos más antiguos
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
except Exception:
    # Ignorar cualquier error silenciosamente para no interrumpir la ejecución
    pass

# Librerías externas
from dotenv import load_dotenv

# Módulos de impresión
from print_manager import initialize_print_state, get_print_state_summary

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


def _schedule_auto_refresh():
    """Dispara rerun periodico mientras hay impresion pendiente."""
    if not st.session_state.get('impresion_en_progreso'):
        st.session_state.pop('_print_auto_refresh_active', None)
        return
    interval = st.session_state.get('_print_auto_refresh_interval', 1.5)
    st.session_state['_print_auto_refresh_active'] = True
    time.sleep(interval)
    st.rerun()


def _show_status_toast(summary):
    version = summary.get('version')
    if version is None:
        return
    last_version = st.session_state.get('_last_toast_version', -1)
    if version <= last_version:
        return
    st.session_state['_last_toast_version'] = version
    message = summary.get('message') or 'Estado de impresion actualizado.'
    severity = summary.get('severity', 'info')
    icon_map = {
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'info': 'ℹ️',
    }
    icon = icon_map.get(severity, 'ℹ️')
    try:
        st.toast(message, icon=icon)
    except Exception:
        pass


def mostrar_boton_diagnostico_rapido(summary=None):
    """Muestra un acceso directo al diagnostico tecnico cuando es necesario."""
    summary = summary or get_print_state_summary()
    if not (summary.get('show_diagnostic') or summary.get('impresion_en_progreso')):
        return
    if st.button('Ver diagnostico de impresion', help='Abrir diagnostico completo con informacion tecnica', key='diagnostico_rapido_impresion'):
        with st.expander('Diagnostico de sistema de impresion', expanded=True):
            ejecutar_diagnostico_completo('automatico')




def verificar_estado_sistema():
    """Obtiene un resumen simplificado del estado de impresion."""
    summary = get_print_state_summary()
    estado = {
        'problemas_detectados': [],
        'nivel_alerta': summary['severity'],
        'mensaje_estado': summary['message'],
        'show_diagnostic': summary['show_diagnostic'],
        'summary': summary,
    }
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
    """Renderiza la interfaz principal sin comprobaciones adicionales."""
    ui_logger.info("Renderizando la interfaz principal...")

    principal = connectivity_info.get("verificacion_principal", {})
    estado_general = connectivity_info.get("estado_general", "DESCONOCIDO")
    recomendacion = connectivity_info.get("recomendacion", "")
    status = estado_general
    status_message = recomendacion

    estado_sistema = verificar_estado_sistema()
    summary = estado_sistema['summary']

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        if is_online:
            st.success(f"{status} - {status_message}")
            ui_logger.info("Sistema conectado a servicios del SIN")
        else:
            st.error(f"{status} - {status_message}")
            ui_logger.warning("Sistema funcionando en modo offline")

    with col2:
        severity = summary['severity']
        message = summary['message']
        if severity == 'error':
            st.error(message)
        elif severity == 'warning':
            st.warning(message)
        elif severity == 'success':
            st.success(message)
        else:
            st.info(message)

    with col3:
        if not is_online and reconectar_callback:
            if st.button('Reconectar', help='Intentar reconectarse a los servicios del SIN'):
                reconectar_callback()

    _show_status_toast(summary)

    current_time = datetime.now().strftime('%H:%M:%S')

    if 'timestamp' in connectivity_info:
        try:
            last_check = datetime.fromisoformat(connectivity_info.get('timestamp')).strftime('%H:%M:%S')
        except (ValueError, TypeError):
            last_check = current_time
    else:
        last_check = connectivity_info.get('last_check', current_time)

    with st.expander(f'Detalles de conectividad (ultimo chequeo: {last_check})', expanded=False):
        st.json(connectivity_info)

    mostrar_boton_diagnostico_rapido(summary)
    if summary.get('impresion_en_progreso') or st.session_state.get('_print_auto_refresh_active'):
        _schedule_auto_refresh()
    st.divider()

    tabs_config = {
        'Facturar': facturacion_tab.render,
        'Ver Facturas': facturas_tab.render,
        'Clientes': clientes_tab.render,
        'Validar NIT': validar_nit_tab.render,
        'Verificar Factura': verificar_factura_tab.render,
        'Gestionar CUIS': cuis_tab.render,
        'Anular o Revertir': anular_factura_tab.render,
        'Revertir Anulacion': revertir_anulacion_tab.render,
        'Diagnostico': diagnostico_tab.render,
        'Pruebas': lambda: ejecutar_diagnostico_completo('tab_pruebas')
    }

    online_only_tabs = [
        'Validar NIT',
        'Verificar Factura',
        'Gestionar CUIS',
        'Anular o Revertir',
        'Revertir Anulacion'
    ]

    tabs_to_render = ['Facturar', 'Ver Facturas', 'Clientes']

    if is_online:
        tabs_to_render.extend(online_only_tabs)

    tabs_to_render.extend(['Diagnostico', 'Pruebas'])

    tab_args = {
        'Facturar': {'is_online': is_online, 'evento_activo': evento_activo},
        'Validar NIT': {'is_online': is_online, 'connectivity_info': connectivity_info},
        'Gestionar CUIS': {'is_online': is_online, 'connectivity_info': connectivity_info},
    }

    previous_selection = st.session_state.get("main_tabs_control")
    if previous_selection not in tabs_to_render:
        previous_selection = tabs_to_render[0]

    selected_tab = st.segmented_control(
        "Secciones principales",
        options=tabs_to_render,
        default=previous_selection,
        key="main_tabs_control",
        label_visibility="collapsed",
        width="stretch",
    )

    if selected_tab is None:
        selected_tab = tabs_to_render[0]

    st.session_state["main_active_tab_name"] = selected_tab

    ui_logger.debug(f'Renderizando pestana: {selected_tab}')
    try:
        render_function = tabs_config[selected_tab]
        args = tab_args.get(selected_tab, {})
        render_function(**args)
    except Exception as exc:
        ui_logger.error(f'Error al renderizar pestana {selected_tab}: {exc}', exc_info=True)
        st.error(f'Error al cargar esta pestana: {exc}')
        st.exception(exc)


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


