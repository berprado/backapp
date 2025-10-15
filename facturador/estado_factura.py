"""
Módulo de Verificación de Estado de Facturas
============================================

PROPÓSITO:
----------
Proporciona funcionalidad para verificar el estado de facturas emitidas
consultando el servicio SIAT (Servicio de Impuestos Nacionales).

FUNCIONALIDADES:
----------------
- Verificación de estado de factura por número
- Actualización de estado en base de datos local
- Procesamiento de respuestas SOAP del SIAT
- Sistema de caché híbrido inteligente (30s con opción force_check)

REFACTORIZACIÓN:
----------------
VERSION: 2.1.0 (15 octubre 2025)
CAMBIOS: 
  - v2.0.0: Migrado a usar siat_service_client.py para eliminar duplicación
  - v2.1.0: Implementado sistema de caché híbrido con force_check para 
            operaciones críticas (anulación/reversión)

CACHÉ INTELIGENTE:
------------------
- Caché de 30 segundos para consultas informativas (mejora rendimiento)
- Parámetro force_check=True para operaciones críticas (ignora caché)
- Logs diferenciados para consultas cacheadas vs forzadas

AUTOR: Sistema de Facturación Electrónica
"""

import os
import sys
import requests
import streamlit as st
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from database import SessionLocal
from data_access import obtener_cuf_por_numero_factura
from datetime import datetime

# Importar loggers
from logger_config import get_logger, get_facturacion_logger
import traceback

# ✅ NUEVA IMPORTACIÓN: Cliente centralizado SIAT
from siat_service_client import get_siat_client

# Obtener loggers para este módulo
logger = get_logger()
facturacion_logger = get_facturacion_logger()

load_dotenv()

# ========================================================================
# FUNCIONES DEPRECADAS (Mantenidas por compatibilidad retroactiva)
# ========================================================================
# Estas funciones ahora son wrappers que delegan al cliente centralizado.
# Se mantienen para no romper código existente que las importe directamente.
# 
# NOTA: Considerar remover en versión 3.0.0 después de migrar todo el código.

def construir_solicitud_verificacion(cuf):
    """
    DEPRECADO: Usa get_siat_client().construir_solicitud_verificacion() directamente.
    
    Mantenido por compatibilidad con código legacy que importa esta función.
    
    Args:
        cuf (str): Código Único de Facturación
        
    Returns:
        bytes: XML de la solicitud
        
    Ejemplo de migración:
        # ANTES
        from estado_factura import construir_solicitud_verificacion
        xml = construir_solicitud_verificacion(cuf)
        
        # DESPUÉS (recomendado)
        from siat_service_client import get_siat_client
        client = get_siat_client()
        xml = client.construir_solicitud_verificacion(cuf)
    """
    logger.warning("[DEPRECADO] Usando construir_solicitud_verificacion(). Migrar a siat_service_client.")
    client = get_siat_client()
    return client.construir_solicitud_verificacion(cuf)


def enviar_solicitud_verificacion(cuf):
    """
    DEPRECADO: Usa get_siat_client().enviar_solicitud() directamente.
    
    Mantenido por compatibilidad con código legacy que importa esta función.
    
    Args:
        cuf (str): Código Único de Facturación
        
    Returns:
        Tuple[bool, Union[bytes, str]]: (éxito, respuesta_xml o mensaje_error)
        
    Ejemplo de migración:
        # ANTES
        from estado_factura import enviar_solicitud_verificacion
        exito, respuesta = enviar_solicitud_verificacion(cuf)
        
        # DESPUÉS (recomendado)
        from siat_service_client import get_siat_client
        client = get_siat_client()
        xml = client.construir_solicitud_verificacion(cuf)
        exito, respuesta = client.enviar_solicitud(xml, "verificación")
    """
    logger.warning("[DEPRECADO] Usando enviar_solicitud_verificacion(). Migrar a siat_service_client.")
    client = get_siat_client()
    solicitud_xml = client.construir_solicitud_verificacion(cuf)
    exito, respuesta = client.enviar_solicitud(solicitud_xml, operacion="verificación de estado")
    
    # Mantener la misma estructura de retorno que antes para compatibilidad
    if exito:
        return True, respuesta
    else:
        # Si es bytes, decodificar; si ya es string, dejar como está
        error_msg = respuesta.decode('utf-8') if isinstance(respuesta, bytes) else respuesta
        return False, error_msg

