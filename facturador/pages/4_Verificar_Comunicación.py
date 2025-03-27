import streamlit as st
import os
import sys
import requests
import time
from dotenv import load_dotenv
import pandas as pd

# Agregar ruta del directorio padre al path de Python
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from facturador.response_handler import parse_siat_response
from logger_config import get_logger

# Obtener logger para este módulo
logger = get_logger()

# Cargar las variables desde el archivo .env
load_dotenv()

# Función para verificar la comunicación con el servicio SIAT
def verificar_servicio(url, nombre_servicio):
    """
    Verifica la comunicación con un servicio del SIAT
    
    Args:
        url (str): URL del servicio SOAP
        nombre_servicio (str): Nombre descriptivo del servicio
        
    Returns:
        tuple: (bool, str) - (éxito, mensaje)
    """
    # Plantilla de solicitud SOAP
    soap_request = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
       <soapenv:Header/>
       <soapenv:Body>
          <siat:verificarComunicacion/>
       </soapenv:Body>
    </soapenv:Envelope>"""
    
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": "",
        "apikey": os.getenv('API_KEY')
    }
    
    start_time = time.time()
    status_placeholder = st.empty()
    
    try:
        status_placeholder.info(f"⏱️ Verificando servicio: {nombre_servicio}...")
        
        # Enviar la solicitud SOAP
        response = requests.post(url, data=soap_request, headers=headers, timeout=10)
        
        # Verificar que la respuesta sea exitosa (código 200)
        response.raise_for_status()
        
        # Calcular tiempo de respuesta
        response_time = time.time() - start_time
        
        # Procesar la respuesta usando el módulo response_handler
        success, response_data = parse_siat_response(response.content)
        
        if success:
            # Verificar si la transacción fue exitosa
            transaccion_ok = response_data.get('transaccion', False)
            
            if transaccion_ok:
                status_placeholder.success(f"✅ Servicio: {nombre_servicio} - OK ({response_time:.2f}s)")
                return True, f"Comunicación exitosa en {response_time:.2f} segundos"
            else:
                codigo = response_data.get('codigoEstado', 'Desconocido')
                desc = response_data.get('codigoDescripcion', 'Sin descripción')
                status_placeholder.warning(f"⚠️ Servicio: {nombre_servicio} - Respuesta: {codigo} ({response_time:.2f}s)")
                return False, f"Respuesta no exitosa: {codigo} - {desc}"
        else:
            error = response_data.get('error', 'Error desconocido')
            status_placeholder.error(f"❌ Servicio: {nombre_servicio} - Error: {error} ({response_time:.2f}s)")
            return False, f"Error en la comunicación: {error}"
            
    except requests.exceptions.Timeout:
        status_placeholder.error(f"⏱️ Servicio: {nombre_servicio} - TIMEOUT (>10s)")
        return False, "Tiempo de espera agotado (>10s)"
    except requests.exceptions.ConnectionError:
        status_placeholder.error(f"🔌 Servicio: {nombre_servicio} - ERROR DE CONEXIÓN")
        return False, "Error de conexión al servidor"
    except requests.exceptions.RequestException as e:
        status_placeholder.error(f"❌ Servicio: {nombre_servicio} - ERROR: {str(e)}")
        return False, f"Error en la solicitud: {str(e)}"

def main():
    st.title("Verificador de Comunicación con SIAT")
    
    # Extraer los endpoints y el API_KEY del .env
    endpoints = {
        "Facturación Códigos": os.getenv("WSDL_URL_CODIGOS"),
        "Facturación Operaciones": os.getenv("WSDL_URL_OPERACIONES"),
        "Facturación Sincronización": os.getenv("WSDL_URL_SYNC"),
        "Documentos de Ajuste": os.getenv("WSDL_URL_AJUSTE"),
        "Facturación Compra-Venta": os.getenv("WSDL_URL_FACTURACION")
    }
    
    st.write("Esta herramienta verifica la comunicación con los servicios de facturación del SIAT.")
    
    # Opciones de verificación
    st.subheader("Opciones de Verificación")
    col1, col2 = st.columns(2)
    
    with col1:
        # Permitir seleccionar servicios específicos
        servicios_seleccionados = st.multiselect(
            "Seleccione los servicios a verificar:",
            options=list(endpoints.keys()),
            default=list(endpoints.keys())
        )
    
    with col2:
        # Botones de acción
        verificar_todos = st.button("Verificar Todos")
        verificar_seleccionados = st.button("Verificar Seleccionados")
    
    # Mostrar resultados en formato tabla
    st.subheader("Estado de los Servicios")
    
    # Si se presiona algún botón, realizar las verificaciones correspondientes
    if verificar_todos or (verificar_seleccionados and servicios_seleccionados):
        # Determinar qué servicios verificar
        servicios_a_verificar = list(endpoints.keys()) if verificar_todos else servicios_seleccionados
        
        # Crear un DataFrame para mostrar los resultados
        results = []
        
        # Verificar cada servicio seleccionado
        for servicio in servicios_a_verificar:
            if servicio in endpoints and endpoints[servicio]:
                exito, mensaje = verificar_servicio(endpoints[servicio], servicio)
                
                results.append({
                    "Servicio": servicio,
                    "Estado": "✅ Operativo" if exito else "❌ Con problemas",
                    "Mensaje": mensaje
                })
            else:
                results.append({
                    "Servicio": servicio,
                    "Estado": "⚠️ No configurado",
                    "Mensaje": "URL no disponible en archivo .env"
                })
        
        # Mostrar resultados en una tabla
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Determinar si todos los servicios están operativos
            todos_operativos = all(row["Estado"] == "✅ Operativo" for row in results)
            
            if todos_operativos:
                st.success("✅ Todos los servicios están operativos")
            else:
                servicios_con_problemas = [row["Servicio"] for row in results if row["Estado"] != "✅ Operativo"]
                st.error(f"⚠️ Hay problemas con los siguientes servicios: {', '.join(servicios_con_problemas)}")
                
                # Sugerir activar modo contingencia si hay problemas
                st.warning("""
                **Sugerencia:** Si los problemas persisten, considere activar el modo de contingencia.
                Puede hacerlo desde la sección 'Gestión de Contingencia' en el menú lateral.
                """)
        else:
            st.warning("No se seleccionó ningún servicio para verificar")

if __name__ == "__main__":
    main()
