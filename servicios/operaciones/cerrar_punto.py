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
st.title("Cierre de Punto de Venta")

# Obtener los puntos de venta activos
puntos_venta = []
if connection:
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, codigo_punto_venta, nombre_punto_venta FROM punto_venta WHERE estado = 'Habilitado'")
    puntos_venta = cursor.fetchall()

# Selección de punto de venta a cerrar
opciones = {f"{pv['nombre_punto_venta']} (ID: {pv['id']})": pv['codigo_punto_venta'] for pv in puntos_venta}
seleccionado = st.selectbox("Seleccione el Punto de Venta a cerrar", list(opciones.keys()))

# Botón para cerrar el punto de venta
if st.button("Cerrar Punto de Venta"):
    codigo_punto_venta = opciones[seleccionado]

    # Preparar la solicitud para el cierre
    solicitud = {
        "SolicitudCierrePuntoVenta": {
            "codigoAmbiente": CODIGO_AMBIENTE,
            "codigoPuntoVenta": codigo_punto_venta,
            "codigoSistema": CODIGO_SISTEMA,
            "codigoSucursal": CODIGO_SUCURSAL,
            "cuis": CUIS,
            "nit": NIT
        }
    }

    # Realizar la llamada SOAP para el cierre
    try:
        response = client.service.cierrePuntoVenta(**solicitud)
        if response:
            transaccion = response['transaccion']
            if transaccion:
                # Actualizar el estado en la base de datos
                try:
                    cursor.execute("UPDATE punto_venta SET estado = 'Deshabilitado' WHERE codigo_punto_venta = %s", (codigo_punto_venta,))
                    connection.commit()
                    st.success("Punto de venta cerrado exitosamente.")
                except Error as e:
                    st.error(f"Error al actualizar la base de datos: {e}")
            else:
                st.error("La transacción no se pudo completar.")
    except Exception as e:
        st.error(f"Error al cerrar el punto de venta: {e}")

# Cerrar la conexión a la base de datos
if connection:
    connection.close()
