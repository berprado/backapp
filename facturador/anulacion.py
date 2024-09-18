import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from database import SessionLocal
from facturador.models import FacturaCabecera, SincronizarParametricaMotivoAnulacion, Cufd
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
        response = requests.post(url, headers=headers, data=solicitud_xml)
        response.raise_for_status()
        return True, response.content
    except requests.exceptions.HTTPError as http_err:
        return False, f"HTTP error occurred: {http_err}"
    except Exception as e:
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

        if "YA SE ENCUENTRA ANULADA" in mensaje_error:
            return False, "La factura ya fue anulada previamente."
        elif "NO EXISTE EN LA BASE DE DATOS DEL SIN" in mensaje_error:
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
    cuf, factura = obtener_cuf_por_numero_factura(numero_factura)

    if factura is None:
        return False, "No se encontró la factura especificada."

    # Verificar si la factura está revertida y bloquear una nueva anulación
    if factura.estado == "Valida" and factura.fechaValidacion is not None:
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
