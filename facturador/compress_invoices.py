#!/usr/bin/env python3
"""
Script extendido para:
1. Comprimir facturas XML en un archivo .tar.gz
2. Calcular el hash SHA-256 del archivo
3. Codificarlo en Base64
4. Generar la solicitud SOAP RAW lista para usar en SOAPUI
 5. Validar la recepción de un paquete de facturas con el código de recepción
"""
import requests
import tarfile
import os
import base64
import hashlib
from datetime import datetime

# 🧷 Configuración manual para completar el SOAP
CONFIG = {
    'codigoAmbiente': 2,
    'codigoDocumentoSector': 1,
    'codigoEmision': 2,
    'codigoModalidad': 1,
    'codigoPuntoVenta': 0,
    'codigoSistema': '54FA0D0FAF8D19AF6BE',
    'codigoSucursal': 0,
    'cufd': 'FBQW9Dfm9pQUE=hEMTlBRjZCRQ==Qksoa2NXR0paVUNTRGQTBEMEZBRj',
    'cuis': 'AC64B51F',
    'nit': 344096024,
    'tipoFacturaDocumento': 1,
    'cafc': '',  # opcional
    'cantidadFacturas': 2,
    'codigoEvento': 9365739,
    'soap_host': 'https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta',
    'api_key': 'TokenApi eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJiZXJwcmFkb0BnbWFpbC5jb20iLCJjb2RpZ29TaXN0ZW1hIjoiNTRGQTBEMEZBRjhEMTlBRjZCRSIsIm5pdCI6Ikg0c0lBQUFBQUFBQUFETTJNVEd3TkRNd01nRUFEQXU2T1FrQUFBQT0iLCJpZCI6NTI4MTU5OCwiZXhwIjoxNzYyNTIxOTIxLCJpYXQiOjE3NTQ1ODc0OTIsIm5pdERlbGVnYWRvIjozNDQwOTYwMjQsInN1YnNpc3RlbWEiOiJTRkUifQ.fhRra3vEC255ktHPoC28cGWeC0OD8hem9rJUQBbhIi1fRQJGWTh74l9ezddPC7FkGgnE0HALOcZjV8vdDQtzPQ'
}

def validar_recepcion_paquete(codigo_recepcion, config):
    """
    Envía la solicitud de validación de recepción de paquete al SIN.
    Imprime la solicitud SOAP y la respuesta.
    """
    soap_body = f'''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
   <soapenv:Header/>
   <soapenv:Body>
      <siat:validacionRecepcionPaqueteFactura>
         <SolicitudServicioValidacionRecepcionPaquete>
            <codigoAmbiente>{config['codigoAmbiente']}</codigoAmbiente>
            <codigoPuntoVenta>{config['codigoPuntoVenta']}</codigoPuntoVenta>
            <codigoSistema>{config['codigoSistema']}</codigoSistema>
            <codigoSucursal>{config['codigoSucursal']}</codigoSucursal>
            <nit>{config['nit']}</nit>
            <codigoDocumentoSector>{config['codigoDocumentoSector']}</codigoDocumentoSector>
            <codigoEmision>{config['codigoEmision']}</codigoEmision>
            <codigoModalidad>{config['codigoModalidad']}</codigoModalidad>
            <cufd>{config['cufd']}</cufd>
            <cuis>{config['cuis']}</cuis>
            <tipoFacturaDocumento>{config['tipoFacturaDocumento']}</tipoFacturaDocumento>
            <codigoRecepcion>{codigo_recepcion}</codigoRecepcion>
         </SolicitudServicioValidacionRecepcionPaquete>
      </siat:validacionRecepcionPaqueteFactura>
   </soapenv:Body>
</soapenv:Envelope>'''

    print("\n\n📨 SOLICITUD DE VALIDACIÓN RAW PARA SOAPUI:\n")
    print(f'''POST {config['soap_host']} HTTP/1.1
Accept-Encoding: gzip,deflate
Content-Type: text/xml;charset=UTF-8
SOAPAction: ""
apikey: {config['api_key']}
Host: pilotosiatservicios.impuestos.gob.bo
Connection: Keep-Alive
User-Agent: Apache-HttpClient/4.5.5 (Java/17.0.12)
Content-Length: {len(soap_body.encode('utf-8'))}

{soap_body}
''')

    headers = {
        "Accept-Encoding": "gzip,deflate",
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": "",
        "apikey": config['api_key'],
        "Host": "pilotosiatservicios.impuestos.gob.bo",
        "Connection": "Keep-Alive",
        "User-Agent": "Apache-HttpClient/4.5.5 (Java/17.0.12)"
    }
    print("\n🚀 Enviando solicitud de validación de paquete al SIAT...")
    try:
        response = requests.post(config['soap_host'], data=soap_body.encode('utf-8'), headers=headers, timeout=30)
        print(f"\n📬 Respuesta HTTP: {response.status_code}")
        print("\n📝 Contenido de la respuesta de validación:")
        print(response.text)
        print("✅ Solicitud de validación enviada correctamente.")
    except Exception as e:
        print(f"\n❌ Error al enviar la solicitud de validación: {e}")


