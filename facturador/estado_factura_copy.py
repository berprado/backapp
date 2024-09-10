import os
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from database import SessionLocal
from models import FacturaCabecera
from datetime import datetime

load_dotenv()

def obtener_cuf_por_numero_factura(numero_factura):
    session = SessionLocal()
    try:
        factura = session.query(FacturaCabecera).filter_by(numeroFactura=numero_factura).first()
        if factura:
            return factura.cuf, factura
        else:
            return None, None  # Devuelve dos valores: None y None si no se encuentra la factura
    except Exception as e:
        return None, str(e)  # En caso de error, devuelve None y el mensaje de error
    finally:
        session.close()


def construir_solicitud_verificacion(cuf):
    envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
    body = ET.SubElement(envelope, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
    verificacion_estado_factura = ET.SubElement(body, "{https://siat.impuestos.gob.bo/}verificacionEstadoFactura")
    solicitud = ET.SubElement(verificacion_estado_factura, "SolicitudServicioVerificacionEstadoFactura")

    # Añadir los elementos necesarios a la solicitud
    ET.SubElement(solicitud, "codigoAmbiente").text = os.getenv('CODIGO_AMBIENTE')
    ET.SubElement(solicitud, "codigoDocumentoSector").text = os.getenv('CODIGO_DOCUMENTO_SECTOR')
    ET.SubElement(solicitud, "codigoEmision").text = os.getenv('CODIGO_TIPO_EMISION')
    ET.SubElement(solicitud, "codigoModalidad").text = os.getenv('CODIGO_MODALIDAD')
    ET.SubElement(solicitud, "codigoPuntoVenta").text = os.getenv('CODIGO_PUNTO_VENTA')
    ET.SubElement(solicitud, "codigoSistema").text = os.getenv('CODIGO_SISTEMA')
    ET.SubElement(solicitud, "codigoSucursal").text = os.getenv('CODIGO_SUCURSAL')
    ET.SubElement(solicitud, "cufd").text = os.getenv('CUFD')
    ET.SubElement(solicitud, "cuis").text = os.getenv('CUIS')
    ET.SubElement(solicitud, "nit").text = os.getenv('NIT')
    ET.SubElement(solicitud, "tipoFacturaDocumento").text = os.getenv('CODIGO_TIPO_FACTURA')
    ET.SubElement(solicitud, "cuf").text = cuf  # Aquí se envía el CUF, que puede estar vacío

    # Convertir la estructura a una cadena XML
    return ET.tostring(envelope, encoding='utf-8', method='xml')


def enviar_solicitud_verificacion(cuf):
    url = "https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta"
    headers = {
        'Content-Type': 'text/xml;charset=UTF-8',
        'apikey': os.getenv('API_KEY')
    }

    solicitud_xml = construir_solicitud_verificacion(cuf)
    try:
        response = requests.post(url, headers=headers, data=solicitud_xml)
        response.raise_for_status()
        return True, response.content
    except requests.exceptions.HTTPError as http_err:
        return False, f"HTTP error occurred: {http_err}"
    except Exception as e:
        return False, f"An error occurred: {e}"


def verificar_estado_factura(numero_factura):
    cuf, factura = obtener_cuf_por_numero_factura(numero_factura)
    
    # Si no se encontró la factura, se envía la solicitud con un CUF vacío
    if cuf is None:
        cuf = ""  # CUF vacío

    exito, respuesta = enviar_solicitud_verificacion(cuf)
    if exito:
        return procesar_respuesta_verificacion(respuesta, factura)  # Pasamos la factura para actualizarla si es válida
    else:
        return False, respuesta


def actualizar_estado_factura(factura, estado_validacion, codigo_recepcion=None, mensaje_error=None):
    session = SessionLocal()
    try:
        # Imprimir el objeto factura para asegurarte de que tiene los datos correctos
        print(factura)

        factura.estadoValidacion = estado_validacion
        factura.codigoRecepcion = codigo_recepcion
        factura.mensajeError = mensaje_error
        if estado_validacion == "VALIDA":
            factura.fechaValidacion = datetime.now()
            factura.resultadoValidacion = "VALIDADA"

        session.add(factura)
        session.commit()
        return True, "Estado de la factura actualizado correctamente."
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()




def procesar_respuesta_verificacion(respuesta_xml, factura=None):
    # Procesar el XML de respuesta para extraer la información relevante
    tree = ET.fromstring(respuesta_xml)
    codigo_descripcion = tree.find('.//codigoDescripcion').text
    codigo_estado = tree.find('.//codigoEstado').text

    if codigo_estado == "690":  # Si el código de estado indica una factura válida
        if factura:  # Si hay un objeto factura, actualiza su estado
            factura.fechaValidacion = datetime.now()  # Asignar la fecha y hora actual
            factura.resultadoValidacion = "VALIDADA"  # Establecer el resultado como VALIDADA
            exito, mensaje = actualizar_estado_factura(factura, "VALIDA", tree.find('.//codigoRecepcion').text)
        return True, f"Factura válida: {codigo_descripcion}"
    else:
        mensaje_error = tree.find('.//mensajesList/descripcion').text if tree.find('.//mensajesList') is not None else "Error desconocido"
        if factura:  # Si hay un objeto factura, actualiza su estado como "RECHAZADA"
            exito, mensaje = actualizar_estado_factura(factura, "RECHAZADA", mensaje_error=mensaje_error)
        return False, f"Factura no válida: {mensaje_error}"