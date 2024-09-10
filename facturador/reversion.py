import os
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from database import SessionLocal
from models import FacturaCabecera
from datetime import datetime
from data_access import obtener_mensaje_por_codigo

load_dotenv()

def obtener_cuf_por_numero_factura(numero_factura):
    session = SessionLocal()
    try:
        factura = session.query(FacturaCabecera).filter_by(numeroFactura=numero_factura).first()
        if factura:
            return factura.cuf, factura
        else:
            return None, None
    except Exception as e:
        return None, str(e)
    finally:
        session.close()

def construir_solicitud_reversion(cuf):
    envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
    body = ET.SubElement(envelope, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
    reversion_anulacion_factura = ET.SubElement(body, "{https://siat.impuestos.gob.bo/}reversionAnulacionFactura")
    solicitud = ET.SubElement(reversion_anulacion_factura, "SolicitudServicioReversionAnulacionFactura")

    # Añadir los elementos necesarios a la solicitud
    ET.SubElement(solicitud, "codigoAmbiente").text = os.getenv('CODIGO_AMBIENTE')
    ET.SubElement(solicitud, "codigoPuntoVenta").text = os.getenv('CODIGO_PUNTO_VENTA')
    ET.SubElement(solicitud, "codigoSistema").text = os.getenv('CODIGO_SISTEMA')
    ET.SubElement(solicitud, "codigoSucursal").text = os.getenv('CODIGO_SUCURSAL')
    ET.SubElement(solicitud, "nit").text = os.getenv('NIT')
    ET.SubElement(solicitud, "codigoDocumentoSector").text = os.getenv('CODIGO_DOCUMENTO_SECTOR')
    ET.SubElement(solicitud, "codigoEmision").text = os.getenv('CODIGO_TIPO_EMISION')
    ET.SubElement(solicitud, "codigoModalidad").text = os.getenv('CODIGO_MODALIDAD')
    ET.SubElement(solicitud, "cufd").text = os.getenv('CUFD')
    ET.SubElement(solicitud, "cuis").text = os.getenv('CUIS')
    ET.SubElement(solicitud, "tipoFacturaDocumento").text = os.getenv('CODIGO_TIPO_FACTURA')
    ET.SubElement(solicitud, "cuf").text = cuf

    # Convertir la estructura a una cadena XML
    return ET.tostring(envelope, encoding='utf-8', method='xml')

def enviar_solicitud_reversion(cuf):
    url = "https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta"
    headers = {
        'Content-Type': 'text/xml;charset=UTF-8',
        'apikey': os.getenv('API_KEY')
    }

    solicitud_xml = construir_solicitud_reversion(cuf)
    try:
        response = requests.post(url, headers=headers, data=solicitud_xml)
        response.raise_for_status()
        return True, response.content
    except requests.exceptions.HTTPError as http_err:
        return False, f"HTTP error occurred: {http_err}"
    except Exception as e:
        return False, f"An error occurred: {e}"

def procesar_respuesta_reversion(respuesta_xml, factura):
    # Procesar el XML de respuesta para extraer la información relevante
    tree = ET.fromstring(respuesta_xml)
    codigo_estado = tree.find('.//codigoEstado').text

    # Obtener la descripción del código desde la base de datos
    descripcion_codigo = obtener_mensaje_por_codigo(codigo_estado)

    if codigo_estado == "907":  # Reversión confirmada
        factura.estado = "Valida"
        factura.fechaValidacion = datetime.now()

        session = SessionLocal()
        try:
            session.add(factura)
            session.commit()
        except Exception as e:
            session.rollback()
            return False, f"Error al actualizar la factura: {e}"
        finally:
            session.close()

        return True, f"Reversión de anulación realizada correctamente: {descripcion_codigo}"

    elif codigo_estado == "981":  # Factura no disponible para reversión
        return False, f"La factura ya fue revertida previamente: {descripcion_codigo}"

    elif codigo_estado == "924":  # Factura no existe en la base de datos
        return False, f"Factura no existe en la base de datos del SIN: {descripcion_codigo}"

    elif codigo_estado == "3011":  # Sistema no autorizado
        return False, f"El sistema no está autorizado para utilizar la reversión: {descripcion_codigo}"

    elif codigo_estado == "3012":  # Solicitud de reversión fuera de plazo
        return False, f"La solicitud de reversión fue realizada fuera de plazo: {descripcion_codigo}"

    else:
        return False, f"Error desconocido en la reversión: {descripcion_codigo}"

def revertir_anulacion_factura(numero_factura):
    cuf, factura = obtener_cuf_por_numero_factura(numero_factura)

    if factura is None:
        return False, "No se encontró la factura especificada."

    exito, respuesta = enviar_solicitud_reversion(cuf)
    if exito:
        return procesar_respuesta_reversion(respuesta, factura)
    else:
        return False, respuesta
