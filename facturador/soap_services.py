# soap_services.py
import os
import requests
import xml.etree.ElementTree as ET
from typing import Tuple, Optional
from dotenv import load_dotenv
from typing import Dict
from datetime import datetime
from database import get_cufd_vigente
from logger_config import get_eventos_logger  # Importación corregida - eliminado el prefijo facturador

# Obtener logger para eventos significativos
logger = get_eventos_logger()

# Cargar variables de entorno desde el archivo .env
load_dotenv()

TOKEN_API: str = os.getenv("API_KEY")
ENDPOINT: str = os.getenv("WSDL_URL_OPERACIONES", "https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionOperaciones")


# =============================
# 🔍 Verificación de comunicación con el SIN
# Devuelve:
# - mensaje: descripción del estado
# - estado: True si hay conexión
# - tipo_deducido: código del evento sugerido (1, 2, 5...), o None
# =============================
def verificar_comunicacion() -> Tuple[str, bool, Optional[str]]:
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "apikey": f"TokenApi {TOKEN_API}"
    }

    body = """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:siat="https://siat.impuestos.gob.bo/">
       <soapenv:Header/>
       <soapenv:Body>
          <siat:verificarComunicacion/>
       </soapenv:Body>
    </soapenv:Envelope>"""

    try:
        response = requests.post(ENDPOINT, data=body.encode("utf-8"), headers=headers, timeout=6)

        if response.status_code == 200:
            ns = {'ns2': 'https://siat.impuestos.gob.bo/'}
            root = ET.fromstring(response.text)
            mensaje = root.find('.//ns2:verificarComunicacionResponse//mensajesList//descripcion', ns)
            transaccion = root.find('.//ns2:verificarComunicacionResponse//transaccion', ns)

            return (
                mensaje.text if mensaje is not None else "Respuesta vacía",
                transaccion.text == "true",
                None
            )

        # Clasificación de errores comunes
        if response.status_code in [500, 502]:
            return f"Error HTTP {response.status_code}", False, "2"  # Inaccesibilidad al servicio SIN
        else:
            return f"Error HTTP {response.status_code}", False, "1"  # Corte de internet general

    except requests.exceptions.Timeout:
        return "Timeout al conectar con el SIN", False, "2"
    except requests.exceptions.ConnectionError:
        return "Error de conexión o DNS", False, "1"
    except Exception as e:
        return f"Error inesperado: {e}", False, "5"  # Falla de software


