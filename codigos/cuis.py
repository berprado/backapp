from zeep import Client
from zeep.transports import Transport
from requests import Session
import os
from dotenv import load_dotenv

# Cargar el archivo .env
load_dotenv()

# Obtener los valores del archivo .env
# Obtener las variables de entorno y convertir las necesarias a enteros
wsdl_url_codigos = os.getenv("WSDL_URL_CODIGOS")
api_key = os.getenv("API_KEY")
codigo_ambiente = int(os.getenv("CODIGO_AMBIENTE"))
codigo_modalidad = int(os.getenv("CODIGO_MODALIDAD"))
codigo_punto_venta = int(os.getenv("CODIGO_PUNTO_VENTA"))
codigo_sistema = os.getenv("CODIGO_SISTEMA")
codigo_sucursal = int(os.getenv("CODIGO_SUCURSAL"))
cuis = os.getenv("CUIS")
nit = int(os.getenv("NIT"))
mysql_host = os.getenv("MYSQL_HOST")
mysql_user = os.getenv("MYSQL_USER")
mysql_password = os.getenv("MYSQL_PASSWORD")
mysql_database = os.getenv("MYSQL_DATABASE")



# Configuración del cliente zeep
session = Session()
session.verify = False
session.headers.update({
    'apikey': api_key
})
transport = Transport(session=session)
client = Client(wsdl=wsdl_url_codigos, transport=transport)

# Datos para la solicitud del CUIS
solicitud_cuis = {
    'codigoAmbiente': codigo_ambiente,  # Ambiente de pruebas y piloto
    'codigoModalidad': codigo_modalidad,  # Electrónica en Línea
    'codigoPuntoVenta': codigo_punto_venta,  #
    'codigoSistema': codigo_sistema,  # Código de sistema asignado
    'codigoSucursal': codigo_sucursal,  # Casa matriz
    'nit': nit  # NIT del emisor
}

# Realizar la solicitud
response = client.service.cuis(solicitud_cuis)

# Procesar la respuesta
if response.RespuestaCuis.transaccion:
    codigo_cuis = response.RespuestaCuis.codigo
    fecha_vigencia = response.RespuestaCuis.fechaVigencia
    print(f'CUIS: {codigo_cuis}')
    print(f'Fecha de Vigencia: {fecha_vigencia}')
else:
    for mensaje in response.RespuestaCuis.mensajesList:
        print(f'Error: {mensaje.descripcion}')
