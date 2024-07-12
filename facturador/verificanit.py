
import streamlit as st
from zeep import Client
from zeep.transports import Transport
import os
from dotenv import load_dotenv
from requests import Session
import time

# Load environment variables
load_dotenv()

# Initialize session for requests with API key in headers
session = Session()
session.headers.update({'apikey': os.getenv('API_KEY')})

# Initialize SOAP client using the WSDL URL and the custom session
wsdl_url = os.getenv('WSDL_URL_CODIGOS')
client = Client(wsdl_url, transport=Transport(session=session))

# Streamlit app interface setup


st.title('VERIFICA EL NIT DEL CONTRIBUYENTE')

# User input for NIT verification
nit_to_verify = st.text_input('Ingresa el NIT:', '')

if st.button('Verificar NIT'):
    # Structured SOAP request data according to the service definition
    solicitud_verificar_nit = {
        'codigoAmbiente': os.getenv('CODIGO_AMBIENTE'),
        'codigoModalidad': os.getenv('CODIGO_MODALIDAD'),
        'codigoSistema': os.getenv('CODIGO_SISTEMA'),
        'codigoSucursal': os.getenv('CODIGO_SUCURSAL'),
        'cuis': os.getenv('CUIS'),
        'nit': os.getenv('NIT'),
        'nitParaVerificacion': nit_to_verify
    }

    # Send the SOAP request
    try:
        response = client.service.verificarNit(SolicitudVerificarNit=solicitud_verificar_nit)
        # Assuming the response object has a structure with 'transaccion' and 'mensajesList'
        if response.transaccion:
           alerta1 = st.success(f"Response: {response.mensajesList[0].descripcion}")
           time.sleep(3) # Wait for 3 seconds
           alerta1.empty() # Clear the alert
        else:
            st.error("NIT inactivo o inexistente")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Run the Streamlit app (this line is needed when running locally)
# if __name__ == "__main__":
#     st.run()
