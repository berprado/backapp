import os
import sys
import traceback
import streamlit as st
from zeep import Client
from zeep.transports import Transport
import requests
from dotenv import load_dotenv
from sqlalchemy import func, Text, String
from datetime import datetime, timezone, timedelta
import pytz
import tzlocal

# Agregar rutas a sys.path para acceder a los modulos del proyecto
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
facturador_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if facturador_dir not in sys.path:
    sys.path.append(facturador_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Importar el logger central de la aplicacion.  Este modulo
# configura y expone todos los loggers necesarios para la app.
# Al utilizarlo evitamos duplicar handlers y aseguramos una
# codificacion consistente y rotacion de archivos.
from facturador.logger_config import get_sincronizacion_logger

# Instancia global del logger de sincronizacion para este modulo.
# Todos los mensajes relacionados con sincronizacion deben
# registrarse a traves de este objeto para que queden en los
# ficheros de log centralizados configurados por ``logger_config.py``.
logger = get_sincronizacion_logger()

def registrar_y_mostrar(tipo: str, mensaje: str) -> None:
    """Envia un mensaje tanto a la interfaz de Streamlit como al
    sistema de logs centralizado.

    Este helper recibe el tipo de mensaje (``info``, ``success``,
    ``warning`` o ``error``) y lo publica tanto en la interfaz
    interactiva como en el archivo de log correspondiente.  Para
    mensajes mas detallados o de depuracion, utilice ``logger.debug``
    directamente.

    Args:
        tipo (str): Tipo de mensaje. Debe ser uno de
            ``info``, ``success``, ``warning`` o ``error``.
        mensaje (str): Texto del mensaje a mostrar y registrar.
    """
    tipo = (tipo or '').lower().strip()
    try:
        if tipo == 'success':
            st.success(mensaje)
            logger.info(mensaje)
        elif tipo == 'warning':
            st.warning(mensaje)
            logger.warning(mensaje)
        elif tipo == 'error':
            st.error(mensaje)
            logger.error(mensaje)
        else:
            st.info(mensaje)
            logger.info(mensaje)
    except Exception:
        # En entornos no interactivos, es posible que ``st`` no este
        # disponible. En tal caso, registrar conservando la severidad.
        if tipo == 'success':
            logger.info(mensaje)
        elif tipo == 'warning':
            logger.warning(mensaje)
        elif tipo == 'error':
            logger.error(mensaje)
        else:
            logger.info(mensaje)


def notificar(tipo: str, mensaje: str, usar_toast: bool = True):
    """
    Sistema de notificaciones mejorado con soporte para toast.
    
    Esta función extiende la funcionalidad de registrar_y_mostrar()
    agregando soporte para notificaciones toast no invasivas,
    mientras mantiene el registro centralizado en logs.
    
    Args:
        tipo (str): Tipo de mensaje ('success', 'warning', 'error', 'info')
        mensaje (str): Texto del mensaje a mostrar y registrar
        usar_toast (bool): Si True, usa toast; si False, usa alertas tradicionales
                          Toast se recomienda para mensajes informativos.
                          Alertas tradicionales para mensajes críticos.
    
    Example:
        >>> # Notificación no invasiva (recomendado)
        >>> notificar('success', 'Sincronización completada', usar_toast=True)
        >>> 
        >>> # Alerta tradicional para errores críticos
        >>> notificar('error', 'Error de conexión con SIAT', usar_toast=False)
    
    Note:
        El logging se realiza siempre, independientemente del tipo de visualización.
    """
    # Mapeo de iconos para el parámetro icon de toast
    iconos_emoji = {
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'info': 'ℹ️'
    }
    
    # Registrar en log (siempre, preservando sistema centralizado)
    if tipo == 'success':
        logger.info(mensaje)
    elif tipo == 'warning':
        logger.warning(mensaje)
    elif tipo == 'error':
        logger.error(mensaje)
    else:
        logger.info(mensaje)
    
    # Mostrar en UI
    try:
        if usar_toast:
            # Usar toast para mensajes menos críticos (nuevo en 1.49.0)
            # IMPORTANTE: Solo pasamos el mensaje, el icono se muestra automáticamente
            # con el parámetro icon= (evita duplicación de iconos)
            st.toast(mensaje, icon=iconos_emoji.get(tipo, 'ℹ️'))
        else:
            # Usar alertas tradicionales para mensajes importantes
            if tipo == 'success':
                st.success(mensaje)
            elif tipo == 'warning':
                st.warning(mensaje)
            elif tipo == 'error':
                st.error(mensaje)
            else:
                st.info(mensaje)
    except Exception as e:
        # Fallback si Streamlit no está disponible
        logger.info(f"[UI no disponible] {tipo.upper()}: {mensaje}")
        logger.debug(f"Error al mostrar mensaje en UI: {e}")


# ============================================================================
# GESTION DE ESTADO DE SINCRONIZACION EN SESSION_STATE
# ============================================================================
# Las siguientes funciones gestionan el estado de sincronizacion de forma
# centralizada usando st.session_state, eliminando la necesidad de variables
# globales y proporcionando persistencia entre recargas de Streamlit.


def inicializar_estado_sincronizacion():
    """
    Inicializa el estado de sincronizacion en st.session_state.
    
    Esta funcion crea una estructura de datos centralizada para mantener
    toda la informacion de sincronizacion de forma persistente entre
    interacciones de Streamlit.
    
    Estructura creada:
        sync_state = {
            'remote_time': datetime | None,        # Hora del servidor SIAT
            'local_time': datetime | None,         # Hora local del sistema
            'time_difference': timedelta | None,   # Diferencia horaria calculada
            'ultima_sincronizacion': datetime | None,  # Timestamp ultima sync
            'estado_comunicacion': str,            # 'conectado', 'desconectado', 'no_verificado'
            'ultima_verificacion': datetime | None,    # Timestamp ultima verificacion
            'sincronizaciones_completadas': list[str]  # Historial de servicios sincronizados
        }
    
    Si existe informacion previa en la base de datos, se carga automaticamente
    al inicializar por primera vez.
    """
    if 'sync_state' not in st.session_state:
        st.session_state.sync_state = {
            'remote_time': None,
            'local_time': None,
            'time_difference': None,
            'ultima_sincronizacion': None,
            'estado_comunicacion': 'no_verificado',
            'ultima_verificacion': None,
            'sincronizaciones_completadas': []
        }
        logger.info("Estado de sincronizacion inicializado en session_state")
    
    # Si existe informacion en la BD pero no en session_state, cargarla
    if st.session_state.sync_state['ultima_sincronizacion'] is None:
        try:
            db = next(get_db())
            try:
                sync_record = db.query(SincronizacionEstado).first()
                if sync_record and sync_record.ultima_sincronizacion:
                    st.session_state.sync_state['ultima_sincronizacion'] = sync_record.ultima_sincronizacion
                    logger.info(f"Ultima sincronizacion cargada desde BD: {sync_record.ultima_sincronizacion}")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"No se pudo cargar estado desde BD: {e}")


def obtener_estado_sync(clave: str, default=None):
    """
    Obtiene un valor del estado de sincronizacion.
    
    Esta funcion proporciona acceso controlado y seguro a los valores
    almacenados en el estado de sincronizacion, garantizando que el
    estado este inicializado antes de acceder.
    
    Args:
        clave (str): Nombre del campo a obtener. Debe ser una de las claves
            definidas en la estructura sync_state (remote_time, local_time,
            time_difference, ultima_sincronizacion, estado_comunicacion,
            ultima_verificacion, sincronizaciones_completadas).
        default: Valor por defecto si la clave no existe o es None.
    
    Returns:
        El valor almacenado o el valor por defecto si no existe.
    
    Example:
        >>> remote_time = obtener_estado_sync('remote_time')
        >>> if remote_time is not None:
        ...     print(f"Hora del servidor: {remote_time}")
    """
    inicializar_estado_sincronizacion()  # Asegurar que existe
    return st.session_state.sync_state.get(clave, default)


