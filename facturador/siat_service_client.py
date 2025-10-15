"""
Cliente Unificado para Servicios SOAP del SIAT
==============================================

Este módulo centraliza toda la comunicación con los servicios web del SIAT
(Servicio de Impuestos Nacionales de Bolivia).

PROPÓSITO:
----------
Eliminar código duplicado presente en múltiples módulos (estado_factura.py, 
reversion.py, anulacion.py) que construían solicitudes SOAP y manejaban 
respuestas HTTP de manera similar pero inconsistente.

CARACTERÍSTICAS:
----------------
- Construcción estandarizada de envelopes SOAP
- Manejo robusto de errores HTTP (timeout, conexión, etc.)
- Logging estructurado con prefijos [SIAT Client]
- Patrón Singleton para evitar múltiples instancias
- Soporte para múltiples operaciones: verificación, reversión, anulación

SERVICIOS SOPORTADOS:
---------------------
1. Verificación de Estado de Factura
2. Reversión de Anulación
3. Anulación de Factura
(Extensible para futuros servicios)

AUTOR: Sistema de Facturación Electrónica
VERSIÓN: 1.0.0
FECHA: 14 de octubre de 2025
"""

import os
import requests
import xml.etree.ElementTree as ET
from typing import Tuple, Optional
from dotenv import load_dotenv
from logger_config import get_logger

# Cargar variables de entorno
load_dotenv()

# Logger para este módulo
logger = get_logger()


