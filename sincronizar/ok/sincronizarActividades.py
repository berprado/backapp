import os
import requests
from zeep import Client
import mysql.connector
from dotenv import load_dotenv

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
mysql_host = os.getenv("MYSQL_HOST")
mysql_user = os.getenv("MYSQL_USER")
mysql_password = os.getenv("MYSQL_PASSWORD")
mysql_database = os.getenv("MYSQL_DATABASE")


def sincronizar():
    mydb = None  # Inicializar mydb como None para asegurarse de que está definida
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
        # Llamar al método sincronizarActividades
        response = client.service.sincronizarActividades(solicitud)
        print("Respuesta completa del servicio SOAP:", response)

        # Verificar si la transacción fue exitosa
        if not response.transaccion:
            print("Error en la transacción SOAP:", response.mensajesList)
            return  # Salir si hay error

        # Conexión a MySQL
        mydb = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        cursor = mydb.cursor()

        # Configuración de variables de sesión
        cursor.execute("SET sql_mode = '';")  # Deshabilitar modo estricto (si es necesario)

        # Crear la tabla si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sincronizaractividades (
            id INT(11) NOT NULL AUTO_INCREMENT,
            codigoCaeb VARCHAR(10) NOT NULL UNIQUE,
            descripcion VARCHAR(255) DEFAULT NULL,
            tipoActividad VARCHAR(255) DEFAULT NULL,
            fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
            fecha_sincronizacion TIMESTAMP NULL DEFAULT NULL,  
            estado_sincronizacion VARCHAR(10) DEFAULT NULL,
            PRIMARY KEY (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        if response.listaActividades:
            for actividad in response.listaActividades:
                print("Procesando actividad:", actividad)
                codigoCaeb = actividad.codigoCaeb
                descripcion = actividad.descripcion
                tipoActividad = actividad.tipoActividad

                # Insertar o actualizar datos
                sql = """
                INSERT INTO sincronizaractividades (codigoCaeb, descripcion, tipoActividad, fecha_creacion, fecha_sincronizacion, estado_sincronizacion)
                VALUES (%s, %s, %s, NOW(), NOW(), 'Exitoso')
                ON DUPLICATE KEY UPDATE 
                    descripcion = VALUES(descripcion), 
                    tipoActividad = VALUES(tipoActividad), 
                    fecha_sincronizacion = NOW(), 
                    estado_sincronizacion = 'Exitoso';
                """
                val = (codigoCaeb, descripcion, tipoActividad)
                cursor.execute(sql, val)

            # Confirmar los cambios en la base de datos
            mydb.commit()
        else:
            # Actualizar fecha de sincronización y estado de todas las leyendas
            cursor.execute(
                """
                UPDATE sincronizaractividades
                SET fecha_sincronizacion = NOW(),
                    estado_sincronizacion = 'Exitoso'
                """
            )
            mydb.commit()
            print("No se encontraron actividades para procesar.")

        print("¡Sincronización completada con éxito!")

    except mysql.connector.Error as err:
        print(f"Error en MySQL: {err}")
    except Exception as e:
        print(f"Error durante la sincronización: {e}")

    finally:
        # Cerrar la conexión (si está abierta)
        if mydb and mydb.is_connected():
            cursor.close()
            mydb.close()

if __name__ == "__main__":
    sincronizar()
