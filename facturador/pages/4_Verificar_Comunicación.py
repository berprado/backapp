import streamlit as st
import requests
from dotenv import load_dotenv
import os

# Cargar las variables desde el archivo .env
load_dotenv()

# Extraer los endpoints y el API_KEY del .env
ENDPOINTS = {
    "Facturación Códigos": os.getenv("WSDL_URL_CODIGOS"),
    "Facturación Operaciones": os.getenv("WSDL_URL_OPERACIONES"),
    "Facturación Sincronización": os.getenv("WSDL_URL_SYNC"),
    "Documentos de Ajuste": os.getenv("WSDL_URL_AJUSTE"),
    "Facturación Compra-Venta": os.getenv("WSDL_URL_FACTURACION")
}

API_KEY = os.getenv("API_KEY")

# Plantilla de solicitud SOAP
SOAP_REQUEST_TEMPLATE = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
   <soapenv:Header/>
   <soapenv:Body>
      <siat:verificarComunicacion/>
   </soapenv:Body>
</soapenv:Envelope>"""

# Placeholder para mostrar mensajes
message_placeholder = st.empty()

# Función para verificar la comunicación con un servicio
def verificar_comunicacion(servicio):
    url = ENDPOINTS[servicio]
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": "",
        "apikey": API_KEY
    }

    try:
        response = requests.post(url, data=SOAP_REQUEST_TEMPLATE, headers=headers)
        response.raise_for_status()  # Verifica si la respuesta es exitosa (código 200)

        if servicio in ["Documentos de Ajuste", "Facturación Compra-Venta"]:
            # Estructura para Facturación Compra-Venta y Documentos de Ajuste
            if "<transaccion>true</transaccion>" in response.text:
                return True, "Comunicación exitosa"
            else:
                return False, "Fallo en la comunicación"
        else:
            # Estructura para otros servicios
            if "<codigo>926</codigo>" in response.text:
                return True, "Comunicación exitosa con código 926"
            else:
                return False, "Fallo en la comunicación"
    except requests.exceptions.RequestException as e:
        return False, f"Error de comunicación: {e}"

# Función para verificar todos los servicios
def verificar_todos_los_servicios():
    resultados = {}
    for servicio in ENDPOINTS:
        exito, mensaje = verificar_comunicacion(servicio)
        resultados[servicio] = mensaje if exito else f"Error: {mensaje}"
    return resultados

# Desarrollo de la interfaz de Streamlit
st.title("Verificar Comunicación")

st.write("Selecciona el servicio con el que deseas verificar la comunicación o elige 'Todos los servicios' para verificarlos en conjunto:")

# Agregamos una opción para verificar todos los servicios
opciones_servicio = list(ENDPOINTS.keys()) + ["Todos los servicios"]
servicio_seleccionado = st.selectbox("Servicios disponibles", opciones_servicio)

if st.button("Verificar comunicación"):
    # Usar el placeholder para actualizar los mensajes
    with message_placeholder.container():
        if servicio_seleccionado == "Todos los servicios":
            with st.spinner("Verificando todos los servicios..."):
                resultados = verificar_todos_los_servicios()
                for servicio, mensaje in resultados.items():
                    if "exitosa" in mensaje:
                        st.success(f"{servicio}: {mensaje}")
                    else:
                        st.error(f"{servicio}: {mensaje}")
        else:
            with st.spinner(f"Verificando comunicación con {servicio_seleccionado}..."):
                exito, mensaje = verificar_comunicacion(servicio_seleccionado)
                if exito:
                    st.success(mensaje)
                else:
                    st.error(mensaje)

st.write("Puedes verificar la comunicación con uno o todos los servicios seleccionando la opción correspondiente.")
