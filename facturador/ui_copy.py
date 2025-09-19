import os
import sys
import logging
from datetime import datetime
import time

# Streamlit
import streamlit as st

# LibrerÃ­as externas
from dotenv import load_dotenv

# MÃ³dulos de impresiÃ³n
from print_manager import initialize_print_state

# ConfiguraciÃ³n de loggers
from logger_config import get_logger

# Importar mÃ³dulos de pestaÃ±as
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

# Importar verificador de session_state para diagnÃ³stico de impresiÃ³n
from verificador_session_state import ejecutar_diagnostico_completo

def mostrar_boton_diagnostico_rapido():
    """Muestra un enlace rapido al diagnostico de impresion."""
    impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)
    print_status = st.session_state.get('print_status', '') or ''
    worker_status = st.session_state.get('printer_worker_status', 'desconocido')

    error_en_status = any(token in print_status.lower() for token in ['error', 'fall', 'reinicie'])
    worker_alerta = worker_status not in ('running', 'desconocido')

    if impresion_en_progreso or error_en_status or worker_alerta:
        st.warning('Se detectaron posibles problemas de impresion')
        if st.button('Abrir diagnostico rapido de impresion', help='Abre el panel de diagnostico completo', key='diagnostico_rapido_impresion'):
            with st.expander('Diagnostico de sistema de impresion', expanded=True):
                ejecutar_diagnostico_completo('automatico')



def verificar_estado_sistema():
    """Verifica el estado del sistema de impresion."""
    estado = {
        'problemas_detectados': [],
        'nivel_alerta': 'normal',
        'mensaje_estado': 'Sistema funcionando correctamente'
    }

    impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)
    impresion_finalizada = st.session_state.get('impresion_finalizada', False)
    worker_status = st.session_state.get('printer_worker_status', 'desconocido')
    worker_heartbeat = st.session_state.get('printer_worker_last_heartbeat')
    ultimo_trabajo = st.session_state.get('ultimo_trabajo_impresion')

    if impresion_en_progreso and not impresion_finalizada:
        estado['problemas_detectados'].append('Impresion en curso')
        estado['nivel_alerta'] = 'warning'
        estado['mensaje_estado'] = 'Impresion en curso'

        if ultimo_trabajo and ultimo_trabajo.get('timestamp'):
            try:
                inicio = datetime.fromisoformat(ultimo_trabajo['timestamp'])
                if time.time() - inicio.timestamp() > 180:
                    estado['problemas_detectados'].append('Proceso de impresion bloqueado (>180s)')
                    estado['nivel_alerta'] = 'error'
                    estado['mensaje_estado'] = 'Proceso de impresion bloqueado'
            except Exception:
                pass
    elif impresion_finalizada:
        estado['mensaje_estado'] = 'Ultima impresion completada'

    if worker_status not in ('running', 'desconocido'):
        estado['problemas_detectados'].append(f'Servicio de impresion en estado {worker_status}')
        if worker_status == 'stopped':
            estado['nivel_alerta'] = 'error'
            estado['mensaje_estado'] = 'Servicio de impresion detenido'
        elif estado['nivel_alerta'] != 'error':
            estado['nivel_alerta'] = 'warning'
            estado['mensaje_estado'] = 'Revisar estado del servicio de impresion'

    if worker_heartbeat:
        retraso = time.time() - worker_heartbeat
        if retraso > 120:
            estado['problemas_detectados'].append('Sin senal del worker de impresion (>120s)')
            estado['nivel_alerta'] = 'error'
            estado['mensaje_estado'] = 'Sin senal del servicio de impresion'
        elif retraso > 60 and estado['nivel_alerta'] != 'error':
            estado['problemas_detectados'].append('Senal del worker antigua (>60s)')
            if estado['nivel_alerta'] == 'normal':
                estado['nivel_alerta'] = 'warning'
                estado['mensaje_estado'] = 'Worker de impresion sin actividad reciente'

    try:
        import glob
        signal_files = glob.glob('debug/*.signal')
        if len(signal_files) > 5:
            estado['problemas_detectados'].append(f'{len(signal_files)} archivos de senal acumulados')
            if estado['nivel_alerta'] == 'normal':
                estado['nivel_alerta'] = 'warning'
                estado['mensaje_estado'] = 'Mantenimiento recomendado'
    except Exception:
        pass

    try:
        import threading
        hilos_impresion = [h for h in threading.enumerate() if 'print' in h.name.lower()]
        if len(hilos_impresion) > 1:
            estado['problemas_detectados'].append(f'{len(hilos_impresion)} hilos de impresion activos')
            if estado['nivel_alerta'] == 'normal':
                estado['nivel_alerta'] = 'warning'
                estado['mensaje_estado'] = 'Hilos de impresion activos detectados'
    except Exception:
        pass

    return estado


