"""
Módulo de Reversión de Anulación de Facturas
============================================

PROPÓSITO:
----------
Gestiona el proceso de reversión de anulación de facturas electrónicas
previamente anuladas, restaurándolas a su estado válido original.

FUNCIONALIDADES:
----------------
- Construcción de solicitudes SOAP para reversión
- Envío de solicitudes al servicio SIAT
- Procesamiento de respuestas con múltiples códigos de estado
- Actualización de estado en base de datos local
- Limpieza de emojis duplicados en descripciones del SIAT

NORMATIVA:
----------
Plazo de reversión: Hasta el día 9 del mes siguiente a la emisión

CÓDIGOS DE ESTADO SOPORTADOS:
------------------------------
- 907: Reversión confirmada
- 909: Reversión rechazada
- 981: Factura ya revertida
- 924: Factura no existe en BD del SIN
- 3011: Sistema no autorizado
- 3012: Solicitud fuera de plazo

VERSIÓN: 2.1.0 (Refactorizado - 16 octubre 2025)
CAMBIOS:
  - Migrado a logger centralizado (logger_config.py)
  - Eliminada configuración manual de logging (30+ líneas)
  - Prefijos de log estandarizados ([REVERSION])
  - 100% consistente con anulacion.py
  - Logs verbosos condicionados a DEBUG level

AUTOR: Sistema de Facturación Electrónica
"""

import os
import sys
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from data_access import SessionLocal
from models import FacturaCabecera
from datetime import datetime
from data_access import obtener_mensaje_por_codigo, obtener_cuf_por_numero_factura, obtener_cufd_vigente

# ========================================================================
# CONFIGURACIÓN DE LOGGING CENTRALIZADA
# ========================================================================
# ANTES: 30+ líneas de configuración manual con handlers duplicados
# AHORA: 1 línea usando el sistema centralizado
from logger_config import get_logger
logger = get_logger()

# Cargar variables de entorno
load_dotenv()

# ========================================================================
# CONSTANTES: Códigos de Estado del SIAT
# ========================================================================

ESTADO_REVERSION_CONFIRMADA = "907"       # Reversión confirmada exitosamente
ESTADO_REVERSION_RECHAZADA = "909"        # Reversión rechazada por el SIAT
ESTADO_FACTURA_YA_REVERTIDA = "981"       # Factura ya revertida anteriormente
ESTADO_FACTURA_NO_EXISTE = "924"          # Factura no existe en base de datos SIAT
ESTADO_SISTEMA_NO_AUTORIZADO = "3011"     # Sistema no autorizado
ESTADO_FUERA_DE_PLAZO = "3012"            # Solicitud fuera de plazo


# ========================================================================
# FUNCIONES AUXILIARES
# ========================================================================


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
    logger.info(f"[REVERSION] Construyendo solicitud para CUF: {cuf[:20]}...")
    
    try:
        # Obtener el CUFD vigente de la base de datos
        cufd_vigente = obtener_cufd_vigente()
        if not cufd_vigente:
            error_msg = "No hay un CUFD vigente en la base de datos"
            logger.error(f"[REVERSION] {error_msg}")
            raise ValueError(error_msg)
        
        logger.debug(f"[REVERSION] CUFD vigente obtenido: {cufd_vigente[:10]}...")
        
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
            "cufd": cufd_vigente,
            "cuis": os.getenv('CUIS'),
            "tipoFacturaDocumento": os.getenv('CODIGO_TIPO_FACTURA'),
            "cuf": cuf
        }
        
        # Logging estandarizado: Solo en DEBUG, con prefijo consistente
        if logger.level <= 10:  # DEBUG = 10
            log_params = parametros.copy()
            # Proteger datos sensibles
            for key in ['cufd', 'cuis']:
                if key in log_params and log_params[key]:
                    val = log_params[key]
                    log_params[key] = f"{val[:5]}...{val[-5:]}" if len(val) > 10 else "[protegido]"
            logger.debug(f"[REVERSION] Parametros: {log_params}")
        
        # Verificar parámetros requeridos
        for key, value in parametros.items():
            if value is None:
                error_msg = f"El parametro '{key}' es requerido pero no esta definido"
                logger.error(f"[REVERSION] {error_msg}")
                raise ValueError(error_msg)
            ET.SubElement(solicitud, key).text = str(value)

        xml_data = ET.tostring(envelope, encoding='utf-8', method='xml')
        
        # Log resumido solo en DEBUG
        if logger.level <= 10:
            xml_str = xml_data.decode('utf-8')
            logger.debug(f"[REVERSION] XML (extracto): ...{xml_str[-100:]}")
        
        return xml_data
    
    except Exception as e:
        logger.error(f"[REVERSION] Error al construir solicitud: {str(e)}", exc_info=True)
        raise

