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
CODIGO_MODALIDAD = int(os.getenv('CODIGO_MODALIDAD', '1'))
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

# Función para crear la tabla si no existe
def create_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS punto_venta (
            codigoPuntoVenta INT PRIMARY KEY,
            nombrePuntoVenta VARCHAR(255),
            descripcion VARCHAR(255),
            codigoAmbiente INT,
            codigoModalidad INT,
            codigoSistema VARCHAR(255),
            codigoSucursal INT,
            codigoTipoPuntoVenta INT,
            cuis VARCHAR(255),
            nit BIGINT
        )
        ''')
        connection.commit()
    except Error as e:
        st.error(f"Error al crear la tabla: {e}")

# Función para obtener tipos de punto de venta desde la base de datos
def get_tipo_punto_venta(connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT descripcion, codigoClasificador FROM sincronizarparametricatipopuntoventa")
    result = cursor.fetchall()
    return result

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
st.title("Registro de Punto de Venta")
nombre_punto_venta = st.text_input("Nombre del Punto de Venta")
descripcion = st.text_input("Descripción")

# Obtener tipos de punto de venta
tipos_punto_venta = get_tipo_punto_venta(connection)
tipo_seleccionado = st.selectbox(
    "Tipo de Punto de Venta",
    [tipo['descripcion'] for tipo in tipos_punto_venta]
)

# Obtener el codigoClasificador del tipo seleccionado
codigo_tipo_punto_venta = next(
    (tipo['codigoClasificador'] for tipo in tipos_punto_venta if tipo['descripcion'] == tipo_seleccionado),
    None
)

# Mostrar datos en la interfaz y permitir edición si es necesario
codigo_ambiente = st.selectbox("Código Ambiente", [1, 2], index=1 if CODIGO_AMBIENTE == 2 else 0)
codigo_modalidad = st.selectbox("Código Modalidad", [1, 2], index=0 if CODIGO_MODALIDAD == 1 else 1)
codigo_sistema = st.text_input("Código del Sistema", CODIGO_SISTEMA)
codigo_sucursal = st.number_input("Código de la Sucursal", min_value=0, value=CODIGO_SUCURSAL)
cuis = st.text_input("CUIS", CUIS)
nit = st.number_input("NIT", min_value=0, value=int(NIT))

# Botón para enviar la solicitud
if st.button("Registrar Punto de Venta"):
    if codigo_tipo_punto_venta is None:
        st.error("Seleccione un tipo de punto de venta válido.")
    else:
        # Preparar la solicitud
        solicitud = {
            "codigoAmbiente": codigo_ambiente,
            "codigoModalidad": codigo_modalidad,
            "codigoSistema": codigo_sistema,
            "codigoSucursal": codigo_sucursal,
            "codigoTipoPuntoVenta": codigo_tipo_punto_venta,
            "cuis": cuis,
            "descripcion": descripcion,
            "nit": nit,
            "nombrePuntoVenta": nombre_punto_venta
        }

        # Realizar la llamada SOAP
        try:
            response = client.service.registroPuntoVenta(SolicitudRegistroPuntoVenta=solicitud)
            if response:
                codigo_punto_venta = response['codigoPuntoVenta']
                transaccion = response['transaccion']

                if transaccion:
                    # Insertar la respuesta en la base de datos
                    cursor = connection.cursor()
                    cursor.execute('''
                    INSERT INTO punto_venta (codigoPuntoVenta, nombrePuntoVenta, descripcion, codigoAmbiente, codigoModalidad, codigoSistema, codigoSucursal, codigoTipoPuntoVenta, cuis, nit)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (codigo_punto_venta, nombre_punto_venta, descripcion, codigo_ambiente, codigo_modalidad, codigo_sistema, codigo_sucursal, codigo_tipo_punto_venta, cuis, nit))
                    connection.commit()
                    st.success(f"Punto de venta registrado exitosamente con código {codigo_punto_venta}.")
                else:
                    st.error("La transacción no se pudo completar.")
        except Exception as e:
            st.error(f"Error al registrar el punto de venta: {e}")

# Cerrar la conexión a la base de datos
if connection:
    connection.close()