# ========================================================================
# FIN DE FUNCIONES DEPRECADAS
# ========================================================================


# ========================================================================
# SISTEMA DE CACHÉ INTELIGENTE (v2.1.0)
# ========================================================================
# Implementa un caché híbrido que balancea rendimiento y precisión:
# - Caché de 30 segundos para consultas informativas (reduce carga SIAT)
# - Opción force_check para operaciones críticas (anulación/reversión)
# - Logs claros que distinguen entre consultas cacheadas y forzadas

@st.cache_data(ttl=30)  # Caché reducido a 30 segundos (balance óptimo)
def _verificar_estado_factura_cached(numero_factura):
    """
    Función interna cacheada que realiza la verificación real al SIAT.
    
    NO USAR DIRECTAMENTE. Usar verificar_estado_factura() en su lugar.
    
    Args:
        numero_factura (int): Número de la factura a verificar
        
    Returns:
        Tuple[bool, str]: (éxito, mensaje_resultado)
        
    Notas:
        - Caché de 30 segundos (balance entre rendimiento y actualidad)
        - Esta función es llamada por verificar_estado_factura()
        - El decorador @st.cache_data maneja automáticamente la invalidación
    """
    cuf, factura = obtener_cuf_por_numero_factura(numero_factura)

    # Si no se encontró la factura, retornamos un mensaje de error claro
    if factura is None:
        logger.warning(f"[VERIFICACIÓN] No se encontró la factura #{numero_factura}")
        return False, "❌ No se encontró la factura especificada."

    # ✅ USAR CLIENTE CENTRALIZADO
    logger.info(f"[VERIFICACIÓN] Ejecutando consulta REAL al SIAT para factura #{numero_factura} (CUF: {cuf[:20]}...)")
    
    client = get_siat_client()
    solicitud_xml = client.construir_solicitud_verificacion(cuf)
    exito, respuesta = client.enviar_solicitud(solicitud_xml, operacion="verificación de estado")
    
    if exito:
        return procesar_respuesta_verificacion(respuesta, factura)
    else:
        # Decodificar mensaje de error si viene en bytes
        error_msg = respuesta.decode('utf-8') if isinstance(respuesta, bytes) else respuesta
        logger.error(f"[VERIFICACIÓN] Error al enviar solicitud: {error_msg}")
        return False, error_msg


def verificar_estado_factura(numero_factura, force_check=False):
    """
    Verifica el estado de una factura consultando el servicio SIAT (VERSIÓN HÍBRIDA INTELIGENTE).
    
    VERSIÓN REFACTORIZADA (v2.1.0): Sistema de caché inteligente que balancea
    rendimiento y precisión según el contexto de uso.
    
    Args:
        numero_factura (int): Número de la factura a verificar
        force_check (bool): Si True, ignora el caché y consulta SIAT en tiempo real.
                           Usar True en operaciones críticas (anulación/reversión).
                           Default: False (usa caché si existe)
        
    Returns:
        Tuple[bool, str]: (éxito, mensaje_resultado)
        
    Códigos de estado SIAT:
        - 690: Factura válida
        - 691: Factura anulada
        - 902: Factura no encontrada en SIAT
    
    Comportamiento del caché:
        - Con force_check=False (default):
          * Primera llamada: Consulta SIAT (~2-3s)
          * Llamadas subsecuentes (30s): Respuesta desde caché (~10ms)
          * Ideal para: Consultas informativas, visualización de estado
          
        - Con force_check=True:
          * Siempre consulta SIAT (~2-3s)
          * Limpia el caché antes de consultar
          * Ideal para: Anulaciones, reversiones, decisiones críticas
    
    Ejemplos de uso:
        # Consulta informativa (usa caché)
        exito, msg = verificar_estado_factura(123)
        
        # Antes de anular/revertir (fuerza consulta real)
        exito, msg = verificar_estado_factura(123, force_check=True)
        
    Notas de seguridad:
        - El caché de 30s reduce la carga en SIAT sin comprometer precisión crítica
        - SIEMPRE usar force_check=True en operaciones de anulación/reversión
        - Los logs indican claramente si se usó caché o consulta forzada
    """
    if force_check:
        logger.info(f"[VERIFICACIÓN FORZADA] 🔴 Ignorando caché para factura #{numero_factura} - Consulta crítica al SIAT")
        _verificar_estado_factura_cached.clear()
        return _verificar_estado_factura_cached(numero_factura)
    else:
        logger.debug(f"[VERIFICACIÓN] Consultando factura #{numero_factura} (caché permitido, TTL=30s)")
        return _verificar_estado_factura_cached(numero_factura)


