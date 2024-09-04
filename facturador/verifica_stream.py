import os
from zeep import Client, Settings
from zeep.transports import Transport
from requests import Session
from dotenv import load_dotenv
import streamlit as st

def get_env_variable(var_name):
    """Get the environment variable or raise an error."""
    value = os.getenv(var_name)
    if value is None:
        st.error(f"Required environment variable {var_name} not set.")
        st.stop()
    return value

def verificar_comunicacion(client):
    """Verifica la comunicación con el servicio y muestra los resultados."""
    try:
        response_comunicacion = client.service.verificarComunicacion()
        st.write("Transacción de comunicación:", response_comunicacion.transaccion)
        if hasattr(response_comunicacion, 'mensajesList') and response_comunicacion.mensajesList:
            for mensaje in response_comunicacion.mensajesList:
                st.write(f"Código: {mensaje.codigo} - Descripción: {mensaje.descripcion}")
        else:
            st.write("Código: N/A - Descripción: No se recibieron mensajes de comunicación")
    except Exception as e:
        st.error("Transacción de comunicación: False")
        st.error("Código: 999 - Descripción: Error al comunicarse con el servicio")
        st.error(f"Detalles del error: {e}")
        st.stop()

def verificar_nit(client, solicitud_verificar_nit):
    """Verifica el NIT y muestra los resultados."""
    try:
        response = client.service.verificarNit(SolicitudVerificarNit=solicitud_verificar_nit)
        st.write("Transacción:", response.transaccion)
        if hasattr(response, 'mensajesList') and response.mensajesList:
            for mensaje in response.mensajesList:
                st.write(f"Código: {mensaje.codigo} - Descripción: {mensaje.descripcion}")
        else:
            st.write("Código: N/A - Descripción: No se recibieron mensajes")
    except Exception as e:
        st.error("Transacción: False")
        st.error("Código: 999 - Descripción: Error al comunicarse con el servicio")
        st.error(f"Detalles del error: {e}")

def main():
    # Cargar variables de entorno desde el archivo .env
    load_dotenv()

    API_KEY = get_env_variable('API_KEY')
    WSDL_URL_CODIGOS = get_env_variable('WSDL_URL_CODIGOS')
    CODIGO_SISTEMA = get_env_variable('CODIGO_SISTEMA')
    NIT = int(get_env_variable('NIT'))
    CODIGO_AMBIENTE = int(get_env_variable('CODIGO_AMBIENTE'))
    CODIGO_MODALIDAD = int(get_env_variable('CODIGO_MODALIDAD'))
    CODIGO_SUCURSAL = int(get_env_variable('CODIGO_SUCURSAL'))
    CUIS = get_env_variable('CUIS')

    # Configuración de la sesión
    session = Session()
    session.headers.update({
        'apikey': f'TokenApi {API_KEY}',
        'Content-Type': 'text/xml;charset=UTF-8'
    })
    transport = Transport(session=session)
    settings = Settings(strict=False, xml_huge_tree=True)
    client = Client(wsdl=WSDL_URL_CODIGOS, transport=transport, settings=settings)

    # Interfaz de usuario en Streamlit
    st.title("Verificación del NIT")

    # Input para NIT a verificar
    nit_para_verificacion = st.number_input("Ingrese el NIT para su verificación", min_value=0, value=0)

    if st.button("Verificar NIT"):
        verificar_comunicacion(client)
        
        # Crear el diccionario de solicitud para verificar NIT
        solicitud_verificar_nit = {
            'codigoAmbiente': CODIGO_AMBIENTE,
            'codigoModalidad': CODIGO_MODALIDAD,
            'codigoSistema': CODIGO_SISTEMA,
            'codigoSucursal': CODIGO_SUCURSAL,
            'cuis': CUIS,
            'nit': NIT,
            'nitParaVerificacion': nit_para_verificacion
        }

        verificar_nit(client, solicitud_verificar_nit)

if __name__ == "__main__":
    main()