def enviar_solicitud_reversion(cuf):
    """
    Envía la solicitud de reversión al servicio SIAT.
    
    Args:
        cuf (str): Código Único de Facturación
        
    Returns:
        tuple: (éxito, respuesta/mensaje de error)
    """
    logger.info(f"[REVERSION] Enviando solicitud para CUF: {cuf[:20]}...")
    
    url = os.getenv('URL_SERVICIO_FACTURACION', "https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta")
    headers = {
        'Content-Type': 'text/xml;charset=UTF-8',
        'apikey': os.getenv('API_KEY')
    }
    
    # Log de URL solo en DEBUG
    if logger.level <= 10:
        logger.debug(f"[REVERSION] URL: {url}")

    try:
        solicitud_xml = construir_solicitud_reversion(cuf)
        
        response = requests.post(url, headers=headers, data=solicitud_xml, timeout=30)
        logger.info(f"[REVERSION] Respuesta HTTP {response.status_code} recibida")
        
        response.raise_for_status()
        
        return True, response.content
    
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"[REVERSION] Error HTTP: {http_err}", exc_info=True)
        return False, f"Error HTTP: {http_err}"
    
    except Exception as e:
        logger.error(f"[REVERSION] Error al enviar: {e}", exc_info=True)
        return False, f"Error: {e}"