def actualizar_estado_sync(clave: str, valor, guardar_bd: bool = True):
    """
    Actualiza un valor en el estado de sincronizacion.
    
    Esta funcion proporciona la unica forma recomendada de modificar
    el estado de sincronizacion, asegurando consistencia entre
    st.session_state y la base de datos cuando sea necesario.
    
    Args:
        clave (str): Nombre del campo a actualizar.
        valor: Nuevo valor a almacenar.
        guardar_bd (bool): Si True, tambien actualiza la base de datos
            (solo aplica para 'ultima_sincronizacion').
    
    Example:
        >>> # Actualizar hora remota sin guardar en BD
        >>> actualizar_estado_sync('remote_time', datetime.now(), guardar_bd=False)
        >>> 
        >>> # Registrar sincronizacion exitosa (se guarda en BD)
        >>> actualizar_estado_sync('ultima_sincronizacion', datetime.now(pytz.utc))
    """
    inicializar_estado_sincronizacion()
    st.session_state.sync_state[clave] = valor
    logger.debug(f"Estado sync actualizado: {clave} = {valor}")
    
    # Sincronizar con BD si es necesario
    if guardar_bd and clave == 'ultima_sincronizacion':
        try:
            db = next(get_db())
            try:
                sync_record = db.query(SincronizacionEstado).first()
                if not sync_record:
                    sync_record = SincronizacionEstado()
                    db.add(sync_record)
                
                sync_record.ultima_sincronizacion = valor
                db.commit()
                logger.debug("Estado sync guardado en BD")
            except Exception as e:
                db.rollback()
                logger.error(f"Error al guardar estado sync en BD: {e}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error al conectar con BD para guardar estado: {e}")


def obtener_diferencia_horaria_formateada() -> str:
    """
    Retorna la diferencia horaria en formato legible.
    
    Convierte el timedelta almacenado en sync_state['time_difference']
    en una cadena de texto facil de leer para mostrar al usuario.
    
    Returns:
        str: Diferencia horaria formateada (ej: "+00:02:15.340" para
            adelantado o "-01:30:00.000" para atrasado), o "No disponible"
            si no se ha sincronizado.
    
    Example:
        >>> diferencia = obtener_diferencia_horaria_formateada()
        >>> print(f"Diferencia con SIAT: {diferencia}")
        Diferencia con SIAT: +00:00:02.150
    """
    time_diff = obtener_estado_sync('time_difference')
    if time_diff is None:
        return "No disponible"
    
    diferencia_segundos = time_diff.total_seconds()
    minutos, segundos = divmod(abs(diferencia_segundos), 60)
    horas, minutos = divmod(minutos, 60)
    dias, horas = divmod(horas, 24)
    
    signo = "+" if diferencia_segundos >= 0 else "-"
    
    if dias > 0:
        return f"{signo}{int(dias)} dias, {int(horas):02}:{int(minutos):02}:{segundos:.3f}"
    elif horas > 0:
        return f"{signo}{int(horas):02}:{int(minutos):02}:{segundos:.3f}"
    else:
        return f"{signo}{int(minutos):02}:{segundos:.3f}"


def mostrar_panel_metricas():
    """
    Muestra un panel de métricas siempre visible en la parte superior.
    
    Este panel proporciona una vista rápida del estado del sistema:
    - Estado de conexión con SIAT
    - Tiempo desde última sincronización
    - Servicios sincronizados correctamente
    - Diferencia horaria actual
    
    Las métricas se obtienen del estado centralizado en st.session_state
    y se actualizan automáticamente con cada sincronización.
    """
    col1, col2, col3, col4 = st.columns(4)
    
    ultima_sync = obtener_estado_sync('ultima_sincronizacion')
    estado_conn = obtener_estado_sync('estado_comunicacion', 'no_verificado')
    servicios_ok = len(obtener_estado_sync('sincronizaciones_completadas', []))
    time_diff = obtener_estado_sync('time_difference')
    
    # Métrica 1: Estado de Conexión
    with col1:
        if estado_conn == 'conectado':
            st.metric("🌐 Conexión", "Online", delta="✓", delta_color="normal")
        elif estado_conn == 'desconectado':
            st.metric("🌐 Conexión", "Offline", delta="✗", delta_color="inverse")
        else:
            st.metric("🌐 Conexión", "Sin verificar", delta="?", delta_color="off")
    
    # Métrica 2: Última Sincronización
    with col2:
        if ultima_sync:
            # Asegurar timezone
            if ultima_sync.tzinfo is None:
                ultima_sync = pytz.utc.localize(ultima_sync)
            
            tiempo_transcurrido = datetime.now(pytz.utc) - ultima_sync
            minutos = int(tiempo_transcurrido.total_seconds() / 60)
            
            if minutos < 60:
                st.metric("⏱️ Última Sync", f"{minutos} min", 
                         delta="Reciente" if minutos < 10 else None)
            else:
                horas = minutos // 60
                st.metric("⏱️ Última Sync", f"{horas} h", 
                         delta="Antigua" if horas > 24 else None, 
                         delta_color="inverse" if horas > 24 else "off")
        else:
            st.metric("⏱️ Última Sync", "Nunca", delta="Sincronizar", delta_color="inverse")
    
    # Métrica 3: Servicios Sincronizados
    with col3:
        total_servicios = len(service_model_map) + 1  # +1 por fecha/hora
        porcentaje = int((servicios_ok / total_servicios) * 100) if servicios_ok > 0 else 0
        st.metric("📊 Servicios", f"{servicios_ok}/{total_servicios}", 
                 delta=f"{porcentaje}%" if servicios_ok > 0 else "0%")
    
    # Métrica 4: Diferencia Horaria
    with col4:
        if time_diff is not None:
            diff_segundos = abs(time_diff.total_seconds())
            if diff_segundos <= 5:
                st.metric("⏰ Diferencia", f"±{diff_segundos:.1f}s", 
                         delta="Óptima", delta_color="normal")
            elif diff_segundos <= 300:
                st.metric("⏰ Diferencia", f"±{diff_segundos:.0f}s", 
                         delta="Aceptable", delta_color="off")
            else:
                st.metric("⏰ Diferencia", f"±{diff_segundos:.0f}s", 
                         delta="Alta", delta_color="inverse")
        else:
            st.metric("⏰ Diferencia", "N/D", delta="Sincronizar")


def mostrar_indicador_estado_sidebar():
    """
    Muestra un indicador compacto de estado en el sidebar.
    
    Este indicador proporciona información rápida sobre:
    - Estado de conexión actual con SIAT
    - Tiempo desde última sincronización
    - Botón de verificación rápida
    
    Diseñado para ser siempre visible y ocupar mínimo espacio.
    """
    with st.sidebar:
        st.markdown("### 📊 Estado del Sistema")
        
        estado_conn = obtener_estado_sync('estado_comunicacion', 'no_verificado')
        
        # Indicador visual con color
        if estado_conn == 'conectado':
            st.success("🟢 **Sistema Online**")
        elif estado_conn == 'desconectado':
            st.error("🔴 **Sistema Offline**")
        else:
            st.warning("🟡 **Estado Desconocido**")
        
        # Última sincronización compacta
        ultima_sync = obtener_estado_sync('ultima_sincronizacion')
        if ultima_sync:
            if ultima_sync.tzinfo is None:
                ultima_sync = pytz.utc.localize(ultima_sync)
            tiempo_transcurrido = datetime.now(pytz.utc) - ultima_sync
            minutos = int(tiempo_transcurrido.total_seconds() / 60)
            
            if minutos < 60:
                st.caption(f"⏱️ Última sync: hace {minutos} min")
            else:
                horas = minutos // 60
                st.caption(f"⏱️ Última sync: hace {horas} h")
        else:
            st.caption("⏱️ Sin sincronización previa")
        
        # Botón de actualización rápida
        if st.button("🔄 Verificar Conexión", use_container_width=True):
            logger.info("Usuario solicitó verificación rápida desde sidebar")
            exito, mensaje = verificar_comunicacion()
            if exito:
                actualizar_estado_sync('estado_comunicacion', 'conectado', guardar_bd=False)
                notificar('success', "✓ Conexión verificada", usar_toast=True)
                logger.info("Verificación rápida exitosa")
            else:
                actualizar_estado_sync('estado_comunicacion', 'desconectado', guardar_bd=False)
                notificar('error', f"✗ {mensaje}", usar_toast=False)
                logger.error(f"Verificación rápida falló: {mensaje}")
            st.rerun()