def actualizar_estado_factura(factura, estado_validacion, codigo_recepcion=None, mensaje_error=None):
    """
    Actualiza el estado de una factura en la base de datos local.
    
    Esta función NO ha sido modificada en la refactorización v2.0.0
    para mantener compatibilidad total con el código existente.
    
    Args:
        factura: Objeto FacturaCabecera de SQLAlchemy
        estado_validacion: "VALIDA", "ANULADA", o "RECHAZADA"
        codigo_recepcion: Código de recepción del SIAT (opcional)
        mensaje_error: Mensaje de error si la validación falló (opcional)
        
    Returns:
        Tuple[bool, str]: (éxito, mensaje_resultado)
    """
    session = SessionLocal()
    try:
        # Registrar mejor la información usando el logger
        facturacion_logger.info(f"[BD] Actualizando estado de factura #{factura.numeroFactura} a '{estado_validacion}'")

        # Update the factura's validation state
        factura.estadoValidacion = estado_validacion
        factura.codigoRecepcion = codigo_recepcion
        factura.mensajeError = mensaje_error

        # If the factura is valid, update the validation date and result
        if estado_validacion == "VALIDA":
            factura.fechaValidacion = datetime.now()
            factura.resultadoValidacion = "VALIDADA"
        
        # If the factura is annulled, update the result as annulled
        elif estado_validacion == "ANULADA":
            factura.fechaAnulacion = datetime.now()
            factura.resultadoValidacion = "ANULADA"
        
        # If the factura is rejected, keep the rejection result
        elif estado_validacion == "RECHAZADA":
            factura.resultadoValidacion = "RECHAZADA"

        # Add and commit changes to the database
        session.add(factura)
        session.commit()
        
        facturacion_logger.info(f"[BD] ✅ Factura #{factura.numeroFactura} actualizada correctamente a estado '{estado_validacion}'")
        
        # Return success and the updated state
        return True, f"Factura: {estado_validacion}"
    except Exception as e:
        session.rollback()
        facturacion_logger.error(f"[BD] ❌ Error al actualizar la factura: {str(e)}")
        facturacion_logger.error(traceback.format_exc())
        return False, f"❌ Error al actualizar la factura: {str(e)}"
    finally:
        session.close()


