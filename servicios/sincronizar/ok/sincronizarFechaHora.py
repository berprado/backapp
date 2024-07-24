import os
import requests
from zeep import Client
from zeep.helpers import serialize_object
from dotenv import load_dotenv
from datetime import datetime, timezone
import pytz

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables de entorno y convertir las necesarias a entero
wsdl_url = os.getenv("WSDL_URL")
api_key = os.getenv("API_KEY")
codigo_ambiente = int(os.getenv("CODIGO_AMBIENTE"))  # Convertido a entero
codigo_punto_venta = int(os.getenv("CODIGO_PUNTO_VENTA"))  # Convertido a entero
codigo_sistema = os.getenv("CODIGO_SISTEMA")
codigo_sucursal = int(os.getenv("CODIGO_SUCURSAL"))  # Convertido a entero
cuis = os.getenv("CUIS")
nit = int(os.getenv("NIT"))  # Convertido a entero

def sincronizar_fecha_hora():
    # Crear el cliente SOAP
    client = Client(wsdl_url)

    # Configurar la sesión con la API Key
    session = requests.Session()
    session.headers.update({"apikey": api_key})
    client.transport.session = session

    # Definir la estructura solicitudSincronizacion
    SolicitudSincronizacion = client.get_type('ns0:solicitudSincronizacion')

    # Crear el objeto SolicitudSincronizacion con los datos
    solicitud = SolicitudSincronizacion(
        codigoAmbiente=codigo_ambiente,
        codigoPuntoVenta=codigo_punto_venta,
        codigoSistema=codigo_sistema,
        codigoSucursal=codigo_sucursal,
        cuis=cuis,
        nit=nit
    )

    try:
        # Llamar al método sincronizarFechaHora
        response = client.service.sincronizarFechaHora(solicitud)
        response_data = serialize_object(response)
        print("Respuesta completa del servicio SOAP:", response_data)

        # Obtener la hora local en UTC
        local_time = datetime.now(pytz.utc)
        print("Hora local:", local_time)

        # Obtener la hora de la respuesta y hacerla offset-aware
        server_time_str = response_data['fechaHora']
        server_time = datetime.fromisoformat(server_time_str.replace("Z", "+00:00")).astimezone(pytz.utc)
        print("Hora del servidor:", server_time)

        # Calcular la diferencia en milisegundos
        time_difference_ms = (local_time - server_time).total_seconds() * 1000
        print("Diferencia en milisegundos:", abs(time_difference_ms))

    except Exception as e:
        print(f"Error durante la sincronización: {e}")

if __name__ == "__main__":
    sincronizar_fecha_hora()