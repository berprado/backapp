import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from database import SessionLocal
from facturador.models import FacturaCabecera
from datetime import datetime
from data_access import obtener_mensaje_por_codigo, obtener_cuf_por_numero_factura, obtener_cufd_vigente
import logging

# Configuración del logger
logger = logging.getLogger('reversion')
logger.setLevel(logging.DEBUG)

# Crear manejadores para archivo y consola
file_handler = logging.FileHandler('logs/reversion.log')
console_handler = logging.StreamHandler()

# Definir formato del log
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Agregar manejadores al logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Evitar registros duplicados si el logger ya tiene handlers
if len(logger.handlers) > 2:
    logger.handlers = logger.handlers[:2]

# Cargar variables de entorno
load_dotenv()

# Códigos de estado como constantes
ESTADO_REVERSION_CONFIRMADA = "907"
ESTADO_FACTURA_YA_REVERTIDA = "981"
ESTADO_FACTURA_NO_EXISTE = "924"
ESTADO_SISTEMA_NO_AUTORIZADO = "3011"
ESTADO_FUERA_DE_PLAZO = "3012"

def construir_solicitud_reversion(cuf):
    """
    Construye el XML para solicitar la reversión de anulación de factura.
    
    Args:
        cuf (str): Código Único de Facturación
        
    Returns:
        bytes: XML de solicitud codificado en UTF-8
    """
    logger.info(f"Construyendo solicitud de reversión para CUF: {cuf}")
    
    try:
        # Obtener el CUFD vigente de la base de datos
        cufd_vigente = obtener_cufd_vigente()
        if not cufd_vigente:
            error_msg = "No hay un CUFD vigente en la base de datos"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug(f"CUFD vigente obtenido de la base de datos: {cufd_vigente[:10]}...")
        
        envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
        body = ET.SubElement(envelope, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
        reversion_anulacion_factura = ET.SubElement(body, "{https://siat.impuestos.gob.bo/}reversionAnulacionFactura")
        solicitud = ET.SubElement(reversion_anulacion_factura, "SolicitudServicioReversionAnulacionFactura")

        # Añadir los elementos necesarios a la solicitud
        parametros = {
            "codigoAmbiente": os.getenv('CODIGO_AMBIENTE'),
            "codigoPuntoVenta": os.getenv('CODIGO_PUNTO_VENTA'),
            "codigoSistema": os.getenv('CODIGO_SISTEMA'),
            "codigoSucursal": os.getenv('CODIGO_SUCURSAL'),
            "nit": os.getenv('NIT'),
            "codigoDocumentoSector": os.getenv('CODIGO_DOCUMENTO_SECTOR'),
            "codigoEmision": os.getenv('CODIGO_TIPO_EMISION'),
            "codigoModalidad": os.getenv('CODIGO_MODALIDAD'),
            "cufd": cufd_vigente,  # Usar el CUFD de la base de datos
            "cuis": os.getenv('CUIS'),
            "tipoFacturaDocumento": os.getenv('CODIGO_TIPO_FACTURA'),
            "cuf": cuf
        }
        
        # Registrar los parámetros en el log (excepto información sensible)
        log_params = parametros.copy()
        if 'cufd' in log_params and log_params['cufd']:
            log_params['cufd'] = f"{log_params['cufd'][:5]}...{log_params['cufd'][-5:]}" if len(log_params['cufd']) > 10 else "[valor protegido]"
        if 'cuis' in log_params and log_params['cuis']:
            log_params['cuis'] = f"{log_params['cuis'][:3]}...{log_params['cuis'][-3:]}" if len(log_params['cuis']) > 6 else "[valor protegido]"
        logger.debug(f"Parámetros de solicitud: {log_params}")
        
        # Verificar que todos los parámetros requeridos estén presentes y no sean None
        for key, value in parametros.items():
            if value is None:
                error_msg = f"El parámetro '{key}' es requerido pero no está definido"
                logger.error(error_msg)
                raise ValueError(error_msg)
            ET.SubElement(solicitud, key).text = str(value)  # Convertir a string para evitar problemas

        # Convertir la estructura a una cadena XML
        xml_data = ET.tostring(envelope, encoding='utf-8', method='xml')
        
        # Registrar una versión resumida del XML para no saturar los logs
        xml_str = xml_data.decode('utf-8')
        logger.debug(f"XML de solicitud (resumido): {xml_str[:100]}...{xml_str[-100:] if len(xml_str) > 200 else ''}")
        
        return xml_data
    
    except Exception as e:
        logger.error(f"Error al construir solicitud de reversión: {str(e)}", exc_info=True)
        raise

def enviar_solicitud_reversion(cuf):
    """
    Envía la solicitud de reversión al servicio SIAT.
    
    Args:
        cuf (str): Código Único de Facturación
        
    Returns:
        tuple: (éxito, respuesta/mensaje de error)
    """
    logger.info(f"Enviando solicitud de reversión para CUF: {cuf}")
    
    url = os.getenv('URL_SERVICIO_FACTURACION', "https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta")
    headers = {
        'Content-Type': 'text/xml;charset=UTF-8',
        'apikey': os.getenv('API_KEY')
    }
    
    # Log de la URL y cabeceras (ocultando la API key)
    log_headers = headers.copy()
    if 'apikey' in log_headers and log_headers['apikey']:
        log_headers['apikey'] = f"{log_headers['apikey'][:5]}...{log_headers['apikey'][-5:]}" if len(log_headers['apikey']) > 10 else "[valor protegido]"
    logger.debug(f"URL del servicio: {url}")
    logger.debug(f"Cabeceras: {log_headers}")

    try:
        solicitud_xml = construir_solicitud_reversion(cuf)
        logger.debug("Enviando solicitud al servicio SIAT...")
        
        response = requests.post(url, headers=headers, data=solicitud_xml)
        logger.debug(f"Respuesta recibida. Código HTTP: {response.status_code}")
        
        response.raise_for_status()
        
        # Registrar un extracto de la respuesta para no saturar los logs
        response_content = response.content.decode('utf-8') if response.content else ""
        logger.debug(f"Respuesta (resumida): {response_content[:100]}...{response_content[-100:] if len(response_content) > 200 else ''}")
        
        return True, response.content
    
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Error HTTP al enviar solicitud: {http_err}", exc_info=True)
        return False, f"HTTP error occurred: {http_err}"
    
    except Exception as e:
        logger.error(f"Error general al enviar solicitud: {e}", exc_info=True)
        return False, f"An error occurred: {e}"

def procesar_respuesta_reversion(respuesta_xml, factura):
    """
    Procesa la respuesta XML del servicio SIAT y actualiza la factura según corresponda.
    
    Args:
        respuesta_xml (bytes): Respuesta XML del servicio
        factura (FacturaCabecera): Objeto de factura a actualizar
        
    Returns:
        tuple: (éxito, mensaje)
    """
    logger.info(f"Procesando respuesta para factura #{factura.numeroFactura}")
    
    try:
        # Procesar el XML de respuesta para extraer la información relevante
        tree = ET.fromstring(respuesta_xml)
        
        # Extraer campos relevantes de la respuesta
        transaccion_elem = tree.find('.//transaccion')
        codigo_estado_elem = tree.find('.//codigoEstado')
        
        if transaccion_elem is None or codigo_estado_elem is None:
            logger.error("Respuesta XML no contiene elementos requeridos (transaccion o codigoEstado)")
            logger.debug(f"Respuesta XML completa: {respuesta_xml}")
            return False, "Respuesta del servicio incorrecta o incompleta"
        
        transaccion = transaccion_elem.text.lower() == 'true'
        codigo_estado = codigo_estado_elem.text
        
        logger.debug(f"Transacción exitosa: {transaccion}")
        logger.debug(f"Código de estado: {codigo_estado}")

        # Obtener la descripción del código desde la base de datos
        descripcion_codigo = obtener_mensaje_por_codigo(codigo_estado)
        logger.debug(f"Descripción del código: {descripcion_codigo}")

        if codigo_estado == ESTADO_REVERSION_CONFIRMADA:  # Reversión confirmada
            logger.info(f"Reversión confirmada para factura #{factura.numeroFactura}")
            
            factura.estado = "Valida"
            factura.fechaValidacion = datetime.now()

            session = SessionLocal()
            try:
                session.add(factura)
                session.commit()
                logger.info("Factura actualizada correctamente en la base de datos")
            except Exception as e:
                session.rollback()
                logger.error(f"Error al actualizar la factura en BD: {e}", exc_info=True)
                return False, f"Error al actualizar la factura: {e}"
            finally:
                session.close()

            return True, f"Reversión de anulación realizada correctamente: {descripcion_codigo}"

        elif codigo_estado == ESTADO_FACTURA_YA_REVERTIDA:  # Factura no disponible para reversión
            logger.warning(f"Factura #{factura.numeroFactura} ya fue revertida previamente")
            return False, f"La factura ya fue revertida previamente: {descripcion_codigo}"

        elif codigo_estado == ESTADO_FACTURA_NO_EXISTE:  # Factura no existe en la base de datos
            logger.warning(f"Factura #{factura.numeroFactura} no existe en la base de datos del SIN")
            return False, f"Factura no existe en la base de datos del SIN: {descripcion_codigo}"

        elif codigo_estado == ESTADO_SISTEMA_NO_AUTORIZADO:  # Sistema no autorizado
            logger.error("El sistema no está autorizado para utilizar la reversión")
            return False, f"El sistema no está autorizado para utilizar la reversión: {descripcion_codigo}"

        elif codigo_estado == ESTADO_FUERA_DE_PLAZO:  # Solicitud de reversión fuera de plazo
            logger.warning(f"Solicitud de reversión para factura #{factura.numeroFactura} fuera de plazo")
            return False, f"La solicitud de reversión fue realizada fuera de plazo: {descripcion_codigo}"

        else:
            logger.error(f"Código de estado desconocido: {codigo_estado}")
            return False, f"Error desconocido en la reversión: {descripcion_codigo}"
    
    except ET.ParseError as e:
        logger.error(f"Error al parsear XML de respuesta: {e}", exc_info=True)
        logger.debug(f"XML problemático: {respuesta_xml}")
        return False, f"Error al procesar la respuesta del servicio: {e}"
    
    except Exception as e:
        logger.error(f"Error al procesar respuesta: {e}", exc_info=True)
        return False, f"Error al procesar la respuesta: {e}"

def revertir_anulacion_factura(numero_factura):
    """
    Función principal para revertir la anulación de una factura.
    
    Args:
        numero_factura (str): Número de la factura a revertir
        
    Returns:
        tuple: (éxito, mensaje)
    """
    logger.info(f"Iniciando proceso de reversión de anulación para factura #{numero_factura}")
    
    try:
        # Obtener CUF y datos de la factura
        cuf, factura = obtener_cuf_por_numero_factura(numero_factura)
        
        if factura is None:
            logger.warning(f"No se encontró la factura #{numero_factura}")
            return False, "No se encontró la factura especificada."
        
        logger.info(f"Factura encontrada. CUF: {cuf}")
        
        # Verificar que exista un CUFD vigente
        cufd_vigente = obtener_cufd_vigente()
        if not cufd_vigente:
            error_msg = "No hay un CUFD vigente. Solicite un nuevo CUFD antes de continuar."
            logger.error(error_msg)
            return False, error_msg
        
        # Validar que las variables de entorno necesarias estén definidas
        variables_requeridas = [
            'CODIGO_AMBIENTE', 'CODIGO_PUNTO_VENTA', 'CODIGO_SISTEMA', 
            'CODIGO_SUCURSAL', 'NIT', 'CODIGO_DOCUMENTO_SECTOR',
            'CODIGO_TIPO_EMISION', 'CODIGO_MODALIDAD',
            'CUIS', 'CODIGO_TIPO_FACTURA', 'API_KEY'
        ]
        
        faltantes = [var for var in variables_requeridas if not os.getenv(var)]
        if faltantes:
            error_msg = f"Faltan variables de entorno requeridas: {', '.join(faltantes)}"
            logger.error(error_msg)
            return False, error_msg
            
        # Enviar solicitud de reversión
        exito, respuesta = enviar_solicitud_reversion(cuf)
        
        if exito:
            logger.debug("Solicitud enviada exitosamente, procesando respuesta...")
            return procesar_respuesta_reversion(respuesta, factura)
        else:
            logger.error(f"Error al enviar solicitud: {respuesta}")
            return False, respuesta
    
    except Exception as e:
        logger.error(f"Error general en proceso de reversión: {e}", exc_info=True)
        return False, f"Error en el proceso de reversión: {str(e)}"

# Punto de entrada si se ejecuta como script independiente
if __name__ == "__main__":
    if len(sys.argv) > 1:
        numero_factura = sys.argv[1]
        print(f"Revirtiendo anulación de factura {numero_factura}...")
        exito, mensaje = revertir_anulacion_factura(numero_factura)
        print(f"Resultado: {'Éxito' if exito else 'Error'} - {mensaje}")
    else:
        print("Uso: python reversion.py <numero_factura>")