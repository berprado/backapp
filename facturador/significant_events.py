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

def register_significant_event(event_code, description, start_time, end_time, cufd):
    """
    Registra un evento significativo en la base de datos y, si es posible, en el SIN.
    Devuelve (exito: bool, mensaje: str)
    """
    logger.info(f"Intentando registrar evento: event_code={event_code}, description={description}, start_time={start_time}, end_time={end_time}, cufd={cufd}")
    try:
        # Validar parámetros
        if not event_code or not description or not start_time or not cufd:
            logger.error(f"Faltan parámetros requeridos: event_code={event_code}, description={description}, start_time={start_time}, cufd={cufd}")
            return False, "Faltan parámetros requeridos para el registro del evento."

        # Si no se provee end_time, usar start_time (evento abierto)
        if not end_time:
            end_time = start_time

        # Validar que no exista ya un evento abierto igual
        session = SessionLocal()
        # Un evento está abierto si fecha_inicio es igual a fecha_fin
        existe = session.query(EventoSignificativoRegistrado).filter(
            EventoSignificativoRegistrado.codigo_evento == event_code,
            EventoSignificativoRegistrado.fecha_inicio == EventoSignificativoRegistrado.fecha_fin,
            EventoSignificativoRegistrado.cufd == cufd
        ).first()
        if existe:
            logger.warning(f"Ya existe un evento abierto para el código {event_code} y CUFD {cufd}")
            session.close()
            return True, "Ya existe un evento abierto para este tipo y CUFD."

        # Registrar en la base de datos local
        nuevo_evento = EventoSignificativoRegistrado(
            codigo_evento=event_code,
            descripcion=description,
            fecha_inicio=start_time,
            fecha_fin=end_time,
            cufd=cufd
        )
        session.add(nuevo_evento)
        session.commit()
        session.refresh(nuevo_evento)
        logger.info(f"Evento significativo registrado localmente: {nuevo_evento}")
        session.close()

        # Intentar registrar en el SIN si el cliente SOAP está disponible
        if WSDL_URL and API_KEY:
            try:
                client = Client(WSDL_URL, transport=transport)
                SolicitudEvento = client.get_type('ns0:solicitudEventoSignificativo')
                solicitud = SolicitudEvento(
                    codigoAmbiente=int(os.getenv('CODIGO_AMBIENTE')),
                    codigoPuntoVenta=int(os.getenv('CODIGO_PUNTO_VENTA')),
                    codigoSistema=os.getenv('CODIGO_SISTEMA'),
                    codigoSucursal=int(os.getenv('CODIGO_SUCURSAL')),
                    cuis=os.getenv('CUIS'),
                    nit=int(os.getenv('NIT')),
                    codigoEvento=int(event_code),
                    descripcion=description,
                    fechaHoraInicioEvento=start_time,
                    fechaHoraFinEvento=end_time,
                    cufd=cufd
                )
                response = client.service.registroEventoSignificativo(solicitud)
                logger.info(f"Respuesta del SIN al registrar evento: {response}")
                if hasattr(response, 'transaccion') and response.transaccion:
                    return True, "Evento registrado correctamente en el SIN."
                else:
                    logger.error(f"Error al registrar evento en el SIN: {getattr(response, 'mensajesList', 'Sin detalle')}")
                    return False, f"Error al registrar evento en el SIN: {getattr(response, 'mensajesList', 'Sin detalle')}"
            except Exception as e:
                logger.error(f"Error al registrar evento en el SIN: {e}")
                return True, "Evento registrado localmente. No se pudo registrar en el SIN por contingencia."
        else:
            logger.warning("No se pudo registrar en el SIN por falta de configuración de WSDL o API_KEY.")
            return True, "Evento registrado localmente. No se pudo registrar en el SIN por falta de configuración."
    except Exception as e:
        logger.error(f"Error general al registrar evento: {e}")
        return False, f"Error general al registrar evento: {e}"

def get_significant_events(limit=50, only_open=False):
    """
    Obtiene los eventos significativos registrados
    
    Args:
        limit (int): Límite de eventos a retornar
        only_open (bool): Si True, retorna solo eventos abiertos
        
    Returns:
        list: Lista de eventos significativos registrados
    """
    session = SessionLocal()
    try:
        query = session.query(EventoSignificativoRegistrado)
        
        if only_open:
            # Un evento está abierto si fecha_fin es igual a fecha_inicio
            # (indicando que se inició pero no se ha cerrado)
            query = query.filter(EventoSignificativoRegistrado.fecha_inicio == EventoSignificativoRegistrado.fecha_fin)
            
        events = query.order_by(EventoSignificativoRegistrado.fecha_registro.desc())\
            .limit(limit)\
            .all()
        
        result = []
        for event in events:
            event_dict = event.to_dict()
            # Añadir una propiedad 'abierto' para facilitar el uso en la interfaz
            event_dict['abierto'] = (event.fecha_inicio == event.fecha_fin)
            result.append(event_dict)
        
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

def close_significant_event(event_id: int, end_time: str) -> tuple[bool, str]:
    """
    Cierra un evento significativo existente actualizando su fecha de finalización.

    Args:
        event_id (int): El ID del evento a cerrar.
        end_time (str): La fecha y hora de finalización en formato ISO.

    Returns:
        tuple[bool, str]: Un booleano de éxito y un mensaje.
    """
    session = SessionLocal()
    try:
        evento = session.query(EventoSignificativoRegistrado).filter(EventoSignificativoRegistrado.id == event_id).first()
        
        if not evento:
            logger.error(f"No se encontró el evento con ID {event_id} para cerrar.")
            return False, f"No se encontró el evento con ID {event_id}."
            
        # Verificar si el evento ya está cerrado (fecha_fin diferente a fecha_inicio)
        if evento.fecha_fin is not None and evento.fecha_fin != evento.fecha_inicio:
            logger.warning(f"El evento {event_id} ya estaba cerrado.")
            return True, "El evento ya estaba cerrado."

        evento.fecha_fin = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        session.commit()
        
        logger.info(f"Evento significativo con ID {event_id} cerrado exitosamente.")
        return True, "Evento cerrado exitosamente."
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error al cerrar el evento significativo {event_id}: {e}", exc_info=True)
        return False, f"Error de base de datos al cerrar el evento: {str(e)}"
    finally:
        session.close()