# ============================================================================
# FIN DE GESTION DE ESTADO
# ============================================================================

# Importar desde database.py en el directorio facturador
from database import get_db, Base

# Importar todos los modelos necesarios con nombres completamente cualificados
from models import (
    SincronizarActividades as ModeloSincronizarActividades,
    SincronizarListaActividadesDocumentoSector as ModeloSincronizarListaActividadesDocumentoSector,
    SincronizarListaLeyendasFactura as ModeloSincronizarListaLeyendasFactura,
    SincronizarListaMensajesServicios as ModeloSincronizarListaMensajesServicios,
    SincronizarListaProductosServicios as ModeloSincronizarListaProductosServicios,
    SincronizarParametricaEventosSignificativos as ModeloSincronizarParametricaEventosSignificativos,
    SincronizarParametricaMotivoAnulacion as ModeloSincronizarParametricaMotivoAnulacion,
    SincronizarParametricaPaisOrigen as ModeloSincronizarParametricaPaisOrigen,
    SincronizarParametricaTipoDocumentoIdentidad as ModeloSincronizarParametricaTipoDocumentoIdentidad,
    SincronizarParametricaTipoDocumentoSector as ModeloSincronizarParametricaTipoDocumentoSector,
    SincronizarParametricaTipoEmision as ModeloSincronizarParametricaTipoEmision,
    SincronizarParametricaTipoHabitacion as ModeloSincronizarParametricaTipoHabitacion,
    SincronizarParametricaTipoMetodoPago as ModeloSincronizarParametricaTipoMetodoPago,
    SincronizarParametricaTipoMoneda as ModeloSincronizarParametricaTipoMoneda,
    SincronizarParametricaTipoPuntoVenta as ModeloSincronizarParametricaTipoPuntoVenta,
    SincronizarParametricaTiposFactura as ModeloSincronizarParametricaTiposFactura,
    SincronizacionEstado,
    SincronizarParametricaUnidadMedida as ModeloSincronizarParametricaUnidadMedida,
)

# Cargar variables de entorno desde el directorio raiz
load_dotenv(os.path.join(root_dir, '.env'))

# --- Eliminada configuracion local de logging ---
# Esta seccion ha sido reemplazada por el uso de ``logger_config.py``.
# Todas las configuraciones de log se manejan de forma centralizada.

# Configuracion del cliente SOAP (fuera de la funcion para reutilizarlo)
wsdl_url = os.getenv("WSDL_URL_SYNC")
api_key = os.getenv("API_KEY")
client = None
client_error_message = None
client_error_details = None

if not wsdl_url:
    client_error_message = "No se configuro la URL del servicio de sincronizacion (WSDL_URL_SYNC)."
    logger.error(client_error_message)
elif not api_key:
    client_error_message = "No se configuro la clave de acceso (API_KEY) para el servicio de sincronizacion."
    logger.error(client_error_message)
else:
    try:
        session = requests.Session()
        session.headers.update({"apikey": api_key})
        transport = Transport(session=session)
        client = Client(wsdl_url, transport=transport)
    except requests.exceptions.RequestException as exc:
        client_error_message = (
            "No se pudo conectar con el servicio de sincronizacion SIAT. "
            "El sistema parece estar sin conexion a Internet."
        )
        client_error_details = str(exc)
        logger.error("Error de conexion al inicializar el cliente SIAT: %s", exc, exc_info=True)
        client = None
    except Exception as exc:
        client_error_message = "Error al inicializar el cliente de sincronizacion SIAT."
        client_error_details = str(exc)
        logger.error("Error general al inicializar el cliente SIAT: %s", exc, exc_info=True)
        client = None

# NOTA: Las variables globales remote_time, local_time y time_difference
# han sido ELIMINADAS y reemplazadas por el sistema de gestion de estado
# en st.session_state. Ver funciones:
# - inicializar_estado_sincronizacion()
# - obtener_estado_sync()
# - actualizar_estado_sync()
# Esto garantiza persistencia entre recargas de Streamlit y elimina
# problemas de estado mutable global.


def estado_cliente_siat():
    """Retorna una tupla (disponible, mensaje, detalle) con el estado del cliente SOAP."""
    if client is None:
        mensaje = client_error_message or "El cliente de sincronizacion SIAT no esta disponible."
        return False, mensaje, client_error_details
    return True, "", None

# Actualizar diccionario que mapea nombres de servicios a clases de modelo con referencia completa
service_model_map = {
    'sincronizarActividades': ModeloSincronizarActividades,
    'sincronizarListaActividadesDocumentoSector': ModeloSincronizarListaActividadesDocumentoSector,
    'sincronizarListaLeyendasFactura': ModeloSincronizarListaLeyendasFactura,
    'sincronizarListaMensajesServicios': ModeloSincronizarListaMensajesServicios,
    'sincronizarListaProductosServicios': ModeloSincronizarListaProductosServicios,
    'sincronizarParametricaEventosSignificativos': ModeloSincronizarParametricaEventosSignificativos,
    'sincronizarParametricaMotivoAnulacion': ModeloSincronizarParametricaMotivoAnulacion,
    'sincronizarParametricaPaisOrigen': ModeloSincronizarParametricaPaisOrigen,
    'sincronizarParametricaTipoDocumentoIdentidad': ModeloSincronizarParametricaTipoDocumentoIdentidad,
    'sincronizarParametricaTipoDocumentoSector': ModeloSincronizarParametricaTipoDocumentoSector,
    'sincronizarParametricaTipoEmision': ModeloSincronizarParametricaTipoEmision,
    'sincronizarParametricaTipoHabitacion': ModeloSincronizarParametricaTipoHabitacion,
    'sincronizarParametricaTipoMetodoPago': ModeloSincronizarParametricaTipoMetodoPago,
    'sincronizarParametricaTipoMoneda': ModeloSincronizarParametricaTipoMoneda,
    'sincronizarParametricaTipoPuntoVenta': ModeloSincronizarParametricaTipoPuntoVenta,
    'sincronizarParametricaTiposFactura': ModeloSincronizarParametricaTiposFactura,
    'sincronizarParametricaUnidadMedida': ModeloSincronizarParametricaUnidadMedida,
}

# Configuracion de campos clave para cada modelo
model_key_fields = {
    ModeloSincronizarActividades: 'codigoCaeb',
    ModeloSincronizarListaActividadesDocumentoSector: ['codigoActividad', 'codigoDocumentoSector'],
    ModeloSincronizarListaLeyendasFactura: 'codigoActividad',
    ModeloSincronizarListaMensajesServicios: 'codigoClasificador',
    ModeloSincronizarListaProductosServicios: ['codigoActividad', 'codigoProducto'],
    ModeloSincronizarParametricaEventosSignificativos: 'codigoClasificador',
    ModeloSincronizarParametricaMotivoAnulacion: 'codigoClasificador',
    ModeloSincronizarParametricaPaisOrigen: 'codigoClasificador',
    ModeloSincronizarParametricaTipoDocumentoIdentidad: 'codigoClasificador',
    ModeloSincronizarParametricaTipoDocumentoSector: 'codigoClasificador',
    ModeloSincronizarParametricaTipoEmision: 'codigoClasificador',
    ModeloSincronizarParametricaTipoHabitacion: 'codigoClasificador',
    ModeloSincronizarParametricaTipoMetodoPago: 'codigoClasificador',
    ModeloSincronizarParametricaTipoMoneda: 'codigoClasificador',
    ModeloSincronizarParametricaTipoPuntoVenta: 'codigoClasificador',
    ModeloSincronizarParametricaTiposFactura: 'codigoClasificador',
    ModeloSincronizarParametricaUnidadMedida: 'codigoClasificador',
}

