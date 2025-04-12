import os
from datetime import datetime
from zeep import Client, Transport
from requests import Session
from database import SessionLocal
from facturador.models import EventoSignificativoRegistrado
from dotenv import load_dotenv
from facturador.logger_config import get_logger  # Cambiar esta importación

logger = get_logger('contingency')  # Usar el logger general con nombre específico
load_dotenv()

# Configuración del cliente SOAP
WSDL_URL = os.getenv('WSDL_URL_OPERACIONES')
API_KEY = os.getenv('API_KEY')

session = Session()
session.headers.update({
    'apikey': API_KEY
})
transport = Transport(session=session)

try:
    client = Client(WSDL_URL, transport=transport)
except Exception as e:
    logger.error(f"Error initializing SOAP client: {e}")
    client = None  # Set client to None to indicate offline mode

def registro_evento_significativo(codigo_ambiente, codigo_sistema, nit, cuis, cufd, codigo_sucursal, codigo_punto_venta, codigo_evento, descripcion, fecha_inicio_evento, fecha_fin_evento, cufd_evento):
    """
    Registra un evento significativo en el sistema del SIN.

    Args:
        codigo_ambiente (int): Código del ambiente (1: Producción, 2: Piloto).
        codigo_sistema (str): Código del sistema autorizado.
        nit (int): NIT del emisor.
        cuis (str): Código único de identificación de sucursal.
        cufd (str): CUFD vigente.
        codigo_sucursal (int): Código de la sucursal (0 para casa matriz).
        codigo_punto_venta (int): Código del punto de venta (0 si no aplica).
        codigo_evento (int): Código del tipo de evento.
        descripcion (str): Descripción del evento.
        fecha_inicio_evento (str): Fecha de inicio del evento (formato ISO 8601).
        fecha_fin_evento (str): Fecha de fin del evento (formato ISO 8601).
        cufd_evento (str): CUFD usado durante la contingencia.

    Returns:
        dict: Respuesta del servicio.
    """
    try:
        response = client.service.registroEventoSignificativo(
            codigoAmbiente=codigo_ambiente,
            codigoSistema=codigo_sistema,
            nit=nit,
            cuis=cuis,
            cufd=cufd,
            codigoSucursal=codigo_sucursal,
            codigoPuntoVenta=codigo_punto_venta,
            codigoEvento=codigo_evento,
            descripcion=descripcion,
            fechaInicioEvento=fecha_inicio_evento,
            fechaFinEvento=fecha_fin_evento,
            cufdEvento=cufd_evento
        )
        return response
    except Exception as e:
        return {"error": str(e)}

def consulta_evento_significativo(codigo_ambiente, codigo_sistema, nit, cuis, cufd, codigo_sucursal, codigo_punto_venta, fecha_evento):
    """
    Consulta los eventos significativos registrados en el sistema del SIN.

    Args:
        codigo_ambiente (int): Código del ambiente (1: Producción, 2: Piloto).
        codigo_sistema (str): Código del sistema autorizado.
        nit (int): NIT del emisor.
        cuis (str): Código único de identificación de sucursal.
        cufd (str): CUFD vigente.
        codigo_sucursal (int): Código de la sucursal (0 para casa matriz).
        codigo_punto_venta (int): Código del punto de venta (0 si no aplica).
        fecha_evento (str): Fecha del evento (formato ISO 8601).

    Returns:
        dict: Respuesta del servicio.
    """
    try:
        response = client.service.consultaEventoSignificativo(
            codigoAmbiente=codigo_ambiente,
            codigoSistema=codigo_sistema,
            nit=nit,
            cuis=cuis,
            cufd=cufd,
            codigoSucursal=codigo_sucursal,
            codigoPuntoVenta=codigo_punto_venta,
            fechaEvento=fecha_evento
        )
        return response
    except Exception as e:
        return {"error": str(e)}

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
    if not client:
        logger.warning("SOAP client is not initialized. Operating in offline mode.")
        return False, "Cannot register event in offline mode."

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

        # Send the request to SIAT
        response = registro_evento_significativo(
            int(os.getenv('CODIGO_AMBIENTE')),
            os.getenv('CODIGO_SISTEMA'),
            int(os.getenv('NIT')),
            os.getenv('CUIS'),
            cufd,
            int(os.getenv('CODIGO_SUCURSAL')),
            int(os.getenv('CODIGO_PUNTO_VENTA')),
            event_code,
            description,
            start_time,
            end_time,
            cufd
        )

        if response and hasattr(response, 'transaccion') and response.transaccion:
            # Save the event in the database
            nuevo_evento = EventoSignificativoRegistrado(
                codigo_evento=event_code,
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
        list: Lista de eventos significativos registrados
    """
    session = SessionLocal()
    try:
        events = session.query(EventoSignificativoRegistrado)\
            .order_by(EventoSignificativoRegistrado.fecha_registro.desc())\
            .limit(limit)\
            .all()
        
        result = []
        for event in events:
            result.append(event.to_dict())
        
        return result
    except Exception as e:
        logger.error(f"Error al obtener eventos significativos registrados: {str(e)}")
        return []
    finally:
        session.close()


def query_siat_significant_events():
    """
    Consulta los eventos significativos registrados en SIAT
    
    Returns:
        tuple: (success, data) donde success es un booleano y data contiene los eventos o un mensaje de error
    """
    session = SessionLocal()
    try:
        # Obtener CUFD vigente
        from facturador.models import Cufd
        cufd_record = session.query(Cufd).filter(Cufd.vigente == 1).first()
        if not cufd_record:
            return False, "No se encontró un CUFD válido"
        
        # Preparar la solicitud
        response = consulta_evento_significativo(
            int(os.getenv('CODIGO_AMBIENTE')),
            os.getenv('CODIGO_SISTEMA'),
            int(os.getenv('NIT')),
            os.getenv('CUIS'),
            cufd_record.codigo,
            int(os.getenv('CODIGO_SUCURSAL')),
            int(os.getenv('CODIGO_PUNTO_VENTA')),
            datetime.now().isoformat()
        )
        
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