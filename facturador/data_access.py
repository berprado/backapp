#data_access.py 24 5 2024

import requests
import streamlit as st
from database import SessionLocal
import models
from config import ENDPOINT_URL

@st.cache_resource
def fetch_comandas():
    try:
        response = requests.get(f"{ENDPOINT_URL}")
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return [], f"Error al obtener los id_comanda: {e}"

@st.cache_resource
def fetch_metodos_pago():
    session = SessionLocal()
    try:
        metodos = session.query(models.SincronizarParametricaTipoMetodoPago).all()
        if not metodos:
            return [], "No se encontraron métodos de pago"
        return [metodo.to_dict() for metodo in metodos], None
    except Exception as e:
        return [], f"Error al obtener los métodos de pago: {e}"
    finally:
        session.close()
        
@st.cache_resource
def fetch_tipos_documento():
    session = SessionLocal()
    try:
        documentos = session.query(models.SincronizarParametricaTipoDocumentoIdentidad).all()
        if not documentos:
            return [], "No se encontraron tipos de documento"
        return [documento.to_dict() for documento in documentos], None
    except Exception as e:
        return [], f"Error al obtener los tipos de documento: {e}"
    finally:
        session.close()

def fetch_cliente(numero_documento):
    session = SessionLocal()
    try:
        cliente = session.query(models.Cliente).filter(models.Cliente.codigo_cliente == numero_documento).first()
        if not cliente:
            return None, "Cliente no encontrado"
        return cliente.to_dict(), None
    except Exception as e:
        return None, f"Error al obtener el cliente: {e}"
    finally:
        session.close()