def procesar_respuesta_reversion(respuesta_xml, factura):
    """
    Procesa la respuesta XML del servicio SIAT y actualiza la factura según corresponda.
    
    VERSIÓN MEJORADA (v2.1.0):
    - Extrae TODOS los campos de la respuesta (codigoEstado, codigoDescripcion, mensajesList)
    - Usa BD local como fuente primaria, SIAT como fallback
    - Construye mensajes detallados para el usuario con formato Markdown
    - Logging estandarizado con prefijos consistentes
    - Prevención de DetachedInstanceError
    
    Args:
        respuesta_xml (bytes): Respuesta XML del servicio
        factura (FacturaCabecera): Objeto de factura a actualizar
        
    Returns:
        tuple: (éxito, mensaje_detallado)
    """
    # Guardar numero_factura ANTES de cualquier operación de BD
    numero_factura = factura.numeroFactura
    
    logger.info(f"[REVERSION] Procesando respuesta para factura #{numero_factura}")
    
    try:
        # ========== PARSEAR XML ==========
        tree = ET.fromstring(respuesta_xml)
        
        transaccion_elem = tree.find('.//transaccion')
        codigo_estado_elem = tree.find('.//codigoEstado')
        codigo_descripcion_elem = tree.find('.//codigoDescripcion')
        
        if transaccion_elem is None or codigo_estado_elem is None:
            logger.error("[REVERSION] XML incompleto: faltan campos obligatorios")
            return False, "❌ Respuesta del servicio incorrecta o incompleta"
        
        transaccion = transaccion_elem.text.lower() == 'true'
        codigo_estado = codigo_estado_elem.text
        codigo_descripcion_siat = codigo_descripcion_elem.text if codigo_descripcion_elem is not None else None
        
        logger.info(f"[REVERSION] Codigo: {codigo_estado}, Transaccion: {transaccion}")
        
        # ========== OBTENER DESCRIPCIÓN DE BD ==========
        descripcion_bd = obtener_mensaje_por_codigo(codigo_estado)
        
        if descripcion_bd and not descripcion_bd.startswith("Código desconocido"):
            descripcion_principal = limpiar_emojis_descripcion(descripcion_bd)
        else:
            descripcion_principal = limpiar_emojis_descripcion(codigo_descripcion_siat) if codigo_descripcion_siat else f"Codigo {codigo_estado}"
            if not descripcion_bd or descripcion_bd.startswith("Código desconocido"):
                logger.warning(f"[REVERSION] Codigo {codigo_estado} no encontrado en BD local")
        
        # ========== EXTRAER mensajesList ==========
        mensajes_detalle = []
        for mensaje_elem in tree.findall('.//mensajesList'):
            codigo_msg_elem = mensaje_elem.find('codigo')
            desc_msg_elem = mensaje_elem.find('descripcion')
            
            if codigo_msg_elem is not None and desc_msg_elem is not None:
                codigo_msg = codigo_msg_elem.text
                desc_msg_siat = desc_msg_elem.text
                
                desc_msg_bd = obtener_mensaje_por_codigo(codigo_msg)
                desc_msg_final = desc_msg_bd if (desc_msg_bd and not desc_msg_bd.startswith("Código desconocido")) else desc_msg_siat
                
                mensajes_detalle.append({
                    'codigo': codigo_msg,
                    'descripcion': desc_msg_final
                })
                
                logger.info(f"[REVERSION] Mensaje adicional [{codigo_msg}]: {desc_msg_final[:50]}...")
        
        # ========== PROCESAR SEGÚN CÓDIGO ==========
        
        if codigo_estado == ESTADO_REVERSION_CONFIRMADA:  # 907
            logger.info(f"[REVERSION] Confirmada para factura #{numero_factura}")
            
            factura.estado = "Valida"
            factura.fechaValidacion = datetime.now()
            factura.fechaAnulacion = None
            factura.motivoAnulacion = None
            factura.anuladaPor = None
            
            session = SessionLocal()
            try:
                session.add(factura)
                session.commit()
                logger.info(f"[REVERSION] BD actualizada para factura #{numero_factura}")
            except Exception as e:
                session.rollback()
                logger.error(f"[REVERSION] Error BD: {e}", exc_info=True)
                return False, f"❌ **Error al actualizar la factura en base de datos**\n\n{str(e)}"
            finally:
                session.close()
            
            mensaje_exito = f"✅ **{descripcion_principal}**\n\n" \
                           f"La factura #{numero_factura} ha sido restaurada exitosamente."
            
            return True, mensaje_exito
        
        elif codigo_estado == ESTADO_REVERSION_RECHAZADA:  # 909
            logger.warning(f"[REVERSION] Rechazada para factura #{numero_factura}")
            
            mensaje_rechazo = f"❌ **{descripcion_principal}**\n\n"
            
            if mensajes_detalle:
                mensaje_rechazo += "**Motivos especificos del rechazo:**\n"
                for msg in mensajes_detalle:
                    mensaje_rechazo += f"• **[{msg['codigo']}]** {msg['descripcion']}\n"
                
                codigos_en_respuesta = [msg['codigo'] for msg in mensajes_detalle]
                
                mensaje_rechazo += "\n**Posibles acciones:**\n"
                
                if "981" in codigos_en_respuesta:
                    mensaje_rechazo += "• Verifique que la factura este efectivamente anulada\n"
                    mensaje_rechazo += "• Confirme que no haya sido revertida previamente\n"
                    mensaje_rechazo += "• La factura pudo haber sido usada en una declaracion jurada\n"
                
                if any(c in ["3012", "970"] for c in codigos_en_respuesta):
                    mensaje_rechazo += "• La reversion esta fuera del plazo normativo (9 dias del mes siguiente)\n"
                
                if "924" in codigos_en_respuesta:
                    mensaje_rechazo += "• Verifique el numero de factura ingresado\n"
            else:
                mensaje_rechazo += "No se proporcionaron detalles especificos. " \
                                  "Verifique el estado actual de la factura en el sistema."
            
            return False, mensaje_rechazo
        
        elif codigo_estado == ESTADO_FACTURA_YA_REVERTIDA:  # 981
            logger.warning(f"[REVERSION] Factura #{numero_factura} ya revertida")
            
            if factura.estado == "Anulada":
                logger.info(f"[REVERSION] Sincronizando estado local de factura #{numero_factura}")
                
                factura.estado = "Valida"
                factura.fechaValidacion = datetime.now()
                factura.fechaAnulacion = None
                factura.motivoAnulacion = None
                
                session = SessionLocal()
                try:
                    session.add(factura)
                    session.commit()
                    logger.info(f"[REVERSION] Estado sincronizado para factura #{numero_factura}")
                    
                    return True, f"ℹ️ **La factura ya estaba revertida en el SIAT**\n\n" \
                                f"Se ha sincronizado el estado local de la factura #{numero_factura}."
                except Exception as e:
                    logger.error(f"[REVERSION] Error al sincronizar: {e}")
                    return False, f"⚠️ **{descripcion_principal}**\n\n" \
                                 f"No se pudo sincronizar el estado local."
                finally:
                    session.close()
            
            return False, f"ℹ️ **{descripcion_principal}**\n\n" \
                         f"La factura ya fue revertida anteriormente."
        
        elif codigo_estado == ESTADO_FACTURA_NO_EXISTE:  # 924
            logger.warning(f"[REVERSION] Factura #{numero_factura} no existe en SIAT")
            return False, f"❌ **{descripcion_principal}**\n\n" \
                         f"La factura no existe en la base de datos del SIN. " \
                         f"Verifique el numero de factura."
        
        elif codigo_estado == ESTADO_SISTEMA_NO_AUTORIZADO:  # 3011
            logger.error("[REVERSION] Sistema no autorizado")
            return False, f"❌ **{descripcion_principal}**\n\n" \
                         f"El sistema no esta autorizado para utilizar el servicio de reversion. " \
                         f"Contacte al administrador."
        
        elif codigo_estado == ESTADO_FUERA_DE_PLAZO:  # 3012
            logger.warning(f"[REVERSION] Fuera de plazo para factura #{numero_factura}")
            return False, f"⏰ **{descripcion_principal}**\n\n" \
                         f"La reversion esta fuera del plazo permitido " \
                         f"(hasta el dia 9 del mes siguiente a la emision)."
        
        else:
            logger.error(f"[REVERSION] Codigo desconocido: {codigo_estado}")
            
            mensaje_desconocido = f"❓ **Codigo de respuesta no reconocido: {codigo_estado}**\n\n" \
                                 f"Descripcion: {descripcion_principal}\n\n"
            
            if mensajes_detalle:
                mensaje_desconocido += "**Mensajes adicionales:**\n"
                for msg in mensajes_detalle:
                    mensaje_desconocido += f"• [{msg['codigo']}] {msg['descripcion']}\n"
            
            return False, mensaje_desconocido
    
    except ET.ParseError as e:
        logger.error(f"[REVERSION] Error al parsear XML: {e}", exc_info=True)
        return False, f"❌ **Error al procesar la respuesta del servicio**\n\n{str(e)}"
    
    except Exception as e:
        logger.error(f"[REVERSION] Error inesperado: {e}", exc_info=True)
        return False, f"❌ **Error inesperado al procesar la respuesta**\n\n{str(e)}"

