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

def save_xml_response(xml_content, force_save=False, operation_type=None):
    """
    Guarda el XML de respuesta en un archivo para depuración
    
    Args:
        xml_content: Contenido XML de la respuesta
        force_save: Si es True, siempre guarda el archivo independiente de la configuración
        operation_type: Tipo de operación (ej. 'verification', 'invoice', 'anulacion')
    
    Returns:
        str: Ruta del archivo guardado o None si no se guardó
    """
    # Verificar si debemos guardar esta respuesta según configuración
    if not force_save:
        # Obtener configuración del archivo .env o de la configuración de la aplicación
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        # Nivel de detalle para guardar respuestas (valores posibles: all, errors_only, important, none)
        save_level = os.getenv('XML_RESPONSE_SAVE_LEVEL', 'errors_only')
        
        # Lista de tipos de operaciones consideradas "importantes"
        important_operations = ['invoice', 'anulacion', 'cufd', 'evento_significativo']
        
        # Decidir si guardar basado en la configuración
        if save_level == 'none':
            return None
        elif save_level == 'errors_only':
            # Verificar si hay un error en la respuesta
            if b'<transaccion>true</transaccion>' in xml_content:
                return None  # Es una respuesta exitosa, no la guardamos
        elif save_level == 'important':
            # Solo guardar operaciones importantes
            if operation_type not in important_operations and not force_save:
                return None
    
    # Si llegamos aquí, debemos guardar el archivo
    # Crear directorio logs/responses si no existe
    os.makedirs("logs/responses", exist_ok=True)
    
    # Obtener timestamp para nombre de archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Incluir tipo de operación en el nombre si está disponible
    op_prefix = f"{operation_type}_" if operation_type else ""
    filepath = f"logs/responses/{op_prefix}response_{timestamp}.xml"
    
    # Guardar el XML en un archivo
    with open(filepath, "wb") as f:
        f.write(xml_content)
    
    logger.info(f"Respuesta XML guardada en {filepath}")
    return filepath

