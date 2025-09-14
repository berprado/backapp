import os
import logging
import sys
# Agregar la ruta del directorio padre al path de Python si no está ya
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logger_config import get_logger, get_facturacion_logger
def get_anulacion_logger():
    logger = logging.getLogger('anulacion')
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'anulacion.log'), encoding='utf-8')
    console_handler = logging.StreamHandler()
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger
import traceback  # Añadir la importación de traceback

# Obtener loggers para este módulo
logger = get_logger()
facturacion_logger = get_facturacion_logger()
anulacion_logger = get_anulacion_logger()

import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from database import SessionLocal
from models import SincronizarParametricaMotivoAnulacion, Cufd
from datetime import datetime
from data_access import obtener_mensaje_por_codigo, obtener_cuf_por_numero_factura

load_dotenv()



def obtener_cufd_vigente():
    session = SessionLocal()
    try:
        cufd_vigente = session.query(Cufd).filter_by(vigente=1).first()
        if cufd_vigente:
            return cufd_vigente.codigo
        else:
            return None
    except Exception as e:
        return None
    finally:
        session.close()

def obtener_codigo_motivo(descripcion_motivo):
    session = SessionLocal()
    try:
        motivo = session.query(SincronizarParametricaMotivoAnulacion).filter_by(descripcion=descripcion_motivo).first()
        if motivo:
            return motivo.codigoClasificador
        else:
            return None
    except Exception as e:
        return None
    finally:
        session.close()

