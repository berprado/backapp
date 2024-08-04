import streamlit as st
from zeep import Client, Settings
from zeep.transports import Transport
from requests import Session
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Leer variables de entorno
API_KEY = os.getenv('API_KEY')
WSDL_URL = os.getenv('WSDL_URL_OPERACIONES')
CODIGO_SISTEMA = os.getenv('CODIGO_SISTEMA')
NIT = os.getenv('NIT')
CODIGO_AMBIENTE = int(os.getenv('CODIGO_AMBIENTE', '2'))
CODIGO_SUCURSAL = int(os.getenv('CODIGO_SUCURSAL', '0'))
CUIS = os.getenv('CUIS')

# Configuración de la conexión a la base de datos MySQL
def create_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE')
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return None

# Configuración de la sesión
session = Session()
session.headers.update({
    'apikey': f'TokenApi {API_KEY}',
    'Content-Type': 'text/xml;charset=UTF-8'
})
transport = Transport(session=session)
settings = Settings(strict=False, xml_huge_tree=True)
client = Client(wsdl=WSDL_URL, transport=transport, settings=settings)

# Conectar a la base de datos
connection = create_connection()

# Interfaz de usuario
st.title("Consulta de Puntos de Venta Habilitados")

# Botón para consultar los puntos de venta habilitados
if st.button("Consultar Puntos de Venta"):
    # Preparar la solicitud para la consulta
    solicitud = {
        "SolicitudConsultaPuntoVenta": {
            "codigoAmbiente": CODIGO_AMBIENTE,
            "codigoSistema": CODIGO_SISTEMA,
            "codigoSucursal": CODIGO_SUCURSAL,
            "cuis": CUIS,
            "nit": NIT
        }
    }

    # Realizar la llamada SOAP para la consulta
    try:
        response = client.service.consultaPuntoVenta(**solicitud)
        if response:
            lista_puntos_ventas = response['listaPuntosVentas']
            if response['transaccion']:
                # Verificar los puntos de venta en la base de datos
                if connection:
                    cursor = connection.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM punto_venta WHERE estado = 'Habilitado' AND codigo_punto_venta != 0")
                    puntos_venta_db = cursor.fetchall()

                    # Crear un conjunto de códigos de puntos de venta habilitados en la respuesta y en la base de datos
                    codigos_respuesta = {pv['codigoPuntoVenta'] for pv in lista_puntos_ventas}
                    codigos_db = {pv['codigo_punto_venta'] for pv in puntos_venta_db}

                    # Verificación
                    puntos_habilitados = [pv for pv in puntos_venta_db if pv['codigo_punto_venta'] in codigos_respuesta]

                    # Mostrar los datos de los puntos de venta habilitados
                    if puntos_habilitados:
                        st.subheader("Puntos de Venta Habilitados en el Sistema:")
                        for pv in puntos_habilitados:
                            st.write(f"Código: {pv['codigo_punto_venta']}, Nombre: {pv['nombre_punto_venta']}, Tipo: {pv['tipo']}, Sucursal: {pv['cod_sucursal']}, Estado: {pv['estado']}")
                    else:
                        st.warning("No hay puntos de venta habilitados en el sistema que coincidan con los datos de la base de datos.")
            else:
                st.error("La transacción no se pudo completar.")
    except Exception as e:
        st.error(f"Error al consultar los puntos de venta: {e}")

# Cerrar la conexión a la base de datos
if connection:
    connection.close()
