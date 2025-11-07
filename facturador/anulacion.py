"""
Módulo de Anulación de Facturas
================================

PROPÓSITO:
----------
Gestiona el proceso de anulación de facturas electrónicas válidas a través
del servicio SIAT (Servicio de Impuestos Nacionales).

FUNCIONALIDADES:
----------------
- Construcción de solicitudes SOAP para anulación
- Envío de solicitudes al servicio SIAT
- Procesamiento de respuestas con manejo de múltiples códigos de estado
- Actualización de estado en base de datos local
- Limpieza de emojis duplicados en descripciones del SIAT

NORMATIVA:
----------
Plazo de anulación: Hasta el día 9 del mes siguiente a la emisión

CÓDIGOS DE ESTADO SOPORTADOS:
------------------------------
- 905: Anulación confirmada
- 906: Anulación rechazada
- 924: Factura no existe en BD del SIN
- 936: Factura ya anulada
- 970: Fuera de plazo para anulación
- 3011: Sistema no autorizado
- 3012: Solicitud fuera de plazo

VERSIÓN: 2.1.0 (Timeout Handler - 16 octubre 2025)
CAMBIOS v2.1.0:
  - ✅ Implementado protocolo oficial SIAT para manejo de timeouts
  - ✅ Verifica estado real en SIAT si hay timeout persistente
  - ✅ Sincronización automática de BD local con estado SIAT
  - ✅ Previene pérdida de operaciones exitosas por timeout
  - ✅ Cumple normativa oficial del SIN sobre timeouts

CAMBIOS v2.0.0:
  - Migrado a siat_service_client.py (eliminación de código duplicado)
  - Implementado sistema de limpieza de emojis
  - Mensajes detallados con formato Markdown
  - Logging estructurado sin emojis en consola
  - Uso de BD local como fuente primaria de mensajes
  - Prevención de DetachedInstanceError

AUTOR: Sistema de Facturación Electrónica
"""

import sys
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime
from dotenv import load_dotenv

# Importaciones de módulos locales
from logger_config import get_logger
from siat_service_client import get_siat_client
from database import SessionLocal
from models import SincronizarParametricaMotivoAnulacion, FacturaCabecera
from data_access import obtener_mensaje_por_codigo, obtener_cuf_por_numero_factura

# ========================================================================
# TIMEOUT HANDLER - Protocolo Oficial SIAT
# ========================================================================
from timeout_handler import ejecutar_anulacion_con_protocolo
from estado_factura import verificar_estado_factura

# Cargar variables de entorno
load_dotenv()

# Configurar logger centralizado (sin emojis para compatibilidad con Windows console)
logger = get_logger()

# ========================================================================
# CONSTANTES: Códigos de Estado del SIAT
# ========================================================================

ESTADO_ANULACION_CONFIRMADA = "905"       # Anulación exitosa
ESTADO_ANULACION_RECHAZADA = "906"        # Anulación rechazada por el SIAT
ESTADO_FACTURA_NO_EXISTE = "924"          # Factura no existe en BD del SIN
ESTADO_FACTURA_YA_ANULADA = "936"         # Factura ya anulada anteriormente
ESTADO_FUERA_DE_PLAZO = "970"             # Solicitud fuera de plazo
ESTADO_SISTEMA_NO_AUTORIZADO = "3011"     # Sistema no autorizado
ESTADO_SOLICITUD_FUERA_PLAZO = "3012"     # Solicitud fuera de plazo (código alternativo)

ESTADO_SISTEMA_NO_AUTORIZADO = "3011"     # Sistema no autorizado
ESTADO_SOLICITUD_FUERA_PLAZO = "3012"     # Solicitud fuera de plazo (código alternativo)


# ========================================================================
# FUNCIONES AUXILIARES
# ========================================================================

