# app.py

import streamlit as st
from negocio import create_pool, get_connection, get_tipo_punto_venta, registrar_punto_venta, cerrar_punto_venta, consultar_puntos_venta, sincronizar_puntos_venta
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Inicializar el pool de conexiones
pool = create_pool()

# Variables de entorno
CODIGO_AMBIENTE = int(os.getenv('CODIGO_AMBIENTE', '2'))
CODIGO_MODALIDAD = int(os.getenv('CODIGO_MODALIDAD', '1'))
CODIGO_SISTEMA = os.getenv('CODIGO_SISTEMA')
CODIGO_SUCURSAL = int(os.getenv('CODIGO_SUCURSAL', '0'))
CUIS = os.getenv('CUIS')
NIT = os.getenv('NIT')

# Configuración de la interfaz de usuario
st.set_page_config(page_title="Gestión de Puntos de Venta", layout="wide")
st.sidebar.title("Menú de Opciones")

# Selección de la acción en la barra lateral
action = st.sidebar.radio("Selecciona una acción", ["Consultar", "Abrir", "Cerrar", "Sincronizar"])

@st.cache_data(ttl=600)
def obtener_tipos_punto_venta():
    return get_tipo_punto_venta(pool)

def consultar():
    st.title("Consulta de Puntos de Venta Habilitados")
    with st.spinner("Consultando puntos de venta..."):
        try:
            response = consultar_puntos_venta(CODIGO_AMBIENTE, CODIGO_SISTEMA, CODIGO_SUCURSAL, CUIS, NIT)
            if response['transaccion']:
                lista_puntos_ventas = response['listaPuntosVentas']
                if lista_puntos_ventas:
                    st.subheader("Puntos de Venta Habilitados en el Servidor Remoto:")
                    for pv in lista_puntos_ventas:
                        st.write(f"Código: {pv['codigoPuntoVenta']}, Nombre: {pv['nombrePuntoVenta']}, Tipo: {pv['tipoPuntoVenta']}")
                else:
                    st.warning("No hay puntos de venta habilitados en el servidor remoto.")
            else:
                st.error("La transacción no se pudo completar en el servidor remoto.")
        except Exception as e:
            st.error(f"Error al consultar los puntos de venta: {e}")

def abrir():
    st.title("Registro de Punto de Venta")
    with st.form("registro_punto_venta"):
        nombre_punto_venta = st.text_input("Nombre del Punto de Venta")
        descripcion = st.text_input("Descripción")
        tipos_punto_venta = obtener_tipos_punto_venta()
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

        submit = st.form_submit_button("Registrar")
        if submit:
            if codigo_tipo_punto_venta is None:
                st.error("Seleccione un tipo de punto de venta válido.")
            else:
                try:
                    response = registrar_punto_venta(nombre_punto_venta, descripcion, codigo_tipo_punto_venta, codigo_ambiente, codigo_modalidad, codigo_sistema, codigo_sucursal, cuis, nit, pool)
                    if response['transaccion']:
                        st.success(f"Punto de venta registrado exitosamente con código {response['codigoPuntoVenta']}.")
                        st.rerun()  # Recargar la página después del registro
                    else:
                        st.error("La transacción no se pudo completar.")
                except Exception as e:
                    st.error(f"Error al registrar el punto de venta: {e}")

def cerrar():
    st.title("Cierre de Puntos de Venta")
    try:
        with get_connection(pool) as connection:
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
            with st.spinner("Cerrando puntos de venta..."):
                for codigo_punto_venta in codigos_seleccionados:
                    try:
                        response = cerrar_punto_venta(codigo_punto_venta, CODIGO_AMBIENTE, CODIGO_SISTEMA, CODIGO_SUCURSAL, CUIS, NIT, pool)
                        if response['transaccion']:
                            st.success(f"Punto de venta con código {codigo_punto_venta} cerrado exitosamente.")
                        else:
                            st.error(f"La transacción no se pudo completar para el código {codigo_punto_venta}.")
                    except Exception as e:
                        st.error(f"Error al cerrar el punto de venta con código {codigo_punto_venta}: {e}")
                st.rerun()  # Recargar la página después de cerrar puntos de venta
    except Exception as e:
        st.error(f"Error al obtener puntos de venta habilitados: {e}")

def sincronizar():
    st.title("Sincronización de Puntos de Venta")
    if st.button("Sincronizar con el servidor remoto"):
        with st.spinner("Sincronizando puntos de venta..."):
            try:
                resultado = sincronizar_puntos_venta(pool)
                st.success(resultado)
                st.rerun()  # Recargar la página después de sincronizar
            except Exception as e:
                st.error(f"Error durante la sincronización: {e}")

# Mostrar la interfaz correspondiente según la acción seleccionada
if action == "Consultar":
    consultar()
elif action == "Abrir":
    abrir()
elif action == "Cerrar":
    cerrar()
elif action == "Sincronizar":
    sincronizar()
