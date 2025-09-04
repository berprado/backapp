#!/usr/bin/env python3
"""
Script extendido para:
1. Comprimir facturas XML en un archivo .tar.gz
2. Calcular el hash SHA-256 del archivo
3. Codificarlo en Base64
4. Generar la solicitud SOAP RAW lista para usar en SOAPUI
"""

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
    'cufd': 'FBQW9Dfm9pQUE=hEMTlBRjZCRQ==QnxraThBRkpaVUNTRGQTBEMEZBRj',
    'cuis': '12345678',
    'nit': 10203040506,
    'tipoFacturaDocumento': 1,
    'cafc': '',  # opcional
    'cantidadFacturas': 2,
    'codigoEvento': 65,
    'soap_host': 'https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta',
    'api_key': 'TokenApi TU_API_KEY_AQUÍ'
}

def main():
    offline_dir = "offline_invoices"
    os.chdir(offline_dir)

    xml_files = ['factura_offline_ev68_n456.xml', 'factura_offline_ev68_n457.xml']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    gz_filename = f'paquete_facturas_ev68_{timestamp}.tar.gz'

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

    print("✅ Solicitud generada correctamente.")

if __name__ == "__main__":
    main()
