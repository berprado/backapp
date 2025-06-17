import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
from zeep import Client
import mysql.connector
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables de entorno y convertir las necesarias a enteros
wsdl_url_codigos = os.getenv("WSDL_URL_CODIGOS")
api_key = os.getenv("API_KEY")
codigo_ambiente = int(os.getenv("CODIGO_AMBIENTE"))
codigo_modalidad = int(os.getenv("CODIGO_MODALIDAD"))
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


def crear_tabla_cufd():
    with mysql.connector.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            # Crear la tabla
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cufd (
                id INT(11) NOT NULL AUTO_INCREMENT,
                codigo VARCHAR(255) DEFAULT NULL,
                codigo_control VARCHAR(20) DEFAULT NULL,
                fecha_solicitud TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_vigencia TIMESTAMP NULL DEFAULT NULL,
                vigente TINYINT(1) DEFAULT NULL,
                id_punto_venta INT(11) NOT NULL,
                direccion VARCHAR(255) DEFAULT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (id_punto_venta) REFERENCES punto_venta(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            print("Tabla 'cufd' funcionando.")

            # Crear la clave única
            cursor.execute("ALTER TABLE cufd ADD UNIQUE KEY (codigo_control);")
            print("Clave única en 'codigo_control' creada.")

            # Actualizar estructura de la tabla
            cursor.execute("ALTER TABLE cufd MODIFY fecha_solicitud TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;")
            print("Estructura de 'fecha_solicitud' actualizada.")



def solicitar_cufd():
    # Validar que la API Key esté configurada
    if not api_key:
        print("Error: La API Key no está configurada. Verifique el archivo .env.")
        return None

    # Crear el cliente SOAP para códigos
    client = Client(wsdl_url_codigos)

    # Configurar la sesión con la API Key
    session = requests.Session()
    session.headers.update({"apikey": api_key})
    client.transport.session = session

    # Definir la estructura SolicitudCufd
    SolicitudCufd = client.get_type('ns0:solicitudCufd')

    # Crear el objeto SolicitudCufd con los datos
    solicitud = SolicitudCufd(
        codigoAmbiente=codigo_ambiente,
        codigoModalidad=codigo_modalidad,  # Asumir modalidad de facturación electrónica en línea
        codigoPuntoVenta=codigo_punto_venta,
        codigoSistema=codigo_sistema,
        codigoSucursal=codigo_sucursal,
        cuis=cuis,
        nit=nit
    )

    try:
        # Llamar al método cufd para obtener un nuevo CUFD
        response = client.service.cufd(solicitud)
        print("Respuesta completa del servicio SOAP:", response)

        # Verificar si la transacción fue exitosa
        if not response.transaccion:
            print("Error en la transacción SOAP:", response.mensajesList)
            return None  # Salir si hay error

        # Extraer datos de la respuesta
        codigo_cufd = response.codigo
        codigo_control = response.codigoControl
        fecha_vigencia = response.fechaVigencia
        direccion = response.direccion

        # Conexión a MySQL
        with mysql.connector.connect(**db_config) as connection:
            with connection.cursor() as cursor:
                # Obtener el id_punto_venta
                print("Obteniendo id_punto_venta...")
                cursor.execute("SELECT id FROM punto_venta WHERE codigo_punto_venta = %s", (codigo_punto_venta,))
                resultado = cursor.fetchone()
                if resultado:
                    id_punto_venta = resultado[0]
                    print(f"id_punto_venta obtenido: {id_punto_venta}")

                    # Actualizar vigencia de CUFDs existentes a 0 sin modificar fecha_solicitud
                    print("Actualizando vigencia de CUFDs existentes...")
                    cursor.execute(
                        "UPDATE cufd SET vigente = 0 WHERE vigente = 1 AND id_punto_venta = %s",
                        (id_punto_venta,),
                    )

                    # Insertar el nuevo CUFD
                    print("Insertando nuevo CUFD...")
                    sql = """
                    INSERT INTO cufd (codigo, codigo_control, fecha_vigencia, vigente, id_punto_venta, direccion)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    val = (codigo_cufd, codigo_control, fecha_vigencia, 1, id_punto_venta, direccion)
                    cursor.execute(sql, val)

                    connection.commit()
                    print("CUFD solicitado y almacenado correctamente.")
                else:
                    print("Error: No se encontró el punto de venta en la tabla 'punto_venta'")
                    return None

    except mysql.connector.Error as db_error:
        print(f"Error en la base de datos: {db_error}")
        return None
    except Exception as e:
        print(f"Error durante la solicitud del CUFD: {e}")
        return None

    # Devolver el nuevo CUFD
    return codigo_cufd

print(codigo_punto_venta)
print(cuis)
if __name__ == "__main__":
    crear_tabla_cufd()
    solicitar_cufd()
