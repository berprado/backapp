import os
import sys
import logging
import traceback
import streamlit as st
from zeep import Client
import requests
from dotenv import load_dotenv
from sqlalchemy import func


# Añadir el directorio raíz y el directorio 'facturador' al path de Python
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
    SincronizarParametricaUnidadMedida
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

# Configuración del cliente SOAP
wsdl_url = os.getenv("WSDL_URL")
api_key = os.getenv("API_KEY")

def sincronizar_generico(service_name, model_class):
    st.text(f"Iniciando sincronización de {service_name}")
    
    # Crear cliente SOAP
    client = Client(wsdl_url)
    session = requests.Session()
    session.headers.update({"apikey": api_key})
    client.transport.session = session

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
                for item in lista_items:
                    # Determinar el campo clave para la búsqueda
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
                        # Crear nuevo item
                        new_item = model_class(**item.__dict__)
                        new_item.fecha_sincronizacion = func.now()
                        new_item.estado_sincronizacion = 'Exitoso'
                        db.add(new_item)
                
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

    except Exception as e:
        st.error(f"Error al sincronizar {service_name}: {str(e)}")
        logging.error(traceback.format_exc())

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

def main():
    st.title("Sincronizar Datos")

    if st.button('Sincronizar Todo'):
        for service_name, model_class in service_model_map.items():
            with st.spinner(f"Sincronizando {service_name}..."):
                sincronizar_generico(service_name, model_class)
        st.success("Todas las sincronizaciones completadas.")

    # Opción para sincronizar servicios individuales
    selected_service = st.selectbox("Seleccione un servicio para sincronizar", list(service_model_map.keys()))
    if st.button('Sincronizar Servicio Seleccionado'):
        with st.spinner(f"Sincronizando {selected_service}..."):
            sincronizar_generico(selected_service, service_model_map[selected_service])
        st.success(f"Sincronización de {selected_service} completada.")

if __name__ == "__main__":
    main()