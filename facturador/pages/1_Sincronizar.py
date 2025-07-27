import os
import sys
import logging
import traceback
import streamlit as st
from zeep import Client
import requests
from dotenv import load_dotenv
from sqlalchemy import func, Text
from datetime import datetime, timezone, timedelta
import pytz
import tzlocal


# Agregar rutas a sys.path para acceder a los módulos del proyecto
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
facturador_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.extend([root_dir, facturador_dir])

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

# Cargar variables de entorno desde el directorio raíz
load_dotenv(os.path.join(root_dir, '.env'))

# Configuración de logging con codificación UTF-8
# Verificar si ya existe un handler para evitar duplicados
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Reiniciar los handlers del logger root para evitar duplicados
root_logger = logging.getLogger()
if root_logger.handlers:
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

# Crear un nuevo logger específico para esta aplicación en lugar de usar el root logger
logger = logging.getLogger('facturador.sincronizacion')
logger.setLevel(logging.DEBUG)

# Asegurarse de que no tenga handlers previos
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

# Crear un handler para archivo con codificación UTF-8
file_handler = logging.FileHandler(
    os.path.join(log_dir, 'sincronizacion_detallada.log'),
    encoding='utf-8'  # Codificación UTF-8 para soportar emojis
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'))
logger.addHandler(file_handler)

# Asegurar que los logs no se propaguen al logger padre para evitar duplicados
logger.propagate = False

# Configuración del cliente SOAP (fuera de la función para reutilizarlo)
wsdl_url = os.getenv("WSDL_URL_SYNC")
api_key = os.getenv("API_KEY")
client = Client(wsdl_url)
session = requests.Session()
session.headers.update({"apikey": api_key})
client.transport.session = session

# Variables globales para sincronización de fecha y hora
remote_time = None
local_time = None
time_difference = None

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

# Configuración de campos clave para cada modelo
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
            return True, "Comunicación exitosa con código 926"
        else:
            return False, "Fallo en la comunicación"
    except requests.exceptions.RequestException as e:
        return False, f"Error de comunicación: {e}"

def calcular_diferencia_horaria(remote_time, local_time):
    """
    Calcula la diferencia horaria entre dos momentos en el tiempo.
    Devuelve la diferencia en segundos y un objeto timedelta.
    """
    # Asegurar que ambos tiempos estén en UTC para una comparación correcta
    remote_time_utc = remote_time.astimezone(pytz.utc)
    local_time_utc = local_time.astimezone(pytz.utc)
    
    # Calculamos tanto la diferencia en segundos como el objeto timedelta
    diferencia_timedelta = remote_time_utc - local_time_utc
    diferencia_segundos = diferencia_timedelta.total_seconds()
    
    # Si la diferencia es casi un día completo, podría ser un problema de zona horaria
    if abs(diferencia_segundos) > 86000 and abs(diferencia_segundos) < 86400:
        # Probablemente hay un problema con la interpretación de la zona horaria
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
    
    st.text("Iniciando sincronización de Fecha y Hora")
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
            error_msg = "Error en la transacción SOAP para sincronizarFechaHora"
            st.error(error_msg)
            logger.error(error_msg)
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
            st.error("Error al obtener la fecha del servidor. Sincronización fallida.")
            return False
        
        # Obtener la hora local actual con su zona horaria
        local_time = datetime.now(tzlocal.get_localzone())
        
        logger.debug(f"Hora remota (Bolivia): {remote_time}")
        logger.debug(f"Hora local: {local_time}")

        # Calcular la diferencia horaria correctamente - modificado
        diferencia_segundos, time_difference = calcular_diferencia_horaria(remote_time, local_time)

        # Verificar si la diferencia de tiempo está en un rango razonable (5 minutos)
        tiempo_razonable = 300  # 5 minutos en segundos
        diferencia_absoluta = abs(diferencia_segundos)
        
        if diferencia_absoluta <= tiempo_razonable:
            mensaje_tiempo = f"La diferencia de tiempo está en un rango razonable ({diferencia_absoluta:.2f} segundos)"
            st.success(f"✅ {mensaje_tiempo}")
            logger.info(mensaje_tiempo)
        else:
            mensaje_tiempo = f"La diferencia de tiempo NO está en un rango razonable ({diferencia_absoluta:.2f} segundos)"
            st.warning(mensaje_tiempo)
            logger.warning(mensaje_tiempo)

        if diferencia_absoluta > 86400:  # Más de 24 horas
            logger.warning(f"Diferencia de tiempo anormal: {time_difference}. Verifique la zona horaria.")
            st.warning(f"Diferencia de tiempo anormal detectada: {time_difference}. ¿Desea corregirla?")
            
            if st.button("Corregir diferencia horaria"):
                time_difference = timedelta(seconds=0)
                diferencia_segundos = 0
                st.success("✅ Diferencia horaria corregida manualmente.")

        logger.debug(f"Diferencia de tiempo calculada: {time_difference}")

        # Guardar resultado en la base de datos
        try:
            db = next(get_db())
            try:
                sync_record = db.query(SincronizacionEstado).first()
                if not sync_record:
                    sync_record = SincronizacionEstado()
                    db.add(sync_record)
                
                # Actualizar fecha de sincronización
                sync_record.ultima_sincronizacion = datetime.now(pytz.utc)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Error al guardar sincronización: {e}")
                # Guardamos la información en la sesión de Streamlit como respaldo
                st.session_state['ultima_sincronizacion'] = datetime.now(pytz.utc)
                st.session_state['remote_time'] = remote_time
                st.session_state['local_time'] = local_time
                st.session_state['time_difference'] = time_difference
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error al conectar con la base de datos: {e}")
            # Guardamos la información en la sesión de Streamlit como respaldo
            st.session_state['ultima_sincronizacion'] = datetime.now(pytz.utc)
            st.session_state['remote_time'] = remote_time
            st.session_state['local_time'] = local_time
            st.session_state['time_difference'] = time_difference
            
        st.success("✅ Sincronización de Fecha y Hora completada.")
        mostrar_informacion_sincronizacion()
        return True

    except Exception as e:
        error_msg = f"Error al sincronizar Fecha y Hora: {str(e)}"
        st.error(error_msg)
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return False

def mostrar_informacion_sincronizacion():
    if remote_time and local_time and time_difference is not None:
        st.info("Información de sincronización:")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Hora del servidor remoto (Bolivia):")
            st.write(remote_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        with col2:
            st.write("Hora local:")
            st.write(local_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        
        # Formateamos la diferencia de tiempo de manera más clara
        diferencia_segundos = time_difference.total_seconds()
        st.write("Diferencia de tiempo:")
        
        # Si es cerca de 24 horas, mostrar una advertencia
        if abs(diferencia_segundos) > 86000 and abs(diferencia_segundos) < 86400:
            st.warning("⚠️ La diferencia parece ser de aproximadamente 24 horas, lo que sugiere un problema con la zona horaria.")
        
        # Mostrar la diferencia en un formato más amigable
        minutos, segundos = divmod(abs(diferencia_segundos), 60)
        horas, minutos = divmod(minutos, 60)
        dias, horas = divmod(horas, 24)
        
        signo = "+" if diferencia_segundos >= 0 else "-"
        
        if dias > 0:
            st.write(f"{signo}{int(dias)} días, {int(horas):02}:{int(minutos):02}:{segundos:.3f}")
        elif horas > 0:
            st.write(f"{signo}{int(horas):02}:{int(minutos):02}:{segundos:.3f}")
        else:
            st.write(f"{signo}{int(minutos):02}:{segundos:.3f}")
            
        # También mostrar en segundos para mayor claridad
        st.write(f"Total en segundos: {signo}{abs(diferencia_segundos):.3f} segundos")
    else:
        st.warning("No hay información de sincronización disponible.")

def crear_solicitud_sincronizacion():
    """Crear una solicitud de sincronización estándar."""
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
    Sincroniza datos paramétricos desde el servicio SOAP.
    """
    st.text(f"Iniciando sincronización de {service_name}")
    
    # Crear solicitud de sincronización
    solicitud = crear_solicitud_sincronizacion()
    
    try:
        # Llamar al servicio de sincronización
        response = getattr(client.service, service_name)(solicitud)
        
        if not response.transaccion:
            st.error(f"Error en la transacción SOAP para {service_name}: {response.mensajesList}")
            logger.error(f"Error en la transacción SOAP para {service_name}: {response.mensajesList}")
            return False
        
        # Obtener nombre de la lista según el mapeo correcto
        lista_nombre = service_list_map.get(service_name)
        
        # Si no está en el mapeo, intentar con el formato genérico
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
                # Usar el primer candidato viable que no esté vacío
                for candidato in listas_candidatas:
                    if getattr(response, candidato):
                        lista_nombre = candidato
                        # Actualizar el mapeo para futuras llamadas
                        st.info(f"Detectado nombre de lista '{lista_nombre}' para {service_name}")
                        logger.info(f"Se ha detectado el nombre de lista '{lista_nombre}' para {service_name}")
                        # Actualizar el mapeo para futuras referencias
                        service_list_map[service_name] = lista_nombre
                        break
                else:
                    lista_nombre = listas_candidatas[0]
                    logger.warning(f"Usando lista candidata '{lista_nombre}' para {service_name}, podría estar vacía")
            else:
                st.warning(f"No se pudo identificar una lista en la respuesta para {service_name}")
                logger.warning(f"No se pudo identificar una lista en la respuesta. Atributos disponibles: {atributos_posibles}")
                return False
        
        # Obtener la lista de items
        lista_items = getattr(response, lista_nombre, [])
        
        # Si la lista está vacía, terminar
        if not lista_items:
            st.info(f"No hay datos para sincronizar en {service_name} (lista: {lista_nombre})")
            return True
        
        # Analizar el primer ítem para identificar nombres de campos reales
        primer_item = lista_items[0] if lista_items else None
        if primer_item:
            campos_encontrados = [key for key in dir(primer_item) if not key.startswith('_') and not callable(getattr(primer_item, key))]
            logger.info(f"Ejemplo de item para {service_name}: {primer_item}")
            logger.info(f"Campos encontrados en respuesta: {campos_encontrados}")
            
            # Depurar datos del primer item para diagnóstico
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
                    logger.info(f"Campo clave determinado automáticamente para {service_name}: {campos_clave}")
            
            # Definir campos requeridos basados en restricciones NOT NULL de la base de datos
            campos_requeridos = []
            for col in model_class.__table__.columns:
                if not col.nullable and not col.primary_key and col.name not in ('fecha_creacion', 'fecha_sincronizacion', 'estado_sincronizacion'):
                    campos_requeridos.append(col.name)
            
            # Obtener todos los campos del modelo para mapeado
            campos_modelo = [col.name for col in model_class.__table__.columns]
            logger.info(f"Campos del modelo para {service_name}: {campos_modelo}")
            logger.info(f"Campos requeridos para {service_name}: {campos_requeridos}")
            
            # Contador para estadísticas
            nuevos = 0
            actualizados = 0
            omitidos = 0
            
            # Preparar mapeo entre nombres de campos SOAP y nombres de campos SQL
            campo_soap_a_sql = {
                'codigo': 'codigoClasificador',
                'codigoMensaje': 'codigoClasificador',
                'codigoClasificador': 'codigoClasificador',
                'descripcion': 'descripcion',
                # Mapeos específicos para TipoPuntoVenta
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
                'descripcion': 'Sin descripción',
            }
            
            for item in lista_items:
                # Mapear todos los atributos del objeto zeep a un diccionario
                item_dict = {}
                for campo in dir(item):
                    if not campo.startswith('_') and not callable(getattr(item, campo)):
                        valor = getattr(item, campo)
                        item_dict[campo] = valor
                
                # Debug para ver campos en el ítem actual
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
                
                # Para los campos requeridos que no están presentes, usar valores por defecto
                for campo in campos_requeridos:
                    if campo not in item_mapeado or item_mapeado[campo] is None:
                        if campo in valores_por_defecto:
                            item_mapeado[campo] = valores_por_defecto[campo]
                            logger.info(f"Aplicando valor por defecto para campo {campo}: {valores_por_defecto[campo]}")
                
                # Reemplazar item_dict con los campos ya mapeados
                item_dict = item_mapeado
                
                # Debug: Mostrar información del item
                logger.debug(f"Item para {service_name} después del mapeo: {item_dict}")
                
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
                
                # Construir el filtro según el tipo de campo clave
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
                    try:
                        # Crear nuevo item
                        new_item = model_class()
                        for key, value in item_dict_filtrado.items():
                            if hasattr(new_item, key):
                                setattr(new_item, key, value)
                        new_item.fecha_sincronizacion = func.now()
                        new_item.estado_sincronizacion = 'Exitoso'
                        db.add(new_item)
                        nuevos += 1
                    except Exception as e:
                        logger.error(f"Error al crear nuevo item en {service_name}: {e}")
                        logger.error(f"Datos del item: {item_dict_filtrado}")
                        omitidos += 1
            
            db.commit()
            mensaje_resumen = f"Sincronización de {service_name} completada: {nuevos} nuevos, {actualizados} actualizados"
            if omitidos > 0:
                mensaje_resumen += f", {omitidos} omitidos por datos inválidos"
            
            # Usar texto plano en lugar de emojis para evitar problemas de codificación
            st.success(f"✅ {mensaje_resumen}")
            logger.info(mensaje_resumen)  # Sin emoji para evitar problemas de codificación
            return True
            
        except Exception as e:
            db.rollback()
            st.error(f"Error al procesar datos de {service_name}: {str(e)}")
            logger.error(f"Error al procesar datos de {service_name}: {traceback.format_exc()}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        st.error(f"Error al sincronizar {service_name}: {str(e)}")
        logger.error(f"Error al sincronizar {service_name}: {traceback.format_exc()}")
        return False

def main():
    st.title("Sincronizar Datos")
    
    # Asegurarse de que las variables globales estén inicializadas
    global remote_time, local_time, time_difference
    
    # Verificar comunicación antes de mostrar opciones de sincronización
    exito, mensaje = verificar_comunicacion()
    if (exito):
        st.success(f"✅ Conexión exitosa con el servidor remoto.")
        
        if st.button('Sincronizar Todo'):
            sincronizar_fecha_hora()
            with st.spinner("Sincronizando tablas paramétricas..."):
                resultados = []
                for service_name, model_class in service_model_map.items():
                    resultado = sincronizar_parametrica(service_name, model_class)
                    resultados.append((service_name, resultado))
                
                # Mostrar resumen
                st.subheader("Resumen de sincronización")
                for service_name, exito in resultados:
                    icon = "✅" if exito else "❌"
                    st.text(f"{icon} {service_name}")
                    
                st.success("Todas las sincronizaciones completadas.")
        
        # Opción para sincronizar servicios individuales
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
                        st.success(f"✅ Sincronización de {selected_service} completada.")
        
        if st.button('Mostrar información de sincronización'):
            mostrar_informacion_sincronizacion()
    else:
        st.error(f"Error de comunicación con el servidor remoto: {mensaje}")
        st.warning("No se pueden realizar sincronizaciones debido a problemas de comunicación.")

if __name__ == "__main__":
    main()