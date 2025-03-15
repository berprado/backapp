import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, Tuple, List, Optional
import streamlit as st
import traceback

# Configuración de logger para este módulo
logger = logging.getLogger(__name__)

def parse_siat_response(response_content: bytes) -> Tuple[bool, Dict[str, Any]]:
    """
    Parsea la respuesta XML del servidor SIAT y extrae la información relevante.
    
    Args:
        response_content: Contenido de la respuesta en bytes
        
    Returns:
        Tuple con (éxito, datos_respuesta)
    """
    try:
        root = ET.fromstring(response_content)
        ns = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/', 
              'ns2': 'https://siat.impuestos.gob.bo/'}
        
        # Buscar el elemento de respuesta usando namespace
        respuesta_servicio = root.find('.//ns2:RespuestaServicioFacturacion', ns)
        
        # Si no lo encuentra con namespace, intentar sin namespace (más flexible)
        if respuesta_servicio is None:
            respuesta_servicio = root.find('.//RespuestaServicioFacturacion')
        
        if respuesta_servicio is None:
            return False, {
                'error': 'No se encontró el elemento RespuestaServicioFacturacion',
                'xml_content': response_content.decode('utf-8', errors='replace')
            }
        
        # Extraer campos individuales con manejo de errores
        resultado = {}
        
        # Lista de campos a extraer
        campos = ['codigoDescripcion', 'codigoEstado', 'codigoRecepcion', 'transaccion']
        
        for campo in campos:
            elemento = respuesta_servicio.find(campo)
            if elemento is not None:
                # Para transaccion, convertir a booleano
                if campo == 'transaccion':
                    resultado[campo] = elemento.text.lower() == 'true'
                else:
                    resultado[campo] = elemento.text
            else:
                resultado[campo] = None
                logger.warning(f"Campo {campo} no encontrado en la respuesta")
        
        # Extraer mensajes de error si existen
        mensajes_list = respuesta_servicio.find('mensajesList')
        resultado['mensajes'] = []
        
        if mensajes_list is not None:
            for mensaje in mensajes_list:
                codigo = mensaje.find('codigo')
                descripcion = mensaje.find('descripcion')
                
                if codigo is not None and descripcion is not None:
                    resultado['mensajes'].append({
                        'codigo': codigo.text,
                        'descripcion': descripcion.text
                    })
        
        return True, resultado
    
    except ET.ParseError as e:
        logger.error(f"Error al parsear XML: {e}")
        return False, {
            'error': f"Error al parsear el XML de respuesta: {str(e)}",
            'traceback': traceback.format_exc()
        }
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return False, {
            'error': f"Error inesperado al procesar la respuesta: {str(e)}",
            'traceback': traceback.format_exc()
        }

def display_siat_response(response_data: Dict[str, Any], message_placeholder) -> bool:
    """
    Muestra la respuesta del SIAT de manera adecuada en la interfaz de Streamlit.
    
    Args:
        response_data: Datos de la respuesta procesada
        message_placeholder: Placeholder de Streamlit para mostrar mensajes
        
    Returns:
        Boolean indicando si la transacción fue exitosa
    """
    if 'error' in response_data:
        message_placeholder.error(f"❌ Error en la respuesta: {response_data['error']}")
        return False
    
    transaccion_exitosa = response_data.get('transaccion', False)
    codigo_descripcion = response_data.get('codigoDescripcion', 'Sin descripción')
    
    if transaccion_exitosa:
        message_placeholder.success(f":heavy_check_mark: FACTURA {codigo_descripcion}")
        return True
    else:
        # Mostrar mensaje principal de error
        error_message = f"❌ FACTURA NO VALIDADA: {codigo_descripcion}"
        message_placeholder.error(error_message)
        
        # Mostrar detalles de errores si existen
        mensajes = response_data.get('mensajes', [])
        if mensajes:
            error_details = [{"Código": m['codigo'], "Descripción": m['descripcion']} for m in mensajes]
            st.error("Detalles del error:")
            st.table(error_details)
            
        # Informar sobre siguientes pasos
        st.warning("Por favor, corrija los errores y vuelva a intentar generar la factura.")
        return False
