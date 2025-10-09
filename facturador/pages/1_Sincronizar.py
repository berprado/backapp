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
    global remote_time, local_time, time_difference
    
    disponible, mensaje_cliente, _ = estado_cliente_siat()
    if not disponible:
        registrar_y_mostrar('warning', mensaje_cliente)
        return False

    registrar_y_mostrar('info', "Iniciando sincronizacion de Fecha y Hora")
    SolicitudSincronizacion = client.get_type('ns0:solicitudSincronizacion')
    solicitud = SolicitudSincronizacion(
        codigoAmbiente=int(os.getenv("CODIGO_AMBIENTE")),
        codigoPuntoVenta=int(os.getenv("CODIGO_PUNTO_VENTA")),
        codigoSistema=os.getenv("CODIGO_SISTEMA"),
        codigoSucursal=int(os.getenv("CODIGO_SUCURSAL")),
        cuis=os.getenv("CUIS"),
        nit=int(os.getenv("NIT"))
    )
    
    logger.debug(f"Solicitud creada: {solicitud}")
    
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

        # Calcular la diferencia horaria correctamente - modificado
        diferencia_segundos, time_difference = calcular_diferencia_horaria(remote_time, local_time)

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
                time_difference = timedelta(seconds=0)
                diferencia_segundos = 0
                registrar_y_mostrar('success', " Diferencia horaria corregida manualmente.")

        logger.debug(f"Diferencia de tiempo calculada: {time_difference}")

        # Guardar resultado en la base de datos
        try:
            db = next(get_db())
            try:
                sync_record = db.query(SincronizacionEstado).first()
                if not sync_record:
                    sync_record = SincronizacionEstado()
                    db.add(sync_record)
                
                # Actualizar fecha de sincronizacion
                sync_record.ultima_sincronizacion = datetime.now(pytz.utc)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Error al guardar sincronizacion: {e}")
                # Guardamos la informacion en la sesion de Streamlit como respaldo
                st.session_state['ultima_sincronizacion'] = datetime.now(pytz.utc)
                st.session_state['remote_time'] = remote_time
                st.session_state['local_time'] = local_time
                st.session_state['time_difference'] = time_difference
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error al conectar con la base de datos: {e}")
            # Guardamos la informacion en la sesion de Streamlit como respaldo
            st.session_state['ultima_sincronizacion'] = datetime.now(pytz.utc)
            st.session_state['remote_time'] = remote_time
            st.session_state['local_time'] = local_time
            st.session_state['time_difference'] = time_difference
            
        registrar_y_mostrar('success', " Sincronizacion de Fecha y Hora completada.")
        mostrar_informacion_sincronizacion()
        return True

    except Exception as e:
        error_msg = f"Error al sincronizar Fecha y Hora: {str(e)}"
        registrar_y_mostrar('error', error_msg)
        logger.error(traceback.format_exc())
        return False

