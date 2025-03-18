import os
from datetime import datetime
from zeep import Client, Transport
from requests import Session
from database import SessionLocal
from facturador.models import SincronizarParametricaEventosSignificativos
from dotenv import load_dotenv
from logger_config import get_contingency_logger

logger = get_contingency_logger()
load_dotenv()

def register_significant_event(event_code, description, start_time, end_time, cufd=None):
    """
    Registra un evento significativo en el sistema del SIAT
    
    Args:
        event_code (int): Código del evento significativo
        description (str): Descripción del evento
        start_time (str): Fecha y hora de inicio (formato: YYYY-MM-DDTHH:MM:SS.SSS)
        end_time (str): Fecha y hora de fin (formato: YYYY-MM-DDTHH:MM:SS.SSS)
        cufd (str, optional): CUFD utilizado durante el evento. Si es None, se usa el vigente.
    
    Returns:
        tuple: (success, message) donde success es un booleano y message es un mensaje descriptivo
    """
    session = SessionLocal()
    try:
        # Obtener CUFD si no se proporcionó
        if not cufd:
            from facturador.models import Cufd
            cufd_record = session.query(Cufd).filter(Cufd.vigente == 1).first()
            if not cufd_record:
                return False, "No se encontró un CUFD válido"
            cufd = cufd_record.codigo
        
        # Preparar la conexión SOAP
        soap_session = Session()
        soap_session.headers.update({'apikey': os.getenv('API_KEY')})
        wsdl_url = os.getenv('WSDL_URL_OPERACIONES')
        
        client = Client(wsdl_url, transport=Transport(session=soap_session))
        
        # Preparar la solicitud
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
        
        # Enviar la solicitud
        response = client.service.registroEventoSignificativo(**solicitud)
        
        if response and hasattr(response, 'transaccion') and response.transaccion:
            # Guardar el evento en la base de datos
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
            
            return True, f"Evento registrado con éxito. Código: {event_code}"
        else:
            error_msg = "Error desconocido al registrar evento"
            if hasattr(response, 'mensajesList') and response.mensajesList:
                error_msg = response.mensajesList[0].descripcion
            
            return False, f"Error al registrar evento: {error_msg}"
    
    except Exception as e:
        logger.error(f"Excepción al registrar evento significativo: {str(e)}")
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
        
        if response and hasattr(response, 'transaccion') and response.transaccion:
            events = []
            
            if hasattr(response, 'listaCodigos') and response.listaCodigos:
                for evento in response.listaCodigos:
                    events.append({
                        'codigoEvento': evento.codigoEvento,
                        'descripcionEvento': evento.descripcionEvento,
                        'fechaInicio': evento.fechaInicio,
                        'fechaFin': evento.fechaFin,
                        'cufdEvento': evento.cufdEvento
                    })
            
            return True, events
        else:
            error_msg = "Error desconocido al consultar eventos"
            if hasattr(response, 'mensajesList') and response.mensajesList:
                error_msg = response.mensajesList[0].descripcion
            
            return False, f"Error al consultar eventos: {error_msg}"
    
    except Exception as e:
        logger.error(f"Excepción al consultar eventos significativos: {str(e)}")
        return False, f"Error: {str(e)}"
    finally:
        session.close()
