import os
import xmlschema
import gzip
import hashlib
import base64
import requests
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import sys
import traceback

# Agregar la ruta del directorio padre al path de Python si no está ya
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logger_config import get_logger, get_xml_logger

# Obtener loggers para este módulo
logger = get_logger()
xml_logger = get_xml_logger()

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Función para validar el XML contra el XSD principal
def validar_xml(xml_path, xsd_main_path):
    xml_logger.info(f"Validando XML: {xml_path} contra el esquema XSD: {xsd_main_path}")
    schema_main = xmlschema.XMLSchema(xsd_main_path)
    try:
        # Validar el XML contra el esquema principal
        schema_main.validate(xml_path)
        logger.info("El XML es válido contra el esquema principal.")
        return True
    except xmlschema.validators.exceptions.XMLSchemaValidationError as e:
        xml_logger.error(f"Error de validación: {e}")
        return False

# Función para comprimir el archivo XML en formato Gzip
def comprimir_xml(xml_path):
    logger.debug(f"Comprimiendo XML: {xml_path}")
    gzip_path = xml_path + '.gz'
    with open(xml_path, 'r', encoding='utf-8') as f_in, gzip.open(gzip_path, 'wb') as f_out:
        content = f_in.read()
        normalized_content = content.replace('\r\n', '\n')
        f_out.write(normalized_content.encode('utf-8'))
    logger.info(f"Archivo comprimido: {gzip_path}")
    return gzip_path

# Función para obtener el hash SHA-256 del archivo comprimido
def obtener_hash(gzip_path):
    logger.debug(f"Obteniendo hash SHA-256 del archivo: {gzip_path}")
    sha256_hash = hashlib.sha256()
    with open(gzip_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    hash_result = sha256_hash.hexdigest()
    logger.info(f"Hash SHA-256 obtenido: {hash_result}")
    return hash_result

# Función para construir el cuerpo de la solicitud SOAP
def construir_cuerpo_soap(archivo_base64, fecha_envio, hash_archivo, cufd):
    logger.debug("Construyendo cuerpo de la solicitud SOAP")
    return f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
       <soapenv:Header/>
       <soapenv:Body>
          <siat:recepcionFactura>
             <SolicitudServicioRecepcionFactura>
                <codigoAmbiente>{os.getenv('CODIGO_AMBIENTE')}</codigoAmbiente>
                <codigoDocumentoSector>{os.getenv('CODIGO_DOCUMENTO_SECTOR')}</codigoDocumentoSector>
                <codigoEmision>{os.getenv('CODIGO_TIPO_EMISION')}</codigoEmision>
                <codigoModalidad>{os.getenv('CODIGO_MODALIDAD')}</codigoModalidad>
                <codigoPuntoVenta>{os.getenv('CODIGO_PUNTO_VENTA')}</codigoPuntoVenta>
                <codigoSistema>{os.getenv('CODIGO_SISTEMA')}</codigoSistema>
                <codigoSucursal>{os.getenv('CODIGO_SUCURSAL')}</codigoSucursal>
                <cufd>{cufd}</cufd>
                <cuis>{os.getenv('CUIS')}</cuis>
                <nit>{os.getenv('NIT')}</nit>
                <tipoFacturaDocumento>{os.getenv('CODIGO_TIPO_FACTURA')}</tipoFacturaDocumento>
                <archivo>{archivo_base64}</archivo>
                <fechaEnvio>{fecha_envio}</fechaEnvio>
                <hashArchivo>{hash_archivo}</hashArchivo>
             </SolicitudServicioRecepcionFactura>
          </siat:recepcionFactura>
       </soapenv:Body>
    </soapenv:Envelope>
    """

# Función para enviar la solicitud SOAP
def enviar_solicitud(xml_path, xsd_main_path, fecha_envio, cufd):
    logger.debug("Enviando solicitud SOAP")
    if not validar_xml(xml_path, xsd_main_path):
        logger.error("El XML no es válido. No se puede proceder con la solicitud.")
        # En caso de error, devolver un diccionario con el error
        return {"error": "XML no válido"}

    gzip_path = comprimir_xml(xml_path)
    hash_archivo = obtener_hash(gzip_path)

    with open(gzip_path, 'rb') as f:
        archivo_base64 = base64.b64encode(f.read()).decode('utf-8')

    url = "https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta"
    headers = {
        'Content-Type': 'text/xml;charset=UTF-8',
        'apikey': os.getenv('API_KEY')
    }
    soap_body = construir_cuerpo_soap(archivo_base64, fecha_envio, hash_archivo, cufd)

    try:
        # Devuelve el objeto de respuesta HTTP
        response = requests.post(url, headers=headers, data=soap_body)
        response.raise_for_status()  # Esto lanzará una excepción para códigos de estado HTTP 4xx/5xx
        logger.info(f"Response status code: {response.status_code}")
        #logger.debug(f"Response content: {response.content.decode('utf-8')}")

        # Devuelve el objeto de respuesta HTTP
        return response
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")  # Manejo de errores HTTP
        # En caso de error, devolver un diccionario con el error
        return {"error": str(http_err)}
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Error connecting: {conn_err}")  # Manejo de errores de conexión
        # En caso de error, devolver un diccionario con el error
        return {"error": str(conn_err)}
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error: {timeout_err}")  # Manejo de errores de tiempo de espera
        # En caso de error, devolver un diccionario con el error
        return {"error": str(timeout_err)}
    except requests.exceptions.RequestException as req_err:
        logger.error(f"An error occurred: {req_err}")  # Manejo de cualquier otro error
        # En caso de error, devolver un diccionario con el error
        return {"error": str(req_err)}