# Importar cliente para verificar conectividad (solo para el botÃ³n de reconexiÃ³n)
from api_clients import reset_soap_client

# Configurar loggers
ui_logger = get_logger('ui')  # Logger especÃ­fico para la interfaz de usuario

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

# La inicializaciÃ³n del cliente SOAP se ha movido a api_clients.py
# para mantener la separaciÃ³n de responsabilidades

# GestiÃ³n de pestaÃ±as con logs
def render_full_ui(is_online: bool, connectivity_info: dict, evento_activo: dict = None, reconectar_callback=None):
    """Renderiza la interfaz principal sin comprobaciones adicionales."""
    ui_logger.info("Renderizando la interfaz principal...")

    principal = connectivity_info.get("verificacion_principal", {})
    estado_general = connectivity_info.get("estado_general", "DESCONOCIDO")
    recomendacion = connectivity_info.get("recomendacion", "")
    status = estado_general
    status_message = recomendacion

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        if is_online:
            st.success(f"{status} - {status_message}")
            ui_logger.info("Sistema conectado a servicios del SIN")
        else:
            st.error(f"{status} - {status_message}")
            ui_logger.warning("Sistema funcionando en modo offline")

    with col2:
        estado_sistema = verificar_estado_sistema()
        if estado_sistema['nivel_alerta'] == 'error':
            st.error(estado_sistema['mensaje_estado'])
        elif estado_sistema['nivel_alerta'] == 'warning':
            st.warning(estado_sistema['mensaje_estado'])
        else:
            st.success('Sistema de impresion sin alertas')

    with col3:
        if not is_online and reconectar_callback:
            if st.button('Reconectar', help='Intentar reconectarse a los servicios del SIN'):
                reconectar_callback()

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

    mostrar_boton_diagnostico_rapido()
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

    rendered_tabs = st.tabs(tabs_to_render)

    for tab, tab_name in zip(rendered_tabs, tabs_to_render):
        with tab:
            ui_logger.debug(f'Renderizando pestana: {tab_name}')
            try:
                render_function = tabs_config[tab_name]
                args = tab_args.get(tab_name, {})
                render_function(**args)
            except Exception as exc:
                ui_logger.error(f'Error al renderizar pestana {tab_name}: {exc}', exc_info=True)
                st.error(f'Error al cargar esta pestana: {exc}')
                st.exception(exc)


if __name__ == "__main__":
    """
    Ejecutor de respaldo. En el flujo normal, main.py es quien llama a render_full_ui.
    """
    try:
        initialize_print_state()
        # Modo de respaldo - funcionalidad bÃ¡sica sin verificaciÃ³n completa
        dummy_connectivity = {
            "estado_general": "RESPALDO",
            "recomendacion": "Ejecutando en modo de respaldo. Use main.py para funcionalidad completa.",
            "verificacion_principal": {"conectado": False}
        }
        render_full_ui(is_online=False, connectivity_info=dummy_connectivity)
    except Exception as e:
        ui_logger.error(f"Error en la ejecuciÃ³n principal: {str(e)}", exc_info=True)
        st.error(f"Ha ocurrido un error: {str(e)}")


