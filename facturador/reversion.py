import os
import sys
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from data_access import SessionLocal
from models import FacturaCabecera
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
ESTADO_REVERSION_CONFIRMADA = "907"       # Reversión confirmada exitosamente
ESTADO_REVERSION_RECHAZADA = "909"        # Reversión rechazada por el SIAT (NUEVO)
ESTADO_FACTURA_YA_REVERTIDA = "981"       # Factura ya revertida anteriormente
ESTADO_FACTURA_NO_EXISTE = "924"          # Factura no existe en base de datos SIAT
ESTADO_SISTEMA_NO_AUTORIZADO = "3011"     # Sistema no autorizado
ESTADO_FUERA_DE_PLAZO = "3012"            # Solicitud fuera de plazo


def limpiar_emojis_descripcion(descripcion):
    """
    Limpia emojis comunes del inicio de una descripción para evitar duplicación.
    
    Algunos mensajes del SIAT vienen con emojis (ej: "✅ REVERSION...").
    Esta función los elimina para que podamos añadir nuestro propio formato consistente.
    
    Args:
        descripcion (str): Descripción que puede contener emojis al inicio
        
    Returns:
        str: Descripción sin emojis al inicio
        
    Ejemplo:
        "✅ REVERSION CONFIRMADA" → "REVERSION CONFIRMADA"
        "❌ ERROR EN PROCESO" → "ERROR EN PROCESO"
        "MENSAJE NORMAL" → "MENSAJE NORMAL"
    """
    if not descripcion:
        return descripcion
    
    # Lista de emojis comunes a remover del inicio
    emojis_a_limpiar = ['✅', '❌', '⚠️', 'ℹ️', '🔴', '🟢', '🟡', '⏰', '❓']
    
    descripcion_limpia = descripcion.strip()
    
    # Remover emojis del inicio (pueden estar repetidos)
    for emoji in emojis_a_limpiar:
        while descripcion_limpia.startswith(emoji):
            descripcion_limpia = descripcion_limpia[len(emoji):].strip()
    
    return descripcion_limpia


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
    
    VERSIÓN MEJORADA:
    - Extrae TODOS los campos de la respuesta (codigoEstado, codigoDescripcion, mensajesList)
    - Usa BD local como fuente primaria, SIAT como fallback
    - Construye mensajes detallados para el usuario con formato Markdown
    - Logging exhaustivo para debugging
    
    Args:
        respuesta_xml (bytes): Respuesta XML del servicio
        factura (FacturaCabecera): Objeto de factura a actualizar
        
    Returns:
        tuple: (éxito, mensaje_detallado)
    """
    logger.info(f"[PROCESAMIENTO] Iniciando análisis de respuesta para factura #{factura.numeroFactura}")
    
    try:
        # ========== PASO 1: PARSEAR XML ==========
        tree = ET.fromstring(respuesta_xml)
        
        # Extraer campos principales
        transaccion_elem = tree.find('.//transaccion')
        codigo_estado_elem = tree.find('.//codigoEstado')
        codigo_descripcion_elem = tree.find('.//codigoDescripcion')
        
        # Validación de campos obligatorios
        if transaccion_elem is None or codigo_estado_elem is None:
            logger.error("[ERROR] Respuesta XML incompleta: faltan campos obligatorios")
            logger.debug(f"XML recibido: {respuesta_xml.decode('utf-8')[:500]}")
            return False, "❌ Respuesta del servicio incorrecta o incompleta"
        
        # Extraer valores
        transaccion = transaccion_elem.text.lower() == 'true'
        codigo_estado = codigo_estado_elem.text
        codigo_descripcion_siat = codigo_descripcion_elem.text if codigo_descripcion_elem is not None else None
        
        logger.info(f"[SIAT] Código estado: {codigo_estado}")
        logger.info(f"[SIAT] Transacción: {transaccion}")
        logger.debug(f"[SIAT] Descripción: {codigo_descripcion_siat}")
        
        # ========== PASO 2: OBTENER DESCRIPCIÓN DE BD LOCAL ==========
        descripcion_bd = obtener_mensaje_por_codigo(codigo_estado)
        
        # Decidir qué descripción usar (BD primero, SIAT como fallback)
        if descripcion_bd and not descripcion_bd.startswith("Código desconocido"):
            descripcion_principal = limpiar_emojis_descripcion(descripcion_bd)
            logger.debug(f"[BD] Descripción encontrada: {descripcion_bd}")
        else:
            descripcion_principal = limpiar_emojis_descripcion(codigo_descripcion_siat) if codigo_descripcion_siat else f"Código {codigo_estado}"
            logger.warning(f"[BD] Código {codigo_estado} no encontrado, usando descripción SIAT")
        
        # ========== PASO 3: EXTRAER MENSAJES ADICIONALES (mensajesList) ==========
        mensajes_detalle = []
        for mensaje_elem in tree.findall('.//mensajesList'):
            codigo_msg_elem = mensaje_elem.find('codigo')
            desc_msg_elem = mensaje_elem.find('descripcion')
            
            if codigo_msg_elem is not None and desc_msg_elem is not None:
                codigo_msg = codigo_msg_elem.text
                desc_msg_siat = desc_msg_elem.text
                
                # Intentar obtener descripción de BD para este código adicional
                desc_msg_bd = obtener_mensaje_por_codigo(codigo_msg)
                
                # Decidir qué descripción usar
                if desc_msg_bd and not desc_msg_bd.startswith("Código desconocido"):
                    desc_msg_final = desc_msg_bd
                else:
                    desc_msg_final = desc_msg_siat
                
                mensajes_detalle.append({
                    'codigo': codigo_msg,
                    'descripcion': desc_msg_final
                })
                
                logger.info(f"[DETALLE] Mensaje adicional: [{codigo_msg}] {desc_msg_final}")
        
        # ========== PASO 4: PROCESAR SEGÚN EL CÓDIGO DE ESTADO ==========
        
        # IMPORTANTE: Guardar numero_factura ANTES de modificar la sesión
        numero_factura = factura.numeroFactura
        
        if codigo_estado == ESTADO_REVERSION_CONFIRMADA:  # 907
            logger.info(f"[EXITO] Reversion confirmada para factura #{numero_factura}")
            
            # Actualizar factura en BD
            factura.estado = "Valida"
            factura.fechaValidacion = datetime.now()
            factura.fechaAnulacion = None
            factura.motivoAnulacion = None
            factura.anuladaPor = None
            
            session = SessionLocal()
            try:
                session.add(factura)
                session.commit()
                logger.info("[BD] Factura actualizada correctamente")
            except Exception as e:
                session.rollback()
                logger.error(f"[BD] Error al actualizar factura: {e}", exc_info=True)
                return False, f"❌ **Error al actualizar la factura en base de datos**\n\n{str(e)}"
            finally:
                session.close()
            
            # Construir mensaje de éxito usando la variable guardada
            mensaje_exito = f"✅ **{descripcion_principal}**\n\n" \
                           f"La factura #{numero_factura} ha sido restaurada exitosamente."
            
            return True, mensaje_exito
        
        elif codigo_estado == ESTADO_REVERSION_RECHAZADA:  # 909
            logger.warning(f"[RECHAZADO] Reversion rechazada para factura #{numero_factura}")
            
            # Construir mensaje detallado con mensajesList
            mensaje_rechazo = f"❌ **{descripcion_principal}**\n\n"
            
            if mensajes_detalle:
                mensaje_rechazo += "**Motivos específicos del rechazo:**\n"
                for msg in mensajes_detalle:
                    mensaje_rechazo += f"• **[{msg['codigo']}]** {msg['descripcion']}\n"
                
                # Agregar interpretación contextual según códigos conocidos
                codigos_en_respuesta = [msg['codigo'] for msg in mensajes_detalle]
                
                mensaje_rechazo += "\n**Posibles acciones:**\n"
                
                if "981" in codigos_en_respuesta:
                    mensaje_rechazo += "• Verifique que la factura esté efectivamente anulada\n"
                    mensaje_rechazo += "• Confirme que no haya sido revertida previamente\n"
                    mensaje_rechazo += "• La factura pudo haber sido usada en una declaración jurada\n"
                
                if any(c in ["3012", "970"] for c in codigos_en_respuesta):
                    mensaje_rechazo += "• La reversión está fuera del plazo normativo (9 días del mes siguiente)\n"
                
                if "924" in codigos_en_respuesta:
                    mensaje_rechazo += "• Verifique el número de factura ingresado\n"
            else:
                # Si no hay mensajesList, dar mensaje genérico
                mensaje_rechazo += "No se proporcionaron detalles específicos. " \
                                  "Verifique el estado actual de la factura en el sistema."
            
            return False, mensaje_rechazo
        
        elif codigo_estado == ESTADO_FACTURA_YA_REVERTIDA:  # 981
            logger.warning(f"[INFO] Factura #{numero_factura} ya revertida")
            
            # Intentar sincronizar estado local si está desactualizado
            if factura.estado == "Anulada":
                logger.info(f"[SYNC] Sincronizando estado local de factura {numero_factura}")

                
                factura.estado = "Valida"
                factura.fechaValidacion = datetime.now()
                factura.fechaAnulacion = None
                factura.motivoAnulacion = None
                
                session = SessionLocal()
                try:
                    session.add(factura)
                    session.commit()
                    logger.info("[SYNC] Estado local sincronizado")
                    
                    return True, f"ℹ️ **La factura ya estaba revertida en el SIAT**\n\n" \
                                f"Se ha sincronizado el estado local de la factura #{numero_factura}."
                except Exception as e:
                    logger.error(f"[SYNC] Error al sincronizar: {e}")
                    return False, f"⚠️ **{descripcion_principal}**\n\n" \
                                 f"No se pudo sincronizar el estado local."
                finally:
                    session.close()
            
            return False, f"ℹ️ **{descripcion_principal}**\n\n" \
                         f"La factura ya fue revertida anteriormente."
        
        elif codigo_estado == ESTADO_FACTURA_NO_EXISTE:  # 924
            logger.warning(f"[ERROR] Factura #{numero_factura} no existe en SIAT")
            return False, f"❌ **{descripcion_principal}**\n\n" \
                         f"La factura no existe en la base de datos del SIN. " \
                         f"Verifique el número de factura."
        
        elif codigo_estado == ESTADO_SISTEMA_NO_AUTORIZADO:  # 3011
            logger.error("[CRITICO] Sistema no autorizado para reversion")
            return False, f"❌ **{descripcion_principal}**\n\n" \
                         f"El sistema no está autorizado para utilizar el servicio de reversión. " \
                         f"Contacte al administrador."
        
        elif codigo_estado == ESTADO_FUERA_DE_PLAZO:  # 3012
            logger.warning(f"[PLAZO] Reversion fuera de plazo para factura #{numero_factura}")
            return False, f"⏰ **{descripcion_principal}**\n\n" \
                         f"La reversión está fuera del plazo permitido " \
                         f"(hasta el día 9 del mes siguiente a la emisión)."
        
        else:
            # Código no contemplado en el sistema
            logger.error(f"[DESCONOCIDO] Codigo {codigo_estado} no contemplado")
            
            mensaje_desconocido = f"❓ **Código de respuesta no reconocido: {codigo_estado}**\n\n" \
                                 f"Descripción: {descripcion_principal}\n\n"
            
            if mensajes_detalle:
                mensaje_desconocido += "**Mensajes adicionales:**\n"
                for msg in mensajes_detalle:
                    mensaje_desconocido += f"• [{msg['codigo']}] {msg['descripcion']}\n"
            
            return False, mensaje_desconocido
    
    except ET.ParseError as e:
        logger.error(f"[PARSE] Error al parsear XML: {e}", exc_info=True)
        logger.debug(f"XML problematico: {respuesta_xml.decode('utf-8')[:500]}")
        return False, f"❌ **Error al procesar la respuesta del servicio**\n\n{str(e)}"
    
    except Exception as e:
        logger.error(f"[ERROR] Error general al procesar respuesta: {e}", exc_info=True)
        return False, f"❌ **Error inesperado al procesar la respuesta**\n\n{str(e)}"

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