# Mapeo de nombres de servicios a nombres de listas en la respuesta SOAP
service_list_map = {
    'sincronizarActividades': 'listaActividades',
    'sincronizarListaActividadesDocumentoSector': 'actividadesDocumentoSector',
    'sincronizarListaLeyendasFactura': 'listaLeyendas',
    'sincronizarListaMensajesServicios': 'listaMensajesServicios',
    'sincronizarListaProductosServicios': 'listaCodigos',
    'sincronizarParametricaEventosSignificativos': 'listaCodigos',
    'sincronizarParametricaMotivoAnulacion': 'listaCodigos',
    'sincronizarParametricaPaisOrigen': 'listaCodigos',
    'sincronizarParametricaTipoDocumentoIdentidad': 'listaCodigos',
    'sincronizarParametricaTipoDocumentoSector': 'listaCodigos',
    'sincronizarParametricaTipoEmision': 'listaCodigos',
    'sincronizarParametricaTipoHabitacion': 'listaCodigos',
    'sincronizarParametricaTipoMetodoPago': 'listaCodigos',
    'sincronizarParametricaTipoMoneda': 'listaCodigos',
    'sincronizarParametricaTipoPuntoVenta': 'listaCodigos',
    'sincronizarParametricaTiposFactura': 'listaCodigos',
    'sincronizarParametricaUnidadMedida': 'listaCodigos',
}

def verificar_comunicacion():
    url = os.getenv("WSDL_URL_SYNC")
    disponible, mensaje_cliente, _ = estado_cliente_siat()
    if not disponible:
        return False, mensaje_cliente

    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": "",
        "apikey": api_key
    }
    soap_request = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
       <soapenv:Header/>
       <soapenv:Body>
          <siat:verificarComunicacion/>
       </soapenv:Body>
    </soapenv:Envelope>"""
    
    try:
        response = requests.post(url, data=soap_request, headers=headers)
        response.raise_for_status()
        if "<codigo>926</codigo>" in response.text:
            return True, "Comunicacion exitosa con codigo 926"
        else:
            return False, "Fallo en la comunicacion"
    except requests.exceptions.RequestException as e:
        return False, f"Error de comunicacion: {e}"

def calcular_diferencia_horaria(remote_time, local_time):
    """
    Calcula la diferencia horaria entre dos momentos en el tiempo.
    Devuelve la diferencia en segundos y un objeto timedelta.
    """
    # Asegurar que ambos tiempos esten en UTC para una comparacion correcta
    remote_time_utc = remote_time.astimezone(pytz.utc)
    local_time_utc = local_time.astimezone(pytz.utc)
    
    # Calculamos tanto la diferencia en segundos como el objeto timedelta
    diferencia_timedelta = remote_time_utc - local_time_utc
    diferencia_segundos = diferencia_timedelta.total_seconds()
    
    # Si la diferencia es casi un dia completo, podria ser un problema de zona horaria
    if abs(diferencia_segundos) > 86000 and abs(diferencia_segundos) < 86400:
        # Probablemente hay un problema con la interpretacion de la zona horaria
        # Intentamos corregir la diferencia
        if diferencia_segundos < 0:
            diferencia_segundos += 86400  # Sumamos 24 horas
            diferencia_timedelta = timedelta(seconds=diferencia_segundos)
        else:
            diferencia_segundos -= 86400  # Restamos 24 horas
            diferencia_timedelta = timedelta(seconds=diferencia_segundos)
            
    return diferencia_segundos, diferencia_timedelta

def sincronizar_fecha_hora():
    """
    Sincroniza la fecha y hora con el servidor SIAT.
    
    Esta función consulta la hora del servidor remoto, la compara con la hora
    local del sistema y calcula la diferencia horaria. Todos los valores se
    almacenan en st.session_state mediante las funciones de acceso.
    
    Returns:
        bool: True si la sincronización fue exitosa, False en caso contrario.
    """
    disponible, mensaje_cliente, _ = estado_cliente_siat()
    if not disponible:
        registrar_y_mostrar('warning', mensaje_cliente)
        return False

    registrar_y_mostrar('info', "Iniciando sincronizacion de Fecha y Hora")
    SolicitudSincronizacion = client.get_type('ns0:solicitudSincronizacion')
    
    # Obtener y validar codigoPuntoVenta
    codigo_punto_venta = os.getenv("CODIGO_PUNTO_VENTA", "0")
    try:
        codigo_punto_venta = int(codigo_punto_venta)
    except (ValueError, TypeError):
        logger.warning(f"CODIGO_PUNTO_VENTA invalido ({codigo_punto_venta}), usando 0 por defecto")
        codigo_punto_venta = 0
    
    solicitud = SolicitudSincronizacion(
        codigoAmbiente=int(os.getenv("CODIGO_AMBIENTE")),
        codigoPuntoVenta=codigo_punto_venta,
        codigoSistema=os.getenv("CODIGO_SISTEMA"),
        codigoSucursal=int(os.getenv("CODIGO_SUCURSAL")),
        cuis=os.getenv("CUIS"),
        nit=int(os.getenv("NIT"))
    )
    
    logger.debug(f"Solicitud creada: {solicitud}")
    logger.debug(f"Parametros: codigoAmbiente={os.getenv('CODIGO_AMBIENTE')}, codigoPuntoVenta={codigo_punto_venta}, codigoSistema={os.getenv('CODIGO_SISTEMA')}, codigoSucursal={os.getenv('CODIGO_SUCURSAL')}, cuis={os.getenv('CUIS')}, nit={os.getenv('NIT')}")
    
    try:
        logger.debug("Enviando solicitud al servicio SOAP")
        response = client.service.sincronizarFechaHora(solicitud)
        logger.debug(f"Respuesta recibida: {response}")
        
        if not response.transaccion:
            error_msg = "Error en la transaccion SOAP para sincronizarFechaHora"
            registrar_y_mostrar('error', error_msg)
            return False
        
        # Zona horaria del servidor remoto (Bolivia)
        bolivia_tz = pytz.timezone("America/La_Paz")
        
        # Convertir la fecha y hora remota de forma segura
        try:
            remote_time = datetime.fromisoformat(response.fechaHora)
            if remote_time.tzinfo is None:
                remote_time = bolivia_tz.localize(remote_time)
            else:
                remote_time = remote_time.astimezone(bolivia_tz)
        except Exception as e:
            logger.error(f"Error al convertir la fecha remota: {e}")
            registrar_y_mostrar('error', "Error al obtener la fecha del servidor. Sincronizacion fallida.")
            return False
        
        # Obtener la hora local actual con su zona horaria
        local_time = datetime.now(tzlocal.get_localzone())
        
        logger.debug(f"Hora remota (Bolivia): {remote_time}")
        logger.debug(f"Hora local: {local_time}")

        # Calcular la diferencia horaria correctamente
        diferencia_segundos, time_difference = calcular_diferencia_horaria(remote_time, local_time)
        
        # Actualizar el estado de sincronización con los valores calculados
        actualizar_estado_sync('remote_time', remote_time, guardar_bd=False)
        actualizar_estado_sync('local_time', local_time, guardar_bd=False)
        actualizar_estado_sync('time_difference', time_difference, guardar_bd=False)

        # Verificar si la diferencia de tiempo esta en un rango razonable (5 minutos)
        tiempo_razonable = 300  # 5 minutos en segundos
        diferencia_absoluta = abs(diferencia_segundos)
        
        if diferencia_absoluta <= tiempo_razonable:
            mensaje_tiempo = f"La diferencia de tiempo esta en un rango razonable ({diferencia_absoluta:.2f} segundos)"
            registrar_y_mostrar('success', f" {mensaje_tiempo}")
        else:
            mensaje_tiempo = f"La diferencia de tiempo NO esta en un rango razonable ({diferencia_absoluta:.2f} segundos)"
            registrar_y_mostrar('warning', mensaje_tiempo)

        if diferencia_absoluta > 86400:  # Mas de 24 horas
            logger.warning(f"Diferencia de tiempo anormal: {time_difference}. Verifique la zona horaria.")
            registrar_y_mostrar('warning', f"Diferencia de tiempo anormal detectada: {time_difference}. Desea corregirla?")
            
            if st.button("Corregir diferencia horaria"):
                # Corregir en el estado centralizado
                actualizar_estado_sync('time_difference', timedelta(seconds=0), guardar_bd=False)
                diferencia_segundos = 0
                registrar_y_mostrar('success', " Diferencia horaria corregida manualmente.")

        logger.debug(f"Diferencia de tiempo calculada: {time_difference}")

        # Guardar resultado en la base de datos y actualizar estado
        try:
            db = next(get_db())
            try:
                sync_record = db.query(SincronizacionEstado).first()
                if not sync_record:
                    sync_record = SincronizacionEstado()
                    db.add(sync_record)
                
                # Actualizar fecha de sincronizacion en BD y en estado
                timestamp_sincronizacion = datetime.now(pytz.utc)
                sync_record.ultima_sincronizacion = timestamp_sincronizacion
                db.commit()
                
                # Actualizar también en el estado de sesión
                actualizar_estado_sync('ultima_sincronizacion', timestamp_sincronizacion, guardar_bd=False)
                logger.info(f"Sincronización guardada exitosamente: {timestamp_sincronizacion}")
            except Exception as e:
                db.rollback()
                logger.error(f"Error al guardar sincronizacion: {e}")
                # Guardamos la información en la sesión como respaldo
                actualizar_estado_sync('ultima_sincronizacion', datetime.now(pytz.utc), guardar_bd=False)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error al conectar con la base de datos: {e}")
            # Guardamos la información en la sesión como respaldo
            actualizar_estado_sync('ultima_sincronizacion', datetime.now(pytz.utc), guardar_bd=False)
            
        registrar_y_mostrar('success', " Sincronizacion de Fecha y Hora completada.")
        mostrar_informacion_sincronizacion()
        return True

    except Exception as e:
        error_msg = f"Error al sincronizar Fecha y Hora: {str(e)}"
        registrar_y_mostrar('error', error_msg)
        logger.error(traceback.format_exc())
        return False

def mostrar_informacion_sincronizacion():
    """
    FUNCIÓN LEGACY: Mantenida por compatibilidad.
    
    Use mostrar_detalles_sincronizacion_expandible() para la nueva interfaz.
    Esta función mantiene el comportamiento original para evitar breaking changes.
    """
    # Obtener valores del estado centralizado
    remote_time = obtener_estado_sync('remote_time')
    local_time = obtener_estado_sync('local_time')
    time_difference = obtener_estado_sync('time_difference')
    
    if remote_time and local_time and time_difference is not None:
        registrar_y_mostrar('info', "Informacion de sincronizacion:")
        col1, col2 = st.columns(2)
        with col1:
            st.write("🌎 Hora del servidor remoto (Bolivia):")
            st.write(remote_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        with col2:
            st.write("💻 Hora local:")
            st.write(local_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        
        # Usar la función centralizada para formatear la diferencia
        st.write("⏱️ Diferencia de tiempo:")
        diferencia_formateada = obtener_diferencia_horaria_formateada()
        
        # Si es cerca de 24 horas, mostrar una advertencia
        diferencia_segundos = time_difference.total_seconds()
        if abs(diferencia_segundos) > 86000 and abs(diferencia_segundos) < 86400:
            registrar_y_mostrar('warning', "⚠️ La diferencia parece ser de aproximadamente 24 horas, lo que sugiere un problema con la zona horaria.")
        
        # Mostrar la diferencia formateada
        st.write(diferencia_formateada)
            
        # Tambien mostrar en segundos para mayor claridad
        signo = "+" if diferencia_segundos >= 0 else "-"
        st.write(f"Total en segundos: {signo}{abs(diferencia_segundos):.3f} segundos")
    else:
        registrar_y_mostrar('warning', "⚠️ No hay informacion de sincronizacion disponible.")


def mostrar_detalles_sincronizacion_expandible():
    """
    Muestra detalles de sincronización en un contenedor expandible.
    
    Usa st.status() para crear un panel colapsable que contiene
    información detallada de la última sincronización de fecha/hora,
    incluyendo comparación de tiempos y análisis de diferencia horaria.
    
    Este diseño ahorra espacio vertical y permite al usuario
    consultar detalles solo cuando los necesita.
    """
    remote_time = obtener_estado_sync('remote_time')
    local_time = obtener_estado_sync('local_time')
    time_difference = obtener_estado_sync('time_difference')
    
    if not all([remote_time, local_time, time_difference is not None]):
        st.info("👉 No hay datos de sincronización. Ejecute 'Sincronizar Fecha y Hora' primero.")
        logger.debug("Intento de mostrar detalles sin datos de sincronización disponibles")
        return
    
    # Contenedor expandible con estado
    with st.status("🔍 Detalles de Sincronización", expanded=False) as status:
        st.write("**📡 Información de Sincronización de Fecha/Hora**")
        
        # Tabla comparativa en columnas
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "🌎 Hora Servidor SIAT (Bolivia)",
                remote_time.strftime("%H:%M:%S"),
                delta=remote_time.strftime("%Y-%m-%d")
            )
        with col2:
            st.metric(
                "💻 Hora Local",
                local_time.strftime("%H:%M:%S"),
                delta=local_time.strftime("%Y-%m-%d")
            )
        
        # Diferencia horaria con visualización condicional
        st.divider()
        diferencia_formateada = obtener_diferencia_horaria_formateada()
        diferencia_segundos = time_difference.total_seconds()
        
        if abs(diferencia_segundos) <= 5:
            st.success(f"⏱️ **Diferencia:** {diferencia_formateada} (Óptima ✓)")
        elif abs(diferencia_segundos) <= 300:
            st.info(f"⏱️ **Diferencia:** {diferencia_formateada} (Aceptable)")
        else:
            st.warning(f"⏱️ **Diferencia:** {diferencia_formateada} (Alta - Revisar)")
        
        # Advertencia especial para problemas de zona horaria
        if abs(diferencia_segundos) > 86000 and abs(diferencia_segundos) < 86400:
            st.error("🚨 **Alerta:** Diferencia cercana a 24 horas - Posible problema de zona horaria")
            logger.warning(f"Diferencia horaria sospechosa detectada: {diferencia_segundos}s (≈24h)")
        
        # Detalles técnicos en expander adicional
        with st.expander("🔧 Detalles Técnicos"):
            st.code(f"""
