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
CODIGO_MODALIDAD = int(os.getenv('CODIGO_MODALIDAD', '1'))  # Definido aquí
CODIGO_SUCURSAL = int(os.getenv('CODIGO_SUCURSAL', '0'))
CUIS = os.getenv('CUIS')

# Configuración de la conexión a la base de datos MySQL
st.cache_resource
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

# Selección de la acción en la barra lateral
st.sidebar.title("Menú de Opciones")
action = st.sidebar.radio("Selecciona una acción", ["Consultar", "Abrir", "Cerrar"])

# Función para obtener tipos de punto de venta desde la base de datos
st.cache_data()
def get_tipo_punto_venta(connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT descripcion, codigoClasificador FROM sincronizarparametricatipopuntoventa")
    result = cursor.fetchall()
    return result

# Función para consultar puntos de venta habilitados

st.cache_data()
def consultar_puntos_venta():
    st.title("Consulta de Puntos de Venta Habilitados")
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
                    if connection:
                        cursor = connection.cursor(dictionary=True)
                        cursor.execute("SELECT * FROM punto_venta WHERE estado = 'Habilitado' AND codigo_punto_venta != 0")
                        puntos_venta_db = cursor.fetchall()

                        codigos_respuesta = {pv['codigoPuntoVenta'] for pv in lista_puntos_ventas}
                        puntos_habilitados = [pv for pv in puntos_venta_db if pv['codigo_punto_venta'] in codigos_respuesta]

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

# Función para abrir un nuevo punto de venta
st.cache_data()
def abrir_punto_venta():
    st.title("Registro de Punto de Venta")
    nombre_punto_venta = st.text_input("Nombre del Punto de Venta")
    descripcion = st.text_input("Descripción")

    # Obtener tipos de punto de venta
    tipos_punto_venta = get_tipo_punto_venta(connection)
    tipo_seleccionado = st.selectbox(
        "Tipo de Punto de Venta",
        [tipo['descripcion'] for tipo in tipos_punto_venta]
    )

    codigo_tipo_punto_venta = next(
        (tipo['codigoClasificador'] for tipo in tipos_punto_venta if tipo['descripcion'] == tipo_seleccionado),
        None
    )

    codigo_ambiente = st.selectbox("Código Ambiente", [1, 2], index=1 if CODIGO_AMBIENTE == 2 else 0)
    codigo_modalidad = st.selectbox("Código Modalidad", [1, 2], index=0 if CODIGO_MODALIDAD == 1 else 1)
    codigo_sistema = st.text_input("Código del Sistema", CODIGO_SISTEMA)
    codigo_sucursal = st.number_input("Código de la Sucursal", min_value=0, value=CODIGO_SUCURSAL)
    cuis = st.text_input("CUIS", CUIS)
    nit = st.number_input("NIT", min_value=0, value=int(NIT))

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
                        try:
                            cursor = connection.cursor()
                            cursor.execute('''
                            INSERT INTO punto_venta (codigo_punto_venta, nombre_punto_venta, descripcion, tipo, estado, cod_sucursal)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ''', (codigo_punto_venta, nombre_punto_venta, descripcion, tipo_seleccionado, 'Habilitado', codigo_sucursal))
                            connection.commit()
                            st.success(f"Punto de venta registrado exitosamente con código {codigo_punto_venta}.")
                        except Error as e:
                            st.error(f"Error al insertar en la base de datos: {e}")
                    else:
                        st.error("La transacción no se pudo completar.")
            except Exception as e:
                st.error(f"Error al registrar el punto de venta: {e}")

# Función para cerrar puntos de venta
st.cache_data()
def cerrar_punto_venta():
    st.title("Cierre de Puntos de Venta")
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM punto_venta WHERE estado = 'Habilitado' AND codigo_punto_venta != 0")
    puntos_venta_db = cursor.fetchall()

    puntos_seleccionados = st.multiselect(
        "Seleccione los Puntos de Venta a cerrar",
        [f"Código: {pv['codigo_punto_venta']}, Nombre: {pv['nombre_punto_venta']}, Tipo: {pv['tipo']}, Sucursal: {pv['cod_sucursal']}"
         for pv in puntos_venta_db],
        format_func=lambda x: x.split(",")[1].split(": ")[1]
    )

    codigos_seleccionados = [int(pv.split(",")[0].split(": ")[1]) for pv in puntos_seleccionados]

    if st.button("Cerrar Puntos de Venta Seleccionados"):
        for codigo_punto_venta in codigos_seleccionados:
            solicitud_cierre = {
                "SolicitudCierrePuntoVenta": {
                    "codigoAmbiente": CODIGO_AMBIENTE,
                    "codigoPuntoVenta": codigo_punto_venta,
                    "codigoSistema": CODIGO_SISTEMA,
                    "codigoSucursal": CODIGO_SUCURSAL,
                    "cuis": CUIS,
                    "nit": NIT
                }
            }

            try:
                response_cierre = client.service.cierrePuntoVenta(**solicitud_cierre)
                if response_cierre:
                    transaccion = response_cierre['transaccion']
                    if transaccion:
                        try:
                            cursor.execute("UPDATE punto_venta SET estado = 'Deshabilitado' WHERE codigo_punto_venta = %s", (codigo_punto_venta,))
                            connection.commit()
                            st.success(f"Punto de venta con código {codigo_punto_venta} cerrado exitosamente.")
                        except Error as e:
                            st.error(f"Error al actualizar la base de datos para el código {codigo_punto_venta}: {e}")
                    else:
                        st.error(f"La transacción no se pudo completar para el código {codigo_punto_venta}.")
            except Exception as e:
                st.error(f"Error al cerrar el punto de venta con código {codigo_punto_venta}: {e}")

# Mostrar la interfaz correspondiente según la acción seleccionada
if action == "Consultar":
    consultar_puntos_venta()
elif action == "Abrir":
    abrir_punto_venta()
elif action == "Cerrar":
    cerrar_punto_venta()

# Cerrar la conexión a la base de datos
if connection:
    connection.close()
