import os
import pymysql
import logging
from zeep import Client, Settings
from zeep.transports import Transport
from requests import Session
from dotenv import load_dotenv
from datetime import datetime

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Leer variables de entorno
def get_env_variable(var_name):
    """Get the environment variable or raise an error."""
    value = os.getenv(var_name)
    if value is None:
        logger.error(f"Required environment variable {var_name} not set.")
        raise EnvironmentError(f"Required environment variable {var_name} not set.")
    return value

API_KEY = get_env_variable('API_KEY')
WSDL_URL_CODIGOS = get_env_variable('WSDL_URL_CODIGOS')
CODIGO_SISTEMA = get_env_variable('CODIGO_SISTEMA')
NIT = int(get_env_variable('NIT'))
CODIGO_AMBIENTE = int(get_env_variable('CODIGO_AMBIENTE'))
CODIGO_MODALIDAD = int(get_env_variable('CODIGO_MODALIDAD'))
CODIGO_SUCURSAL = int(get_env_variable('CODIGO_SUCURSAL'))
CODIGO_PUNTO_VENTA = int(get_env_variable('CODIGO_PUNTO_VENTA'))

# Parámetros de la base de datos
MYSQL_HOST = get_env_variable('MYSQL_HOST')
MYSQL_USER = get_env_variable('MYSQL_USER')
MYSQL_PASSWORD = get_env_variable('MYSQL_PASSWORD')
MYSQL_DATABASE = get_env_variable('MYSQL_DATABASE')
MYSQL_PORT = int(get_env_variable('MYSQL_PORT'))

# Conectar a la base de datos y obtener los puntos de venta habilitados
try:
    connection = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        port=MYSQL_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )
    with connection.cursor() as cursor:
        sql = """
        SELECT codigo_punto_venta, id
        FROM punto_venta
        WHERE cod_sucursal = %s AND estado = 'Habilitado'
        """
        cursor.execute(sql, (CODIGO_SUCURSAL,))
        puntos_venta_habilitados = cursor.fetchall()
    connection.close()
    logger.info("Puntos de venta habilitados obtenidos exitosamente.")
except Exception as e:
    logger.error(f"Error al conectar a la base de datos: {e}")
    raise

# Crear la lista de solicitudes de CUIS
datos_solicitud = [
    {'codigoSucursal': CODIGO_SUCURSAL, 'codigoPuntoVenta': CODIGO_PUNTO_VENTA}
]

for punto_venta in puntos_venta_habilitados:
    if punto_venta['codigo_punto_venta'] != CODIGO_PUNTO_VENTA:
        datos_solicitud.append({
            'codigoSucursal': CODIGO_SUCURSAL,
            'codigoPuntoVenta': punto_venta['codigo_punto_venta']
        })

logger.info(f"Solicitud de CUIS preparada: {datos_solicitud}")

# Configuración de la sesión SOAP
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
    'datosSolicitud': datos_solicitud
}

# Llamar al método cuisMasivo
try:
    response = client.service.cuisMasivo(SolicitudCuisMasivoSistemas=solicitud_cuis_masivo)
    logger.info(f"Respuesta del servicio cuisMasivo: {response}")
    print("Transacción:", response.transaccion)
    if hasattr(response, 'mensajesList') and response.mensajesList:
        for mensaje in response.mensajesList:
            print(f"Código: {mensaje.codigo} - Descripción: {mensaje.descripcion}")
    
    # Guardar los CUIS en la base de datos
    if hasattr(response, 'listaRespuestasCuis') and response.listaRespuestasCuis:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=MYSQL_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            with connection.cursor() as cursor:
                for respuesta in response.listaRespuestasCuis:
                    # Verificar si el CUIS ya está almacenado
                    sql_check = """
                    SELECT codigo FROM cuis
                    WHERE id_punto_venta = (
                        SELECT id FROM punto_venta WHERE codigo_punto_venta = %s AND cod_sucursal = %s
                    )
                    """
                    cursor.execute(sql_check, (respuesta.codigoPuntoVenta, CODIGO_SUCURSAL))
                    existing_cuis = cursor.fetchone()

                    if not existing_cuis or existing_cuis['codigo'] != respuesta.codigo:
                        sql_insert = """
                        INSERT INTO cuis (codigo, fecha_solicitud, fecha_vigencia, vigente, id_punto_venta)
                        VALUES (%s, %s, %s, %s, (
                            SELECT id FROM punto_venta WHERE codigo_punto_venta = %s AND cod_sucursal = %s
                        ))
                        ON DUPLICATE KEY UPDATE
                            codigo = VALUES(codigo),
                            fecha_vigencia = VALUES(fecha_vigencia),
                            vigente = VALUES(vigente),
                            fecha_solicitud = VALUES(fecha_solicitud)
                        """
                        cursor.execute(sql_insert, (
                            respuesta.codigo,
                            datetime.now(),
                            respuesta.fechaVigencia,
                            1,  # Assuming the CUIS is valid (vigente = 1)
                            respuesta.codigoPuntoVenta,
                            CODIGO_SUCURSAL
                        ))
                connection.commit()
                logger.info("CUIS guardados exitosamente en la base de datos.")
        except Exception as e:
            logger.error(f"Error al guardar CUIS en la base de datos: {e}")
            raise
        finally:
            connection.close()
except Exception as e:
    logger.error(f"Error al comunicarse con el servicio cuisMasivo: {e}")
    print("Transacción: False")
    print("Código: 999 - Descripción: Error al comunicarse con el servicio")
    print(f"Detalles del error: {e}")
    print("Asegúrate de que el WSDL contiene la operación cuisMasivo.")
