import streamlit as st
import zeep
from zeep import Client, Settings
from zeep.transports import Transport
import requests
from requests import Session
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import os
import logging
from business_logic import verificar_comunicacion

# Configuración del sistema de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# Crear un marcador de posición para mensajes
message_placeholder = st.empty()
# Verificar la comunicación con el endpoint de Operaciones
exito, mensaje = verificar_comunicacion("Facturación Operaciones")
if not exito:
    message_placeholder.error(f"Error de comunicación con el servicio de Operaciones: {mensaje}")
    st.stop()  # Detener la ejecución del código si la verificación falla
else:
    message_placeholder.success("Conexión exitosa con el servicio de Operaciones.")

# Configuración de la sesión SOAP
def get_soap_client():
    session = Session()
    session.headers.update({
        'apikey': f'TokenApi {API_KEY}',
        'Content-Type': 'text/xml;charset=UTF-8'
    })
    transport = Transport(session=session)
    settings = Settings(strict=False, xml_huge_tree=True)
    client = Client(wsdl=WSDL_URL, transport=transport, settings=settings)
    return client
# Función para gestionar la conexión a la base de datos
@st.cache_resource
def get_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE')
        )
        return connection
    except Error as e:
        log_and_display_error("Error al conectar a la base de datos", e)
        return None

# Función para loguear y mostrar errores
def log_and_display_error(message, exception=None):
    logging.error(message, exc_info=exception)
    message_placeholder.error(message)

# Configuración de la sesión SOAP
@st.cache_resource
def get_soap_client():
    session = Session()
    session.headers.update({
        'apikey': f'TokenApi {API_KEY}',
        'Content-Type': 'text/xml;charset=UTF-8'
    })
    transport = Transport(session=session)
    settings = Settings(strict=False, xml_huge_tree=True)
    client = Client(wsdl=WSDL_URL, transport=transport, settings=settings)
    return client

# Función para obtener tipos de punto de venta desde la base de datos
@st.cache_data
def get_tipo_punto_venta(_connection):
    query = "SELECT descripcion, codigoClasificador FROM sincronizarparametricatipopuntoventa"
    return execute_query(_connection, query)


# Función para ejecutar consultas a la base de datos
def execute_query(connection, query, params=None):
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, params or ())
    return cursor.fetchall()

# Función para actualizar la base de datos
def update_database(connection, query, params):
    cursor = connection.cursor()
    cursor.execute(query, params)
    connection.commit()

# Función para sincronizar puntos de venta
def sincronizar_puntos_venta():
    st.title("Sincronización de Puntos de Venta")
    if st.button("Sincronizar Puntos de Venta"):
        solicitud = {
            "SolicitudConsultaPuntoVenta": {
                "codigoAmbiente": CODIGO_AMBIENTE,
                "codigoSistema": CODIGO_SISTEMA,
                "codigoSucursal": CODIGO_SUCURSAL,
                "cuis": CUIS,
                "nit": NIT
            }
        }

        try:
            # Obtener el cliente SOAP desde la caché
            client = get_soap_client()

            # Consulta SOAP al servidor remoto
            response = client.service.consultaPuntoVenta(**solicitud)
            if response and response['transaccion']:
                lista_puntos_ventas = response['listaPuntosVentas']
                codigos_respuesta = {pv['codigoPuntoVenta'] for pv in lista_puntos_ventas}

                connection = get_connection()
                if connection:
                    # Obtener los códigos de puntos de venta habilitados en la base de datos local
                    query = "SELECT codigo_punto_venta FROM punto_venta WHERE estado = 'Habilitado' AND codigo_punto_venta != 0"
                    puntos_venta_db = execute_query(connection, query)
                    codigos_locales = {pv['codigo_punto_venta'] for pv in puntos_venta_db}

                    # Identificar puntos de venta que están en el servidor remoto pero no en la base de datos local
                    nuevos_puntos_venta = [pv for pv in lista_puntos_ventas if pv['codigoPuntoVenta'] not in codigos_locales]

                    if nuevos_puntos_venta:
                        # Insertar los nuevos puntos de venta en la base de datos local
                        for pv in nuevos_puntos_venta:
                            insert_query = '''
                            INSERT INTO punto_venta (codigo_punto_venta, nombre_punto_venta, descripcion, tipo, estado, cod_sucursal)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            '''
                            insert_params = (
                                pv['codigoPuntoVenta'],
                                pv['nombrePuntoVenta'],
                                '',  # Asume que la descripción está vacía o ajusta según sea necesario
                                pv['tipoPuntoVenta'],
                                'Habilitado',
                                CODIGO_SUCURSAL
                            )
                            try:
                                update_database(connection, insert_query, insert_params)
                                message_placeholder.success(f"El punto de venta {pv['codigoPuntoVenta']} fue añadido a la base de datos.")
                            except mysql.connector.IntegrityError:
                                # Maneja el caso donde el punto de venta ya existe (aunque no debería llegar aquí)
                                message_placeholder.warning(f"El punto de venta {pv['codigoPuntoVenta']} ya existe en la base de datos.")
                    else:
                        message_placeholder.info("No hay nuevos puntos de venta para sincronizar.")
            else:
                message_placeholder.error("La transacción no se pudo completar o no se recibió respuesta del servicio.")
        except (zeep.exceptions.Fault, requests.exceptions.RequestException) as e:
            log_and_display_error("Error en la solicitud SOAP o de conexión", e)
        except Exception as e:
            log_and_display_error("Error inesperado durante la sincronización", e)

