import os
import xmlschema
import gzip
import hashlib
import base64
import requests
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Función para validar el XML contra el XSD principal
def validar_xml(xml_path, xsd_main_path):
    schema_main = xmlschema.XMLSchema(xsd_main_path)
    try:
        # Validar el XML contra el esquema principal
        schema_main.validate(xml_path)
        print("El XML es válido contra el esquema principal..")
        return True
    except xmlschema.validators.exceptions.XMLSchemaValidationError as e:
        print(f"Error de validación: {e}")
        return False

# Función para comprimir el archivo XML en formato Gzip
def comprimir_xml(xml_path):
    gzip_path = xml_path + '.gz'
    with open(xml_path, 'r', encoding='utf-8') as f_in, gzip.open(gzip_path, 'wb') as f_out:
        content = f_in.read()
        normalized_content = content.replace('\r\n', '\n')
        f_out.write(normalized_content.encode('utf-8'))
    return gzip_path

# Función para obtener el hash SHA-256 del archivo comprimido
def obtener_hash(gzip_path):
    sha256_hash = hashlib.sha256()
    with open(gzip_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# Función para enviar la solicitud SOAP
def enviar_solicitud(xml_path, xsd_main_path, fecha_envio, cufd):
    if not validar_xml(xml_path, xsd_main_path):
        print("El XML no es válido. No se puede proceder con la solicitud.")
        return

    gzip_path = comprimir_xml(xml_path)
    hash_archivo = obtener_hash(gzip_path)

    with open(gzip_path, 'rb') as f:
        archivo_base64 = base64.b64encode(f.read()).decode('utf-8')

    url = "https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta"
    headers = {
        'Content-Type': 'text/xml;charset=UTF-8',
        'apikey': os.getenv('API_KEY')
    }
    soap_body = f"""
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

    response = requests.post(url, headers=headers, data=soap_body)
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content.decode('utf-8')}")
    print(f"Request headers: {fecha_envio}")

