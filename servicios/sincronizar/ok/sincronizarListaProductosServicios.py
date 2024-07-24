import os
import requests
from zeep import Client
from zeep.transports import Transport
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

def sincronizar_lista_productos_servicios():
    mydb = None
    logging.debug('Iniciando sincronización de lista de productos y servicios...')
    
    # Crear el cliente SOAP
    try:
        session = requests.Session()
        session.headers.update({"apikey": api_key})
        transport = Transport(session=session)
        client = Client(wsdl_url, transport=transport)
        logging.debug('Cliente SOAP creado.')
    except Exception as e:
        logging.error(f'Error al crear el cliente SOAP: {e}')
        logging.error(traceback.format_exc())
        return

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
        # Llamar al método sincronizarListaProductosServicios
        response = client.service.sincronizarListaProductosServicios(solicitud)
        logging.info(f'Respuesta completa del servicio SOAP: {response}')

        # Verificar si la transacción fue exitosa
        if not response.transaccion:
            logging.error(f'Error en la transacción SOAP: {response.mensajesList}')
            return  # Salir si hay error

        # Conexión a MySQL
        mydb = mysql.connector.connect(**db_config)
        cursor = mydb.cursor()
        logging.debug('Conexión a MySQL establecida.')

        # Crear la tabla de relación si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sincronizarListaProductosServicios (
            id INT(11) NOT NULL AUTO_INCREMENT,
            codigoActividad VARCHAR(20) NOT NULL,
            codigoProducto VARCHAR(20) NOT NULL,
            descripcionProducto VARCHAR(255) DEFAULT NULL,
            nandina TEXT DEFAULT NULL,
            fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            fecha_sincronizacion TIMESTAMP NULL DEFAULT NULL,
            estado_sincronizacion VARCHAR(10) DEFAULT NULL,
            PRIMARY KEY (id)
        ) ENGINE=INNODB,
        CHARACTER SET utf8mb4,
        COLLATE=utf8mb4_unicode_ci;
        """)
        logging.debug('Tabla sincronizarListaProductosServicios verificada/creada.')

        if response.listaCodigos:
            for codigo in response.listaCodigos:
                logging.info(f'Procesando código: {codigo}')
                codigoActividad = codigo.codigoActividad
                codigoProducto = codigo.codigoProducto
                descripcionProducto = codigo.descripcionProducto
                # Manejar el caso donde nandina puede ser una lista o None
                nandina = ",".join(codigo.nandina) if hasattr(codigo, 'nandina') else None

                # Insertar o actualizar datos
                sql = """
                INSERT INTO sincronizarListaProductosServicios (codigoActividad, codigoProducto, descripcionProducto, nandina, fecha_creacion, fecha_sincronizacion, estado_sincronizacion)
                VALUES (%s, %s, %s, %s, NOW(), NOW(), 'actualizado')
                ON DUPLICATE KEY UPDATE descripcionProducto = VALUES(descripcionProducto), nandina = VALUES(nandina), fecha_sincronizacion = NOW(), estado_sincronizacion = 'actualizado';
                """
                val = (codigoActividad, codigoProducto, descripcionProducto, nandina, 'actualizado')
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
    sincronizar_lista_productos_servicios()
    logging.debug('Fin de la función principal.')
