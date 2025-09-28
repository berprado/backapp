import os
import xmlschema
import gzip
import hashlib
import base64
import requests
from dotenv import load_dotenv
import sys
import time

# Agregar la ruta del directorio padre al path de Python si no está ya
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logger_config import get_xml_logger, get_zeeper_logger

# Obtener loggers para este módulo
xml_logger = get_xml_logger()
logger = get_zeeper_logger()

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Función para validar el XML contra el XSD principal
def validar_xml(xml_path, xsd_main_path):
    start_time = time.perf_counter()
    xml_logger.info(
        f"[VALIDACIÓN] Iniciando validación del XML: ruta={xml_path}, esquema={xsd_main_path}"
    )

    try:
        schema_main = xmlschema.XMLSchema(xsd_main_path)
    except Exception as exc:  # pragma: no cover - xmlschema lanza múltiples tipos
        xml_logger.error(
            f"[VALIDACIÓN] No se pudo cargar el esquema XSD '{xsd_main_path}': {exc}"
        )
        return False

    try:
        schema_main.validate(xml_path)
    except xmlschema.validators.exceptions.XMLSchemaValidationError as exc:
        xml_logger.error(f"[VALIDACIÓN] XML inválido contra el esquema: {exc}")
        return False
    except Exception as exc:  # pragma: no cover - captura fallos inesperados
        xml_logger.error(f"[VALIDACIÓN] Error inesperado durante la validación: {exc}")
        return False

    elapsed = time.perf_counter() - start_time
    xml_logger.info(
        f"[VALIDACIÓN] XML válido contra el esquema. Tiempo empleado: {elapsed:.2f}s"
    )
    return True

# Función para comprimir el archivo XML en formato Gzip
def comprimir_xml(xml_path):
    start_time = time.perf_counter()
    xml_logger.debug(f"[COMPRESIÓN] Preparando compresión de: {xml_path}")

    try:
        original_size = os.path.getsize(xml_path)
    except OSError as exc:
        xml_logger.error(f"[COMPRESIÓN] No se pudo acceder al XML '{xml_path}': {exc}")
        raise

    gzip_path = xml_path + '.gz'

    try:
        with open(xml_path, 'r', encoding='utf-8') as f_in, gzip.open(
            gzip_path, 'wt', encoding='utf-8'
        ) as f_out:
            content = f_in.read()
            normalized_content = content.replace('\r\n', '\n')
            f_out.write(normalized_content)
    except Exception as exc:
        xml_logger.error(
            f"[COMPRESIÓN] Error durante la compresión del XML '{xml_path}': {exc}"
        )
        raise

    try:
        compressed_size = os.path.getsize(gzip_path)
    except OSError as exc:
        xml_logger.warning(
            f"[COMPRESIÓN] Archivo comprimido generado pero no se pudo obtener su tamaño: {exc}"
        )
        compressed_size = 0

    elapsed = time.perf_counter() - start_time
    reduction = (
        (1 - (compressed_size / original_size)) * 100 if original_size else 0.0
    )
    xml_logger.info(
        "[COMPRESIÓN] Archivo comprimido exitosamente: {gzip_path} | "
        "Tamaño original: {orig:.2f} KB | Tamaño comprimido: {comp:.2f} KB | "
        "Reducción: {reduc:.1f}% | Tiempo: {elapsed:.2f}s".format(
            gzip_path=gzip_path,
            orig=original_size / 1024,
            comp=compressed_size / 1024,
            reduc=reduction,
            elapsed=elapsed,
        )
    )
    return gzip_path