def limpiar_emojis_descripcion(descripcion):
    """
    Limpia emojis comunes del inicio de una descripción para evitar duplicación.
    
    Algunos mensajes del SIAT vienen con emojis (ej: "✅ ANULACION CONFIRMADA").
    Esta función los elimina para que podamos añadir nuestro propio formato consistente.
    
    Args:
        descripcion (str): Descripción que puede contener emojis al inicio
        
    Returns:
        str: Descripción sin emojis al inicio
        
    Ejemplo:
        "✅ ANULACION CONFIRMADA" → "ANULACION CONFIRMADA"
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


def obtener_cufd_vigente():
    """
    DEPRECADO: Esta función será removida en v3.0.0
    
    Usar data_access.obtener_cufd_vigente() en su lugar para mantener
    consistencia en el acceso a datos.
    
    Returns:
        str: Código CUFD vigente o None si no existe
    """
    from models import Cufd
    
    logger.warning("[DEPRECADO] Usando obtener_cufd_vigente() local. Migrar a data_access.")
    
    session = SessionLocal()
    try:
        cufd_vigente = session.query(Cufd).filter_by(vigente=1).first()
        if cufd_vigente:
            return cufd_vigente.codigo
        else:
            logger.error("No se encontro CUFD vigente en la base de datos.")
            return None
    except Exception as e:
        logger.error(f"Error al obtener CUFD vigente: {e}")
        return None
    finally:
        session.close()


def obtener_codigo_motivo(descripcion_motivo):
    """
    Obtiene el código clasificador del motivo de anulación desde la BD.
    
    Args:
        descripcion_motivo (str): Descripción del motivo (ej: "Emitido con error")
        
    Returns:
        str: Código clasificador o None si no se encuentra
    """
    logger.info(f"Buscando codigo de motivo para: {descripcion_motivo}")
    
    session = SessionLocal()
    try:
        motivo = session.query(SincronizarParametricaMotivoAnulacion).filter_by(
            descripcion=descripcion_motivo
        ).first()
        
        if motivo:
            logger.info(f"Codigo de motivo encontrado: {motivo.codigoClasificador}")
            return motivo.codigoClasificador
        else:
            logger.error(f"No se encontro codigo para el motivo: {descripcion_motivo}")
            return None
    except Exception as e:
        logger.error(f"Error al obtener codigo de motivo: {e}")
        return None
    finally:
        session.close()


# ========================================================================
# FUNCIONES PRINCIPALES
# ========================================================================

def enviar_solicitud_anulacion(cuf, codigo_motivo):
    """
    Envía la solicitud de anulación al servicio SIAT usando el cliente centralizado.
    
    VERSIÓN REFACTORIZADA (v2.0.0):
    - Usa siat_service_client.py en lugar de código duplicado
    - Manejo de errores robusto y consistente
    - Logging estructurado sin emojis en consola
    - Validación de parámetros antes de enviar
    
    Args:
        cuf (str): Código Único de Facturación
        codigo_motivo (int): Código del motivo de anulación
        
    Returns:
        tuple: (éxito, respuesta_xml/mensaje_error)
    """
    logger.info(f"Iniciando envio de solicitud de anulacion para CUF: {cuf[:20]}...")
    
    # Validación de parámetros críticos
    if not cuf or len(cuf) == 0:
        logger.error("[VALIDACION] CUF vacio o None")
        return False, "CUF no válido: está vacío"
    
    if not codigo_motivo or int(codigo_motivo) <= 0:
        logger.error(f"[VALIDACION] Codigo de motivo invalido: {codigo_motivo}")
        return False, f"Código de motivo no válido: {codigo_motivo}"
    
    logger.info(f"[VALIDACION] CUF: {cuf[:20]}... (longitud: {len(cuf)})")
    logger.info(f"[VALIDACION] Codigo motivo: {codigo_motivo}")
    
    try:
        # Obtener cliente SIAT centralizado
        client = get_siat_client()
        
        # Construir solicitud usando cliente centralizado
        solicitud_xml = client.construir_solicitud_anulacion(cuf, int(codigo_motivo))
        
        # Enviar solicitud
        exito, respuesta = client.enviar_solicitud(solicitud_xml, operacion="anulación")
        
        if exito:
            logger.info("[EXITO] Solicitud de anulacion enviada correctamente.")
            return True, respuesta
        else:
            logger.error(f"[ERROR] Fallo al enviar solicitud: {respuesta}")
            return False, respuesta
            
    except Exception as e:
        logger.error(f"[ERROR] Excepcion al enviar solicitud de anulacion: {e}")
        logger.error(traceback.format_exc())
        return False, f"Error inesperado al enviar solicitud: {str(e)}"



def procesar_respuesta_anulacion(respuesta_xml, factura, descripcion_motivo):
    """
    Procesa la respuesta XML del servicio SIAT y actualiza la factura según corresponda.
    
    VERSIÓN MEJORADA (v2.0.0):
    - Extrae TODOS los campos de la respuesta (codigoEstado, codigoDescripcion, mensajesList)
    - Usa BD local como fuente primaria, SIAT como fallback
    - Construye mensajes detallados para el usuario con formato Markdown
    - Logging exhaustivo para debugging
    - Limpieza de emojis duplicados
    
    Args:
        respuesta_xml (bytes): Respuesta XML del servicio SIAT
        factura (FacturaCabecera): Objeto de factura a anular
        descripcion_motivo (str): Descripción del motivo de anulación
        
    Returns:
        tuple: (éxito, mensaje_detallado)
    """
    logger.info(f"[PROCESAMIENTO] Iniciando analisis de respuesta para factura #{factura.numeroFactura}")
    
    try:
        # Parsear el XML de respuesta
        tree = ET.fromstring(respuesta_xml)
        codigo_estado = tree.find('.//codigoEstado')
        codigo_descripcion = tree.find('.//codigoDescripcion')
        
        # Extraer valores con validación
        codigo_estado_valor = codigo_estado.text if codigo_estado is not None else None
        codigo_descripcion_siat = codigo_descripcion.text if codigo_descripcion is not None else "Sin descripción"
        
        logger.info(f"[PROCESAMIENTO] Codigo de estado: {codigo_estado_valor}")
        logger.info(f"[PROCESAMIENTO] Descripcion SIAT: {codigo_descripcion_siat}")
        
        # Buscar mensajes adicionales (advertencias/errores)
        mensajes_lista = tree.findall('.//mensajesList')
        mensajes_adicionales = []
        
        if mensajes_lista:
            for mensaje in mensajes_lista:
                desc = mensaje.find('descripcion')
                if desc is not None and desc.text:
                    mensajes_adicionales.append(desc.text)
                    logger.info(f"[PROCESAMIENTO] Mensaje adicional SIAT: {desc.text}")
        
        # ====================================================================
        # ESTRATEGIA DE DESCRIPCIÓN: BD primero, SIAT como fallback
        # ====================================================================
        
        # Intentar obtener mensaje desde BD local (más confiable y consistente)
        descripcion_bd = obtener_mensaje_por_codigo(int(codigo_estado_valor)) if codigo_estado_valor else None
        
        # Aplicar limpieza de emojis a ambas fuentes
        descripcion_principal = limpiar_emojis_descripcion(
            descripcion_bd if descripcion_bd else limpiar_emojis_descripcion(codigo_descripcion_siat)
        )
        
        logger.info(f"[PROCESAMIENTO] Descripcion final (limpia): {descripcion_principal}")
        
        # ====================================================================
        # GUARDAR numero_factura ANTES de cualquier operación de sesión
        # (Prevención de DetachedInstanceError)
        # ====================================================================
        numero_factura = factura.numeroFactura
        
        # ====================================================================
        # MANEJO DE ESTADOS ESPECÍFICOS
        # ====================================================================
        
        if codigo_estado_valor == ESTADO_ANULACION_CONFIRMADA:  # 905 - Anulación confirmada
            logger.info(f"[EXITO] Anulacion confirmada para factura #{numero_factura}")
            
            # Actualizar estado en BD
            factura.estado = "Anulada"
            factura.fechaAnulacion = datetime.now()
            factura.motivoAnulacion = descripcion_motivo
            
            session = SessionLocal()
            try:
                session.add(factura)
                session.commit()
                logger.info(f"[BD] Factura #{numero_factura} actualizada exitosamente.")
            except Exception as e:
                session.rollback()
                logger.error(f"[BD ERROR] Error al actualizar factura: {e}")
                return False, f"❌ Error al actualizar la factura en BD: {e}"
            finally:
                session.close()
            
            # Construir mensaje de éxito con formato Markdown
            mensaje_exito = f" **{descripcion_principal}**\n\n"
            mensaje_exito += f"📄 **Factura #{numero_factura}** anulada correctamente.\n"
            mensaje_exito += f"📅 **Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            mensaje_exito += f"📝 **Motivo:** {descripcion_motivo}"
            
            if mensajes_adicionales:
                mensaje_exito += f"\n\nℹ️ **Mensajes adicionales:**\n"
                for msg in mensajes_adicionales:
                    mensaje_exito += f"- {msg}\n"
            
            return True, mensaje_exito
        
        elif codigo_estado_valor == ESTADO_ANULACION_RECHAZADA:  # 906 - Rechazada
            logger.warning(f"[RECHAZADO] Anulacion rechazada para factura #{numero_factura}")
            
            mensaje_rechazo = f"❌ **{descripcion_principal}**\n\n"
            mensaje_rechazo += f"📄 **Factura #{numero_factura}**: La anulación fue rechazada por el SIAT.\n"
            
            # Agregar detalles de mensajes adicionales si existen
            if mensajes_adicionales:
                mensaje_rechazo += f"\n**Razones del rechazo:**\n"
                for msg in mensajes_adicionales:
                    # Casos especiales comunes
                    if "YA SE ENCUENTRA ANULADA" in msg.upper():
                        mensaje_rechazo += f"⚠️ La factura ya fue anulada previamente.\n"
                    elif "NO EXISTE EN LA BASE DE DATOS" in msg.upper():
                        mensaje_rechazo += f"⚠️ La factura no existe en la base de datos del SIN.\n"
                    else:
                        mensaje_rechazo += f"- {msg}\n"
            
            return False, mensaje_rechazo
        
        elif codigo_estado_valor == ESTADO_FACTURA_NO_EXISTE:  # 924
            logger.warning(f"[RECHAZO] Factura #{numero_factura} no existe en BD del SIN")
            
            mensaje = f"⚠️ **{descripcion_principal}**\n\n"
            mensaje += f"📄 **Factura #{numero_factura}** no se encuentra registrada en el SIN.\n"
            mensaje += f"Por favor, verifica el número de factura."
            
            return False, mensaje
        
        elif codigo_estado_valor == ESTADO_FACTURA_YA_ANULADA:  # 936
            logger.warning(f"[RECHAZO] Factura #{numero_factura} ya estaba anulada")
            
            mensaje = f"⚠️ **{descripcion_principal}**\n\n"
            mensaje += f"📄 **Factura #{numero_factura}** ya fue anulada anteriormente.\n"
            mensaje += f"No es posible anular una factura múltiples veces."
            
            return False, mensaje
        
        elif codigo_estado_valor == ESTADO_FUERA_DE_PLAZO:  # 970
            logger.warning(f"[RECHAZO] Factura #{numero_factura} fuera de plazo")
            
            mensaje = f"⏰ **{descripcion_principal}**\n\n"
            mensaje += f"📄 **Factura #{numero_factura}** está fuera del plazo permitido.\n"
            mensaje += f"**Normativa:** Solo se pueden anular facturas hasta el día 9 del mes siguiente a su emisión."
            
            return False, mensaje
        
        elif codigo_estado_valor == ESTADO_SISTEMA_NO_AUTORIZADO:  # 3011
            logger.error(f"[ERROR CRITICO] Sistema no autorizado")
            
            mensaje = f"🔴 **{descripcion_principal}**\n\n"
            mensaje += f"El sistema no está autorizado para realizar esta operación.\n"
            mensaje += f"Contacte al administrador del sistema."
            
            return False, mensaje
        
        elif codigo_estado_valor == ESTADO_SOLICITUD_FUERA_PLAZO:  # 3012
            logger.warning(f"[RECHAZO] Solicitud fuera de plazo")
            
            mensaje = f"⏰ **{descripcion_principal}**\n\n"
            mensaje += f"La solicitud fue rechazada por estar fuera del plazo permitido."
            
            return False, mensaje
        
        else:  # Código desconocido
            logger.error(f"[ERROR] Codigo de estado desconocido: {codigo_estado_valor}")
            
            mensaje = f"❓ **Estado desconocido:** {descripcion_principal}\n\n"
            mensaje += f"Código: {codigo_estado_valor}\n"
            mensaje += f"Descripción SIAT: {codigo_descripcion_siat}"
            
            if mensajes_adicionales:
                mensaje += f"\n\n**Mensajes adicionales:**\n"
                for msg in mensajes_adicionales:
                    mensaje += f"- {msg}\n"
            
            return False, mensaje
    
    except ET.ParseError as e:
        logger.error(f"[ERROR XML] Error al parsear respuesta XML: {e}")
        return False, f"❌ Error al procesar la respuesta del SIAT (XML malformado): {str(e)}"
    
    except Exception as e:
        logger.error(f"[ERROR] Excepcion inesperada al procesar respuesta: {e}")
        logger.error(traceback.format_exc())
        return False, f"❌ Error inesperado al procesar la respuesta: {str(e)}"



def anular_factura(numero_factura, descripcion_motivo):
    """
    Función principal para anular una factura electrónica.
    
    VERSIÓN MEJORADA (v2.1.0) - CON PROTOCOLO OFICIAL DE TIMEOUTS:
    - ✅ Implementa protocolo oficial SIAT para manejo de timeouts
    - ✅ Verifica estado real en SIAT si hay timeout persistente
    - ✅ Sincroniza automáticamente BD local con estado SIAT
    - ✅ Previene pérdida de operaciones exitosas por timeout
    - ✅ Validaciones robustas antes de enviar al SIAT
    - ✅ Uso de cliente centralizado (siat_service_client)
    - ✅ Mensajes detallados con formato Markdown
    - ✅ Logging estructurado sin emojis en consola
    
    Referencia: Documentación SIAT - "Anulación de Facturas" (sección Timeouts)
    
    Args:
        numero_factura (str): Número de la factura a anular
        descripcion_motivo (str): Descripción del motivo de anulación
        
    Returns:
        tuple: (éxito, mensaje_detallado)
    """
    logger.info(f"Iniciando proceso de anulacion para factura #{numero_factura}")
    
    try:
        # ====================================================================
        # 1. OBTENER CUF Y FACTURA DESDE BD
        # ====================================================================
        cuf, factura = obtener_cuf_por_numero_factura(numero_factura)
        
        # Validar que se encontró la factura
        if factura is None:
            logger.error(f"[ERROR] No se encontro la factura #{numero_factura}")
            return False, f"❌ No se encontró la factura **#{numero_factura}** en la base de datos."
        
        # Verificar si factura es un mensaje de error (str)
        if isinstance(factura, str):
            logger.error(f"[ERROR] Error al obtener factura: {factura}")
            return False, f"❌ Error al recuperar la factura: {factura}"
        
        logger.info(f"[BD] Factura #{numero_factura} encontrada. Estado actual: {factura.estado}")
        
        # ====================================================================
        # 2. VALIDACIONES DE ESTADO
        # ====================================================================
        
        # Verificar si la factura ya fue revertida (no se puede anular de nuevo)
        if str(factura.estado) == "Valida" and factura.fechaValidacion is not None:
            logger.warning(f"[RECHAZO] Factura #{numero_factura} fue revertida, no se puede anular")
            mensaje = f"⚠️ **Operación no permitida**\n\n"
            mensaje += f"📄 **Factura #{numero_factura}** ya fue revertida y no puede ser anulada nuevamente.\n"
            mensaje += f"Una factura revertida recupera su estado válido y no puede ser anulada."
            return False, mensaje
        
        # Verificar si ya está anulada
        if str(factura.estado) == "Anulada":
            logger.warning(f"[RECHAZO] Factura #{numero_factura} ya esta anulada")
            mensaje = f"⚠️ **Factura ya anulada**\n\n"
            mensaje += f"📄 **Factura #{numero_factura}** ya se encuentra en estado **Anulada**.\n"
            mensaje += f"No es posible anular una factura múltiples veces."
            return False, mensaje
        
        # ====================================================================
        # 3. VALIDACIÓN DE PLAZO (Hasta día 9 del mes siguiente)
        # ====================================================================
        fecha_emision = factura.fechaEmision
        fecha_actual = datetime.now()
        
        # Calcular si está fuera de plazo
        mes_siguiente = fecha_emision.month + 1 if fecha_emision.month < 12 else 1
        anio_siguiente = fecha_emision.year if fecha_emision.month < 12 else fecha_emision.year + 1
        
        if fecha_actual.month > mes_siguiente or (fecha_actual.month == mes_siguiente and fecha_actual.day > 9):
            logger.warning(f"[RECHAZO] Factura #{numero_factura} fuera de plazo")
            mensaje = f"⏰ **Fuera de plazo**\n\n"
            mensaje += f"📄 **Factura #{numero_factura}** está fuera del plazo permitido.\n"
            mensaje += f"**Fecha de emisión:** {fecha_emision.strftime('%d/%m/%Y')}\n"
            mensaje += f"**Normativa:** Solo se pueden anular facturas hasta el día 9 del mes siguiente."
            return False, mensaje
        
        logger.info(f"[VALIDACION] Factura dentro del plazo de anulacion")
        
        # ====================================================================
        # 4. OBTENER CUFD Y CÓDIGO DE MOTIVO
        # ====================================================================
        cufd = obtener_cufd_vigente()
        if cufd is None:
            logger.error("[ERROR] No se pudo obtener CUFD vigente")
            return False, "❌ No se pudo obtener el **CUFD vigente**. Verifique la sincronización con el SIAT."
        
        logger.info(f"[CUFD] Obtenido exitosamente: {cufd[:20]}...")
        
        codigo_motivo = obtener_codigo_motivo(descripcion_motivo)
        if codigo_motivo is None:
            logger.error(f"[ERROR] No se encontro codigo para el motivo: {descripcion_motivo}")
            return False, f"❌ No se pudo obtener el **código del motivo** '{descripcion_motivo}'."
        
        logger.info(f"[MOTIVO] Codigo de motivo: {codigo_motivo} - {descripcion_motivo}")
        
        # ====================================================================
        # 5. ENVIAR SOLICITUD AL SIAT CON PROTOCOLO DE TIMEOUTS
        # ====================================================================
        logger.info(f"[SIAT] Aplicando protocolo oficial SIAT de timeouts...")
        
        # Función que sincroniza la BD local después de verificación exitosa
        def sincronizar_bd_local_anulacion(cuf_param: str, estado_esperado: str) -> bool:
            """Sincroniza el estado de la factura en BD local después de anulación."""
            try:
                # Recargar la factura desde la BD
                session = SessionLocal()
                factura_sync = session.query(FacturaCabecera).filter_by(cuf=cuf_param).first()
                
                if not factura_sync:
                    logger.error(f"[ANULACION] No se pudo recargar factura para sincronización")
                    return False
                
                # Actualizar estado
                factura_sync.estado = "Anulada"
                factura_sync.estadoValidacion = "ANULADA"
                factura_sync.resultadoValidacion = "ANULADA"
                factura_sync.fechaAnulacion = datetime.now()
                factura_sync.motivoAnulacion = descripcion_motivo
                
                session.commit()
                session.close()
                
                logger.info(f"[ANULACION] ✅ BD local sincronizada: estado='Anulada'")
                return True
                
            except Exception as e:
                logger.error(f"[ANULACION] Error al sincronizar BD: {e}")
                return False
        
        # Ejecutar anulación con protocolo de timeout
        resultado = ejecutar_anulacion_con_protocolo(
            cuf=cuf,
            funcion_anular=lambda: enviar_solicitud_anulacion(cuf, codigo_motivo)[1],
            funcion_verificar=lambda cuf_param, force: verificar_estado_factura(numero_factura, force_check=force),
            funcion_sync=sincronizar_bd_local_anulacion
        )
        
        # Procesar resultado del protocolo
        if resultado['exito']:
            # Si la operación fue exitosa (con o sin timeout)
            if resultado.get('response'):
                # Respuesta directa del SIAT
                return procesar_respuesta_anulacion(resultado['response'], factura, descripcion_motivo)
            else:
                # Operación verificada después de timeout
                mensaje_exito = (
                    f"✅ Anulación completada para factura #{numero_factura}\n\n"
                    f"{resultado['mensaje']}\n\n"
                    f"**Motivo:** {descripcion_motivo}\n"
                    f"**Estado sincronizado con SIAT**"
                )
                logger.info(f"[ANULACION] {mensaje_exito}")
                return True, mensaje_exito
        else:
            # Operación falló
            mensaje_error = resultado['mensaje']
            logger.error(f"[ANULACION] {mensaje_error}")
            return False, f"❌ **Error en la anulación:**\n\n{mensaje_error}"
    
    except Exception as e:
        logger.error(f"[ERROR] Excepcion inesperada al anular factura #{numero_factura}: {e}")
        logger.error(traceback.format_exc())
        return False, f"❌ **Error inesperado durante la anulación:**\n\n{str(e)}"


# ========================================================================
# PUNTO DE ENTRADA PARA TESTING/DEBUGGING
# ========================================================================

if __name__ == "__main__":
    """
    Permite ejecutar el módulo directamente para testing.
    
    Uso:
        python anulacion.py <numero_factura> <descripcion_motivo>
    
    Ejemplo:
        python anulacion.py 12345 "Emitido con error"
    """
    if len(sys.argv) > 2:
        numero = sys.argv[1]
        motivo = sys.argv[2]
        print(f"\n{'='*60}")
        print(f"Testing: Anulación de factura #{numero}")
        print(f"Motivo: {motivo}")
        print(f"{'='*60}\n")
        
        exito, mensaje = anular_factura(numero, motivo)
        
        print(f"\n{'='*60}")
        print(f"Resultado: {'ÉXITO' if exito else 'ERROR'}")
        print(f"{'='*60}")
        print(mensaje)
        print(f"{'='*60}\n")
    else:
        print("Uso: python anulacion.py <numero_factura> <descripcion_motivo>")
        print('Ejemplo: python anulacion.py 12345 "Emitido con error"')
