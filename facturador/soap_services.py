"""
Servicios SOAP para comunicación con el SIN (Servicio de Impuestos Nacionales)
Versión refactorizada con logging centralizado y cumplimiento normativo total.
"""
import os
import requests
import xml.etree.ElementTree as ET
from typing import Tuple, Optional, Dict
from datetime import datetime
from dotenv import load_dotenv
from logger_config import get_logger, timed_call

# Cargar variables de entorno
load_dotenv()

# Logger centralizado
logger = get_logger('siat')

# Constantes de configuración
TOKEN_API: str = os.getenv("API_KEY")
ENDPOINT: str = os.getenv("WSDL_URL_OPERACIONES", "https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionOperaciones")

# Namespace SOAP estándar del SIN
SOAP_NS = {'ns2': 'https://siat.impuestos.gob.bo/'}




def verificar_comunicacion() -> Tuple[str, bool, Optional[str]]:
    """
    Verifica la comunicación con el SIN mediante el servicio verificarComunicacion.
    
    Returns:
        Tuple[mensaje, conectado, codigo_evento_sugerido]
        - mensaje: Descripción del estado de la conexión
        - conectado: True si hay conexión exitosa con el SIN
        - codigo_evento_sugerido: Código del tipo de evento según normativa (1, 2, etc.)
    """
    logger.info("🔍 Iniciando verificación de comunicación con el SIN...")
    
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "apikey": f"TokenApi {TOKEN_API}"
    }

    body = """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:siat="https://siat.impuestos.gob.bo/">
       <soapenv:Header/>
       <soapenv:Body>
          <siat:verificarComunicacion/>
       </soapenv:Body>
    </soapenv:Envelope>"""

    try:
        response = timed_call(
            logger,
            "[SOAP] verificarComunicacion -> POST",
            requests.post,
            ENDPOINT,
            data=body.encode("utf-8"),
            headers=headers,
            timeout=6
        )
        
        logger.debug(f"Respuesta HTTP del SIN: Status {response.status_code}")

        if response.status_code == 200:
            root = ET.fromstring(response.text)
            mensaje_elem = root.find('.//ns2:verificarComunicacionResponse//mensajesList//descripcion', SOAP_NS)
            transaccion_elem = root.find('.//ns2:verificarComunicacionResponse//transaccion', SOAP_NS)

            mensaje = mensaje_elem.text if mensaje_elem is not None else "Respuesta vacía del SIN"
            conectado = transaccion_elem is not None and transaccion_elem.text == "true"
            
            if conectado:
                logger.info(f"✅ Comunicación exitosa con el SIN: {mensaje}")
            else:
                logger.warning(f"⚠️ SIN responde pero transacción fallida: {mensaje}")
            
            return mensaje, conectado, None

        # Clasificación de errores HTTP según normativa SIN
        if response.status_code in [500, 502, 503]:
            msg = f"Error HTTP {response.status_code} - Servidor SIN no disponible"
            logger.error(f"🔴 {msg}")
            return msg, False, "2"
            
        elif response.status_code in [400, 404]:
            msg = f"Error HTTP {response.status_code} - Servicio remoto inaccesible"
            logger.error(f"🔴 {msg}")
            return msg, False, "2"
            
        elif response.status_code in [401, 403]:
            msg = f"Error HTTP {response.status_code} - Problemas de autenticación"
            logger.error(f"🔴 {msg}")
            return msg, False, "2"
            
        else:
            msg = f"Error HTTP {response.status_code}"
            logger.error(f"🔴 {msg} - Corte de internet general")
            return msg, False, "1"

    except requests.exceptions.Timeout:
        msg = "Timeout al conectar con el SIN (activar contingencia)"
        logger.error(f"⏱️ {msg}")
        return msg, False, "2"
        
    except requests.exceptions.ConnectionError as e:
        error_str = str(e).lower()
        if "java null" in error_str or "nullpointer" in error_str:
            msg = "Java Null Point Exception detectado (activar contingencia)"
            logger.error(f"☕ {msg}")
            return msg, False, "2"
        else:
            msg = "Error de conexión o DNS (activar contingencia)"
            logger.error(f"🌐 {msg} - Detalle: {str(e)[:200]}")
            return msg, False, "1"
            
    except Exception as e:
        error_str = str(e).lower()
        if "-1" in error_str or "codigo -1" in error_str:
            msg = "Código -1 detectado (activar contingencia)"
            logger.error(f"❌ {msg}")
            return msg, False, "2"
        else:
            msg = f"Error inesperado: {e} (requiere clasificación manual)"
            logger.error(f"❓ {msg}", exc_info=True)
            return msg, False, None