def procesar_respuesta_verificacion(respuesta_xml, factura):
    """
    Procesa la respuesta XML del servicio SIAT de verificación.
    
    Esta función NO ha sido modificada en la refactorización v2.0.0
    para mantener compatibilidad total con el código existente.
    
    Args:
        respuesta_xml (bytes): Respuesta SOAP del SIAT
        factura: Objeto FacturaCabecera de SQLAlchemy
        
    Returns:
        Tuple[bool, str]: (éxito, mensaje_resultado)
        
    Códigos de estado procesados:
        - 690: Factura válida → actualizar como VALIDA
        - 691: Factura anulada → actualizar como ANULADA
        - 902: Factura no encontrada → actualizar como RECHAZADA
        - Otros: Error desconocido → actualizar como RECHAZADA
    """
    logger.debug(f"[VERIFICACIÓN] Procesando respuesta para factura #{factura.numeroFactura}")
    
    try:
        # Procesar el XML de respuesta para extraer la información relevante
        tree = ET.fromstring(respuesta_xml)
        codigo_estado_elem = tree.find('.//codigoEstado')
        
        if codigo_estado_elem is None:
            logger.error("[VERIFICACIÓN] Respuesta XML no contiene elemento codigoEstado")
            return False, "❌ Respuesta del servicio incorrecta o incompleta."
        
        codigo_estado = codigo_estado_elem.text

        if factura is None:
            return False, "❌ No se encontró la factura especificada."

        logger.debug(f"[VERIFICACIÓN] Código de estado recibido: {codigo_estado}")

        if codigo_estado == "690":  # Factura válida
            logger.info(f"[VERIFICACIÓN] ✅ Factura #{factura.numeroFactura} es VÁLIDA")
            factura.estadoValidacion = "VALIDADA"
            factura.resultadoValidacion = "VALIDA"
            factura.fechaValidacion = datetime.now()
            
            codigo_recepcion_elem = tree.find('.//codigoRecepcion')
            if codigo_recepcion_elem is not None:
                factura.codigoRecepcion = codigo_recepcion_elem.text
                logger.debug(f"[VERIFICACIÓN] Código recepción: {factura.codigoRecepcion}")

            # Actualizar el estado de la factura con los datos correspondientes
            return actualizar_estado_factura(factura, "VALIDA", factura.codigoRecepcion)

        elif codigo_estado == "691":  # Factura anulada
            logger.warning(f"[VERIFICACIÓN] ⚠️ Factura #{factura.numeroFactura} está ANULADA")
            factura.estadoValidacion = "ANULADA"
            factura.resultadoValidacion = "ANULADA"
            factura.mensajeError = "La factura ha sido anulada."
            
            # Actualizar el estado de la factura con estado anulada
            return actualizar_estado_factura(factura, "ANULADA", None, factura.mensajeError)

        elif codigo_estado == "902":  # Factura no encontrada
            logger.warning(f"[VERIFICACIÓN] ⚠️ Factura #{factura.numeroFactura} NO ENCONTRADA en SIAT")
            mensaje_error_elem = tree.find('.//mensajesList/descripcion')
            mensaje_error = mensaje_error_elem.text if mensaje_error_elem is not None else "Factura no encontrada en el sistema SIAT"
            
            factura.estadoValidacion = "RECHAZADA"
            factura.mensajeError = mensaje_error
            
            # Actualizar el estado de la factura con estado rechazada
            return actualizar_estado_factura(factura, "RECHAZADA", None, factura.mensajeError)

        else:
            # Manejo de otros códigos de error
            logger.warning(f"[VERIFICACIÓN] ⚠️ Código de estado no reconocido: {codigo_estado}")
            mensaje_error_elem = tree.find('.//mensajesList/descripcion')
            if mensaje_error_elem is not None:
                mensaje_error = mensaje_error_elem.text
            else:
                mensaje_error = f"Error desconocido en la verificación. Código: {codigo_estado}"
            
            factura.estadoValidacion = "RECHAZADA"
            factura.mensajeError = mensaje_error

            # Actualizar el estado de la factura con un error genérico
            return actualizar_estado_factura(factura, "RECHAZADA", None, mensaje_error)
    
    except ET.ParseError as e:
        logger.error(f"[VERIFICACIÓN] ❌ Error al parsear XML de respuesta: {e}", exc_info=True)
        return False, f"❌ Error al procesar la respuesta del servicio: {e}"
    
    except Exception as e:
        logger.error(f"[VERIFICACIÓN] ❌ Error al procesar respuesta: {e}", exc_info=True)
        return False, f"❌ Error inesperado al procesar la respuesta: {e}"