class SIATServiceClient:
    """
    Cliente centralizado para comunicación con servicios SOAP del SIAT.
    
    Este cliente proporciona métodos unificados para:
    - Construir solicitudes SOAP con estructura estándar
    - Enviar peticiones HTTP con manejo de errores robusto
    - Gestionar credenciales y configuración desde variables de entorno
    
    Ejemplo de uso:
        >>> from siat_service_client import get_siat_client
        >>> client = get_siat_client()
        >>> xml_bytes = client.construir_solicitud_verificacion("CUF123...")
        >>> exito, respuesta = client.enviar_solicitud(xml_bytes, "verificación")
    """
    
    # URL base del servicio SIAT (Ambiente Piloto)
    BASE_URL = "https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta"
    
    def __init__(self):
        """
        Inicializa el cliente con las credenciales y configuración del archivo .env
        
        Valida que los campos críticos estén presentes y registra advertencias
        si alguno falta.
        """
        self.config = {
            'codigoAmbiente': os.getenv('CODIGO_AMBIENTE'),
            'codigoSistema': os.getenv('CODIGO_SISTEMA'),
            'codigoSucursal': os.getenv('CODIGO_SUCURSAL'),
            'codigoPuntoVenta': os.getenv('CODIGO_PUNTO_VENTA', '0'),
            'nit': os.getenv('NIT'),
            'cuis': os.getenv('CUIS'),
            'cufd': os.getenv('CUFD'),
            'apikey': os.getenv('API_KEY'),
            'codigoDocumentoSector': os.getenv('CODIGO_DOCUMENTO_SECTOR'),
            'codigoEmision': os.getenv('CODIGO_TIPO_EMISION'),
            'codigoModalidad': os.getenv('CODIGO_MODALIDAD'),
            'tipoFacturaDocumento': os.getenv('CODIGO_TIPO_FACTURA')
        }
        
        # Validar configuración crítica
        campos_criticos = ['codigoAmbiente', 'codigoSistema', 'nit', 'cuis', 'apikey']
        for campo in campos_criticos:
            if not self.config.get(campo):
                logger.error(f"[SIAT Client] ❌ Falta configuración crítica: {campo}")
        
        logger.debug(f"[SIAT Client] Cliente inicializado con NIT: {self.config.get('nit', 'N/A')}")
    
    def _construir_envelope_base(self, metodo_soap: str) -> Tuple[ET.Element, ET.Element]:
        """
        Construye la estructura base del envelope SOAP según estándar del SIAT.
        
        Estructura generada:
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <{metodo_soap} xmlns="https://siat.impuestos.gob.bo/">
                    ...
                </{metodo_soap}>
            </soap:Body>
        </soap:Envelope>
        
        Args:
            metodo_soap: Nombre del método SOAP (ej: "verificacionEstadoFactura")
            
        Returns:
            Tuple[ET.Element, ET.Element]: (envelope_raiz, elemento_metodo)
        """
        envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
        body = ET.SubElement(envelope, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
        metodo = ET.SubElement(body, f"{{https://siat.impuestos.gob.bo/}}{metodo_soap}")
        return envelope, metodo
    
    def _agregar_parametros_comunes(self, solicitud: ET.Element, incluir_cufd: bool = True):
        """
        Agrega los parámetros comunes a todas las solicitudes SIAT.
        
        Parámetros estándar según normativa SIAT:
        - codigoAmbiente: 1=Producción, 2=Pruebas
        - codigoDocumentoSector: Código del sector económico
        - codigoEmision: 1=En línea, 2=Fuera de línea
        - codigoModalidad: 1=Electrónica, 2=Computarizada
        - codigoPuntoVenta: Identificador del punto de venta
        - codigoSistema: Código del sistema autorizado
        - codigoSucursal: 0=Casa matriz, 1..n=Sucursales
        - cufd: Código Único de Facturación Diaria (opcional en algunos servicios)
        - cuis: Código Único de Inicio de Sistema
        - nit: NIT del contribuyente
        - tipoFacturaDocumento: Tipo de documento fiscal
        
        Args:
            solicitud: Elemento XML donde se agregarán los parámetros
            incluir_cufd: Si False, omite el CUFD (útil para solicitud de nuevo CUFD)
        """
        ET.SubElement(solicitud, "codigoAmbiente").text = self.config['codigoAmbiente']
        ET.SubElement(solicitud, "codigoDocumentoSector").text = self.config['codigoDocumentoSector']
        ET.SubElement(solicitud, "codigoEmision").text = self.config['codigoEmision']
        ET.SubElement(solicitud, "codigoModalidad").text = self.config['codigoModalidad']
        ET.SubElement(solicitud, "codigoPuntoVenta").text = self.config['codigoPuntoVenta']
        ET.SubElement(solicitud, "codigoSistema").text = self.config['codigoSistema']
        ET.SubElement(solicitud, "codigoSucursal").text = self.config['codigoSucursal']
        
        if incluir_cufd:
            ET.SubElement(solicitud, "cufd").text = self.config['cufd']
        
        ET.SubElement(solicitud, "cuis").text = self.config['cuis']
        ET.SubElement(solicitud, "nit").text = self.config['nit']
        ET.SubElement(solicitud, "tipoFacturaDocumento").text = self.config['tipoFacturaDocumento']
    
    def construir_solicitud_verificacion(self, cuf: str) -> bytes:
        """
        Construye la solicitud SOAP para verificación de estado de factura.
        
        Servicio: verificacionEstadoFactura
        Propósito: Consultar el estado actual de una factura en el SIAT
        
        Args:
            cuf: Código Único de Facturación (64 caracteres alfanuméricos)
            
        Returns:
            bytes: XML de la solicitud en formato UTF-8
            
        Ejemplo:
            >>> client = get_siat_client()
            >>> xml = client.construir_solicitud_verificacion("ABC123...")
            >>> print(len(xml))  # ~800 bytes aprox
        """
        envelope, metodo = self._construir_envelope_base("verificacionEstadoFactura")
        solicitud = ET.SubElement(metodo, "SolicitudServicioVerificacionEstadoFactura")
        
        self._agregar_parametros_comunes(solicitud)
        ET.SubElement(solicitud, "cuf").text = cuf
        
        xml_bytes = ET.tostring(envelope, encoding='utf-8', method='xml')
        logger.debug(f"[SIAT Client] Solicitud verificación construida para CUF: {cuf[:20]}...")
        return xml_bytes
    
    def construir_solicitud_reversion(self, cuf: str) -> bytes:
        """
        Construye la solicitud SOAP para reversión de anulación de factura.
        
        Servicio: reversionAnulacionFactura
        Propósito: Revertir una anulación previamente realizada
        
        Args:
            cuf: Código Único de Facturación de la factura a revertir
            
        Returns:
            bytes: XML de la solicitud en formato UTF-8
            
        Nota:
            Solo se pueden revertir facturas que:
            - Estén en estado "Anulada"
            - No hayan sido incluidas en una declaración jurada
            - Estén dentro del plazo permitido
        """
        envelope, metodo = self._construir_envelope_base("reversionAnulacionFactura")
        solicitud = ET.SubElement(metodo, "SolicitudServicioReversionAnulacionFactura")
        
        self._agregar_parametros_comunes(solicitud)
        ET.SubElement(solicitud, "cuf").text = cuf
        
        xml_bytes = ET.tostring(envelope, encoding='utf-8', method='xml')
        logger.debug(f"[SIAT Client] Solicitud reversión construida para CUF: {cuf[:20]}...")
        return xml_bytes
    
    def construir_solicitud_anulacion(self, cuf: str, codigo_motivo: int) -> bytes:
        """
        Construye la solicitud SOAP para anulación de factura.
        
        Servicio: anulacionFactura
        Propósito: Anular una factura previamente emitida
        
        Args:
            cuf: Código Único de Facturación de la factura a anular
            codigo_motivo: Código del motivo de anulación según catálogo SIAT
                          1 = Error en datos del cliente
                          2 = Devolución de mercancía
                          ... (ver catálogo completo en normativa)
            
        Returns:
            bytes: XML de la solicitud en formato UTF-8
            
        Nota:
            La anulación debe realizarse antes de que la factura sea incluida
            en una declaración jurada mensual.
        """
        envelope, metodo = self._construir_envelope_base("anulacionFactura")
        solicitud = ET.SubElement(metodo, "SolicitudServicioAnulacionFactura")
        
        self._agregar_parametros_comunes(solicitud)
        ET.SubElement(solicitud, "cuf").text = cuf
        ET.SubElement(solicitud, "codigoMotivoAnulacion").text = str(codigo_motivo)
        
        xml_bytes = ET.tostring(envelope, encoding='utf-8', method='xml')
        logger.debug(f"[SIAT Client] Solicitud anulación construida para CUF: {cuf[:20]}...")
        return xml_bytes
    
    def enviar_solicitud(
        self, 
        solicitud_xml: bytes, 
        operacion: str = "operación genérica",
        timeout: int = 30
    ) -> Tuple[bool, bytes]:
        """
        Envía una solicitud SOAP al servicio SIAT con manejo robusto de errores.
        
        Maneja los siguientes escenarios de error:
        - Timeout: Cuando el servidor SIAT no responde en el tiempo especificado
        - HTTPError: Errores HTTP como 400, 401, 403, 500, 503
        - ConnectionError: Sin conexión a Internet o servidor SIAT caído
        - Exception genérica: Cualquier otro error inesperado
        
        Args:
            solicitud_xml: XML de la solicitud en bytes (UTF-8)
            operacion: Nombre descriptivo de la operación para logging
                      Ejemplos: "verificación", "reversión", "anulación"
            timeout: Tiempo máximo de espera en segundos (default: 30s)
            
        Returns:
            Tuple[bool, bytes]: 
                - Si éxito=True: (True, respuesta_xml_bytes)
                - Si éxito=False: (False, mensaje_error_bytes)
            
        Ejemplo:
            >>> client = get_siat_client()
            >>> xml = client.construir_solicitud_verificacion("CUF...")
            >>> exito, respuesta = client.enviar_solicitud(xml, "verificación")
            >>> if exito:
            ...     print("Respuesta recibida exitosamente")
            ... else:
            ...     print(f"Error: {respuesta.decode('utf-8')}")
        """
        headers = {
            'Content-Type': 'text/xml;charset=UTF-8',
            'apikey': self.config['apikey']
        }
        
        logger.info(f"[SIAT Client] 📡 Enviando solicitud: {operacion}")
        logger.debug(f"[SIAT Client] URL: {self.BASE_URL}")
        logger.debug(f"[SIAT Client] Headers: Content-Type, apikey: {self.config['apikey'][:20]}...")
        
        try:
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                data=solicitud_xml,
                timeout=timeout
            )
            
            # Verificar código HTTP (lanza HTTPError si status >= 400)
            response.raise_for_status()
            
            logger.info(f"[SIAT Client] ✅ Respuesta exitosa para {operacion} (HTTP {response.status_code})")
            logger.debug(f"[SIAT Client] Tamaño respuesta: {len(response.content)} bytes")
            
            return True, response.content
            
        except requests.exceptions.Timeout:
            error_msg = f"⏱️ Timeout ({timeout}s) al conectar con SIAT durante {operacion}"
            logger.error(f"[SIAT Client] {error_msg}")
            return False, error_msg.encode('utf-8')
            
        except requests.exceptions.HTTPError as http_err:
            # Extraer código de estado si está disponible
            status_code = response.status_code if 'response' in locals() else 'N/A'
            error_msg = f"❌ Error HTTP {status_code} durante {operacion}: {http_err}"
            logger.error(f"[SIAT Client] {error_msg}")
            
            # Intentar extraer mensaje de error del cuerpo de la respuesta
            if 'response' in locals() and response.content:
                logger.debug(f"[SIAT Client] Cuerpo de respuesta HTTP: {response.content[:200]}")
            
            return False, error_msg.encode('utf-8')
            
        except requests.exceptions.ConnectionError as conn_err:
            error_msg = f"🔌 Error de conexión durante {operacion}: Sin acceso a Internet o servidor SIAT caído"
            logger.error(f"[SIAT Client] {error_msg}")
            logger.debug(f"[SIAT Client] Detalle: {conn_err}")
            return False, error_msg.encode('utf-8')
            
        except Exception as e:
            error_msg = f"💥 Error inesperado durante {operacion}: {str(e)}"
            logger.error(f"[SIAT Client] {error_msg}", exc_info=True)
            return False, error_msg.encode('utf-8')