def mostrar_informacion_sincronizacion():
    if remote_time and local_time and time_difference is not None:
        registrar_y_mostrar('info', "Informacion de sincronizacion:")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Hora del servidor remoto (Bolivia):")
            st.write(remote_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        with col2:
            st.write("Hora local:")
            st.write(local_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        
        # Formateamos la diferencia de tiempo de manera mas clara
        diferencia_segundos = time_difference.total_seconds()
        st.write("Diferencia de tiempo:")
        
        # Si es cerca de 24 horas, mostrar una advertencia
        if abs(diferencia_segundos) > 86000 and abs(diferencia_segundos) < 86400:
            registrar_y_mostrar('warning', " La diferencia parece ser de aproximadamente 24 horas, lo que sugiere un problema con la zona horaria.")
        
        # Mostrar la diferencia en un formato mas amigable
        minutos, segundos = divmod(abs(diferencia_segundos), 60)
        horas, minutos = divmod(minutos, 60)
        dias, horas = divmod(horas, 24)
        
        signo = "+" if diferencia_segundos >= 0 else "-"
        
        if dias > 0:
            st.write(f"{signo}{int(dias)} dias, {int(horas):02}:{int(minutos):02}:{segundos:.3f}")
        elif horas > 0:
            st.write(f"{signo}{int(horas):02}:{int(minutos):02}:{segundos:.3f}")
        else:
            st.write(f"{signo}{int(minutos):02}:{segundos:.3f}")
            
        # Tambien mostrar en segundos para mayor claridad
        st.write(f"Total en segundos: {signo}{abs(diferencia_segundos):.3f} segundos")
    else:
        registrar_y_mostrar('warning', "No hay informacion de sincronizacion disponible.")

def crear_solicitud_sincronizacion():
    """Crear una solicitud de sincronizacion estandar."""
    disponible, mensaje_cliente, _ = estado_cliente_siat()
    if not disponible:
        raise RuntimeError(mensaje_cliente)

    SolicitudSincronizacion = client.get_type('ns0:solicitudSincronizacion')
    solicitud = SolicitudSincronizacion(
        codigoAmbiente=int(os.getenv("CODIGO_AMBIENTE")),
        codigoPuntoVenta=int(os.getenv("CODIGO_PUNTO_VENTA")),
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

def main():
    st.title("Sincronizar Datos")

    # Asegurarse de que las variables globales esten inicializadas
    global remote_time, local_time, time_difference

    disponible, mensaje_cliente, detalle = estado_cliente_siat()
    if not disponible:
        registrar_y_mostrar('warning', mensaje_cliente)
        st.info("El sistema se encuentra en modo offline; no es posible sincronizar sin conexion a Internet.")
        st.markdown(
            "- Verifique su conexion de red.\n"
            "- Intente nuevamente cuando el enlace a SIAT este disponible.\n"
            "- Si el problema persiste estando en linea, revise la configuracion de variables de entorno."
        )
        if detalle:
            st.caption(f"Detalle tecnico: {detalle}")
        st.stop()

    # Verificar comunicacion antes de mostrar opciones de sincronizacion
    exito, mensaje = verificar_comunicacion()
    if exito:
        registrar_y_mostrar('success', "[OK] Conexion exitosa con el servidor remoto.")

        if st.button('Sincronizar Todo'):
            sincronizar_fecha_hora()
            with st.spinner("Sincronizando tablas parametricas..."):
                resultados = []
                for service_name, model_class in service_model_map.items():
                    resultado = sincronizar_parametrica(service_name, model_class)
                    resultados.append((service_name, resultado))

                # Mostrar resumen
                st.subheader("Resumen de sincronizacion")
                for service_name, exito in resultados:
                    icon = "[OK]" if exito else "[ERROR]"
                    # Mostrar un resumen en la interfaz y registrar en el log
                    st.text(f"{icon} {service_name}")
                    logger.info(f"Resultado sincronizacion {service_name}: {'Exitoso' if exito else 'Fallido'}")

                registrar_y_mostrar('success', "Todas las sincronizaciones completadas.")

        # Opcion para sincronizar servicios individuales
        selected_service = st.selectbox(
            "Seleccione un servicio para sincronizar",
            ['sincronizarFechaHora'] + list(service_model_map.keys())
        )

        if st.button('Sincronizar Servicio Seleccionado'):
            if selected_service == 'sincronizarFechaHora':
                sincronizar_fecha_hora()
            else:
                with st.spinner(f"Sincronizando {selected_service}..."):
                    resultado = sincronizar_parametrica(selected_service, service_model_map[selected_service])
                    if resultado:
                        registrar_y_mostrar('success', f"[OK] Sincronizacion de {selected_service} completada.")

        if st.button('Mostrar informacion de sincronizacion'):
            mostrar_informacion_sincronizacion()
    else:
        registrar_y_mostrar('error', f"Error de comunicacion con el servidor remoto: {mensaje}")
        registrar_y_mostrar('warning', "No se pueden realizar sincronizaciones debido a problemas de comunicacion.")


if __name__ == "__main__":
    main()
