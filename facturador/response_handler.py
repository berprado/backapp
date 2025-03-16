import xml.etree.ElementTree as ET
from typing import Dict, Any, Tuple, List, Optional
import streamlit as st
import traceback
from datetime import datetime
import re
import os
from pprint import pformat

# Importar el logger configurado específico para este módulo
from logger_config import get_response_logger

# Obtener el logger específico para este módulo
logger = get_response_logger()

def parse_siat_response(response_content: bytes) -> Tuple[bool, Dict[str, Any]]:
    """
    Parsea la respuesta XML del servidor SIAT y extrae la información relevante.
    
    Args:
        response_content: Contenido de la respuesta en bytes
        
    Returns:
        Tuple con (éxito, datos_respuesta)
    """
    try:
        # Guardar respuesta cruda para diagnóstico
        response_dir = "logs/responses"
        os.makedirs(response_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_response_path = f"{response_dir}/response_{timestamp}.xml"
        
        with open(raw_response_path, "wb") as f:
            f.write(response_content)
        
        logger.info(f"Respuesta XML guardada en {raw_response_path}")
        
        # Continuar con el procesamiento normal
        root = ET.fromstring(response_content)
        ns = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/', 
              'ns2': 'https://siat.impuestos.gob.bo/'}
        
        # Buscar el elemento de respuesta usando namespace
        respuesta_servicio = root.find('.//ns2:RespuestaServicioFacturacion', ns)
        
        # Si no lo encuentra con namespace, intentar sin namespace (más flexible)
        if respuesta_servicio is None:
            respuesta_servicio = root.find('.//RespuestaServicioFacturacion')
        
        if respuesta_servicio is None:
            # Intentar extraer mensajes de error SOAP si existe
            fault = root.find('.//soap:Fault', ns)
            if fault is not None:
                fault_code = fault.find('faultcode')
                fault_string = fault.find('faultstring')
                error_msg = f"Error SOAP: {fault_string.text if fault_string is not None else 'Desconocido'}"
                return False, {
                    'error': error_msg,
                    'codigo': fault_code.text if fault_code is not None else 'Desconocido',
                    'xml_content': response_content.decode('utf-8', errors='replace'),
                    'raw_response_path': raw_response_path
                }
            
            return False, {
                'error': 'No se encontró el elemento RespuestaServicioFacturacion',
                'xml_content': response_content.decode('utf-8', errors='replace'),
                'raw_response_path': raw_response_path
            }
        
        # Extraer campos individuales con manejo de errores
        resultado = {'raw_response_path': raw_response_path}
        
        # Lista de campos a extraer
        campos_requeridos = ['codigoDescripcion', 'codigoEstado', 'transaccion']
        campos_opcionales = ['codigoRecepcion']  # Puede no existir en respuestas de rechazo
        
        # Procesar campos requeridos
        for campo in campos_requeridos:
            elemento = respuesta_servicio.find(campo)
            if elemento is not None:
                # Para transaccion, convertir a booleano
                if campo == 'transaccion':
                    resultado[campo] = elemento.text.lower() == 'true'
                else:
                    resultado[campo] = elemento.text
            else:
                logger.error(f"Campo requerido {campo} no encontrado en la respuesta")
                return False, {
                    'error': f"La respuesta no contiene el campo requerido {campo}",
                    'xml_content': response_content.decode('utf-8', errors='replace'),
                    'raw_response_path': raw_response_path
                }
        
        # Procesar campos opcionales
        for campo in campos_opcionales:
            elemento = respuesta_servicio.find(campo)
            if elemento is not None:
                resultado[campo] = elemento.text
            else:
                # Si la transacción fue exitosa pero falta un campo opcional crítico, es un error grave
                if resultado.get('transaccion', False) and campo == 'codigoRecepcion':
                    logger.error(f"ERROR CRÍTICO: La transacción reporta éxito pero falta el código de recepción")
                    logger.error(f"Contenido XML: {response_content.decode('utf-8', errors='replace')[:500]}...")
                    
                    # Esta es una inconsistencia grave - la factura podría haberse registrado sin código de recepción
                    return False, {
                        'error': f"La transacción reporta éxito pero falta el código de recepción. Contacte soporte técnico.",
                        'codigo_estado': resultado.get('codigoEstado', 'Desconocido'),
                        'codigo_descripcion': resultado.get('codigoDescripcion', 'Desconocido'),
                        'transaccion': resultado.get('transaccion'),
                        'xml_content': response_content.decode('utf-8', errors='replace'),
                        'raw_response_path': raw_response_path
                    }
                else:
                    logger.info(f"Campo opcional {campo} no encontrado en la respuesta")
                resultado[campo] = None
        
        # Extraer mensajes de error si existen
        resultado['mensajes'] = []
        
        # Método 1: Buscar elementos mensajesList directamente como hijos
        mensajes_list_elements = respuesta_servicio.findall('mensajesList')
        
        if mensajes_list_elements:
            for mensaje_list in mensajes_list_elements:
                codigo = mensaje_list.find('codigo')
                descripcion = mensaje_list.find('descripcion')
                
                if codigo is not None and descripcion is not None:
                    resultado['mensajes'].append({
                        'codigo': codigo.text,
                        'descripcion': descripcion.text
                    })
        
        # Análisis adicional de la respuesta si no hay mensajes y la transacción es falsa
        if not resultado['mensajes'] and resultado.get('transaccion') is False:
            # Buscar en toda la respuesta por patrones de error comunes
            texto_respuesta = response_content.decode('utf-8', errors='replace')
            
            # Problemas comunes:
            problemas_conocidos = {
                r'CUFD.+fuera\s+de\s+tolerancia': 'El CUFD proporcionado está fuera de tolerancia o expirado.',
                r'fecha.+envio.+invalido': 'La fecha de envío es inválida. Verifique la sincronización del reloj del servidor.',
                r'inconsistencia.+datos': 'Hay inconsistencias en los datos enviados. Verifique los montos y datos fiscales.',
                r'NITs\s+iguales': 'El sistema puede estar rechazando la factura porque el NIT emisor y receptor son iguales.'
            }
            
            for patron, descripcion in problemas_conocidos.items():
                if re.search(patron, texto_respuesta, re.IGNORECASE):
                    resultado['mensajes'].append({
                        'codigo': 'ANALISIS',
                        'descripcion': descripcion
                    })
        
        # Información de diagnóstico adicional
        if not resultado['transaccion']:
            resultado['diagnostico'] = {
                'fecha_hora_servidor': datetime.now().isoformat(),
                'codigo_estado': resultado.get('codigoEstado'),
                'descripcion_estado': resultado.get('codigoDescripcion')
            }
            
            # Añadir contexto sobre posibles causas comunes según el código de estado
            codigo_estado = resultado.get('codigoEstado')
            if codigo_estado:
                if codigo_estado == '902':
                    resultado['diagnostico']['causa_probable'] = "Rechazo general. Revise los mensajes específicos."
                elif codigo_estado == '904':
                    resultado['diagnostico']['causa_probable'] = "La factura tiene observaciones que deben corregirse."
                elif codigo_estado == '906':
                    resultado['diagnostico']['causa_probable'] = "Error en el formato o estructura del XML enviado."
        
        return True, resultado
    
    except ET.ParseError as e:
        logger.error(f"Error al parsear XML: {e}")
        return False, {
            'error': f"Error al parsear el XML de respuesta: {str(e)}",
            'traceback': traceback.format_exc(),
            'xml_content_sample': response_content[:1000].decode('utf-8', errors='replace')
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
        
        # Si hay información adicional de diagnóstico, mostrarla en un área expandible
        diagnostico = {}
        for k, v in response_data.items():
            if k not in ['error', 'traceback', 'xml_content', 'xml_content_sample', 'raw_response_path']:
                diagnostico[k] = v
        
        if diagnostico:
            with st.expander("Información de diagnóstico"):
                for k, v in diagnostico.items():
                    st.text(f"{k}: {v}")
        
        # Mostrar ruta del archivo de respuesta para referencia
        if 'raw_response_path' in response_data:
            with st.expander("Datos técnicos para soporte"):
                st.info(f"Respuesta completa guardada en: {response_data['raw_response_path']}")
        
        return False
    
    transaccion_exitosa = response_data.get('transaccion', False)
    codigo_descripcion = response_data.get('codigoDescripcion', 'Sin descripción')
    codigo_estado = response_data.get('codigoEstado', 'Sin código')
    
    if transaccion_exitosa:
        mensaje_exito = f":heavy_check_mark: FACTURA {codigo_descripcion}"
        if response_data.get('codigoRecepcion'):
            mensaje_exito += f" (Código de recepción: {response_data['codigoRecepcion']})"
        message_placeholder.success(mensaje_exito)
        return True
    else:
        # Mostrar mensaje principal de error
        error_message = f"❌ FACTURA NO VALIDADA: {codigo_descripcion} (Código: {codigo_estado})"
        message_placeholder.error(error_message)
        
        # Mostrar detalles de errores si existen
        mensajes = response_data.get('mensajes', [])
        if mensajes:
            error_details = [{"Código": m['codigo'], "Descripción": m['descripcion']} for m in mensajes]
            st.error("Detalles del error:")
            st.table(error_details)
            
            # Agregar información sobre posibles soluciones según los códigos de error
            soluciones = []
            for m in mensajes:
                codigo = m['codigo']
                if codigo == '123':
                    soluciones.append("• El CUFD está vencido o es inválido. Solicite un nuevo CUFD.")
                elif codigo == '935':
                    soluciones.append("• La fecha de envío está fuera del rango permitido. Verifique la sincronización de la hora del servidor.")
                elif codigo == 'ANALISIS':
                    soluciones.append(f"• {m['descripcion']}")
            
            if soluciones:
                st.info("**Posibles soluciones:**\n" + "\n".join(soluciones))
        
        # Si hay información de diagnóstico, mostrarla en un área expandible
        if 'diagnostico' in response_data:
            with st.expander("Información de diagnóstico adicional"):
                st.json(response_data['diagnostico'])
        
        # Mostrar ruta del archivo de respuesta para referencia
        if 'raw_response_path' in response_data:
            with st.expander("Datos técnicos para soporte"):
                st.info(f"Respuesta completa guardada en: {response_data['raw_response_path']}")
        
        # Informar sobre siguientes pasos
        st.warning("Por favor, corrija los errores y vuelva a intentar generar la factura.")
        return False

# Mapa ampliado de códigos de error y sus soluciones
ERROR_SOLUTIONS = {
    '123': "El CUFD está vencido o es inválido. Solicite un nuevo CUFD.",
    '935': "La fecha de envío está fuera del rango permitido. Verifique la sincronización de la hora del servidor.",
    '901': "Error de comunicación con el servidor SIAT. Reintente más tarde.",
    '902': "La factura ha sido rechazada. Verifique los datos enviados.",
    '904': "La factura tiene observaciones que deben corregirse.",
    '906': "Error de estructura en el archivo XML. Verifique el formato."
}

def get_error_solution(codigo: str) -> str:
    """Obtiene la solución sugerida para un código de error"""
    return ERROR_SOLUTIONS.get(codigo, "No hay solución específica para este código. Comuníquese con soporte.")
