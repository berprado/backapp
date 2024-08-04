import os
from zeep import Client, Settings
from zeep.transports import Transport
from requests import Session
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Leer variables de entorno
def get_env_variable(var_name):
    """Get the environment variable or raise an error."""
    value = os.getenv(var_name)
    if value is None:
        raise EnvironmentError(f"Required environment variable {var_name} not set.")
    return value

API_KEY = get_env_variable('API_KEY')
WSDL_URL_CODIGOS = get_env_variable('WSDL_URL_CODIGOS')
CODIGO_SISTEMA = get_env_variable('CODIGO_SISTEMA')
NIT = int(get_env_variable('NIT'))
CODIGO_AMBIENTE = int(get_env_variable('CODIGO_AMBIENTE'))
CODIGO_MODALIDAD = int(get_env_variable('CODIGO_MODALIDAD'))

# Configuración de la sesión
session = Session()
session.headers.update({
    'apikey': f'TokenApi {API_KEY}',
    'Content-Type': 'text/xml;charset=UTF-8'
})
transport = Transport(session=session)
settings = Settings(strict=False, xml_huge_tree=True)
client = Client(wsdl=WSDL_URL_CODIGOS, transport=transport, settings=settings)

# Crear el diccionario de solicitud
solicitud_cuis_masivo = {
    'codigoAmbiente': CODIGO_AMBIENTE,
    'codigoModalidad': CODIGO_MODALIDAD,
    'codigoSistema': CODIGO_SISTEMA,
    'nit': NIT,
    'datosSolicitud': [
        {'codigoSucursal': 0, 'codigoPuntoVenta': 0},
        {'codigoSucursal': 0, 'codigoPuntoVenta': 0}
    ]
}

# Llamar al método cuisMasivo
try:
    response = client.service.cuisMasivo(SolicitudCuisMasivoSistemas=solicitud_cuis_masivo)
    # Imprimir la respuesta
    print("Transacción:", response.transaccion)
    if hasattr(response, 'mensajesList') and response.mensajesList:
        for mensaje in response.mensajesList:
            print(f"Código: {mensaje.codigo} - Descripción: {mensaje.descripcion}")
    if hasattr(response, 'listaRespuestasCuis') and response.listaRespuestasCuis:
        for respuesta in response.listaRespuestasCuis:
            print(f"Código CUIS: {respuesta.codigo} - Sucursal: {respuesta.codigoSucursal} - Punto de Venta: {respuesta.codigoPuntoVenta}")
except Exception as e:
    print("Transacción: False")
    print("Código: 999 - Descripción: Error al comunicarse con el servicio")
    print(f"Detalles del error: {e}")
    print("Asegúrate de que el WSDL contiene la operación cuisMasivo.")