def enviar_evento_significativo(evento: Dict, fecha_fin: datetime, cufd: str) -> Tuple[Optional[str], bool]:
    """
    Registra un evento significativo en el SIN después de una contingencia.
    
    Documentación oficial:
    https://siatinfo.impuestos.gob.bo/index.php/facturacion-en-linea/implementacion-servicios-facturacion/operaciones/registro-evento-significativo
    
    Args:
        evento: Diccionario con claves obligatorias:
            - 'codigo_evento' (str): Código del tipo de evento (ej: "2")
            - 'cufd' (str): CUFD usado DURANTE la contingencia (cufdEvento)
            - 'descripcion' (str): Descripción del evento
            - 'fecha_inicio' (datetime): Fecha/hora de inicio del evento
        fecha_fin: Fecha/hora de finalización del evento (ahora)
        cufd: CUFD ACTUAL obtenido después de recuperar la conexión
        
    Returns:
        Tuple[codigo_recepcion, transaccion_exitosa]
        - codigo_recepcion: Código de recepción del SIN (si fue aceptado)
        - transaccion_exitosa: True si el SIN aceptó el registro
    """
    logger.info("📤 Iniciando registro de evento significativo en el SIN...")
    
    # ========================================
    # 1. VALIDAR VARIABLES DE ENTORNO CRÍTICAS
    # ========================================
    NIT = os.getenv("NIT")
    CUIS = os.getenv("CUIS")
    CODIGO_SISTEMA = os.getenv("CODIGO_SISTEMA")
    CODIGO_SUCURSAL = os.getenv("CODIGO_SUCURSAL", "0")
    CODIGO_AMBIENTE = os.getenv("CODIGO_AMBIENTE")
    CODIGO_PUNTO_VENTA = os.getenv("CODIGO_PUNTO_VENTA", "0")

    campos_faltantes = []
    if not NIT: campos_faltantes.append("NIT")
    if not CUIS: campos_faltantes.append("CUIS")
    if not CODIGO_SISTEMA: campos_faltantes.append("CODIGO_SISTEMA")
    if not CODIGO_AMBIENTE: campos_faltantes.append("CODIGO_AMBIENTE")
    if not TOKEN_API: campos_faltantes.append("API_KEY")
    
    if campos_faltantes:
        error_msg = f"❌ Faltan variables de entorno críticas: {', '.join(campos_faltantes)}"
        logger.error(error_msg)
        return None, False

    # ========================================
    # 2. VALIDAR DATOS DEL EVENTO
    # ========================================
    try:
        codigo_evento = evento['codigo_evento']
        cufd_evento = evento['cufd']  # CUFD usado DURANTE la contingencia
        descripcion = evento['descripcion']
        fecha_inicio = evento['fecha_inicio']
    except KeyError as e:
        error_msg = f"❌ Falta campo obligatorio en diccionario 'evento': {e}"
        logger.error(error_msg)
        return None, False

    # Validar que las fechas sean objetos datetime
    if not isinstance(fecha_inicio, datetime):
        logger.error(f"❌ fecha_inicio debe ser datetime, recibido: {type(fecha_inicio)}")
        return None, False
    
    if not isinstance(fecha_fin, datetime):
        logger.error(f"❌ fecha_fin debe ser datetime, recibido: {type(fecha_fin)}")
        return None, False

    # Validar rango de fechas
    if fecha_fin <= fecha_inicio:
        logger.error("❌ Rango de fechas inválido: fecha_fin debe ser posterior a fecha_inicio")
        return None, False

    # ========================================
    # 3. FORMATEAR FECHAS SEGÚN NORMATIVA
    # ========================================
    # Formato requerido: "yyyy-MM-dd'T'HH:mm:ss.SSS"
    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    fecha_fin_str = fecha_fin.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    
    # Sanitizar descripción
    descripcion_escaped = _xml_escape(descripcion)

    # Helper para truncar logs
    def _safe_tail(val: str) -> str:
        return f"{val[:8]}...{val[-8:]}" if val and len(val) > 20 else val

    logger.info(f"📊 Datos del evento a registrar:")
    logger.info(f"   • Código evento: {codigo_evento}")
    logger.info(f"   • Descripción: {descripcion}")
    logger.info(f"   • Fecha inicio: {fecha_inicio_str}")
    logger.info(f"   • Fecha fin: {fecha_fin_str}")
    logger.info(f"   • CUFD evento: {_safe_tail(cufd_evento)}")
    logger.info(f"   • CUFD actual: {_safe_tail(cufd)}")

    # Cast numéricos (defensivo)
    try:
        CODIGO_AMBIENTE_INT = int(CODIGO_AMBIENTE)
        CODIGO_SUCURSAL_INT = int(CODIGO_SUCURSAL)
        CODIGO_PUNTO_VENTA_INT = int(CODIGO_PUNTO_VENTA)
        NIT_INT = int(NIT)
    except (TypeError, ValueError):
        logger.error("❌ Variables numéricas con formato inválido")
        return None, False

    # ========================================
    # 4. CONSTRUIR SOLICITUD SOAP
    # ========================================
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "apikey": f"TokenApi {TOKEN_API}"
    }

    # Ajuste de tags según mensaje de error del servidor (WSDL real vs Documentación web):
    # codigoEvento -> codigoMotivoEvento
    # fechaFinEvento -> fechaHoraFinEvento
    # fechaInicioEvento -> fechaHoraInicioEvento
    soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                      xmlns:siat="https://siat.impuestos.gob.bo/">
       <soapenv:Header/>
       <soapenv:Body>
          <siat:registroEventoSignificativo>
             <SolicitudEventoSignificativo>
                <codigoAmbiente>{CODIGO_AMBIENTE_INT}</codigoAmbiente>
                <codigoPuntoVenta>{CODIGO_PUNTO_VENTA_INT}</codigoPuntoVenta>
                <codigoSistema>{CODIGO_SISTEMA}</codigoSistema>
                <codigoSucursal>{CODIGO_SUCURSAL_INT}</codigoSucursal>
                <cufd>{cufd}</cufd>
                <cufdEvento>{cufd_evento}</cufdEvento>
                <cuis>{CUIS}</cuis>
                <descripcion>{descripcion_escaped}</descripcion>
                <fechaHoraFinEvento>{fecha_fin_str}</fechaHoraFinEvento>
                <fechaHoraInicioEvento>{fecha_inicio_str}</fechaHoraInicioEvento>
                <nit>{NIT_INT}</nit>
                <codigoMotivoEvento>{codigo_evento}</codigoMotivoEvento>
             </SolicitudEventoSignificativo>
          </siat:registroEventoSignificativo>
       </soapenv:Body>
    </soapenv:Envelope>"""

    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("📄 SOLICITUD SOAP COMPLETA (sin truncar):")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(soap_body)
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # ========================================
    # 5. ENVIAR SOLICITUD AL SIN
    # ========================================
    endpoint_url = ENDPOINT.replace("?wsdl", "")

    try:
        logger.info(f"📡 Enviando solicitud al SIN: {endpoint_url}")
        response = timed_call(
            logger,
            "[SOAP] registroEventoSignificativo -> POST",
            requests.post,
            endpoint_url,
            data=soap_body.encode("utf-8"),
            headers=headers,
            timeout=10
        )
        
        logger.info(f"📥 Respuesta recibida del SIN: HTTP {response.status_code}")
        
        # REGISTRAR LA RESPUESTA COMPLETA PARA DIAGNÓSTICO
        logger.debug(f"📄 Contenido completo de la respuesta:\n{response.text}")
        
        # ========================================
        # 6. PROCESAR RESPUESTA EXITOSA (HTTP 200)
        # ========================================
        if response.status_code == 200:
            try:
                root = ET.fromstring(response.text)
                
                # Buscar elementos de respuesta
                recepcion = root.find(
                    './/ns2:registroEventoSignificativoResponse//codigoRecepcionEventoSignificativo', 
                    SOAP_NS
                )
                transaccion = root.find(
                    './/ns2:registroEventoSignificativoResponse//transaccion', 
                    SOAP_NS
                )
                
                # Buscar mensajes (éxito o error)
                mensajes_list = root.findall(
                    './/ns2:registroEventoSignificativoResponse//mensajesList',
                    SOAP_NS
                )
                
                codigo_recepcion = recepcion.text if recepcion is not None else None
                transaccion_exitosa = transaccion is not None and transaccion.text == "true"
                
                # Registrar mensajes del SIN
                if mensajes_list:
                    logger.info("📋 Mensajes del SIN:")
                    for mensaje in mensajes_list:
                        codigo = mensaje.find('codigo')
                        descripcion_msg = mensaje.find('descripcion')
                        if codigo is not None and descripcion_msg is not None:
                            logger.info(f"   • [{codigo.text}] {descripcion_msg.text}")
                
                if transaccion_exitosa:
                    logger.info(f"✅ Evento registrado exitosamente en el SIN")
                    logger.info(f"   • Código de recepción: {codigo_recepcion}")
                else:
                    logger.warning(f"⚠️ El SIN rechazó el registro del evento")
                    logger.warning(f"   • Código recepción recibido: {codigo_recepcion}")
                    logger.warning(f"   • Transacción: {transaccion.text if transaccion is not None else 'null'}")
                
                return codigo_recepcion, transaccion_exitosa
                
            except ET.ParseError as e:
                logger.error(f"❌ Error al parsear XML de respuesta del SIN: {e}")
                logger.error(f"📄 XML recibido:\n{response.text}")
                return None, False
        
        # ========================================
        # 7. PROCESAR ERRORES HTTP
        # ========================================
        else:
            logger.error(f"🔴 El SIN respondió con HTTP {response.status_code}")
            
            # Intentar parsear mensaje de error SOAP
            try:
                root = ET.fromstring(response.text)
                fault = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault')
                
                if fault is not None:
                    faultcode = fault.find('faultcode')
                    faultstring = fault.find('faultstring')
                    
                    codigo = faultcode.text if faultcode is not None else "N/A"
                    mensaje = faultstring.text if faultstring is not None else "Sin descripción"
                    
                    logger.error(f"❌ SOAP Fault del SIN:")
                    logger.error(f"   • Código: {codigo}")
                    logger.error(f"   • Mensaje: {mensaje}")
                else:
                    logger.error(f"📄 Respuesta del SIN:\n{response.text[:500]}")
            except:
                logger.error(f"📄 Respuesta no parseable del SIN:\n{response.text[:500]}")
            
            return None, False
    
    # ========================================
    # 8. MANEJO DE EXCEPCIONES DE RED
    # ========================================
    except requests.exceptions.Timeout:
        logger.error("⏱️ Timeout al enviar evento significativo al SIN (10s)")
        return None, False
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"🌐 Error de conexión al enviar evento: {str(e)[:200]}")
        return None, False
    
    except Exception as e:
        logger.error(f"❌ Error inesperado al registrar evento significativo: {e}", exc_info=True)
        return None, False


def _xml_escape(val: str) -> str:
    """Escapa caracteres especiales para XML."""
    return (val.replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;")
               .replace('"', "&quot;")
               .replace("'", "&apos;"))

