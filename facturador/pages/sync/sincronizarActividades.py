import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from models import SincronizarActividades  # Import using absolute path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from zeep import Client
import requests
import logging
import traceback
from sqlalchemy.sql import func
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection settings
DATABASE_URL = os.getenv('DATABASE_URL')

# Configure logging
log_file_path = os.path.splitext(__file__)[0] + '.txt'
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# SOAP API settings
wsdl_url = os.getenv("WSDL_URL")
api_key = os.getenv("API_KEY")
codigo_ambiente = int(os.getenv("CODIGO_AMBIENTE"))
codigo_punto_venta = int(os.getenv("CODIGO_PUNTO_VENTA"))
codigo_sistema = os.getenv("CODIGO_SISTEMA")
codigo_sucursal = int(os.getenv("CODIGO_SUCURSAL"))
cuis = os.getenv("CUIS")
nit = int(os.getenv("NIT"))

# Initialize SQLAlchemy engine and session factory
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def sincronizar():
    logging.debug('Iniciando sincronización...')

    # SOAP Client creation
    try:
        client = Client(wsdl_url)
        logging.debug('Cliente SOAP creado.')
    except Exception as e:
        logging.error(f'Error al crear el cliente SOAP: {e}')
        logging.error(traceback.format_exc())
        return

    # Configure the session with the API Key
    request_session = requests.Session()
    request_session.headers.update({"apikey": api_key})
    client.transport.session = request_session
    logging.debug('Sesión configurada con la API Key.')

    # Create SQLAlchemy session
    db_session = Session()
    try:
        # Create the synchronization request
        try:
            SolicitudSincronizacion = client.get_type('ns0:solicitudSincronizacion')
            solicitud = SolicitudSincronizacion(
                codigoAmbiente=codigo_ambiente,
                codigoPuntoVenta=codigo_punto_venta,
                codigoSistema=codigo_sistema,
                codigoSucursal=codigo_sucursal,
                cuis=cuis,
                nit=nit
            )
            logging.info(f'Solicitud enviada: {solicitud}')
        except Exception as e:
            logging.error(f'Error al crear la solicitud de sincronización: {e}')
            logging.error(traceback.format_exc())
            return

        # Call the SOAP method
        response = client.service.sincronizarActividades(solicitud)
        logging.info(f'Respuesta completa del servicio SOAP: {response}')

        # Check if the transaction was successful
        if not response.transaccion:
            logging.error(f'Error en la transacción SOAP: {response.mensajesList}')
            return

        # Process each activity in the response
        if response.listaActividades:
            for actividad in response.listaActividades:
                logging.info(f'Procesando actividad: {actividad}')
                codigoCaeb = actividad.codigoCaeb
                descripcion = actividad.descripcion
                tipoActividad = actividad.tipoActividad

                # Insert or update using SQLAlchemy
                actividad_existente = db_session.query(SincronizarActividades).filter_by(codigoCaeb=codigoCaeb).first()

                if actividad_existente:
                    actividad_existente.descripcion = descripcion
                    actividad_existente.tipoActividad = tipoActividad
                    actividad_existente.fecha_sincronizacion = func.now()
                    actividad_existente.estado_sincronizacion = 'Exitoso'
                else:
                    nueva_actividad = SincronizarActividades(
                        codigoCaeb=codigoCaeb,
                        descripcion=descripcion,
                        tipoActividad=tipoActividad,
                        fecha_sincronizacion=func.now(),
                        estado_sincronizacion='Exitoso'
                    )
                    db_session.add(nueva_actividad)

                logging.debug(f'Actividad {codigoCaeb} procesada.')

            # Commit the changes
            db_session.commit()
            logging.debug('Cambios en la base de datos confirmados.')
        else:
            # If no activities were found, update all records
            db_session.query(SincronizarActividades).update({
                SincronizarActividades.fecha_sincronizacion: func.now(),
                SincronizarActividades.estado_sincronizacion: 'Exitoso'
            })
            db_session.commit()
            logging.info("No se encontraron actividades para procesar.")

        logging.info("¡Sincronización completada con éxito!")

    except Exception as e:
        logging.error(f"Error durante la sincronización: {e}")
        logging.error(traceback.format_exc())
    finally:
        db_session.close()

# Only run if the script is invoked directly
if __name__ == "__main__":
    sincronizar()
