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

# Agregar rutas a sys.path para acceder a los módulos del proyecto
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
facturador_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.extend([root_dir, facturador_dir])

# Importar desde database.py en el directorio facturador
from facturador.database import get_db, Base

# Importar todos los modelos necesarios
from facturador.models import (
    SincronizarActividades, SincronizarListaActividadesDocumentoSector,
    SincronizarListaLeyendasFactura, SincronizarListaMensajesServicios,
    SincronizarListaProductosServicios, SincronizarParametricaEventosSignificativos,
    SincronizarParametricaMotivoAnulacion, SincronizarParametricaPaisOrigen,
    SincronizarParametricaTipoDocumentoIdentidad, SincronizarParametricaTipoDocumentoSector,
    SincronizarParametricaTipoEmision, SincronizarParametricaTipoHabitacion,
    SincronizarParametricaTipoMetodoPago, SincronizarParametricaTipoMoneda,
    SincronizarParametricaTipoPuntoVenta, SincronizarParametricaTiposFactura,
    SincronizarParametricaUnidadMedida,
)

# Cargar variables de entorno desde el directorio raíz
load_dotenv(os.path.join(root_dir, '.env'))

# Configuración de logging
log_dir = os.path.join(facturador_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, 'sincronizacion.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
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

# Diccionario que mapea nombres de servicios a clases de modelo
service_model_map = {
    'sincronizarActividades': SincronizarActividades,
    'sincronizarListaActividadesDocumentoSector': SincronizarListaActividadesDocumentoSector,
    'sincronizarListaLeyendasFactura': SincronizarListaLeyendasFactura,
    'sincronizarListaMensajesServicios': SincronizarListaMensajesServicios,
    'sincronizarListaProductosServicios': SincronizarListaProductosServicios,
    'sincronizarParametricaEventosSignificativos': SincronizarParametricaEventosSignificativos,
    'sincronizarParametricaMotivoAnulacion': SincronizarParametricaMotivoAnulacion,
    'sincronizarParametricaPaisOrigen': SincronizarParametricaPaisOrigen,
    'sincronizarParametricaTipoDocumentoIdentidad': SincronizarParametricaTipoDocumentoIdentidad,
    'sincronizarParametricaTipoDocumentoSector': SincronizarParametricaTipoDocumentoSector,
    'sincronizarParametricaTipoEmision': SincronizarParametricaTipoEmision,
    'sincronizarParametricaTipoHabitacion': SincronizarParametricaTipoHabitacion,
    'sincronizarParametricaTipoMetodoPago': SincronizarParametricaTipoMetodoPago,
    'sincronizarParametricaTipoMoneda': SincronizarParametricaTipoMoneda,
    'sincronizarParametricaTipoPuntoVenta': SincronizarParametricaTipoPuntoVenta,
    'sincronizarParametricaTiposFactura': SincronizarParametricaTiposFactura,
    'sincronizarParametricaUnidadMedida': SincronizarParametricaUnidadMedida
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

def sincronizar_fecha_hora():
    global remote_time, local_time, time_difference
    st.text("Iniciando sincronización de Fecha y Hora")
    logging.debug("Iniciando sincronización de Fecha y Hora")

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
        
        # Convertir la fecha y hora remota a un objeto datetime aware en la zona horaria de Bolivia
        remote_time = bolivia_tz.localize(datetime.fromisoformat(response.fechaHora))
        
        # Obtener la hora local actual en UTC
        local_time = datetime.now(pytz.utc)
        
        logging.debug(f"Hora remota (Bolivia): {remote_time}")
        logging.debug(f"Hora local (UTC): {local_time}")

        # Calcular la diferencia de tiempo
        time_difference = remote_time.astimezone(pytz.utc) - local_time
        
        # Ajustar la diferencia si es cercana a un día completo
        if abs(time_difference.total_seconds()) > 43200:  # 12 horas en segundos
            if time_difference.total_seconds() > 0:
                time_difference = time_difference - timedelta(days=1)
            else:
                time_difference = time_difference + timedelta(days=1)
        
        logging.debug(f"Diferencia de tiempo calculada: {time_difference}")

        st.success("Sincronización de Fecha y Hora completada.")
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
            st.write("Hora local (UTC):")
            st.write(local_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        
        st.write("Diferencia de tiempo:")
        if time_difference.total_seconds() >= 0:
            st.write(f"+{time_difference}")
        else:
            st.write(time_difference)
    else:
        st.warning("No hay información de sincronización disponible.")

def sincronizar_generico(service_name, model_class):
    st.text(f"Iniciando sincronización de {service_name}")

    # Crear solicitud de sincronización
    SolicitudSincronizacion = client.get_type('ns0:solicitudSincronizacion')
    solicitud = SolicitudSincronizacion(
        codigoAmbiente=int(os.getenv("CODIGO_AMBIENTE")),
        codigoPuntoVenta=int(os.getenv("CODIGO_PUNTO_VENTA")),
        codigoSistema=os.getenv("CODIGO_SISTEMA"),
        codigoSucursal=int(os.getenv("CODIGO_SUCURSAL")),
        cuis=os.getenv("CUIS"),
        nit=int(os.getenv("NIT"))
    )

    try:
        # Llamar al servicio de sincronización
        response = getattr(client.service, service_name)(solicitud)

        if not response.transaccion:
            st.error(f"Error en la transacción SOAP para {service_name}: {response.mensajesList}")
            return

        # Procesar la respuesta
        db = next(get_db())
        try:
            lista_items = getattr(response, f"lista{service_name[11:]}", [])
            if lista_items:
                # Utilizar bulk insert/update para optimizar inserciones masivas
                items_a_insertar = []
                for item in lista_items:
                    campo_clave = 'codigoClasificador' if hasattr(item, 'codigoClasificador') else 'codigoCaeb'
                    valor_clave = getattr(item, campo_clave)

                    # Buscar el item en la base de datos
                    db_item = db.query(model_class).filter(getattr(model_class, campo_clave) == valor_clave).first()

                    if db_item:
                        # Actualizar item existente
                        for key, value in item.__dict__.items():
                            if hasattr(db_item, key):
                                setattr(db_item, key, value)
                        db_item.fecha_sincronizacion = func.now()
                        db_item.estado_sincronizacion = 'Exitoso'
                    else:
                        # Preparar nuevo item para insertar
                        new_item = model_class(**item.__dict__)
                        new_item.fecha_sincronizacion = func.now()
                        new_item.estado_sincronizacion = 'Exitoso'
                        items_a_insertar.append(new_item)

                # Insertar todos los nuevos ítems de una vez
                if items_a_insertar:
                    db.bulk_save_objects(items_a_insertar)
                    db.commit()

                st.success(f"Sincronización de {service_name} completada con éxito.")
            else:
                st.info(f"No se encontraron items para sincronizar en {service_name}.")

        except Exception as e:
            db.rollback()
            st.error(f"Error al procesar la respuesta de {service_name}: {str(e)}")
            logging.error(traceback.format_exc())
        finally:
            db.close()

    except requests.RequestException as e:
        st.error(f"Error de red al sincronizar {service_name}: {str(e)}")
        logging.error(traceback.format_exc())
    except Exception as e:
        st.error(f"Error inesperado al sincronizar {service_name}: {str(e)}")
        logging.error(traceback.format_exc())

def main():
    st.title("Sincronizar Datos")

    # Asegurarse de que las variables globales estén inicializadas
    global remote_time, local_time, time_difference
    remote_time = None
    local_time = None
    time_difference = None

    # Verificar comunicación antes de mostrar opciones de sincronización
    exito, mensaje = verificar_comunicacion()
    if exito:
        st.success("Conexión exitosa con el servidor remoto.")
        
        if st.button('Sincronizar Todo'):
            sincronizar_fecha_hora()
            for service_name, model_class in service_model_map.items():
                with st.spinner(f"Sincronizando {service_name}..."):
                    sincronizar_generico(service_name, model_class)
            st.success("Todas las sincronizaciones completadas.")

        # Opción para sincronizar servicios individuales
        selected_service = st.selectbox("Seleccione un servicio para sincronizar", 
                                        ['sincronizarFechaHora'] + list(service_model_map.keys()))
        if st.button('Sincronizar Servicio Seleccionado'):
            if selected_service == 'sincronizarFechaHora':
                sincronizar_fecha_hora()
            else:
                with st.spinner(f"Sincronizando {selected_service}..."):
                    sincronizar_generico(selected_service, service_model_map[selected_service])
            st.success(f"Sincronización de {selected_service} completada.")

        # Mostrar la información de sincronización
        if st.button('Mostrar información de sincronización'):
            mostrar_informacion_sincronizacion()

    else:
        st.error(f"Error de comunicación con el servidor remoto: {mensaje}")
        st.warning("No se pueden realizar sincronizaciones debido a problemas de comunicación.")

if __name__ == "__main__":
    main()