def parse_siat_response(content, operation_type=None, force_save=False):
    """
    Parsea una respuesta SOAP del SIAT para extraer información relevante
    
    Args:
        content: Contenido de respuesta XML del servicio SIAT
        operation_type: Tipo de operación que generó esta respuesta
        force_save: Si es True, siempre guarda la respuesta en archivo
    
    Returns:
        tuple: (exito: bool, datos: dict) - Indicador de éxito y datos extraídos
    """
    # Guardar la respuesta para depuración si corresponde
    save_xml_response(content, force_save=force_save, operation_type=operation_type)
    
    try:
        # Parse el XML
        root = ET.fromstring(content)
        
        # Extraer la respuesta basada en namespaces comunes en respuestas SOAP
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns2': 'https://siat.impuestos.gob.bo/'
        }
        
        # Verificar si es una respuesta de verificarComunicacion (estructura especial)
        is_verification = False
        verification_elements = root.findall('.//ns2:verificarComunicacionResponse', namespaces)
        if verification_elements:
            is_verification = True
        
        # Proceso especial para respuestas de verificación de comunicación
        if is_verification:
            # Buscar directamente el elemento 'transaccion', independiente de su contenedor
            transaction_elements = root.findall('.//*transaccion')
            if transaction_elements:
                transaccion = transaction_elements[0].text.lower() == 'true'
                
                # Buscar elementos de mensajes (solo presente en algunos servicios)
                mensaje_elements = root.findall('.//*mensajesList')
                codigo = None
                descripcion = None
                
                if mensaje_elements:
                    codigo_elements = root.findall('.//*codigo')
                    descripcion_elements = root.findall('.//*descripcion')
                    
                    if codigo_elements:
                        codigo = codigo_elements[0].text
                    
                    if descripcion_elements:
                        descripcion = descripcion_elements[0].text
                
                # Creamos una estructura normalizada
                return True, {
                    'transaccion': transaccion,
                    'codigoEstado': codigo,
                    'codigoDescripcion': descripcion
                }
            else:
                # No se encontró el elemento 'transaccion'
                logger.error("No se encontró el elemento 'transaccion' en la respuesta de verificación")
                return False, {
                    'error': "No se encontró el elemento 'transaccion' en la respuesta",
                    'xml_content': content.decode('utf-8') if isinstance(content, bytes) else content
                }
        
        # Buscar elementos RespuestaServicioFacturacion (respuesta específica de facturación)
        facturacion_elements = root.findall('.//RespuestaServicioFacturacion')
        if facturacion_elements:
            facturacion_element = facturacion_elements[0]
            
            # Preparar diccionario de respuesta
            response_data = {}
            
            # Extraer campos comunes
            for field in ['transaccion', 'codigoEstado', 'codigoDescripcion', 'codigoRecepcion']:
                element = facturacion_element.find(f'.//{field}')
                if element is not None:
                    # Convertir 'transaccion' a booleano
                    if field == 'transaccion':
                        response_data[field] = (element.text.lower() == 'true')
                    else:
                        response_data[field] = element.text
            
            # Si no se encontró una transacción, asumir error
            if 'transaccion' not in response_data:
                logger.warning("No se encontró el elemento 'transaccion' en RespuestaServicioFacturacion")
                response_data['transaccion'] = False
            
            return True, response_data
        
        # Proceso para respuestas regulares de operaciones SIAT
        respuesta_elements = root.findall('.//ns2:*Response', namespaces)
        
        if not respuesta_elements:
            # Buscar diferentes patrones de nombres de respuesta
            respuesta_elements = root.findall('.//*Response')
        
        if respuesta_elements:
            respuesta = respuesta_elements[0]
            
            # Obtener el nodo 'return' que contiene la respuesta principal
            return_elements = respuesta.findall('.//return')
            
            if return_elements:
                return_element = return_elements[0]
                
                # Buscar elementos principales en la respuesta
                transaccion_element = return_element.find('.//transaccion')
                codigo_estado_element = return_element.find('.//codigoEstado')
                
                # Preparar diccionario de respuesta
                response_data = {}
                
                # Extraer transacción
                if transaccion_element is not None:
                    response_data['transaccion'] = (transaccion_element.text.lower() == 'true')
                
                # Extraer código de estado
                if codigo_estado_element is not None:
                    response_data['codigoEstado'] = codigo_estado_element.text
                
                # Extraer mensajes
                mensajes_list = return_element.findall('.//mensajesList')
                if mensajes_list:
                    mensajes = []
                    for mensaje in mensajes_list:
                        codigo = mensaje.find('.//codigo')
                        descripcion = mensaje.find('.//descripcion')
                        
                        if codigo is not None and descripcion is not None:
                            mensajes.append({
                                'codigo': codigo.text,
                                'descripcion': descripcion.text
                            })
                    
                    response_data['mensajes'] = mensajes
                    
                    # Si existe un primer mensaje, extraer como código y descripción principal
                    if mensajes:
                        response_data['codigoEstado'] = response_data.get('codigoEstado', mensajes[0]['codigo'])
                        response_data['codigoDescripcion'] = mensajes[0]['descripcion']
                
                # Extraer otros campos comunes
                for field in ['codigoRecepcion', 'cuf', 'fechaRecepcion']:
                    element = return_element.find(f'.//{field}')
                    if element is not None:
                        response_data[field] = element.text
                
                # Buscar elementos de facturas/documentos
                facturas_elements = return_element.findall('.//codigosFacturas')
                if facturas_elements:
                    facturas = []
                    for factura in facturas_elements:
                        codigo_fact = factura.find('.//codigoFactura')
                        codigo_rec = factura.find('.//codigoRecepcion')
                        
                        if codigo_fact is not None and codigo_rec is not None:
                            facturas.append({
                                'codigoFactura': codigo_fact.text,
                                'codigoRecepcion': codigo_rec.text
                            })
                    
                    response_data['facturas'] = facturas
                
                return True, response_data
            else:
                logger.error("No se encontró el elemento 'return' en la respuesta")
                return False, {
                    'error': "No se encontró el elemento 'return' en la respuesta",
                    'xml_content': content.decode('utf-8') if isinstance(content, bytes) else content
                }
        else:
            # Antes de reportar un error, buscar cualquier elemento que pueda contener información útil
            potential_elements = [
                './/RespuestaServicioFacturacion',
                './/return',
                './/respuesta'
            ]
            
            for xpath in potential_elements:
                elements = root.findall(xpath)
                if elements:
                    element = elements[0]
                    response_data = {}
                    
                    # Intentar extraer campos comunes
                    for field in ['transaccion', 'codigoEstado', 'codigoDescripcion', 'codigoRecepcion']:
                        field_elem = element.find(f'.//{field}')
                        if field_elem is not None:
                            if field == 'transaccion':
                                response_data[field] = (field_elem.text.lower() == 'true')
                            else:
                                response_data[field] = field_elem.text
                    
                    # Si encontramos al menos 'transaccion', considerar éxito
                    if 'transaccion' in response_data:
                        logger.info(f"Se encontró un elemento alternativo válido: {xpath}")
                        return True, response_data
            
            logger.error("No se encontró un elemento Response en la respuesta SOAP")
            return False, {
                'error': "No se encontró un elemento Response en la respuesta SOAP",
                'xml_content': content.decode('utf-8') if isinstance(content, bytes) else content
            }
    except ET.ParseError as e:
        logger.error(f"Error al parsear el XML: {e}")
        return False, {
            'error': f"Error al parsear el XML: {e}",
            'xml_content': content.decode('utf-8') if isinstance(content, bytes) else content
        }
    except Exception as e:
        logger.error(f"Error inesperado al procesar la respuesta: {e}")
        return False, {
            'error': f"Error inesperado al procesar la respuesta: {e}",
            'xml_content': content.decode('utf-8') if isinstance(content, bytes) else content
        }

def display_siat_response(response_data, placeholder):
    """
    Muestra la respuesta del SIAT de manera amigable en la interfaz
    
    Args:
        response_data (dict): Datos extraídos de la respuesta
        placeholder: Placeholder de Streamlit para mostrar mensajes
    
    Returns:
        bool: Éxito de la operación
    """
    # Verificar transacción exitosa
    if response_data.get('transaccion'):
        # Obtener código de recepción si existe
        codigo_recepcion = response_data.get('codigoRecepcion', '')
        fecha_recepcion = response_data.get('fechaRecepcion', '')
        
        if codigo_recepcion:
            placeholder.success(f"✅ Operación exitosa: Código de recepción {codigo_recepcion}")
            if fecha_recepcion:
                placeholder.info(f"📅 Fecha de recepción: {fecha_recepcion}")
        else:
            placeholder.success(f"✅ Operación exitosa")
        
        # Mostrar detalles adicionales si existen
        if 'codigoEstado' in response_data:
            placeholder.info(f"🔵 Código de estado: {response_data['codigoEstado']}")
            
        if 'codigoDescripcion' in response_data:
            placeholder.info(f"📝 Descripción: {response_data['codigoDescripcion']}")
        
        return True
    else:
        # Mostrar errores
        mensaje = "❌ La operación no fue exitosa"
        
        if 'codigoDescripcion' in response_data:
            mensaje += f": {response_data['codigoDescripcion']}"
        elif 'mensajes' in response_data and response_data['mensajes']:
            mensaje += f": {response_data['mensajes'][0]['descripcion']}"
        
        placeholder.error(mensaje)
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
