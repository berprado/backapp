import os
import requests
from zeep import Client
import mysql.connector
from dotenv import load_dotenv
import logging
import traceback

# Configurar el logging
log_file_path = os.path.splitext(__file__)[0] + '.txt'
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,  # Nivel de detalle
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables de entorno y convertir las necesarias a enteros
wsdl_url = os.getenv("WSDL_URL")
api_key = os.getenv("API_KEY")
codigo_ambiente = int(os.getenv("CODIGO_AMBIENTE"))
codigo_punto_venta = int(os.getenv("CODIGO_PUNTO_VENTA"))
codigo_sistema = os.getenv("CODIGO_SISTEMA")
codigo_sucursal = int(os.getenv("CODIGO_SUCURSAL"))
cuis = os.getenv("CUIS")
nit = int(os.getenv("NIT"))
mysql_host = os.getenv("MYSQL_HOST")
mysql_user = os.getenv("MYSQL_USER")
mysql_password = os.getenv("MYSQL_PASSWORD")
mysql_database = os.getenv("MYSQL_DATABASE")

logging.debug(f'Variables de entorno cargadas: WSDL_URL={wsdl_url}, API_KEY={api_key}, '
              f'CODIGO_AMBIENTE={codigo_ambiente}, CODIGO_PUNTO_VENTA={codigo_punto_venta}, '
              f'CODIGO_SISTEMA={codigo_sistema}, CODIGO_SUCURSAL={codigo_sucursal}, CUIS={cuis}, NIT={nit}, '
              f'MYSQL_HOST={mysql_host}, MYSQL_USER={mysql_user}, MYSQL_DATABASE={mysql_database}')

# Configuración de la conexión a la base de datos
db_config = {
    "host": mysql_host,
    "user": mysql_user,
    "password": mysql_password,
    "database": mysql_database
}

def sincronizar_parametrica_eventos_significativos():
    mydb = None  # Inicializar mydb como None para asegurarse de que está definida

    logging.debug('Iniciando sincronización de parametrica eventos significativos...')
    
    # Crear el cliente SOAP
    try:
        client = Client(wsdl_url)
        logging.debug('Cliente SOAP creado.')
    except Exception as e:
        logging.error(f'Error al crear el cliente SOAP: {e}')
        logging.error(traceback.format_exc())
        return

    # Configurar la sesión con la API Key
    session = requests.Session()
    session.headers.update({"apikey": api_key})
    client.transport.session = session
    logging.debug('Sesión configurada con la API Key.')

    # Definir la estructura solicitudSincronizacion
    try:
        SolicitudSincronizacion = client.get_type('ns0:solicitudSincronizacion')
        solicitud = SolicitudSincronizacion(
            codigoAmbiente=codigo_ambiente,
            codigoPuntoVenta=codigo_punto_venta,
            codigoSistema=codigo_sistema,
            codigoSucursal=codigo_sucursal,
            cuis=cuis,
            nit=nit
        )
        logging.info(f'Solicitud enviada: {solicitud}')
    except Exception as e:
        logging.error(f'Error al crear la solicitud de sincronización: {e}')
        logging.error(traceback.format_exc())
        return

    try:
        # Llamar al método sincronizarParametricaEventosSignificativos
        response = client.service.sincronizarParametricaEventosSignificativos(solicitud)
        logging.info(f'Respuesta completa del servicio SOAP: {response}')

        # Verificar si la transacción fue exitosa
        if not response.transaccion:
            logging.error(f'Error en la transacción SOAP: {response.mensajesList}')
            return  # Salir si hay error

        # Conexión a MySQL
        mydb = mysql.connector.connect(**db_config)
        cursor = mydb.cursor()
        logging.debug('Conexión a MySQL establecida.')

        # Configuración de variables de sesión
        cursor.execute("SET sql_mode = '';")

        # Crear la tabla si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sincronizarParametricaEventosSignificativos (
            id INT(11) NOT NULL AUTO_INCREMENT,
            codigoClasificador VARCHAR(5) NOT NULL,
            descripcion VARCHAR(255) DEFAULT NULL,
            fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            fecha_sincronizacion TIMESTAMP NULL DEFAULT NULL,
            estado_sincronizacion VARCHAR(10) DEFAULT NULL,
            PRIMARY KEY (id),
            UNIQUE KEY (codigoClasificador)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        logging.debug('Tabla sincronizarParametricaEventosSignificativos verificada/creada.')

        if response.listaCodigos:
            for codigo in response.listaCodigos:
                logging.info(f'Procesando código: {codigo}')
                codigoClasificador = codigo.codigoClasificador
                descripcion = codigo.descripcion

                # Insertar o actualizar datos
                sql = """
                INSERT INTO sincronizarParametricaEventosSignificativos (codigoClasificador, descripcion, fecha_creacion, fecha_sincronizacion, estado_sincronizacion)
                VALUES (%s, %s, NOW(), NOW(), 'Exitoso')
                ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion), fecha_sincronizacion = NOW(), estado_sincronizacion = 'Exitoso';
                """
                val = (codigoClasificador, descripcion)
                logging.debug(f'Ejecutando SQL: {sql} con valores {val}')
                cursor.execute(sql, val)

            # Confirmar los cambios en la base de datos
            mydb.commit()
            logging.debug('Cambios en la base de datos confirmados.')
        else:
            logging.info("No se encontraron códigos para procesar.")

        logging.info("¡Sincronización completada con éxito!")

    except mysql.connector.Error as err:
        logging.error(f"Error en MySQL: {err}")
        logging.error(traceback.format_exc())
    except Exception as e:
        logging.error(f"Error durante la sincronización: {e}")
        logging.error(traceback.format_exc())
    finally:
        # Cerrar la conexión (si está abierta)
        if mydb and mydb.is_connected():
            cursor.close()
            mydb.close()
            logging.debug('Conexión a MySQL cerrada.')

if __name__ == "__main__":
    logging.debug('Inicio de la función principal.')
    sincronizar_parametrica_eventos_significativos()
    logging.debug('Fin de la función principal.')
