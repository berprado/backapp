# soap_services.py
import os
import requests
import xml.etree.ElementTree as ET
from typing import Tuple, Optional
from dotenv import load_dotenv
from typing import Dict
from datetime import datetime
load_dotenv()

TOKEN_API: str = os.getenv("API_KEY")
ENDPOINT: str = os.getenv("WSDL_URL_OPERACIONES", "https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionOperaciones")


# =============================
# 🔍 Verificación de comunicación con el SIN
# Devuelve:
# - mensaje: descripción del estado
# - estado: True si hay conexión
# - tipo_deducido: código del evento sugerido (1, 2, 5...), o None
# =============================
def verificar_comunicacion() -> Tuple[str, bool, Optional[str]]:
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "apikey": f"TokenApi {TOKEN_API}"
    }

    body = """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:siat="https://siat.impuestos.gob.bo/">
       <soapenv:Header/>
       <soapenv:Body>
          <siat:verificarComunicacion/>
       </soapenv:Body>
    </soapenv:Envelope>"""

    try:
        response = requests.post(ENDPOINT, data=body.encode("utf-8"), headers=headers, timeout=6)

        if response.status_code == 200:
            ns = {'ns2': 'https://siat.impuestos.gob.bo/'}
            root = ET.fromstring(response.text)
            mensaje = root.find('.//ns2:verificarComunicacionResponse//mensajesList//descripcion', ns)
            transaccion = root.find('.//ns2:verificarComunicacionResponse//transaccion', ns)

            return (
                mensaje.text if mensaje is not None else "Respuesta vacía",
                transaccion.text == "true",
                None
            )

        # Clasificación de errores comunes
        if response.status_code in [500, 502]:
            return f"Error HTTP {response.status_code}", False, "2"  # Inaccesibilidad al servicio SIN
        else:
            return f"Error HTTP {response.status_code}", False, "1"  # Corte de internet general

    except requests.exceptions.Timeout:
        return "Timeout al conectar con el SIN", False, "2"
    except requests.exceptions.ConnectionError:
        return "Error de conexión o DNS", False, "1"
    except Exception as e:
        return f"Error inesperado: {e}", False, "5"  # Falla de software

from typing import Dict

def enviar_evento_significativo(evento: Dict, fecha_fin: datetime, cufd: str) -> Tuple[Optional[str], bool]:
    from os import getenv

    NIT = getenv("NIT")
    CUIS = getenv("CUIS")
    CODIGO_SISTEMA = getenv("CODIGO_SISTEMA")
    CODIGO_SUCURSAL = getenv("CODIGO_SUCURSAL")
    CODIGO_AMBIENTE = getenv("CODIGO_AMBIENTE")
    CODIGO_PUNTO_VENTA = getenv("CODIGO_PUNTO_VENTA", "0")

    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "apikey": f"TokenApi {TOKEN_API}"
    }

    soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
       <soapenv:Header/>
       <soapenv:Body>
          <siat:registroEventoSignificativo>
             <SolicitudEventoSignificativo>
                <codigoAmbiente>{CODIGO_AMBIENTE}</codigoAmbiente>
                <codigoMotivoEvento>{evento['codigo_evento']}</codigoMotivoEvento>
                <codigoPuntoVenta>{CODIGO_PUNTO_VENTA}</codigoPuntoVenta>
                <codigoSistema>{CODIGO_SISTEMA}</codigoSistema>
                <codigoSucursal>{CODIGO_SUCURSAL}</codigoSucursal>
                <cufd>{cufd}</cufd>
                <cufdEvento>{evento['cufd']}</cufdEvento>
                <cuis>{CUIS}</cuis>
                <descripcion>{evento['descripcion']}</descripcion>
                <fechaHoraFinEvento>{fecha_fin.isoformat()}</fechaHoraFinEvento>
                <fechaHoraInicioEvento>{evento['fecha_inicio'].isoformat()}</fechaHoraInicioEvento>
                <nit>{NIT}</nit>
             </SolicitudEventoSignificativo>
          </siat:registroEventoSignificativo>
       </soapenv:Body>
    </soapenv:Envelope>"""

    try:
        response = requests.post(ENDPOINT, data=soap_body.encode("utf-8"), headers=headers)
        if response.status_code == 200:
            ns = {'ns2': 'https://siat.impuestos.gob.bo/'}
            root = ET.fromstring(response.text)
            recepcion = root.find('.//ns2:registroEventoSignificativoResponse//codigoRecepcionEventoSignificativo', ns)
            transaccion = root.find('.//ns2:registroEventoSignificativoResponse//transaccion', ns)
            return recepcion.text if recepcion is not None else None, transaccion.text == "true"
        return None, False
    except Exception:
        return None, False
