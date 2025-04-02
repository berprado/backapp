import os
from datetime import datetime
from zeep import Client, Transport
from requests import Session
from database import SessionLocal
from facturador.models import SincronizarParametricaEventosSignificativos
from dotenv import load_dotenv
from facturador.logger_config import get_logger  # Cambiar esta importación

logger = get_logger('contingency')  # Usar el logger general con nombre específico
load_dotenv()

def register_significant_event(event_code, description, start_time, end_time, cufd=None):
    """
    Registers a significant event in the SIAT system.

    Args:
        event_code (int): Code of the significant event.
        description (str): Description of the event.
        start_time (str): Start date and time (format: YYYY-MM-DDTHH:MM:SS.SSS).
        end_time (str): End date and time (format: YYYY-MM-DDTHH:MM:SS.SSS).
        cufd (str, optional): CUFD used during the event. If None, the current CUFD is used.

    Returns:
        tuple: (success, message) where success is a boolean and message is a descriptive message.
    """
    session = SessionLocal()
    try:
        # Validate inputs
        if not event_code or not description or not start_time or not end_time:
            logger.error("All parameters (event_code, description, start_time, end_time) are required.")
            return False, "Missing required parameters."

        # Ensure end_time is after start_time
        if datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%f") <= datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%f"):
            logger.error("End time must be after start time.")
            return False, "End time must be after start time."

        # Obtain CUFD if not provided
        if not cufd:
            from facturador.models import Cufd
            cufd_record = session.query(Cufd).filter(Cufd.vigente == 1).first()
            if not cufd_record:
                return False, "No valid CUFD found."
            cufd = cufd_record.codigo

        # Prepare the SOAP connection
        soap_session = Session()
        soap_session.headers.update({'apikey': os.getenv('API_KEY')})
        wsdl_url = os.getenv('WSDL_URL_OPERACIONES')

        client = Client(wsdl_url, transport=Transport(session=soap_session))

        # Prepare the request
        solicitud = {
            'codigoAmbiente': os.getenv('CODIGO_AMBIENTE'),
            'codigoSistema': os.getenv('CODIGO_SISTEMA'),
            'nit': os.getenv('NIT'),
            'cuis': os.getenv('CUIS'),
            'cufd': cufd,
            'codigoSucursal': os.getenv('CODIGO_SUCURSAL'),
            'codigoPuntoVenta': os.getenv('CODIGO_PUNTO_VENTA'),
            'codigoEvento': event_code,
            'descripcion': description,
            'fechaInicio': start_time,
            'fechaFin': end_time
        }

        # Send the request
        response = client.service.registroEventoSignificativo(**solicitud)

        if response and hasattr(response, 'transaccion') and response.transaccion:
            # Save the event in the database
            nuevo_evento = SincronizarParametricaEventosSignificativos(
                codigoClasificador=event_code,
                descripcion=description,
                fecha_inicio=datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%f"),
                fecha_fin=datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%f"),
                cufd=cufd,
                fecha_registro=datetime.now()
            )

            session.add(nuevo_evento)
            session.commit()

            return True, f"Event registered successfully. Code: {event_code}"
        else:
            error_msg = "Unknown error while registering event."
            if hasattr(response, 'mensajesList') and response.mensajesList:
                error_msg = response.mensajesList[0].descripcion

            return False, f"Error registering event: {error_msg}"

    except Exception as e:
        logger.error(f"Exception while registering significant event: {str(e)}")
        return False, f"Error: {str(e)}"
    finally:
        session.close()

def get_significant_events(limit=50):
    """
    Obtiene los eventos significativos registrados
    
    Args:
        limit (int): Límite de eventos a retornar
        
    Returns:
        list: Lista de eventos significativos
    """
    session = SessionLocal()
    try:
        events = session.query(SincronizarParametricaEventosSignificativos)\
            .order_by(SincronizarParametricaEventosSignificativos.fecha_registro.desc())\
            .limit(limit)\
            .all()
        
        result = []
        for event in events:
            result.append({
                'codigo': event.codigoClasificador,
                'descripcion': event.descripcion,
                'fecha_inicio': event.fecha_inicio,
                'fecha_fin': event.fecha_fin,
                'cufd': event.cufd,
                'fecha_registro': event.fecha_registro
            })
        
        return result
    except Exception as e:
        logger.error(f"Error al obtener eventos significativos: {str(e)}")
        return []
    finally:
        session.close()

def query_siat_significant_events():
    """
    Consulta los eventos significativos registrados en SIAT
    
    Returns:
        tuple: (success, data) donde success es un booleano y data contiene los eventos o un mensaje de error
    """
    try:
        # Preparar la conexión SOAP
        soap_session = Session()
        soap_session.headers.update({'apikey': os.getenv('API_KEY')})
        wsdl_url = os.getenv('WSDL_URL_OPERACIONES')
        
        client = Client(wsdl_url, transport=Transport(session=soap_session))
        
        # Obtener CUFD vigente
        session = SessionLocal()
        from facturador.models import Cufd
        cufd_record = session.query(Cufd).filter(Cufd.vigente == 1).first()
        if not cufd_record:
            return False, "No se encontró un CUFD válido"
        
        # Preparar la solicitud
        solicitud = {
            'codigoAmbiente': os.getenv('CODIGO_AMBIENTE'),
            'codigoSistema': os.getenv('CODIGO_SISTEMA'),
            'nit': os.getenv('NIT'),
            'cuis': os.getenv('CUIS'),
            'cufd': cufd_record.codigo,
            'codigoSucursal': os.getenv('CODIGO_SUCURSAL'),
            'codigoPuntoVenta': os.getenv('CODIGO_PUNTO_VENTA')
        }
        
        # Enviar la solicitud
        response = client.service.consultaEventoSignificativo(**solicitud)
        
        if response and hasattr(response, 'transaccion'):
            if response.transaccion:
                return True, response.eventos
            else:
                error_msg = "Error desconocido al consultar eventos."
                if hasattr(response, 'mensajesList') and response.mensajesList:
                    error_msg = response.mensajesList[0].descripcion
                return False, error_msg
        else:
            return False, "No se recibió respuesta válida del servicio."
    except Exception as e:
        logger.error(f"Error al consultar eventos significativos en SIAT: {str(e)}")
        return False, f"Error: {str(e)}"
    finally:
        session.close()