Diferencia total: {diferencia_segundos:+.3f} segundos
Sistema local: {"Adelantado" if diferencia_segundos > 0 else "Atrasado"}
Zona horaria remota: {remote_time.tzinfo}
Zona horaria local: {local_time.tzinfo}
Última sincronización: {obtener_estado_sync('ultima_sincronizacion', 'No disponible')}
            """)
        
        # Marcar como completado
        status.update(label="✅ Detalles mostrados", state="complete")
    
    logger.debug("Detalles de sincronización mostrados en contenedor expandible")

def crear_solicitud_sincronizacion():
    """Crear una solicitud de sincronizacion estandar."""
    disponible, mensaje_cliente, _ = estado_cliente_siat()
    if not disponible:
        raise RuntimeError(mensaje_cliente)

    SolicitudSincronizacion = client.get_type('ns0:solicitudSincronizacion')
    
    # Obtener y validar codigoPuntoVenta
    codigo_punto_venta = os.getenv("CODIGO_PUNTO_VENTA", "0")
    try:
        codigo_punto_venta = int(codigo_punto_venta)
    except (ValueError, TypeError):
        logger.warning(f"CODIGO_PUNTO_VENTA invalido ({codigo_punto_venta}), usando 0 por defecto")
        codigo_punto_venta = 0
    
    solicitud = SolicitudSincronizacion(
        codigoAmbiente=int(os.getenv("CODIGO_AMBIENTE")),
        codigoPuntoVenta=codigo_punto_venta,
        codigoSistema=os.getenv("CODIGO_SISTEMA"),
        codigoSucursal=int(os.getenv("CODIGO_SUCURSAL")),
        cuis=os.getenv("CUIS"),
        nit=int(os.getenv("NIT"))
    )
    return solicitud

def sincronizar_parametrica(service_name, model_class):
    """
    Sincroniza datos parametricos desde el servicio SOAP.
    """
    disponible, mensaje_cliente, detalle = estado_cliente_siat()
    if not disponible:
        registrar_y_mostrar('warning', mensaje_cliente)
        if detalle:
            logger.debug("Detalle tecnico cliente SIAT: %s", detalle)
        return False

    registrar_y_mostrar('info', f"Iniciando sincronizacion de {service_name}")
    
    # Crear solicitud de sincronizacion
    solicitud = crear_solicitud_sincronizacion()
    
    try:
        # Llamar al servicio de sincronizacion
        response = getattr(client.service, service_name)(solicitud)
        
        if not response.transaccion:
            registrar_y_mostrar('error', f"Error en la transaccion SOAP para {service_name}: {response.mensajesList}")
            return False
        
        # Obtener nombre de la lista segun el mapeo correcto
        lista_nombre = service_list_map.get(service_name)
        
        # Si no esta en el mapeo, intentar con el formato generico
        if not lista_nombre:
            lista_nombre = f"lista{service_name[11:]}"
        
        # Inspeccionar la respuesta para identificar el nombre de la lista si no se encuentra
        if not hasattr(response, lista_nombre):
            # Intentar buscar el nombre correcto de la lista explorando atributos de respuesta
            atributos_posibles = [attr for attr in dir(response) if not attr.startswith('_') and not callable(getattr(response, attr))]
            listas_candidatas = [attr for attr in atributos_posibles if 
                                attr.startswith('lista') or 'lista' in attr.lower() or 
                                'codigos' in attr.lower() or attr.endswith('s')]
            
            if listas_candidatas:
                # Usar el primer candidato viable que no este vacio
                for candidato in listas_candidatas:
                    if getattr(response, candidato):
                        lista_nombre = candidato
                        # Actualizar el mapeo para futuras llamadas
                        registrar_y_mostrar('info', f"Se ha detectado el nombre de lista '{lista_nombre}' para {service_name}")
                        # Actualizar el mapeo para futuras referencias
                        service_list_map[service_name] = lista_nombre
                        break
                else:
                    lista_nombre = listas_candidatas[0]
                    logger.warning(f"Usando lista candidata '{lista_nombre}' para {service_name}, podria estar vacia")
            else:
                registrar_y_mostrar('warning', f"No se pudo identificar una lista en la respuesta para {service_name}")
                logger.warning(f"Atributos disponibles en la respuesta: {atributos_posibles}")
                return False
        
        # Obtener la lista de items
        lista_items = getattr(response, lista_nombre, [])
        
        # Si la lista esta vacia, terminar
        if not lista_items:
            registrar_y_mostrar('info', f"No hay datos para sincronizar en {service_name} (lista: {lista_nombre})")
            return True
        
        # Analizar el primer item para identificar nombres de campos reales
        primer_item = lista_items[0] if lista_items else None
        if primer_item:
            campos_encontrados = [key for key in dir(primer_item) if not key.startswith('_') and not callable(getattr(primer_item, key))]
            logger.info(f"Ejemplo de item para {service_name}: {primer_item}")
            logger.info(f"Campos encontrados en respuesta: {campos_encontrados}")
            
            # Depurar datos del primer item para diagnostico
            for campo in campos_encontrados:
                valor = getattr(primer_item, campo)
                logger.info(f"Campo: {campo}, Valor: {valor}, Tipo: {type(valor)}")
        
        # Procesar la respuesta
        db = next(get_db())
        try:
            # Obtener el campo clave para este modelo
            campos_clave = model_key_fields.get(model_class)
            if not campos_clave:
                campos_posibles = [col.name for col in model_class.__table__.columns if col.primary_key or col.unique]
                if campos_posibles:
                    campos_clave = campos_posibles[0]
                    logger.info(f"Campo clave determinado automaticamente para {service_name}: {campos_clave}")
            
            # Definir campos requeridos basados en restricciones NOT NULL de la base de datos
            campos_requeridos = []
            for col in model_class.__table__.columns:
                if not col.nullable and not col.primary_key and col.name not in ('fecha_creacion', 'fecha_sincronizacion', 'estado_sincronizacion'):
                    campos_requeridos.append(col.name)
            
            # Obtener todos los campos del modelo para mapeado
            campos_modelo = [col.name for col in model_class.__table__.columns]
            logger.info(f"Campos del modelo para {service_name}: {campos_modelo}")
            logger.info(f"Campos requeridos para {service_name}: {campos_requeridos}")
            
            # Contador para estadisticas
            nuevos = 0
            actualizados = 0
            omitidos = 0
            duplicados_respuesta = 0

            # Cache de elementos creados en esta sesion para evitar duplicados cuando autoflush esta desactivado
            items_creados = {}
            
            # Preparar mapeo entre nombres de campos SOAP y nombres de campos SQL
            campo_soap_a_sql = {
                'codigo': 'codigoClasificador',
                'codigoMensaje': 'codigoClasificador',
                'codigoClasificador': 'codigoClasificador',
                'descripcion': 'descripcion',
                # Mapeos especificos para TipoPuntoVenta
                'codigoPuntoVenta': 'codigoClasificador',
                'descripcionPuntoVenta': 'descripcion',
                # Mapeos generales para todos los servicios
                'codigoActividad': 'codigoActividad',
                'codigoProducto': 'codigoProducto',
                'codigoDocumentoSector': 'codigoDocumentoSector',
                'tipoDocumentoSector': 'descripcion',
            }
            
            # Diccionario para valores por defecto para campos requeridos
            valores_por_defecto = {
                'codigoClasificador': '0',
                'descripcion': 'Sin descripcion',
            }
            
            for item in lista_items:
                # Mapear todos los atributos del objeto zeep a un diccionario
                item_dict = {}
                for campo in dir(item):
                    if not campo.startswith('_') and not callable(getattr(item, campo)):
                        valor = getattr(item, campo)
                        item_dict[campo] = valor
                
                # Debug para ver campos en el item actual
                logger.debug(f"Campos originales en item SOAP: {list(item_dict.keys())}")
                
                # Aplicar mapeos de nombres si es necesario
                item_mapeado = {}
                for soap_name, value in item_dict.items():
                    # Usar el nombre mapeado si existe, o el original
                    sql_name = campo_soap_a_sql.get(soap_name, soap_name)
                    
                    # Verificar si el valor es una lista y convertirlo a string
                    if isinstance(value, list):
                        # Si el campo es 'nandina' u otro campo TEXT
                        if sql_name == 'nandina' or (hasattr(model_class, sql_name) and 
                                                   hasattr(getattr(model_class, sql_name), 'type') and
                                                   isinstance(getattr(model_class, sql_name).type, Text)):
                            value = ', '.join(str(item) for item in value if item is not None)
                            logger.info(f"Campo {sql_name} convertido de lista a string: {value}")
                    
                    item_mapeado[sql_name] = value
                
                # Para los campos requeridos que no estan presentes, usar valores por defecto
                for campo in campos_requeridos:
                    if campo not in item_mapeado or item_mapeado[campo] is None:
                        if campo in valores_por_defecto:
                            item_mapeado[campo] = valores_por_defecto[campo]
                            logger.info(f"Aplicando valor por defecto para campo {campo}: {valores_por_defecto[campo]}")
                
                # Reemplazar item_dict con los campos ya mapeados
                item_dict = item_mapeado
                
                # Debug: Mostrar informacion del item
                logger.debug(f"Item para {service_name} despues del mapeo: {item_dict}")
                
                # Verificar campos requeridos
                datos_validos = True
                campos_faltantes = []
                
                for campo in campos_requeridos:
                    # Si el campo no existe en el diccionario o es nulo
                    if campo not in item_dict or item_dict[campo] is None:
                        campos_faltantes.append(campo)
                        datos_validos = False
                
                if not datos_validos:
                    logger.warning(f"Omitiendo registro en {service_name} - Campos faltantes o nulos: {campos_faltantes}")
                    logger.warning(f"Datos del item: {item_dict}")
                    logger.warning(f"Campos disponibles en item: {list(item_dict.keys())}")
                    omitidos += 1
                    continue
                
                # Filtrar el diccionario para incluir solo campos existentes en el modelo
                item_dict_filtrado = {k: v for k, v in item_dict.items() if k in campos_modelo}

                # Normalizar valores de columnas de texto y preparar una clave identificadora
                for clave, valor in list(item_dict_filtrado.items()):
                    columna = model_class.__table__.columns.get(clave)
                    if columna is not None and isinstance(columna.type, (String, Text)) and valor is not None:
                        item_dict_filtrado[clave] = str(valor)

                clave_actual = None
                if campos_clave:
                    if isinstance(campos_clave, list):
                        valores_clave = []
                        for campo in campos_clave:
                            valor_campo = item_dict_filtrado.get(campo)
                            if valor_campo is None:
                                valores_clave = []
                                break
                            valores_clave.append(str(valor_campo))
                        if valores_clave:
                            clave_actual = tuple(valores_clave)
                    else:
                        valor_campo = item_dict_filtrado.get(campos_clave)
                        if valor_campo is not None:
                            clave_actual = str(valor_campo)

                # Construir el filtro segun el tipo de campo clave
                db_item = None
                if isinstance(campos_clave, list):
                    # Manejo de claves compuestas
                    filtros = []
                    for campo in campos_clave:
                        if campo in item_dict_filtrado and item_dict_filtrado[campo] is not None:
                            filtros.append(getattr(model_class, campo) == item_dict_filtrado[campo])
                    
                    if filtros:
                        db_item = db.query(model_class).filter(*filtros).first()
                else:
                    # Manejo de clave simple
                    if campos_clave in item_dict_filtrado and item_dict_filtrado[campos_clave] is not None:
                        db_item = db.query(model_class).filter(getattr(model_class, campos_clave) == item_dict_filtrado[campos_clave]).first()

                # Si ya existe, actualizar
                if db_item:
                    for key, value in item_dict_filtrado.items():
                        if hasattr(db_item, key):
                            setattr(db_item, key, value)
                    db_item.fecha_sincronizacion = func.now()
                    db_item.estado_sincronizacion = 'Exitoso'
                    actualizados += 1
                else:
                    if clave_actual and clave_actual in items_creados:
                        duplicados_respuesta += 1
                        objeto_existente = items_creados[clave_actual]
                        for key, value in item_dict_filtrado.items():
                            if hasattr(objeto_existente, key):
                                setattr(objeto_existente, key, value)
                        logger.warning(f"Elemento duplicado detectado en respuesta de {service_name} para clave {clave_actual}; se actualizo el registro ya agregado en esta sesion.")
                        continue
                    try:
                        # Crear nuevo item
                        new_item = model_class()
                        for key, value in item_dict_filtrado.items():
                            if hasattr(new_item, key):
                                setattr(new_item, key, value)
                        new_item.fecha_sincronizacion = func.now()
                        new_item.estado_sincronizacion = 'Exitoso'
                        db.add(new_item)
                        if clave_actual:
                            items_creados[clave_actual] = new_item
                        nuevos += 1
                    except Exception as e:
                        logger.error(f"Error al crear nuevo item en {service_name}: {e}")
                        logger.error(f"Datos del item: {item_dict_filtrado}")
                        omitidos += 1
            
            db.commit()
            mensaje_resumen = f"Sincronizacion de {service_name} completada: {nuevos} nuevos, {actualizados} actualizados"
            if omitidos > 0:
                mensaje_resumen += f", {omitidos} omitidos por datos invalidos"
            if duplicados_respuesta > 0:
                mensaje_resumen += f", {duplicados_respuesta} duplicados en la respuesta ignorados"
            
            # Informar el resumen tanto en la UI como en el log
            registrar_y_mostrar('success', f"[OK] {mensaje_resumen}")
            return True
            
        except Exception as e:
            db.rollback()
            registrar_y_mostrar('error', f"Error al procesar datos de {service_name}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
        finally:
            db.close()
            
    except Exception as e:
        registrar_y_mostrar('error', f"Error al sincronizar {service_name}: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def sincronizar_todo_con_progreso():
    """
    Sincroniza todos los servicios mostrando progreso en tiempo real.
    
    Esta función reemplaza el botón "Sincronizar Todo" con una interfaz
    mejorada que incluye:
    - Barra de progreso visual
    - Métricas en tiempo real (exitosos/fallidos/tiempo)
    - Notificaciones toast por servicio
    - Celebración visual si todo es exitoso
    
    Usa las nuevas capacidades de Streamlit 1.49.0+ para proporcionar
    una experiencia de usuario superior durante la sincronización masiva.
    """
    logger.info("Iniciando sincronización completa con indicadores de progreso")
    
    # Contenedor para métricas en tiempo real
    metricas_container = st.empty()
    progress_bar = st.progress(0, text="🚀 Iniciando sincronización completa...")
    
    # Inicializar contadores
    exitosos = 0
    fallidos = 0
    total_servicios = len(service_model_map) + 1  # +1 por fecha/hora
    inicio_tiempo = datetime.now(pytz.utc)
    
    # Función auxiliar para actualizar métricas
    def actualizar_metricas_progreso(procesados):
        tiempo_transcurrido = (datetime.now(pytz.utc) - inicio_tiempo).total_seconds()
        with metricas_container.container():
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "✅ Exitosos", 
                    exitosos, 
                    delta=f"{(exitosos/total_servicios)*100:.0f}%",
                    delta_color="normal"
                )
            with col2:
                st.metric(
                    "❌ Fallidos", 
                    fallidos,
                    delta=f"{(fallidos/total_servicios)*100:.0f}%" if fallidos > 0 else "0%",
                    delta_color="inverse"
                )
            with col3:
                st.metric(
                    "📊 Progreso",
                    f"{procesados}/{total_servicios}",
                    delta=f"{(procesados/total_servicios)*100:.1f}%"
                )
            with col4:
                st.metric(
                    "⏱️ Tiempo",
                    f"{tiempo_transcurrido:.1f}s",
                    delta=f"{tiempo_transcurrido/procesados:.1f}s/serv" if procesados > 0 else "0s/serv"
                )
    
    try:
        # Paso 1: Sincronizar fecha y hora
        progress_bar.progress(0, text="🕐 Sincronizando fecha y hora...")
        resultado_fecha = sincronizar_fecha_hora()
        
        if resultado_fecha:
            exitosos += 1
            notificar('success', "⏰ Fecha/hora sincronizada", usar_toast=True)
        else:
            fallidos += 1
            notificar('error', "⏰ Error en sincronización de fecha/hora", usar_toast=True)
        
        actualizar_metricas_progreso(1)
        
        # Paso 2: Sincronizar servicios paramétricos
        procesados = 1
        for service_name, model_class in service_model_map.items():
            # Actualizar barra de progreso
            progreso = procesados / total_servicios
            progress_bar.progress(
                progreso, 
                text=f"📡 Sincronizando {service_name} ({procesados}/{total_servicios})..."
            )
            
            # Ejecutar sincronización
            resultado = sincronizar_parametrica(service_name, model_class)
            
            # Registrar resultado
            if resultado:
                exitosos += 1
                # Toast solo para servicios críticos o cada 3 servicios
                if procesados % 3 == 0 or 'Documento' in service_name or 'Moneda' in service_name:
                    notificar('success', f"✓ {service_name}", usar_toast=True)
            else:
                fallidos += 1
                # Siempre notificar errores
                notificar('error', f"✗ {service_name}", usar_toast=True)
            
            procesados += 1
            actualizar_metricas_progreso(procesados)
        
        # Finalización
        progress_bar.progress(1.0, text="✅ Sincronización completa!")
        tiempo_total = (datetime.now(pytz.utc) - inicio_tiempo).total_seconds()
        
        # Resumen final
        if fallidos == 0:
            st.success(f"🎉 ¡Sincronización perfecta! {exitosos} servicios en {tiempo_total:.1f}s")
            st.balloons()  # Celebración visual
            logger.info(f"Sincronización completa exitosa: {exitosos}/{total_servicios} en {tiempo_total:.1f}s")
        elif exitosos > fallidos:
            st.warning(f"⚠️ Sincronización con advertencias: {exitosos} exitosos, {fallidos} fallidos en {tiempo_total:.1f}s")
            logger.warning(f"Sincronización parcial: {exitosos} exitosos, {fallidos} fallidos")
        else:
            st.error(f"❌ Sincronización con errores: {exitosos} exitosos, {fallidos} fallidos en {tiempo_total:.1f}s")
            logger.error(f"Sincronización con errores: {exitosos} exitosos, {fallidos} fallidos")
        
        # Actualizar estado de última sincronización
        actualizar_estado_sync('ultima_sincronizacion', datetime.now(pytz.utc))
        
        return exitosos, fallidos
        
    except Exception as e:
        progress_bar.progress(0, text="❌ Error durante sincronización")
        error_msg = f"Error crítico en sincronización completa: {str(e)}"
        notificar('error', error_msg, usar_toast=False)
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return exitosos, fallidos


def main():
    """
    Función principal del módulo de sincronización - REFACTORIZADA FASE 3.
    
    Presenta una interfaz modernizada con tabs para sincronizar datos
    con el servidor SIAT. Incluye:
    - Panel de métricas superior siempre visible
    - Indicador de estado en sidebar
    - Tab 1: Sincronización rápida (todo a la vez)
    - Tab 2: Sincronización manual (servicio por servicio)
    - Notificaciones toast no invasivas
    - Detalles expandibles de última sincronización
    
    Versión: Fase 3 - Streamlit 1.49.0+
    """
    st.title("🔄 Sincronización de Datos SIAT")

    # Inicializar el estado de sincronización
    inicializar_estado_sincronizacion()
    
    # ========== VERIFICACIÓN INICIAL AUTOMÁTICA ==========
    # Ejecutar verificación al cargar la página para tener estado real
    # IMPORTANTE: Esto se ejecuta UNA VEZ gracias al caché de 30s del communication_manager
    try:
        from communication_manager import communication_manager
        # Esta llamada usa el caché, por lo que es prácticamente gratis
        resultado_inicial = communication_manager.verificar_comunicacion_completa()
        logger.debug(f"Verificación inicial automática completada: {resultado_inicial.get('estado_general')}")
    except Exception as e:
        logger.warning(f"No se pudo ejecutar verificación inicial automática: {e}")
    
    # ========== FASE 3: PANEL DE MÉTRICAS SUPERIOR ==========
    # Siempre visible, proporciona visibilidad instantánea del estado
    mostrar_panel_metricas()
    
    st.markdown("---")
    
    # ========== FASE 3: INDICADOR COMPACTO EN SIDEBAR ==========
    with st.sidebar:
        mostrar_indicador_estado_sidebar()
    
    # ========== FASE 3: DETALLES EXPANDIBLES DE SINCRONIZACIÓN ==========
    # Reemplaza el botón antiguo con contenedor colapsable
    mostrar_detalles_sincronizacion_expandible()
    
    st.markdown("---")
    
    # Verificar disponibilidad del cliente SIAT
    disponible, mensaje_cliente, detalle = estado_cliente_siat()
    if not disponible:
        notificar('warning', mensaje_cliente, usar_toast=False)
        st.info("🔌 El sistema se encuentra en modo offline; no es posible sincronizar sin conexión a Internet.")
        st.markdown(
            "**Posibles soluciones:**\n"
            "- Verifique su conexión de red\n"
            "- Intente nuevamente cuando el enlace a SIAT esté disponible\n"
            "- Si el problema persiste estando en línea, revise la configuración de variables de entorno"
        )
        if detalle:
            with st.expander("🔧 Detalle Técnico"):
                st.code(detalle)
        st.stop()

    # Verificar comunicación antes de mostrar opciones de sincronización
    exito, mensaje = verificar_comunicacion()
    
    if not exito:
        notificar('error', f"Error de comunicación con el servidor remoto: {mensaje}", usar_toast=False)
        st.error("❌ No se pueden realizar sincronizaciones debido a problemas de comunicación.")
        st.info("💡 Use el botón de 'Verificar Conexión' en el sidebar para intentar reconectar")
        st.stop()
    
    # Si llegamos aquí, la comunicación es exitosa
    notificar('success', "🌐 Conexión exitosa con el servidor SIAT", usar_toast=True)
    
    # ========== FASE 3: INTERFAZ CON TABS ==========
    tab_rapida, tab_manual = st.tabs(["🚀 Sincronización Rápida", "🔧 Sincronización Manual"])
    
    # ===== TAB 1: SINCRONIZACIÓN RÁPIDA =====
    with tab_rapida:
        st.header("⚡ Sincronización Completa")
        st.info(
            "**Esta opción sincroniza todos los servicios paramétricos** incluyendo:\n"
            "- ⏰ Fecha y hora del servidor\n"
            "- 📋 Todas las tablas paramétricas (tipos de documento, monedas, actividades, etc.)\n\n"
            "**Tiempo estimado:** 30-90 segundos dependiendo de la conexión"
        )
        
        if st.button('🚀 Sincronizar Todo Ahora', type="primary", use_container_width=True):
            logger.info("Usuario inició sincronización completa desde Tab Rápida")
            exitosos, fallidos = sincronizar_todo_con_progreso()
            
            # Actualizar el panel de métricas después de la sincronización
            if exitosos > 0:
                mostrar_panel_metricas()
    
    # ===== TAB 2: SINCRONIZACIÓN MANUAL =====
    with tab_manual:
        st.header("🛠️ Sincronización Selectiva")
        st.info(
            "**Sincronice servicios individuales** cuando:\n"
            "- Necesite actualizar solo un tipo de datos específico\n"
            "- Quiera verificar un servicio particular\n"
            "- Desee un control más granular del proceso"
        )
        
        # Crear lista de servicios con descripciones amigables
        servicios_opciones = ['⏰ Fecha y Hora del Servidor'] + [
            f"📊 {name.replace('sincronizar', '').replace('Parametrica', '')}" 
            for name in service_model_map.keys()
        ]
        servicios_valores = ['sincronizarFechaHora'] + list(service_model_map.keys())
        
        selected_service_idx = st.selectbox(
            "🎯 Seleccione el servicio a sincronizar:",
            range(len(servicios_opciones)),
            format_func=lambda x: servicios_opciones[x],
            help="Elija un servicio específico para actualizar solo esos datos"
        )
        
        selected_service = servicios_valores[selected_service_idx]

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button('▶️ Sincronizar Servicio Seleccionado', use_container_width=True):
                logger.info(f"Usuario inició sincronización manual de: {selected_service}")
                
                if selected_service == 'sincronizarFechaHora':
                    with st.spinner("⏰ Sincronizando fecha y hora..."):
                        resultado = sincronizar_fecha_hora()
                        if resultado:
                            notificar('success', "✅ Fecha/hora sincronizada correctamente", usar_toast=True)
                            mostrar_detalles_sincronizacion_expandible()
                        else:
                            notificar('error', "❌ Error al sincronizar fecha/hora", usar_toast=False)
                else:
                    with st.spinner(f"📡 Sincronizando {selected_service}..."):
                        resultado = sincronizar_parametrica(selected_service, service_model_map[selected_service])
                        if resultado:
                            notificar('success', f"✅ {selected_service} sincronizado correctamente", usar_toast=True)
                        else:
                            notificar('error', f"❌ Error en {selected_service}", usar_toast=False)
                
                # Actualizar métricas después de cualquier sincronización
                mostrar_panel_metricas()
        
        with col2:
            if st.button('🔄', help="Refrescar lista de servicios"):
                st.rerun()


if __name__ == "__main__":
    main()
