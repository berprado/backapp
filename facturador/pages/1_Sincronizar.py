import os
import sys
import logging
import traceback
import streamlit as st
from zeep import Client
import requests
from dotenv import load_dotenv
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
import pytz
import tzlocal

# Agregar rutas a sys.path para acceder a los módulos del proyecto
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
facturador_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.extend([root_dir, facturador_dir])

# Importar desde database.py en el directorio facturador
from facturador.database import get_db, Base

# Importar todos los modelos necesarios con nombres completamente cualificados
from facturador.models import (
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

# Configuración de logging con mayor detalle
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, 'sincronizacion_detallada.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
)

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
    # Asegurar que ambos tiempos estén en UTC para una comparación correcta
    remote_time_utc = remote_time.astimezone(pytz.utc)
    local_time_utc = local_time.astimezone(pytz.utc)
    return remote_time_utc - local_time_utc

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
    
    logging.debug(f"Solicitud creada: {solicitud}")
    
    try:
        logging.debug("Enviando solicitud al servicio SOAP")
        response = client.service.sincronizarFechaHora(solicitud)
        logging.debug(f"Respuesta recibida: {response}")
        
        if not response.transaccion:
            error_msg = "Error en la transacción SOAP para sincronizarFechaHora"
            st.error(error_msg)
            logging.error(error_msg)
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
            logging.error(f"Error al convertir la fecha remota: {e}")
            st.error("Error al obtener la fecha del servidor. Sincronización fallida.")
            return False
        
        # Obtener la hora local actual con su zona horaria
        local_time = datetime.now(tzlocal.get_localzone())
        
        logging.debug(f"Hora remota (Bolivia): {remote_time}")
        logging.debug(f"Hora local: {local_time}")

        # Calcular la diferencia horaria correctamente
        time_difference = calcular_diferencia_horaria(remote_time, local_time)

        # Verificar si la diferencia de tiempo está en un rango razonable (5 minutos)
        tiempo_razonable = 300  # 5 minutos en segundos
        diferencia_segundos = abs(time_difference.total_seconds())
        
        if diferencia_segundos <= tiempo_razonable:
            mensaje_tiempo = f"La diferencia de tiempo está en un rango razonable ({diferencia_segundos:.2f} segundos)"
            st.success(f"✅ {mensaje_tiempo}")
            logging.info(mensaje_tiempo)
        else:
            mensaje_tiempo = f"La diferencia de tiempo NO está en un rango razonable ({diferencia_segundos:.2f} segundos)"
            st.warning(mensaje_tiempo)
            logging.warning(mensaje_tiempo)

        if abs(time_difference.total_seconds()) > 86400:  # 24 horas
            logging.warning(f"Diferencia de tiempo anormal: {time_difference}. Verifique la zona horaria.")
            st.warning(f"Diferencia de tiempo anormal detectada: {time_difference}. ¿Desea corregirla?")
            
            if st.button("Corregir diferencia horaria"):
                time_difference = timedelta(seconds=0)
                st.success("✅ Diferencia horaria corregida manualmente.")

        logging.debug(f"Diferencia de tiempo calculada: {time_difference}")

        # Guardar resultado en la base de datos
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
            logging.error(f"Error al guardar sincronización: {e}")
        finally:
            db.close()
            
        st.success("✅ Sincronización de Fecha y Hora completada.")
        mostrar_informacion_sincronizacion()
        return True

    except Exception as e:
        error_msg = f"Error al sincronizar Fecha y Hora: {str(e)}"
        st.error(error_msg)
        logging.error(error_msg)
        logging.error(traceback.format_exc())
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
        
        st.write("Diferencia de tiempo:")
        if time_difference.total_seconds() >= 0:
            st.write(f"+{time_difference}")
        else:
            st.write(time_difference)
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
            logging.error(f"Error en la transacción SOAP para {service_name}: {response.mensajesList}")
            return False
        
        # Obtener nombre de la lista según el servicio
        lista_nombre = f"lista{service_name[11:]}"
        if not hasattr(response, lista_nombre):
            st.warning(f"No se encontró la lista '{lista_nombre}' en la respuesta")
            logging.warning(f"No se encontró la lista '{lista_nombre}' en la respuesta")
            return False
            
        lista_items = getattr(response, lista_nombre, [])
        if not lista_items:
            st.info(f"No hay datos para sincronizar en {service_name}")
            return True
            
        # Procesar la respuesta
        db = next(get_db())
        try:
            # Obtener el campo clave para este modelo
            campos_clave = model_key_fields.get(model_class)
            
            # Contador para estadísticas
            nuevos = 0
            actualizados = 0
            
            for item in lista_items:
                # Convertir el objeto zeep a un diccionario
                item_dict = {key: value for key, value in item.__dict__.items()}
                
                # Construir el filtro según el tipo de campo clave
                if isinstance(campos_clave, list):
                    # Manejo de claves compuestas
                    filtros = []
                    for campo in campos_clave:
                        if hasattr(item, campo):
                            filtros.append(getattr(model_class, campo) == getattr(item, campo))
                    
                    if filtros:
                        db_item = db.query(model_class).filter(*filtros).first()
                    else:
                        db_item = None
                else:
                    # Manejo de clave simple
                    if hasattr(item, campos_clave):
                        valor_clave = getattr(item, campos_clave)
                        db_item = db.query(model_class).filter(getattr(model_class, campos_clave) == valor_clave).first()
                    else:
                        db_item = None
                        
                if db_item:
                    # Actualizar item existente
                    for key, value in item_dict.items():
                        if hasattr(db_item, key):
                            setattr(db_item, key, value)
                    db_item.fecha_sincronizacion = func.now()
                    db_item.estado_sincronizacion = 'Exitoso'
                    actualizados += 1
                else:
                    # Crear nuevo item
                    new_item = model_class()
                    for key, value in item_dict.items():
                        if hasattr(new_item, key):
                            setattr(new_item, key, value)
                    new_item.fecha_sincronizacion = func.now()
                    new_item.estado_sincronizacion = 'Exitoso'
                    db.add(new_item)
                    nuevos += 1
            
            db.commit()
            st.success(f"✅ Sincronización de {service_name} completada: {nuevos} nuevos, {actualizados} actualizados")
            return True
            
        except Exception as e:
            db.rollback()
            st.error(f"Error al procesar datos de {service_name}: {str(e)}")
            logging.error(f"Error al procesar datos de {service_name}: {traceback.format_exc()}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        st.error(f"Error al sincronizar {service_name}: {str(e)}")
        logging.error(f"Error al sincronizar {service_name}: {traceback.format_exc()}")
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