# Función para consultar puntos de venta habilitados
def consultar_puntos_venta():
    st.title("Consulta de Puntos de Venta Habilitados")
    if st.button("Consultar Puntos de Venta"):
        solicitud = {
            "SolicitudConsultaPuntoVenta": {
                "codigoAmbiente": CODIGO_AMBIENTE,
                "codigoSistema": CODIGO_SISTEMA,
                "codigoSucursal": CODIGO_SUCURSAL,
                "cuis": CUIS,
                "nit": NIT
            }
        }

        try:
            client = get_soap_client()
            response = client.service.consultaPuntoVenta(**solicitud)
            if response and response['transaccion']:
                lista_puntos_ventas = response['listaPuntosVentas']
                codigos_respuesta = {pv['codigoPuntoVenta'] for pv in lista_puntos_ventas}

                connection = get_connection()
                if connection:
                    query = "SELECT * FROM punto_venta WHERE estado = 'Habilitado' AND codigo_punto_venta != 0"
                    puntos_venta_db = execute_query(connection, query)
                    puntos_habilitados = [pv for pv in puntos_venta_db if pv['codigo_punto_venta'] in codigos_respuesta]

                    if puntos_habilitados:
                        message_placeholder.success("Transacción completada con éxito.")
                        st.subheader("Puntos de Venta Habilitados en el Sistema:")
                        for pv in puntos_habilitados:
                            st.write(f"Código: {pv['codigo_punto_venta']}, Nombre: {pv['nombre_punto_venta']}, Tipo: {pv['tipo']}, Sucursal: {pv['cod_sucursal']}, Estado: {pv['estado']}")
                    else:
                        message_placeholder.warning("No hay puntos de venta habilitados en el sistema que coincidan con los datos de la base de datos.")
            else:
                message_placeholder.error("La transacción no se pudo completar o no se recibió respuesta del servicio.")
        except (zeep.exceptions.Fault, requests.exceptions.RequestException) as e:
            log_and_display_error("Error en la solicitud SOAP o de conexión", e)
        except Exception as e:
            log_and_display_error("Error inesperado durante la consulta", e)