def main():
    offline_dir = "offline_invoices"
    os.chdir(offline_dir)

    xml_files = ['factura_offline_ev85_n501.xml', 'factura_offline_ev85_n502.xml']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    gz_filename = f'paquete_facturas_ev85_{timestamp}.tar.gz'

    # Comprimir XMLs
    with tarfile.open(gz_filename, 'w:gz') as tar:
        for xml_file in xml_files:
            if os.path.exists(xml_file):
                tar.add(xml_file)
    
    # Leer archivo comprimido
    with open(gz_filename, 'rb') as f:
        file_data = f.read()
        hash_sha256 = hashlib.sha256(file_data).hexdigest()
        archivo_b64 = base64.b64encode(file_data).decode('utf-8')

    # Fecha envío en formato ISO8601
    fecha_envio = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]

    # Generar XML SOAP
    soap_body = f'''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
   <soapenv:Header/>
   <soapenv:Body>
      <siat:recepcionPaqueteFactura>
         <SolicitudServicioRecepcionPaquete>
            <codigoAmbiente>{CONFIG['codigoAmbiente']}</codigoAmbiente>
            <codigoDocumentoSector>{CONFIG['codigoDocumentoSector']}</codigoDocumentoSector>
            <codigoEmision>{CONFIG['codigoEmision']}</codigoEmision>
            <codigoModalidad>{CONFIG['codigoModalidad']}</codigoModalidad>
            <codigoPuntoVenta>{CONFIG['codigoPuntoVenta']}</codigoPuntoVenta>
            <codigoSistema>{CONFIG['codigoSistema']}</codigoSistema>
            <codigoSucursal>{CONFIG['codigoSucursal']}</codigoSucursal>
            <cufd>{CONFIG['cufd']}</cufd>
            <cuis>{CONFIG['cuis']}</cuis>
            <nit>{CONFIG['nit']}</nit>
            <tipoFacturaDocumento>{CONFIG['tipoFacturaDocumento']}</tipoFacturaDocumento>
            <archivo>{archivo_b64}</archivo>
            <fechaEnvio>{fecha_envio}</fechaEnvio>
            <hashArchivo>{hash_sha256}</hashArchivo>
            <cafc>{CONFIG['cafc']}</cafc>
            <cantidadFacturas>{CONFIG['cantidadFacturas']}</cantidadFacturas>
            <codigoEvento>{CONFIG['codigoEvento']}</codigoEvento>
         </SolicitudServicioRecepcionPaquete>
      </siat:recepcionPaqueteFactura>
   </soapenv:Body>
</soapenv:Envelope>'''

    # Mostrar solicitud RAW completa
    print("\n\n📨 SOLICITUD RAW PARA SOAPUI:\n")
    print(f'''POST {CONFIG['soap_host']} HTTP/1.1
Accept-Encoding: gzip,deflate
Content-Type: text/xml;charset=UTF-8
SOAPAction: ""
apikey: {CONFIG['api_key']}
Host: pilotosiatservicios.impuestos.gob.bo
Connection: Keep-Alive
User-Agent: Apache-HttpClient/4.5.5 (Java/17.0.12)
Content-Length: {len(soap_body.encode('utf-8'))}

{soap_body}
''')

    print("✅ Solicitud RAW generada correctamente.")
    
    # Enviar la solicitud al SIAT
    print("\n🚀 Enviando solicitud al SIAT...")
    headers = {
        "Accept-Encoding": "gzip,deflate",
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": "",
        "apikey": CONFIG['api_key'],
        "Host": "pilotosiatservicios.impuestos.gob.bo",
        "Connection": "Keep-Alive",
        "User-Agent": "Apache-HttpClient/4.5.5 (Java/17.0.12)"
    }
    try:
        response = requests.post(CONFIG['soap_host'], data=soap_body.encode('utf-8'), headers=headers, timeout=30)
        print(f"\n📬 Respuesta HTTP: {response.status_code}")
        print("\n📝 Contenido de la respuesta:")
        print(response.text)
        print("✅ Solicitud enviada correctamente.")
    except Exception as e:
        print(f"\n❌ Error al enviar la solicitud: {e}")

if __name__ == "__main__":
    # Ejecuta solo la validación de recepción de paquete
    # Puedes cambiar el valor de codigo_recepcion por el que recibiste del SIAT
    codigo_recepcion = "90fd82ff-8acc-11f0-8ba3-2fb828926c78"  # <-- Cambia aquí si es necesario
    print("\n=== VALIDACIÓN DE RECEPCIÓN DE PAQUETE ===")
    validar_recepcion_paquete(codigo_recepcion, CONFIG)
