import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from database import SessionLocal
from facturador.data_access import obtener_cuf_por_numero_factura
from datetime import datetime

load_dotenv()




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

    # Si no se encontró la factura, retornamos un mensaje de error claro
    if factura is None:
        return False, "No se encontró la factura especificada."

    # Si se encontró la factura, procedemos a la verificación
    exito, respuesta = enviar_solicitud_verificacion(cuf)
    if exito:
        return procesar_respuesta_verificacion(respuesta, factura)
    else:
        return False, respuesta



def actualizar_estado_factura(factura, estado_validacion, codigo_recepcion=None, mensaje_error=None):
    session = SessionLocal()
    try:
        # Ensure the factura object contains the correct data
        print(factura)

        # Update the factura's validation state
        factura.estadoValidacion = estado_validacion
        factura.codigoRecepcion = codigo_recepcion
        factura.mensajeError = mensaje_error

        # If the factura is valid, update the validation date and result
        if estado_validacion == "VALIDA":
            factura.fechaValidacion = datetime.now()
            factura.resultadoValidacion = "VALIDADA"
        
        # If the factura is annulled, update the result as annulled
        elif estado_validacion == "ANULADA":
            factura.fechaAnulacion = datetime.now()
            factura.resultadoValidacion = "ANULADA"
        
        # If the factura is rejected, keep the rejection result
        elif estado_validacion == "RECHAZADA":
            factura.resultadoValidacion = "RECHAZADA"

        # Add and commit changes to the database
        session.add(factura)
        session.commit()
        
        # Return success and the updated state
        return True, f"Factura: {estado_validacion}"
    except Exception as e:
        session.rollback()
        return False, f"Error al actualizar la factura: {str(e)}"
    finally:
        session.close()





def procesar_respuesta_verificacion(respuesta_xml, factura):
    # Procesar el XML de respuesta para extraer la información relevante
    tree = ET.fromstring(respuesta_xml)
    codigo_estado = tree.find('.//codigoEstado').text

    if factura is None:
        return False, "No se encontró la factura especificada."

    if codigo_estado == "690":  # Factura válida
        factura.estadoValidacion = "VALIDADA"
        factura.resultadoValidacion = "VALIDA"
        factura.fechaValidacion = datetime.now()
        codigo_recepcion = tree.find('.//codigoRecepcion')
        if codigo_recepcion is not None:
            factura.codigoRecepcion = codigo_recepcion.text

        # Actualizar el estado de la factura con los datos correspondientes
        return actualizar_estado_factura(factura, "VALIDA", factura.codigoRecepcion)

    elif codigo_estado == "691":  # Factura anulada
        factura.estadoValidacion = "ANULADA"
        factura.resultadoValidacion = "ANULADA"
        factura.mensajeError = "La factura ha sido anulada."
        
        # Actualizar el estado de la factura con estado anulada
        return actualizar_estado_factura(factura, "ANULADA", None, factura.mensajeError)

    elif codigo_estado == "902":  # Factura no encontrada
        mensaje_error = tree.find('.//mensajesList/descripcion').text
        factura.estadoValidacion = "RECHAZADA"
        factura.mensajeError = mensaje_error
        
        # Actualizar el estado de la factura con estado rechazada
        return actualizar_estado_factura(factura, "RECHAZADA", None, factura.mensajeError)

    else:
        # Manejo de otros códigos de error
        mensaje_error = tree.find('.//mensajesList/descripcion')
        if mensaje_error is not None:
            mensaje_error = mensaje_error.text
        else:
            mensaje_error = "Error desconocido en la verificación."
        
        factura.estadoValidacion = "RECHAZADA"
        factura.mensajeError = mensaje_error

        # Actualizar el estado de la factura con un error genérico
        return actualizar_estado_factura(factura, "RECHAZADA", None, mensaje_error)