# ============================================================================
# PATRÓN SINGLETON: Instancia única del cliente SIAT
# ============================================================================
# Este patrón asegura que solo exista una instancia del cliente en toda la
# aplicación, evitando recrear configuración y conexiones innecesariamente.

_siat_client_instance = None

def get_siat_client() -> SIATServiceClient:
    """
    Obtiene la instancia singleton del cliente SIAT.
    
    Este patrón (Singleton) asegura que solo exista una instancia del cliente
    en toda la aplicación, evitando:
    - Recrear configuración múltiples veces
    - Cargar variables de entorno repetidamente
    - Inconsistencias entre diferentes instancias
    
    Returns:
        SIATServiceClient: Instancia única y reutilizable del cliente
        
    Ejemplo:
        >>> from siat_service_client import get_siat_client
        >>> 
        >>> # En cualquier parte de la aplicación
        >>> client1 = get_siat_client()
        >>> client2 = get_siat_client()
        >>> 
        >>> # Ambas variables apuntan a la misma instancia
        >>> assert client1 is client2  # True
    """
    global _siat_client_instance
    
    if _siat_client_instance is None:
        _siat_client_instance = SIATServiceClient()
        logger.info("[SIAT Client] 🚀 Instancia singleton creada exitosamente")
    
    return _siat_client_instance


# ============================================================================
# NOTAS DE IMPLEMENTACIÓN
# ============================================================================
#
# MIGRACIÓN DESDE CÓDIGO LEGACY:
# -------------------------------
# Este módulo reemplaza código duplicado en:
# - estado_factura.py: construir_solicitud_verificacion() + enviar_solicitud_verificacion()
# - reversion.py: construir_solicitud_reversion() + enviar_solicitud_reversion()
# - anulacion.py: construir_solicitud_anulacion() + enviar_solicitud_anulacion()
#
# VENTAJAS DE LA CENTRALIZACIÓN:
# -------------------------------
# 1. Eliminación de ~80 líneas duplicadas por módulo
# 2. Manejo de errores consistente y robusto
# 3. Logging estructurado en un solo lugar
# 4. Fácil extensión para nuevos servicios SIAT
# 5. Configuración centralizada (un solo lugar para cambiar)
#
# COMPATIBILIDAD:
# ---------------
# Los módulos legacy mantienen wrappers de compatibilidad para no romper
# código existente durante la transición. Ver estado_factura.py líneas 30-50.
#
# TESTING:
# --------
# Ver: facturador/docs/TESTING_SIAT_CLIENT.md
#
# ============================================================================
