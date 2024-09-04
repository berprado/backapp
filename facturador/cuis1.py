import urllib3
import os
from dotenv import load_dotenv
from zeep import Client, Settings
from zeep.transports import Transport
import requests
import streamlit as st
from database import SessionLocal
from business_logic import solicitar_y_almacenar_nuevo_cuis, verificar_cuis_vigente
# Desactivar advertencias de seguridad SSL en desarrollo
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
def get_env_variable(var_name, default_value=None):
    """Obtiene la variable de entorno o devuelve un valor predeterminado si está configurado, de lo contrario muestra un error."""
    value = os.getenv(var_name, default_value)
    if value is None:
        st.error(f"La variable de entorno requerida '{var_name}' no está configurada.")
        st.stop()
    return value

def cargar_configuracion():
    """Carga los parámetros desde el archivo .env."""
    load_dotenv()
    return {
        'wsdl': get_env_variable('WSDL_URL_CODIGOS'),
        'apikey': get_env_variable('API_KEY'),
        'nit': int(get_env_variable('NIT')),
        'codigo_sistema': get_env_variable('CODIGO_SISTEMA'),
        'codigo_ambiente': int(get_env_variable('CODIGO_AMBIENTE')),
        'codigo_modalidad': int(get_env_variable('CODIGO_MODALIDAD')),
        'codigo_sucursal': int(get_env_variable('CODIGO_SUCURSAL')),
        'codigo_punto_venta': int(get_env_variable('CODIGO_PUNTO_VENTA', 0)),
    }

def obtener_cliente_soap(config):
    """Configura y devuelve un cliente SOAP."""
    st.write("Inicializando cliente SOAP...")  # Mensaje de depuración
    try:
        session = requests.Session()
        session.verify = False  # Cambiar a True si el certificado SSL es confiable
        session.headers.update({
            'apikey': config['apikey'],  # Autenticación con API_KEY
            'Content-Type': 'text/xml;charset=UTF-8',
            'SOAPAction': ''
        })

        transport = Transport(session=session)
        settings = Settings(strict=False, xml_huge_tree=True)

        cliente = Client(
            wsdl=config['wsdl'], 
            transport=transport,
            settings=settings
        )
        st.write("Cliente SOAP inicializado correctamente.")  # Confirmación de éxito
        return cliente
    except Exception as e:
        st.error(f"Error al inicializar el cliente SOAP: {e}")
        return None

def verificar_comunicacion(cliente):
    """Verifica la comunicación con el servidor."""
    try:
        response = cliente.service.verificarComunicacion()
        if response:
            st.success(f"Comunicación con el servidor verificada: {response}")
            return True
        else:
            st.error("No se pudo verificar la comunicación con el servidor.")
            return False
    except Exception as e:
        st.error(f"Error al verificar la comunicación: {e}")
        return False

def main():
    st.title("Gestión de CUIS")
    st.write("Esta herramienta te permite gestionar el CUIS de tu punto de venta.")

    st.write("Cargando configuración...")
    config = cargar_configuracion()
    st.write("Configuración cargada:", config)

    session = SessionLocal()
    try:
        cliente_soap = obtener_cliente_soap(config)
        
        # Verificar la comunicación con el servidor
        st.write("Verificando comunicación con el servidor...")
        if not verificar_comunicacion(cliente_soap):
            st.error("No se pudo verificar la comunicación con el servidor. Revisa la configuración y la conectividad.")
            return

        st.write("Comunicación verificada, verificando CUIS vigente...")
        cuis, dias_restantes = verificar_cuis_vigente(session, config['codigo_punto_venta'])

        if cuis:
            st.info(f"CUIS vigente: {cuis.codigo}")
            st.write(f"Punto de Venta: {config['codigo_punto_venta']}")
            st.write(f"Días restantes de vigencia: {dias_restantes}")
            if dias_restantes > 5:
                st.write("No es necesario solicitar un nuevo CUIS.")
                st.button("Solicitar nuevo CUIS", disabled=True)
            else:
                if st.button("Solicitar nuevo CUIS"):
                    with st.spinner("Solicitando nuevo CUIS..."):
                        result = solicitar_y_almacenar_nuevo_cuis(cliente_soap, config, session)
                        if result["success"]:
                            st.success(f"Nuevo CUIS almacenado: {result['codigo']}")
                            st.write(f"Puedes copiar este código CUIS y pegarlo en tu archivo .env: `{result['codigo']}`")
                        else:
                            st.error(result["error"])
        else:
            st.write("No se encontró un CUIS vigente.")
            if st.button("Solicitar nuevo CUIS"):
                with st.spinner("Solicitando nuevo CUIS..."):
                    result = solicitar_y_almacenar_nuevo_cuis(cliente_soap, config, session)
                    if result["success"]:
                        st.success(f"Nuevo CUIS almacenado: {result['codigo']}")
                        st.write(f"Puedes copiar este código CUIS y pegarlo en tu archivo .env: `{result['codigo']}`")
                    else:
                        st.error(result["error"])
    finally:
        session.close()

if __name__ == "__main__":
    main()
