import os
import requests
from zeep import Client
from zeep.transports import Transport
import mysql.connector
from dotenv import load_dotenv

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

def sincronizar_lista_productos_servicios():
    mydb = None

    # Crear el cliente SOAP
    session = requests.Session()
    session.headers.update({"apikey": api_key})
    transport = Transport(session=session)
    client = Client(wsdl_url, transport=transport)

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
        # Llamar al método sincronizarListaProductosServicios
        response = client.service.sincronizarListaProductosServicios(solicitud)
        print("Respuesta completa del servicio SOAP:", response)

        # Verificar si la transacción fue exitosa
        if not response.transaccion:
            print("Error en la transacción SOAP:", response.mensajesList)
            return  # Salir si hay error

        # Conexión a MySQL
        mydb = mysql.connector.connect(**db_config)
        cursor = mydb.cursor()

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

        

        if response.listaCodigos:
            for codigo in response.listaCodigos:
                print("Procesando código:", codigo)
                codigoActividad = codigo.codigoActividad
                codigoProducto = codigo.codigoProducto
                descripcionProducto = codigo.descripcionProducto
                # Manejar el caso donde nandina puede ser una lista o None
                nandina = ",".join(codigo.nandina) if hasattr(codigo, 'nandina') else None

                # Insertar o actualizar datos
                sql = """
                INSERT INTO sincronizarListaProductosServicios (codigoActividad, codigoProducto, descripcionProducto, nandina, fecha_creacion, fecha_sincronizacion, estado_sincronizacion)
                VALUES (%s, %s, %s, %s, NOW(), NOW(), %s)
                ON DUPLICATE KEY UPDATE descripcionProducto = VALUES(descripcionProducto), nandina = VALUES(nandina), fecha_sincronizacion = NOW(), estado_sincronizacion = 'actualizado';
                """
                val = (codigoActividad, codigoProducto, descripcionProducto, nandina, 'actualizado')
                cursor.execute(sql, val)

            # Confirmar los cambios en la base de datos
            mydb.commit()

        print("¡Sincronización completada con éxito!")

    except Exception as e:
        print(f"Error durante la sincronización: {e}")

    finally:
        # Cerrar la conexión (si está abierta)
        if mydb and mydb.is_connected():
            cursor.close()
            mydb.close()

if __name__ == "__main__":
    sincronizar_lista_productos_servicios()