def revertir_anulacion_factura(numero_factura):
    """
    Función principal para revertir la anulación de una factura.
    
    VERSIÓN MEJORADA (v2.1.0):
    - Logging estandarizado con prefijos consistentes [REVERSION]
    - Mejor manejo de errores con mensajes descriptivos
    - Validación exhaustiva de parámetros
    
    Args:
        numero_factura (str): Número de la factura a revertir
        
    Returns:
        tuple: (éxito, mensaje)
    """
    logger.info(f"[REVERSION] Iniciando proceso para factura #{numero_factura}")
    
    try:
        # Obtener CUF y datos de la factura
        cuf, factura = obtener_cuf_por_numero_factura(numero_factura)
        
        if factura is None:
            logger.warning(f"[REVERSION] Factura #{numero_factura} no encontrada en BD")
            return False, "No se encontró la factura especificada."
        
        logger.info(f"[REVERSION] Factura encontrada. CUF: {cuf}")
        
        # Verificar que exista un CUFD vigente
        cufd_vigente = obtener_cufd_vigente()
        if not cufd_vigente:
            error_msg = "No hay un CUFD vigente. Solicite un nuevo CUFD antes de continuar."
            logger.error(f"[REVERSION] {error_msg}")
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
            logger.error(f"[REVERSION] {error_msg}")
            return False, error_msg
            
        # Enviar solicitud de reversión
        exito, respuesta = enviar_solicitud_reversion(cuf)
        
        if exito:
            if logger.level <= 10:
                logger.debug("[REVERSION] Solicitud enviada exitosamente, procesando respuesta")
            return procesar_respuesta_reversion(respuesta, factura)
        else:
            logger.error(f"[REVERSION] Error al enviar solicitud: {respuesta}")
            return False, respuesta
    
    except Exception as e:
        logger.error(f"[REVERSION] Error inesperado: {e}", exc_info=True)
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