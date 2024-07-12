import os
import requests
from zeep import Client
from zeep.transports import Transport
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import logging

# Configurar logging para guardar en un archivo
log_file = 'sincronizacion.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_file),
    logging.StreamHandler()
])

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

# Configuración de la conexión a la base de datos
db_config = {
    "host": mysql_host,
    "user": mysql_user,
    "password": mysql_password,
    "database": mysql_database
}

def conectar_bd():
    try:
        conexion = mysql.connector.connect(**db_config)
        return conexion
    except Error as e:
        logging.error(f"Error al conectar a la base de datos: {e}")
        return None

def crear_tabla(cursor):
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
        PRIMARY KEY (id),
        UNIQUE KEY unique_codigo (codigoActividad, codigoProducto)
    ) ENGINE=INNODB,
    CHARACTER SET utf8mb4,
    COLLATE=utf8mb4_unicode_ci;
    """)

def obtener_datos_servicio():
    session = requests.Session()
    session.headers.update({"apikey": api_key})
    transport = Transport(session=session)
    client = Client(wsdl_url, transport=transport)

    SolicitudSincronizacion = client.get_type('ns0:solicitudSincronizacion')
    solicitud = SolicitudSincronizacion(
        codigoAmbiente=codigo_ambiente,
        codigoPuntoVenta=codigo_punto_venta,
        codigoSistema=codigo_sistema,
        codigoSucursal=codigo_sucursal,
        cuis=cuis,
        nit=nit
    )

    try:
        response = client.service.sincronizarListaProductosServicios(solicitud)
        logging.info("Respuesta completa del servicio SOAP: %s", response)
        if not response.transaccion:
            logging.error("Error en la transacción SOAP: %s", response.mensajesList)
            return None
        return response.listaCodigos
    except Exception as e:
        logging.error(f"Error durante la sincronización: {e}")
        return None

def limpiar_y_validar_datos(codigo):
    codigoActividad = codigo.codigoActividad
    codigoProducto = codigo.codigoProducto
    descripcionProducto = codigo.descripcionProducto
    nandina = ",".join(codigo.nandina) if hasattr(codigo, 'nandina') else None
    return codigoActividad, codigoProducto, descripcionProducto, nandina

def sincronizar_lista_productos_servicios():
    mydb = conectar_bd()
    if mydb is None:
        return

    productos = obtener_datos_servicio()
    if productos is None:
        return

    total_productos = len(productos)
    productos_procesados = 0
    productos_fallidos = []

    try:
        with mydb.cursor() as cursor:
            crear_tabla(cursor)

            for codigo in productos:
                logging.info("Procesando código: %s", codigo)
                codigoActividad, codigoProducto, descripcionProducto, nandina = limpiar_y_validar_datos(codigo)

                logging.info(
                    "Datos del producto - Código Actividad: %s, Código Producto: %s, Descripción Producto: %s, Nandina: %s",
                    codigoActividad, codigoProducto, descripcionProducto, nandina
                )

                try:
                    sql = """
                    INSERT INTO sincronizarListaProductosServicios (codigoActividad, codigoProducto, descripcionProducto, nandina, fecha_creacion, fecha_sincronizacion, estado_sincronizacion)
                    VALUES (%s, %s, %s, %s, NOW(), NOW(), %s)
                    ON DUPLICATE KEY UPDATE descripcionProducto = VALUES(descripcionProducto), nandina = VALUES(nandina), fecha_sincronizacion = NOW(), estado_sincronizacion = 'actualizado';
                    """
                    val = (codigoActividad, codigoProducto, descripcionProducto, nandina, 'actualizado')
                    cursor.execute(sql, val)
                    mydb.commit()
                    productos_procesados += 1
                    logging.info("SQL Ejecutado: %s con valores %s", cursor.statement, val)
                except Error as e:
                    mydb.rollback()
                    productos_fallidos.append({
                        "codigoActividad": codigoActividad,
                        "codigoProducto": codigoProducto,
                        "error": str(e)
                    })
                    logging.error(f"Error al ejecutar SQL: {e}")
                    continue

            logging.info("¡Sincronización completada con éxito! Productos procesados: %d de %d", productos_procesados, total_productos)

            # Validar los datos insertados/actualizados
            cursor.execute("SELECT COUNT(*) FROM sincronizarListaProductosServicios")
            count_result = cursor.fetchone()
            logging.info("Cantidad de productos en la base de datos: %s", count_result[0])

            # Reportar productos fallidos
            if productos_fallidos:
                logging.error("Productos que fallaron al procesarse:")
                for producto in productos_fallidos:
                    logging.error("Código Actividad: %s, Código Producto: %s, Error: %s",
                                  producto["codigoActividad"], producto["codigoProducto"], producto["error"])

    except Error as e:
        logging.error(f"Error durante la sincronización: {e}")
    finally:
        if mydb.is_connected():
            mydb.close()

if __name__ == "__main__":
    sincronizar_lista_productos_servicios()
