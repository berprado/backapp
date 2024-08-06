# negocio.py

from zeep import Client, Settings
from zeep.transports import Transport
from requests import Session
from mysql.connector import pooling, Error
from dotenv import load_dotenv
import os
import logging


# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Leer variables de entorno
API_KEY = os.getenv('API_KEY')
WSDL_URL = os.getenv('WSDL_URL_OPERACIONES')
CODIGO_SISTEMA = os.getenv('CODIGO_SISTEMA')
NIT = os.getenv('NIT')
CODIGO_AMBIENTE = int(os.getenv('CODIGO_AMBIENTE', '2'))
CODIGO_MODALIDAD = int(os.getenv('CODIGO_MODALIDAD', '1'))
CODIGO_SUCURSAL = int(os.getenv('CODIGO_SUCURSAL', '0'))
CUIS = os.getenv('CUIS')

# Configuración del logging
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de la sesión SOAP
session = Session()
session.headers.update({
    'apikey': f'TokenApi {API_KEY}',
    'Content-Type': 'text/xml;charset=UTF-8'
})
transport = Transport(session=session)
settings = Settings(strict=False, xml_huge_tree=True)
client = Client(wsdl=WSDL_URL, transport=transport, settings=settings)


# Configuración del pool de conexiones
def create_pool():
    try:
        pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=10,  # Incrementado el tamaño del pool
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE'),
            pool_reset_session=True,  # Restablece la sesión al obtener una conexión del pool
            connection_timeout=10  # Tiempo de espera para obtener una conexión en segundos
        )
        logging.info("Pool de conexiones creado exitosamente.")
        return pool
    except Error as e:
        logging.error(f"Error al crear el pool de conexiones: {e}")
        raise Exception(f"Error al crear el pool de conexiones: {e}")

# Obtener una conexión desde el pool
def get_connection(pool):
    try:
        connection = pool.get_connection()
        if connection.is_connected():
            logging.info("Conexión obtenida exitosamente del pool.")
            return connection
        else:
            logging.error("La conexión no se pudo establecer.")
            raise Exception("La conexión no se pudo establecer.")
    except Error as e:
        logging.error(f"Error al obtener la conexión del pool: {e}")
        raise Exception(f"Error al obtener la conexión del pool: {e}")

# Obtener tipos de punto de venta desde la base de datos
def get_tipo_punto_venta(pool):
    connection = get_connection(pool)
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT descripcion, codigoClasificador FROM sincronizarparametricatipopuntoventa")
        result = cursor.fetchall()
        return result
    except Error as e:
        logging.error(f"Error al obtener tipos de punto de venta: {e}")
        raise Exception(f"Error al obtener tipos de punto de venta: {e}")
    finally:
        cursor.close()
        connection.close()

# Registrar un nuevo punto de venta
def registrar_punto_venta(nombre_punto_venta, descripcion, tipo_seleccionado, codigo_ambiente, codigo_modalidad, codigo_sistema, codigo_sucursal, cuis, nit, pool):
    solicitud = {
        "codigoAmbiente": codigo_ambiente,
        "codigoModalidad": codigo_modalidad,
        "codigoSistema": codigo_sistema,
        "codigoSucursal": codigo_sucursal,
        "codigoTipoPuntoVenta": tipo_seleccionado,
        "cuis": cuis,
        "descripcion": descripcion,
        "nit": nit,
        "nombrePuntoVenta": nombre_punto_venta
    }

    try:
        response = client.service.registroPuntoVenta(SolicitudRegistroPuntoVenta=solicitud)
        if response['transaccion']:
            codigo_punto_venta = response['codigoPuntoVenta']
            # Obtener la descripción del tipo de punto de venta
            tipo_descripcion = next(
                (tipo['descripcion'] for tipo in get_tipo_punto_venta(pool) if tipo['codigoClasificador'] == tipo_seleccionado),
                None
            )
            # Actualizar la base de datos local
            connection = get_connection(pool)
            cursor = connection.cursor()
            try:
                cursor.execute('''
                INSERT INTO punto_venta (codigo_punto_venta, nombre_punto_venta, descripcion, tipo, estado, cod_sucursal)
                VALUES (%s, %s, %s, %s, %s, %s)
                ''', (codigo_punto_venta, nombre_punto_venta, descripcion, tipo_descripcion, 'Habilitado', codigo_sucursal))
                connection.commit()
                logging.info(f"Punto de venta {codigo_punto_venta} registrado exitosamente.")
            except Error as e:
                connection.rollback()
                logging.error(f"Error al insertar en la base de datos local: {e}")
                raise Exception(f"Error al insertar en la base de datos local: {e}")
            finally:
                cursor.close()
                connection.close()
        return response
    except Exception as e:
        logging.error(f"Error en la solicitud SOAP para registrar punto de venta: {e}")
        raise Exception(f"Error en la solicitud SOAP: {e}")