def enviar_evento_significativo(evento: Dict, fecha_fin: datetime, cufd: str) -> Tuple[Optional[str], bool]:
    """
    Envía un evento significativo al SIN
    
    Args:
        evento (Dict): Datos del evento a enviar
        fecha_fin (datetime): Fecha de finalización del evento
        cufd (str): CUFD vigente para enviar el evento
    
    Returns:
        Tuple[Optional[str], bool]: Código de recepción y estado de la transacción
    """
    from os import getenv

    NIT = getenv("NIT")
    CUIS = getenv("CUIS")
    CODIGO_SISTEMA = getenv("CODIGO_SISTEMA")
    CODIGO_SUCURSAL = getenv("CODIGO_SUCURSAL")
    CODIGO_AMBIENTE = getenv("CODIGO_AMBIENTE")
    CODIGO_PUNTO_VENTA = getenv("CODIGO_PUNTO_VENTA", "0")

    logger.info(f"Enviando evento significativo #{evento.get('id', 'N/A')} al SIN")
    logger.debug(f"Datos de evento: código={evento['codigo_evento']}, inicio={evento['fecha_inicio']}, fin={fecha_fin}")

    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "apikey": f"TokenApi {TOKEN_API}"
    }

    soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
       <soapenv:Header/>
       <soapenv:Body>
          <siat:registroEventoSignificativo>
             <SolicitudEventoSignificativo>
                <codigoAmbiente>{CODIGO_AMBIENTE}</codigoAmbiente>
                <codigoMotivoEvento>{evento['codigo_evento']}</codigoMotivoEvento>
                <codigoPuntoVenta>{CODIGO_PUNTO_VENTA}</codigoPuntoVenta>
                <codigoSistema>{CODIGO_SISTEMA}</codigoSistema>
                <codigoSucursal>{CODIGO_SUCURSAL}</codigoSucursal>
                <cufd>{cufd}</cufd>
                <cufdEvento>{evento['cufd']}</cufdEvento>
                <cuis>{CUIS}</cuis>
                <descripcion>{evento['descripcion']}</descripcion>
                <fechaHoraFinEvento>{fecha_fin.isoformat()}</fechaHoraFinEvento>
                <fechaHoraInicioEvento>{evento['fecha_inicio'].isoformat()}</fechaHoraInicioEvento>
                <nit>{NIT}</nit>
             </SolicitudEventoSignificativo>
          </siat:registroEventoSignificativo>
       </soapenv:Body>
    </soapenv:Envelope>"""

    try:
        response = requests.post(ENDPOINT, data=soap_body.encode("utf-8"), headers=headers)
        logger.debug(f"Respuesta HTTP: {response.status_code}")
        
        if response.status_code == 200:
            ns = {'ns2': 'https://siat.impuestos.gob.bo/'}
            root = ET.fromstring(response.text)
            recepcion = root.find('.//ns2:registroEventoSignificativoResponse//codigoRecepcionEventoSignificativo', ns)
            transaccion = root.find('.//ns2:registroEventoSignificativoResponse//transaccion', ns)
            
            if transaccion is not None and transaccion.text == "true":
                logger.info(f"Evento enviado exitosamente. Código de recepción: {recepcion.text if recepcion is not None else 'No recibido'}")
                return recepcion.text if recepcion is not None else None, True
            else:
                # Buscar mensajes de error si la transacción falló
                mensajes = []
                for mensaje in root.findall('.//ns2:registroEventoSignificativoResponse//mensajesList', ns):
                    codigo = mensaje.findtext('codigo', default='', namespaces=ns)
                    descripcion = mensaje.findtext('descripcion', default='', namespaces=ns)
                    mensajes.append(f"{codigo}: {descripcion}")
                
                logger.error(f"Error al enviar evento significativo: {', '.join(mensajes)}")
                return None, False
                
        logger.error(f"Error HTTP {response.status_code} al enviar evento significativo: {response.text}")
        return None, False
        
    except Exception as e:
        logger.exception(f"Error al enviar evento significativo: {str(e)}")
        return None, False


def consulta_eventos_significativos(fecha_evento: str = None) -> Optional[list]:
    """
    Consulta los eventos significativos registrados en el SIN para una fecha específica en formato extendido UTC.
    Args:
        fecha_evento (str): Fecha completa con hora en formato ISO: 'YYYY-MM-DDTHH:MM:SS.000'

    Returns:
        Lista de eventos registrados o None si falla.
    """
    from os import getenv
    from datetime import date

    NIT = getenv("NIT")
    CUIS = getenv("CUIS")
    CODIGO_SISTEMA = getenv("CODIGO_SISTEMA")
    CODIGO_SUCURSAL = getenv("CODIGO_SUCURSAL", "0")
    CODIGO_AMBIENTE = getenv("CODIGO_AMBIENTE", "2")
    CODIGO_PUNTO_VENTA = getenv("CODIGO_PUNTO_VENTA", "0")
    TOKEN_API = getenv("API_KEY")
    ENDPOINT = getenv("WSDL_URL_OPERACIONES")

    # Obtener CUFD vigente desde la base de datos
    CUFD = get_cufd_vigente()
    if not CUFD:
        logger.error("CUFD vigente no encontrado para consulta de eventos significativos")
        return None

    # Si no se pasó fecha_evento, usar fecha actual con hora 01:00:00.000
    if not fecha_evento:
        fecha_evento = f"{date.today().strftime('%Y-%m-%d')}T01:00:00.000"
        logger.info(f"Usando fecha por defecto para consulta de eventos: {fecha_evento}")
    
    logger.info(f"Consultando eventos significativos para fecha: {fecha_evento}")

    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "apikey": f"TokenApi {TOKEN_API}"
    }

    soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:siat="https://siat.impuestos.gob.bo/">
       <soapenv:Header/>
       <soapenv:Body>
          <siat:consultaEventoSignificativo>
             <SolicitudConsultaEvento>
                <codigoAmbiente>{CODIGO_AMBIENTE}</codigoAmbiente>
                <codigoPuntoVenta>{CODIGO_PUNTO_VENTA}</codigoPuntoVenta>
                <codigoSistema>{CODIGO_SISTEMA}</codigoSistema>
                <codigoSucursal>{CODIGO_SUCURSAL}</codigoSucursal>
                <cufd>{CUFD}</cufd>
                <cuis>{CUIS}</cuis>
                <fechaEvento>{fecha_evento}</fechaEvento>
                <nit>{NIT}</nit>
             </SolicitudConsultaEvento>
          </siat:consultaEventoSignificativo>
       </soapenv:Body>
    </soapenv:Envelope>"""

    try:
        response = requests.post(ENDPOINT, data=soap_body.encode("utf-8"), headers=headers)
        logger.debug(f"Respuesta HTTP: {response.status_code}")
        
        if response.status_code == 200:
            ns = {'ns2': 'https://siat.impuestos.gob.bo/'}
            root = ET.fromstring(response.text)
            
            # Verificamos si la transacción fue exitosa
            transaccion_elem = root.find('.//RespuestaListaEventos/transaccion')
            if transaccion_elem is not None and transaccion_elem.text == "false":
                # Buscar mensajes de error si la transacción falló
                mensajes = []
                for mensaje in root.findall('.//RespuestaListaEventos/mensajesList', ns):
                    codigo = mensaje.findtext('codigo', default='', namespaces=ns)
                    descripcion = mensaje.findtext('descripcion', default='', namespaces=ns)
                    mensajes.append(f"{codigo}: {descripcion}")
                
                logger.error(f"Error en la consulta de eventos significativos: {', '.join(mensajes)}")
                return None

            eventos = []
            # Primero intentamos con la estructura de respuesta más común (listaCodigos)
            for evento in root.findall('.//RespuestaListaEventos/listaCodigos', ns):
                eventos.append({
                    'codigoEvento': evento.findtext('codigoEvento', default='', namespaces=ns),
                    'descripcion': evento.findtext('descripcion', default='', namespaces=ns),
                    'fechaInicioEvento': evento.findtext('fechaInicio', default='', namespaces=ns),
                    'fechaFinEvento': evento.findtext('fechaFin', default='', namespaces=ns),
                    'cufd': evento.findtext('cufd', default='', namespaces=ns),
                    'codigoRecepcionEventoSignificativo': evento.findtext('codigoRecepcionEventoSignificativo', default='', namespaces=ns)
                })
            
            # Si no encontramos eventos, intentamos con la estructura alternativa (listaEventos)
            if not eventos:
                for evento in root.findall('.//ns2:listaEventos', ns):
                    eventos.append({
                        'codigoEvento': evento.findtext('codigoEvento', default='', namespaces=ns),
                        'descripcion': evento.findtext('descripcion', default='', namespaces=ns),
                        'fechaInicioEvento': evento.findtext('fechaInicioEvento', default='', namespaces=ns),
                        'fechaFinEvento': evento.findtext('fechaFinEvento', default='', namespaces=ns),
                        'cufd': evento.findtext('cufd', default='', namespaces=ns),
                        'codigoRecepcionEventoSignificativo': evento.findtext('codigoRecepcionEventoSignificativo', default='', namespaces=ns)
                    })
            
            if eventos:
                logger.info(f"Se encontraron {len(eventos)} eventos significativos")
            else:
                logger.info("No se encontraron eventos significativos para la fecha consultada")

            return eventos if eventos else None

        logger.error(f"Error HTTP {response.status_code} al consultar eventos significativos: {response.text}")
        return None

    except Exception as e:
        logger.exception(f"Error al consultar eventos significativos: {str(e)}")
        return None