def construir_solicitud_anulacion(cuf, cufd, codigo_motivo):
    envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
    body = ET.SubElement(envelope, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
    anulacion_factura = ET.SubElement(body, "{https://siat.impuestos.gob.bo/}anulacionFactura")
    solicitud = ET.SubElement(anulacion_factura, "SolicitudServicioAnulacionFactura")

    # Añadir los elementos necesarios a la solicitud
    ET.SubElement(solicitud, "codigoAmbiente").text = os.getenv('CODIGO_AMBIENTE')
    ET.SubElement(solicitud, "codigoDocumentoSector").text = os.getenv('CODIGO_DOCUMENTO_SECTOR')
    ET.SubElement(solicitud, "codigoEmision").text = os.getenv('CODIGO_TIPO_EMISION')
    ET.SubElement(solicitud, "codigoModalidad").text = os.getenv('CODIGO_MODALIDAD')
    ET.SubElement(solicitud, "codigoPuntoVenta").text = os.getenv('CODIGO_PUNTO_VENTA')
    ET.SubElement(solicitud, "codigoSistema").text = os.getenv('CODIGO_SISTEMA')
    ET.SubElement(solicitud, "codigoSucursal").text = os.getenv('CODIGO_SUCURSAL')
    ET.SubElement(solicitud, "cufd").text = cufd
    ET.SubElement(solicitud, "cuis").text = os.getenv('CUIS')
    ET.SubElement(solicitud, "nit").text = os.getenv('NIT')
    ET.SubElement(solicitud, "tipoFacturaDocumento").text = os.getenv('CODIGO_TIPO_FACTURA')
    ET.SubElement(solicitud, "codigoMotivo").text = str(codigo_motivo)
    ET.SubElement(solicitud, "cuf").text = cuf

    # Convertir la estructura a una cadena XML
    return ET.tostring(envelope, encoding='utf-8', method='xml')

def enviar_solicitud_anulacion(cuf, cufd, codigo_motivo):
    url = "https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta"
    headers = {
        'Content-Type': 'text/xml;charset=UTF-8',
        'apikey': os.getenv('API_KEY')
    }

    solicitud_xml = construir_solicitud_anulacion(cuf, cufd, codigo_motivo)
    try:
        anulacion_logger.info(f"Enviando solicitud de anulación para CUF: {cuf}")
        anulacion_logger.debug(f"URL del servicio: {url}")
        anulacion_logger.debug(f"Cabeceras: {headers}")
        anulacion_logger.info(f"Construyendo solicitud de anulación para CUF: {cuf}")
        anulacion_logger.debug(f"CUFD vigente utilizado: {cufd}")
        anulacion_logger.debug(f"Parámetros de solicitud: {{'codigoAmbiente': os.getenv('CODIGO_AMBIENTE'), 'codigoPuntoVenta': os.getenv('CODIGO_PUNTO_VENTA'), 'codigoSistema': os.getenv('CODIGO_SISTEMA'), 'codigoSucursal': os.getenv('CODIGO_SUCURSAL'), 'nit': os.getenv('NIT'), 'codigoDocumentoSector': os.getenv('CODIGO_DOCUMENTO_SECTOR'), 'codigoEmision': os.getenv('CODIGO_TIPO_EMISION'), 'codigoModalidad': os.getenv('CODIGO_MODALIDAD'), 'cufd': cufd, 'cuis': os.getenv('CUIS'), 'tipoFacturaDocumento': os.getenv('CODIGO_TIPO_FACTURA'), 'codigoMotivo': codigo_motivo, 'cuf': cuf}}")
        anulacion_logger.debug(f"XML de solicitud (resumido): {solicitud_xml[:100]}...{solicitud_xml[-100:] if len(solicitud_xml) > 200 else ''}")
        anulacion_logger.debug("Enviando solicitud al servicio SIAT...")
        response = requests.post(url, headers=headers, data=solicitud_xml, timeout=45)
        anulacion_logger.debug(f"Respuesta recibida. Código HTTP: {response.status_code}")
        response_content = response.content.decode('utf-8') if response.content else ""
        anulacion_logger.debug(f"Respuesta (resumida): {response_content[:100]}...{response_content[-100:] if len(response_content) > 200 else ''}")
        anulacion_logger.info(f"[SIAT] Respuesta recibida: {response.content}")
        response.raise_for_status()
        return True, response.content
    except requests.exceptions.Timeout:
        anulacion_logger.error("Error inesperado: Timeout al intentar conectar con el servicio de anulación.")
        return False, "Error inesperado: Timeout al intentar conectar con el servicio de anulación."
    except requests.exceptions.HTTPError as http_err:
        anulacion_logger.error(f"HTTP error occurred: {http_err}")
        return False, f"HTTP error occurred: {http_err}"
    except Exception as e:
        anulacion_logger.error(f"An error occurred: {e}")
        return False, f"An error occurred: {e}"

def procesar_respuesta_anulacion(respuesta_xml, factura, descripcion_motivo):
    # Procesar el XML de respuesta para extraer la información relevante
    tree = ET.fromstring(respuesta_xml)
    codigo_estado = tree.find('.//codigoEstado').text
    codigo_descripcion = tree.find('.//codigoDescripcion').text

    # Manejar diferentes códigos de estado basados en la respuesta
    if codigo_estado == "905":  # Anulación confirmada
        factura.estado = "Anulada"
        factura.fechaAnulacion = datetime.now()
        factura.motivoAnulacion = descripcion_motivo  # Guardar el motivo seleccionado

        session = SessionLocal()
        try:
            session.add(factura)
            session.commit()
        except Exception as e:
            session.rollback()
            return False, f"Error al actualizar la factura: {e}"
        finally:
            session.close()

        return True, "Factura anulada correctamente."

    elif codigo_estado == "906":  # Anulación rechazada
        mensaje_error = tree.find('.//mensajesList/descripcion').text

        if mensaje_error is not None and "YA SE ENCUENTRA ANULADA" in mensaje_error:
            return False, "La factura ya fue anulada previamente."
        elif mensaje_error is not None and "NO EXISTE EN LA BASE DE DATOS DEL SIN" in mensaje_error:
            return False, "La factura no existe en la base de datos del SIN."
        else:
            return False, f"Error en la anulación: {mensaje_error}"

    elif codigo_estado == "924":  # Factura no existe
        return False, "La factura no existe en la base de datos del SIN."

    elif codigo_estado == "936":  # Factura ya anulada
        return False, "La factura ya ha sido anulada previamente."

    elif codigo_estado == "970":  # Factura fuera de plazo
        return False, "La factura está fuera del plazo permitido para su anulación."

    else:
        return False, f"Error desconocido en la anulación: {codigo_descripcion}"


def anular_factura(numero_factura, descripcion_motivo):
    try:
        facturacion_logger.info(f"Iniciando anulación de la factura {numero_factura}")
        cuf, factura = obtener_cuf_por_numero_factura(numero_factura)

        # Verificar si la factura no se encontró o si hubo un error
        if factura is None:
            return False, "No se encontró la factura especificada."
        
        # Verificar si factura es un mensaje de error (str)
        if isinstance(factura, str):
            facturacion_logger.error(f"Error al obtener la factura: {factura}")
            return False, f"Error al recuperar la factura: {factura}"

            # Registrar la respuesta completa del SIAT en el log (formato unificado)
            logger.info(f"[SIAT] Respuesta recibida: {respuesta_siat}")

            # Verificar si la factura está revertida y bloquear una nueva anulación
            if str(factura.estado) == "Valida" and factura.fechaValidacion is not None:
                return False, "La factura ya fue revertida y no puede ser anulada nuevamente."

        # Verificar si la fecha actual supera el plazo de anulación
        if datetime.now().month > factura.fechaEmision.month + 1:
            return False, "La factura está fuera del plazo para su anulación."

        cufd = obtener_cufd_vigente()
        if cufd is None:
            return False, "No se pudo obtener el CUFD vigente."

        codigo_motivo = obtener_codigo_motivo(descripcion_motivo)
        if codigo_motivo is None:
            return False, "No se pudo obtener el código del motivo de anulación."

        exito, respuesta = enviar_solicitud_anulacion(cuf, cufd, codigo_motivo)
        if exito:
            return procesar_respuesta_anulacion(respuesta, factura, descripcion_motivo)
        else:
            return False, respuesta
    except Exception as e:
        facturacion_logger.error(f"Error al anular factura {numero_factura}: {e}")
        facturacion_logger.error(traceback.format_exc())
        return False, f"Error durante la anulación: {str(e)}"
