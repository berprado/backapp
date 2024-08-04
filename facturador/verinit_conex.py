import os
import argparse
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
CODIGO_SUCURSAL = int(get_env_variable('CODIGO_SUCURSAL'))
CUIS = get_env_variable('CUIS')

# Configuración de la sesión
session = Session()
session.headers.update({
    'apikey': f'TokenApi {API_KEY}',
    'Content-Type': 'text/xml;charset=UTF-8'
})
transport = Transport(session=session)
settings = Settings(strict=False, xml_huge_tree=True)
client = Client(wsdl=WSDL_URL_CODIGOS, transport=transport, settings=settings)

# Configurar el parser de argumentos
parser = argparse.ArgumentParser(
    description="Verificar NIT a través del servicio SIAT",
    epilog="""
    Ejemplos de uso:
    1. Proporcionar el NIT a verificar mediante la línea de comando:
       python script.py --nit-verificar 1234567890
    2. Introducir el NIT a verificar de manera interactiva:
       python script.py
    """
)

parser.add_argument('--nit-verificar', type=int, help="NIT para verificación")

# Parsear los argumentos
args = parser.parse_args()

# Obtener NIT a verificar
if args.nit_verificar:
    NIT_PARA_VERIFICACION = args.nit_verificar
else:
    NIT_PARA_VERIFICACION = int(input("Ingrese el NIT para verificación: "))

# Verificar las operaciones disponibles
print("Operaciones disponibles:", client.service._binding._operations.keys())

# Llamar al método verificarComunicacion para asegurar la conectividad
try:
    response_comunicacion = client.service.verificarComunicacion()
    print("Transacción de comunicación:", response_comunicacion.transaccion)
    if hasattr(response_comunicacion, 'mensajesList') and response_comunicacion.mensajesList:
        for mensaje in response_comunicacion.mensajesList:
            print(f"Código: {mensaje.codigo} - Descripción: {mensaje.descripcion}")
    else:
        print("Código: N/A - Descripción: No se recibieron mensajes de comunicación")
except Exception as e:
    print("Transacción de comunicación: False")
    print("Código: 999 - Descripción: Error al comunicarse con el servicio")
    print(f"Detalles del error: {e}")
    print("Asegúrate de que el WSDL contiene la operación verificarComunicacion.")
    exit(1)  # Salir del script si no se puede verificar la comunicación

# Crear el diccionario de solicitud para verificar NIT
solicitud_verificar_nit = {
    'codigoAmbiente': CODIGO_AMBIENTE,
    'codigoModalidad': CODIGO_MODALIDAD,
    'codigoSistema': CODIGO_SISTEMA,
    'codigoSucursal': CODIGO_SUCURSAL,
    'cuis': CUIS,
    'nit': NIT,
    'nitParaVerificacion': NIT_PARA_VERIFICACION
}

# Llamar al método verificarNit
try:
    response = client.service.verificarNit(SolicitudVerificarNit=solicitud_verificar_nit)
    # Imprimir la respuesta
    print("Transacción:", response.transaccion)
    if hasattr(response, 'mensajesList') and response.mensajesList:
        for mensaje in response.mensajesList:
            print(f"Código: {mensaje.codigo} - Descripción: {mensaje.descripcion}")
    else:
        print("Código: N/A - Descripción: No se recibieron mensajes")
except Exception as e:
    print("Transacción: False")
    print("Código: 999 - Descripción: Error al comunicarse con el servicio")
    print(f"Detalles del error: {e}")
    print("Asegúrate de que el WSDL contiene la operación verificarNit.")