# Función para abrir un nuevo punto de venta
def abrir_punto_venta():
    st.title("Registro de Punto de Venta")
    with st.form("registro_punto_venta"):
        nombre_punto_venta = st.text_input("Nombre del Punto de Venta")
        descripcion = st.text_input("Descripción")

        connection = get_connection()
        if connection:
            tipos_punto_venta = get_tipo_punto_venta(connection)
            tipo_seleccionado = st.selectbox("Tipo de Punto de Venta", [tipo['descripcion'] for tipo in tipos_punto_venta])
            codigo_tipo_punto_venta = next((tipo['codigoClasificador'] for tipo in tipos_punto_venta if tipo['descripcion'] == tipo_seleccionado), None)

        if st.form_submit_button("Registrar Punto de Venta"):
            if not nombre_punto_venta.strip() or not codigo_tipo_punto_venta:
                message_placeholder.error("El nombre del punto de venta y el tipo de punto de venta son obligatorios.")
                return

            solicitud = {
                "codigoAmbiente": CODIGO_AMBIENTE,
                "codigoModalidad": CODIGO_MODALIDAD,
                "codigoSistema": CODIGO_SISTEMA,
                "codigoSucursal": CODIGO_SUCURSAL,
                "codigoTipoPuntoVenta": codigo_tipo_punto_venta,
                "cuis": CUIS,
                "descripcion": descripcion,
                "nit": NIT,
                "nombrePuntoVenta": nombre_punto_venta
            }

            try:
                client = get_soap_client()
                response = client.service.registroPuntoVenta(SolicitudRegistroPuntoVenta=solicitud)
                if response and response['transaccion']:
                    codigo_punto_venta = response['codigoPuntoVenta']

                    if connection:
                        query = '''
                        INSERT INTO punto_venta (codigo_punto_venta, nombre_punto_venta, descripcion, tipo, estado, cod_sucursal)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        '''
                        params = (codigo_punto_venta, nombre_punto_venta, descripcion, tipo_seleccionado, 'Habilitado', CODIGO_SUCURSAL)
                        update_database(connection, query, params)
                        message_placeholder.success(f"Punto de venta registrado exitosamente con código {codigo_punto_venta}.")
                else:
                    message_placeholder.error("La transacción no se pudo completar.")
            except (zeep.exceptions.Fault, requests.exceptions.RequestException) as e:
                log_and_display_error("Error en la solicitud SOAP o de conexión", e)
            except Exception as e:
                log_and_display_error("Error inesperado durante el registro", e)


# Función para cerrar puntos de venta
def cerrar_punto_venta():
    st.title("Cerrar Punto de Venta")

    connection = get_connection()
    if connection:
        query = "SELECT * FROM punto_venta WHERE estado = 'Habilitado' AND codigo_punto_venta != 0"
        puntos_venta_db = execute_query(connection, query)

    puntos_seleccionados = st.multiselect(
        "Seleccione los Puntos de Venta a cerrar",
        [f"Código: {pv['codigo_punto_venta']}, Nombre: {pv['nombre_punto_venta']}, Tipo: {pv['tipo']}, Sucursal: {pv['cod_sucursal']}"
         for pv in puntos_venta_db],
        format_func=lambda x: x.split(",")[1].split(": ")[1]
    )

    if st.button("Cerrar Puntos de Venta Seleccionados"):
        for codigo_punto_venta in [int(pv.split(",")[0].split(": ")[1]) for pv in puntos_seleccionados]:
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
                client = get_soap_client()
                response_cierre = client.service.cierrePuntoVenta(**solicitud_cierre)
                if response_cierre and response_cierre['transaccion']:
                    if connection:
                        query = "UPDATE punto_venta SET estado = 'Deshabilitado' WHERE codigo_punto_venta = %s"
                        update_database(connection, query, (codigo_punto_venta,))
                        message_placeholder.success(f"Punto de venta con código {codigo_punto_venta} cerrado exitosamente.")
                else:
                    message_placeholder.error(f"La transacción no se pudo completar para el código {codigo_punto_venta}.")
            except (zeep.exceptions.Fault, requests.exceptions.RequestException) as e:
                log_and_display_error("Error en la solicitud SOAP o de conexión", e)
            except Exception as e:
                log_and_display_error(f"Error al cerrar el punto de venta con código {codigo_punto_venta}", e)

# Menú principal
st.sidebar.title("Menú de Opciones")
action = st.sidebar.radio("Selecciona una acción", ["Sincronizar", "Consultar", "Abrir", "Cerrar"])

# Mostrar la interfaz correspondiente según la acción seleccionada
if action == "Sincronizar":
    sincronizar_puntos_venta()
elif action == "Consultar":
    consultar_puntos_venta()
elif action == "Abrir":
    abrir_punto_venta()
elif action == "Cerrar":
    cerrar_punto_venta()