# Función para obtener el hash SHA-256 del archivo comprimido
def obtener_hash(gzip_path):
    start_time = time.perf_counter()
    xml_logger.debug(f"[HASH] Calculando hash SHA-256 para: {gzip_path}")

    sha256_hash = hashlib.sha256()
    bytes_read = 0
    try:
        with open(gzip_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                bytes_read += len(byte_block)
                sha256_hash.update(byte_block)
    except FileNotFoundError as exc:
        xml_logger.error(f"[HASH] Archivo no encontrado para hash '{gzip_path}': {exc}")
        raise
    except OSError as exc:
        xml_logger.error(f"[HASH] Error de E/S al leer '{gzip_path}': {exc}")
        raise

    hash_result = sha256_hash.hexdigest()
    elapsed = time.perf_counter() - start_time
    xml_logger.info(
        f"[HASH] Hash SHA-256 calculado: {hash_result} | Bytes procesados: {bytes_read} | Tiempo: {elapsed:.2f}s"
    )
    return hash_result

# Función para construir el cuerpo de la solicitud SOAP
def construir_cuerpo_soap(archivo_base64, fecha_envio, hash_archivo, cufd):
    logger.debug(
        "[SOAP] Construyendo cuerpo de solicitud con hash %s y fecha %s",
        hash_archivo,
        fecha_envio,
    )
    return f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
       <soapenv:Header/>
       <soapenv:Body>
          <siat:recepcionFactura>
             <SolicitudServicioRecepcionFactura>
                <codigoAmbiente>{os.getenv('CODIGO_AMBIENTE')}</codigoAmbiente>
                <codigoDocumentoSector>{os.getenv('CODIGO_DOCUMENTO_SECTOR')}</codigoDocumentoSector>
                <codigoEmision>{os.getenv('CODIGO_TIPO_EMISION')}</codigoEmision>
                <codigoModalidad>{os.getenv('CODIGO_MODALIDAD')}</codigoModalidad>
                <codigoPuntoVenta>{os.getenv('CODIGO_PUNTO_VENTA')}</codigoPuntoVenta>
                <codigoSistema>{os.getenv('CODIGO_SISTEMA')}</codigoSistema>
                <codigoSucursal>{os.getenv('CODIGO_SUCURSAL')}</codigoSucursal>
                <cufd>{cufd}</cufd>
                <cuis>{os.getenv('CUIS')}</cuis>
                <nit>{os.getenv('NIT')}</nit>
                <tipoFacturaDocumento>{os.getenv('CODIGO_TIPO_FACTURA')}</tipoFacturaDocumento>
                <archivo>{archivo_base64}</archivo>
                <fechaEnvio>{fecha_envio}</fechaEnvio>
                <hashArchivo>{hash_archivo}</hashArchivo>
             </SolicitudServicioRecepcionFactura>
          </siat:recepcionFactura>
       </soapenv:Body>
    </soapenv:Envelope>
    """

# Función para enviar la solicitud SOAP
def enviar_solicitud(xml_path, xsd_main_path, fecha_envio, cufd):
    logger.info(
        "[ENVÍO] Iniciando envío SOAP | xml=%s | fecha_envio=%s | cufd=%s",
        xml_path,
        fecha_envio,
        cufd,
    )

    if not validar_xml(xml_path, xsd_main_path):
        logger.error("[ENVÍO] El XML no es válido. Abandonando solicitud.")
        return {"error": "XML no válido"}

    try:
        gzip_path = comprimir_xml(xml_path)
        hash_archivo = obtener_hash(gzip_path)
    except Exception as exc:
        logger.error(f"[ENVÍO] Fallo preparando artefactos del XML: {exc}")
        return {"error": str(exc)}

    try:
        with open(gzip_path, 'rb') as f:
            archivo_bytes = f.read()
    except OSError as exc:
        logger.error(f"[ENVÍO] No se pudo leer el XML comprimido '{gzip_path}': {exc}")
        return {"error": str(exc)}

    archivo_base64 = base64.b64encode(archivo_bytes).decode('utf-8')
    xml_logger.debug(
        "[BASE64] Archivo comprimido codificado correctamente | bytes=%d | longitud_base64=%d",
        len(archivo_bytes),
        len(archivo_base64),
    )

    url = "https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta"
    headers = {
        'Content-Type': 'text/xml;charset=UTF-8',
        'apikey': os.getenv('API_KEY')
    }
    soap_body = construir_cuerpo_soap(archivo_base64, fecha_envio, hash_archivo, cufd)

    max_retries = 3
    retry_delay = 5  # Segundos entre reintentos

    for attempt in range(max_retries):
        attempt_start = time.perf_counter()
        logger.info(
            "[ENVÍO] Intento %d/%d al servicio SIAT...",
            attempt + 1,
            max_retries,
        )
        try:
            response = requests.post(
                url,
                headers=headers,
                data=soap_body,
                timeout=30,
            )
            response.raise_for_status()
            elapsed = time.perf_counter() - attempt_start
            logger.info(
                "[ENVÍO] Respuesta exitosa | estado=%s | tiempo=%.2fs",
                response.status_code,
                elapsed,
            )
            return response
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"[ENVÍO] Error HTTP: {http_err}")
            return {"error": str(http_err)}
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"[ENVÍO] Error de conexión: {conn_err}")
            return {"error": str(conn_err)}
        except requests.exceptions.Timeout as timeout_err:
            logger.warning(
                "[ENVÍO] Timeout en intento %d/%d: %s",
                attempt + 1,
                max_retries,
                timeout_err,
            )
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return {"error": "Timeout después de múltiples intentos"}
        except requests.exceptions.RequestException as req_err:
            logger.error(f"[ENVÍO] Error general de solicitud: {req_err}")
            return {"error": str(req_err)}

    return {"error": "Error desconocido durante el envío"}