import os
import requests
from zeep import Client
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


def obtener_origen_producto(id_producto):
    return "importado"  # Asumir que todos los productos son importados


def sincronizar_lista_productos_servicios():
    mydb = None 

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

        # Configuración de variables de sesión
        cursor.execute("SET sql_mode = '';") 

        # Crear la tabla de relación si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS producto_nandina (
            id INT(11) NOT NULL AUTO_INCREMENT,
            id_producto INT(11) NOT NULL,
            codigoActividad VARCHAR(20) NOT NULL,
            codigoProducto VARCHAR(20) NOT NULL, 
            descripcionProducto VARCHAR(255) DEFAULT NULL,
            nandina VARCHAR(255) DEFAULT NULL, 
            origenProducto VARCHAR(20) NOT NULL, 
            fecha_creacion DATETIME DEFAULT NULL,
            fecha_sincronizacion DATETIME DEFAULT NULL,
            PRIMARY KEY (id),
            UNIQUE KEY (id_producto, origenProducto), 
            FOREIGN KEY (id_producto) REFERENCES productos(codigo_sin) 
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        if response.listaCodigos:
            for codigo in response.listaCodigos:
                print("Procesando código:", codigo)
                codigoActividad = codigo.codigoActividad
                codigoProducto = codigo.codigoProducto
                descripcionProducto = codigo.descripcionProducto
                # Obtener los id_producto de la tabla "productos" con el mismo codigo_sin
                cursor.execute("SELECT id FROM productos WHERE codigo_sin = %s", (codigoProducto,))
                resultados = cursor.fetchall()
                if resultados:
                    for id_producto, in resultados:
                        # Obtener el origen del producto (asumimos "importado")
                        origenProducto = obtener_origen_producto(id_producto)
                        # Manejar el caso donde nandina puede ser una lista o None
                        nandina = ",".join(codigo.nandina) if codigo.nandina else None

                        # Insertar o actualizar datos
                        sql = """
                        INSERT INTO producto_nandina (id_producto, codigoActividad, codigoProducto, descripcionProducto, nandina, origenProducto, fecha_creacion, fecha_sincronizacion)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON DUPLICATE KEY UPDATE descripcionProducto = VALUES(descripcionProducto), nandina = VALUES(nandina), origenProducto = VALUES(origenProducto), fecha_sincronizacion = NOW();
                        """
                        val = (id_producto, codigoActividad, codigoProducto, descripcionProducto, nandina, origenProducto)
                        cursor.execute(sql, val)
                else:
                    print(f"Advertencia: No se encontró el producto con código SIN {codigoProducto} en la tabla 'productos'")

            # Confirmar los cambios en la base de datos
            mydb.commit()
        else:
            print("No se encontraron códigos para procesar.")

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