# Cerrar un punto de venta
def cerrar_punto_venta(codigo_punto_venta, codigo_ambiente, codigo_sistema, codigo_sucursal, cuis, nit, pool):
    solicitud = {
        "SolicitudCierrePuntoVenta": {
            "codigoAmbiente": codigo_ambiente,
            "codigoPuntoVenta": codigo_punto_venta,
            "codigoSistema": codigo_sistema,
            "codigoSucursal": codigo_sucursal,
            "cuis": cuis,
            "nit": nit
        }
    }

    try:
        response = client.service.cierrePuntoVenta(**solicitud)
        if response['transaccion']:
            # Actualizar la base de datos local
            connection = get_connection(pool)
            cursor = connection.cursor()
            try:
                cursor.execute("UPDATE punto_venta SET estado = 'Deshabilitado' WHERE codigo_punto_venta = %s", (codigo_punto_venta,))
                connection.commit()
                logging.info(f"Punto de venta {codigo_punto_venta} cerrado exitosamente.")
            except Error as e:
                connection.rollback()
                logging.error(f"Error al actualizar la base de datos local: {e}")
                raise Exception(f"Error al actualizar la base de datos local: {e}")
            finally:
                cursor.close()
                connection.close()
        return response
    except Exception as e:
        logging.error(f"Error en la solicitud SOAP para cerrar punto de venta: {e}")
        raise Exception(f"Error en la solicitud SOAP: {e}")

# Consultar puntos de venta habilitados
def consultar_puntos_venta(codigo_ambiente, codigo_sistema, codigo_sucursal, cuis, nit):
    solicitud = {
        "SolicitudConsultaPuntoVenta": {
            "codigoAmbiente": codigo_ambiente,
            "codigoSistema": codigo_sistema,
            "codigoSucursal": codigo_sucursal,
            "cuis": cuis,
            "nit": nit
        }
    }

    try:
        response = client.service.consultaPuntoVenta(**solicitud)
        if response:
            logging.info("Consulta de puntos de venta exitosa.")
            return response
        else:
            raise Exception("La transacción no se pudo completar en el servidor remoto.")
    except Exception as e:
        logging.error(f"Error en la solicitud SOAP para consultar puntos de venta: {e}")
        raise Exception(f"Error en la solicitud SOAP: {e}")

# Sincronizar puntos de venta entre el servidor remoto y la base de datos local
def sincronizar_puntos_venta(pool):
    try:
        # Obtener puntos de venta habilitados del servidor remoto
        response = consultar_puntos_venta(CODIGO_AMBIENTE, CODIGO_SISTEMA, CODIGO_SUCURSAL, CUIS, NIT)
        if response['transaccion']:
            # Filtrar puntos de venta remotos excluyendo el punto de venta 0
            puntos_venta_remotos = {
                pv['codigoPuntoVenta']: pv
                for pv in response['listaPuntosVentas']
                if pv['codigoPuntoVenta'] != 0
            }
            
            # Obtener la lista de tipos de punto de venta desde la base de datos local
            tipos_punto_venta = get_tipo_punto_venta(pool)

            # Conectar a la base de datos local
            connection = get_connection(pool)
            cursor = connection.cursor(dictionary=True)
            
            # Obtener puntos de venta habilitados de la base de datos local excluyendo el punto de venta 0
            cursor.execute("SELECT * FROM punto_venta WHERE estado = 'Habilitado' AND codigo_punto_venta != 0")
            puntos_venta_locales = {pv['codigo_punto_venta']: pv for pv in cursor.fetchall()}
            
            # Sincronizar puntos de venta
            for codigo, pv_remoto in puntos_venta_remotos.items():
                if codigo not in puntos_venta_locales:
                    # Obtener la descripción del tipo de punto de venta
                    tipo_descripcion = next(
                        (tipo['descripcion'] for tipo in tipos_punto_venta if tipo['codigoClasificador'] == pv_remoto['codigoTipoPuntoVenta']),
                        "Desconocido"
                    )
                    # Agregar nuevo punto de venta a la base de datos local
                    cursor.execute('''
                    INSERT INTO punto_venta (codigo_punto_venta, nombre_punto_venta, descripcion, tipo, estado, cod_sucursal)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (codigo, pv_remoto['nombrePuntoVenta'], "punto sincronizado", tipo_descripcion, 'Habilitado', CODIGO_SUCURSAL))
                    logging.info(f"Nuevo punto de venta sincronizado: {codigo}")
            
            for codigo, pv_local in puntos_venta_locales.items():
                if codigo not in puntos_venta_remotos:
                    # Deshabilitar punto de venta en la base de datos local
                    cursor.execute("UPDATE punto_venta SET estado = 'Deshabilitado' WHERE codigo_punto_venta = %s", (codigo,))
                    logging.info(f"Punto de venta deshabilitado: {codigo}")
            
            connection.commit()
            cursor.close()
            connection.close()
            return "Sincronización completada"
        else:
            raise Exception("La transacción no se pudo completar en el servidor remoto.")
    except Exception as e:
        logging.error(f"Error durante la sincronización de puntos de venta: {e}")
        raise Exception(f"Error durante la sincronización de puntos de venta: {e}")
