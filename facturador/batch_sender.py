import os
import gzip
import base64
import hashlib
from datetime import datetime
from zeep import Client, Transport, helpers
from requests import Session
from sqlalchemy import text
from database import SessionLocal
from models import FacturaCabecera, Cufd
from offline_billing import update_invoice_status_after_sending
from logger_config import get_logger  # Cambiar esta importación
from dotenv import load_dotenv

logger = get_logger('contingency')  # Usar el logger general con nombre específico
load_dotenv()

class BatchSender:
    """Clase para el envío de facturas en lotes"""
    
    def __init__(self):
        self.session = SessionLocal()
        self.max_batch_size = 500  # Máximo 500 facturas por paquete según normativa
        self.soap_session = Session()
        self.soap_session.headers.update({'apikey': os.getenv('API_KEY') or ''})
        self.wsdl_url = os.getenv('WSDL_URL_FACTURACION')
        
        # Asegurar que existe el directorio para archivos comprimidos
        os.makedirs("xmls_batch", exist_ok=True)
    
    def prepare_batches(self):
        """
        Prepara los lotes de facturas pendientes para envío
        
        Returns:
            list: Lista de lotes, donde cada lote es una lista de números de factura
        """
        try:
            # Obtener todas las facturas en contingencia
            facturas = self.session.query(FacturaCabecera).filter(
                FacturaCabecera.estadoFirma == "CONTINGENCIA"
            ).all()
            
            logger.info(f"Se encontraron {len(facturas)} facturas pendientes de envío")
            
            # Agrupar en lotes de hasta max_batch_size facturas
            batches = []
            current_batch = []
            
            for factura in facturas:
                current_batch.append(factura.numeroFactura)
                
                if len(current_batch) >= self.max_batch_size:
                    batches.append(current_batch)
                    current_batch = []
            
            # Agregar el último lote si tiene facturas
            if current_batch:
                batches.append(current_batch)
            
            logger.info(f"Se prepararon {len(batches)} lotes para envío")
            return batches
        
        except Exception as e:
            logger.error(f"Error al preparar lotes: {str(e)}")
            return []
    
    def create_batch_file(self, batch_numbers):
        """
        Crea un archivo .tar.gz con los XML individuales de las facturas del lote (normativa SIN).
        Args:
            batch_numbers (list): Lista de números de factura en el lote
        Returns:
            tuple: (str, str) Ruta del archivo .tar.gz generado y lista de XML incluidos
        """
        import tarfile
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tar_filename = f"xmls_batch/paquete_facturas_{timestamp}.tar.gz"
            xml_paths_incluidos = []
            with tarfile.open(tar_filename, "w:gz") as tar:
                for numero_factura in batch_numbers:
                    factura = self.session.query(FacturaCabecera).filter(
                        FacturaCabecera.numeroFactura == numero_factura
                    ).first()
                    if factura:
                        xml_path = f"offline_invoices/factura_offline_ev{factura.codigoEvento}_n{factura.numeroFactura}.xml"
                        if os.path.exists(xml_path):
                            tar.add(xml_path, arcname=os.path.basename(xml_path))
                            xml_paths_incluidos.append(xml_path)
                        else:
                            logger.warning(f"No se encontró el XML para la factura {numero_factura} en {xml_path}")
                    else:
                        logger.warning(f"No se encontró la factura {numero_factura} en la base de datos")
            logger.info(f"Archivo comprimido generado: {tar_filename} con {len(xml_paths_incluidos)} XMLs")
            return tar_filename, xml_paths_incluidos
        except Exception as e:
            logger.error(f"Error al crear archivo comprimido de lote: {str(e)}")
            return None, []
    
    def calculate_hash(self, file_path):
        """
        Calcula el hash SHA-256 de un archivo
        
        Args:
            file_path (str): Ruta del archivo
            
        Returns:
            str: Hash en hexadecimal
        """
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as file:
                buf = file.read()
                hasher.update(buf)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error al calcular hash: {str(e)}")
            return None
    
    def encode_file_to_base64(self, file_path):
        """
        Codifica un archivo en base64
        
        Args:
            file_path (str): Ruta del archivo
            
        Returns:
            str: Contenido del archivo en base64
        """
        try:
            with open(file_path, 'rb') as file:
                return base64.b64encode(file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error al codificar archivo: {str(e)}")
            return None
    
    def _get_client(self, service_name):
        """
        Obtiene el cliente SOAP para el servicio especificado.
        
        Args:
            service_name (str): Nombre del servicio
            
        Returns:
            Client: Cliente SOAP configurado
        """
        try:
            return Client(
                self.wsdl_url,
                transport=Transport(session=self.soap_session)
            )
        except Exception as e:
            logger.error(f"Error al crear cliente SOAP para {service_name}: {e}")
            return None
    
    def validate_package_status(self, codigo_recepcion, cufd):
        """
        Valida el estado de un paquete de facturas enviado al SIN.
        
        Args:
            codigo_recepcion (str): Código de recepción del paquete
            cufd (str): CUFD vigente para la validación
            
        Returns:
            Response: Respuesta del servicio de validación o None si hay error
        """
        client = self._get_client("FacturaCompraVenta")
        if not client:
            return None
            
        solicitud_validacion_paquete = {
            'codigoAmbiente': int(os.getenv('CODIGO_AMBIENTE')),
            'codigoSistema': os.getenv('CODIGO_SISTEMA'),
            'codigoSucursal': int(os.getenv('CODIGO_SUCURSAL')),
            'codigoPuntoVenta': int(os.getenv('CODIGO_PUNTO_VENTA', 0)),
            'codigoDocumentoSector': int(os.getenv('CODIGO_DOCUMENTO_SECTOR')),
            'codigoEmision': 2,  # offline
            'codigoModalidad': int(os.getenv('CODIGO_MODALIDAD')),
            'cuis': os.getenv('CUIS'),
            'cufd': cufd,
            'nit': int(os.getenv('NIT')),
            'tipoFacturaDocumento': int(os.getenv('CODIGO_TIPO_FACTURA', 1)),
            'codigoRecepcion': codigo_recepcion
        }
        try:
            response = client.service.validacionRecepcionPaqueteFactura(
                SolicitudServicioValidacionRecepcionPaquete=solicitud_validacion_paquete
            )
            logger.info(f"[📡] Respuesta validación paquete: {response}")
            return response
        except Exception as e:
            logger.error(f"[❌] Error al validar paquete {codigo_recepcion}: {e}")
            return None
    
    def send_batch(self, xml_path, compressed_path, cufd_code, batch_numbers, codigo_evento):
        """
        Envía un paquete de facturas al sistema SIAT.

        Args:
            xml_path (str): Ruta del archivo XML.
            compressed_path (str): Ruta del archivo comprimido.
            cufd_code (str): Código CUFD actual.
            batch_numbers (list): Lista de números de factura del lote.
            codigo_evento (int): Código del evento significativo.

        Returns:
            Response object: Respuesta del servicio o None si hay error.
        """
        try:
            # Validate inputs
            if not os.path.exists(compressed_path):
                logger.error(f"Compressed file not found: {compressed_path}")
                return None

            if not cufd_code:
                logger.error("CUFD code is required but not provided.")
                return None

            if not codigo_evento:
                logger.error("Código evento is required but not provided.")
                return None

            # Verificaciones adicionales recomendadas
            if not os.path.getsize(compressed_path) > 0:
                logger.error(f"Compressed file is empty: {compressed_path}")
                return None

            if len(batch_numbers) < 1:
                logger.error("cantidadFacturas must be >= 1")
                return None

            # Read and encode the compressed file
            with open(compressed_path, "rb") as f:
                archivo_gzip = f.read()

            base64_file = base64.b64encode(archivo_gzip).decode("utf-8")
            sha256_hash = hashlib.sha256(archivo_gzip).hexdigest()

            # Create the SOAP client
            client = self._get_client("FacturaCompraVenta")
            if not client:
                logger.error("Failed to create SOAP client")
                return None


            # Prepare the request with ALL required normative parameters
            solicitud_recepcion_paquete = {
                'codigoAmbiente': int(os.getenv('CODIGO_AMBIENTE')),
                'codigoPuntoVenta': int(os.getenv('CODIGO_PUNTO_VENTA', 0)),
                'codigoSistema': os.getenv('CODIGO_SISTEMA'),
                'codigoSucursal': int(os.getenv('CODIGO_SUCURSAL')),
                'codigoDocumentoSector': int(os.getenv('CODIGO_DOCUMENTO_SECTOR')),
                'codigoEmision': 2,  # offline
                'codigoModalidad': int(os.getenv('CODIGO_MODALIDAD')),
                'cufd': cufd_code,
                'cuis': os.getenv('CUIS'),
                'nit': int(os.getenv('NIT')),
                'tipoFacturaDocumento': int(os.getenv('CODIGO_TIPO_FACTURA', 1)),
                'archivo': base64_file,
                'fechaEnvio': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
                'hashArchivo': sha256_hash,
                'cafc': os.getenv('CAFC', ''),
                'cantidadFacturas': len(batch_numbers),
                'codigoEvento': codigo_evento
            }

            logger.info(f"[📦] Enviando paquete con {len(batch_numbers)} facturas, evento {codigo_evento}")
            logger.info("[📝] Valores de la solicitud SOAP RecepcionPaqueteFactura:")
            for k, v in solicitud_recepcion_paquete.items():
                if k == 'archivo':
                    logger.info(f"  {k}: [base64, longitud={len(v)}]")
                elif k == 'hashArchivo':
                    logger.info(f"  {k}: {v}")
                else:
                    logger.info(f"  {k}: {v}")

            # Retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempt {attempt + 1} to send batch...")
                    # CORREGIDO: Usar el nombre exacto del argumento según WSDL
                    response = client.service.recepcionPaqueteFactura(
                        SolicitudServicioRecepcionPaquete=solicitud_recepcion_paquete
                    )
                    logger.info(f"[📡] Respuesta RecepcionPaqueteFactura: {response}")
                    return response
                except Exception as e:
                    logger.error(f"Exception during batch sending attempt {attempt + 1}: {str(e)}")
            return None

        except Exception as e:
            logger.error(f"Exception in send_batch: {str(e)}")
            return None
    
    def process_and_validate_batch(self, xml_path, gzip_path, cufd, batch_numbers, evento_id):
        """
        Orquestador completo para envío y validación de paquetes offline.
        Args:
            xml_path (str): Ruta del archivo XML del paquete
            gzip_path (str): Ruta del archivo comprimido
            cufd (str): CUFD para el envío
            batch_numbers (list): Lista de números de factura del lote
            evento_id (int): ID del evento significativo
        Returns:
            bool: True si el proceso fue exitoso, False en caso contrario
        """
        # Obtener el código de recepción del evento desde la base de datos
        try:
            from data_access import obtener_evento_por_id
            evento_data = obtener_evento_por_id(evento_id)
            if not evento_data:
                logger.error(f"[❌] No se pudo obtener los datos del evento #{evento_id}")
                return False
            codigo_evento = evento_data.get('codigo_recepcion')
            if not codigo_evento:
                logger.error(f"[❌] El evento #{evento_id} no tiene código de recepción asignado.")
                return False
        except Exception as e:
            logger.error(f"[❌] Error al obtener código de recepción del evento #{evento_id}: {e}")
            return False

        # Paso 1: Enviar el paquete
        response = self.send_batch(xml_path, gzip_path, cufd, batch_numbers, codigo_evento)
        if not response or not getattr(response, "codigoRecepcion", None):
            logger.error("[❌] No se obtuvo codigoRecepcion en el envío del paquete.")
            return False

        codigo_recepcion = response.codigoRecepcion
        logger.info(f"[✅] Paquete enviado exitosamente. Código de recepción: {codigo_recepcion}")

        # Paso 2: Validar el estado del paquete
        result = self.validate_package_status(codigo_recepcion, cufd)
        if not result:
            logger.error(f"[❌] No se pudo validar el estado del paquete {codigo_recepcion}")
            return False

        # Paso 3: Determinar el estado basado en la respuesta
        if getattr(result, "transaccion", False):
            estado_paquete = "VALIDADO"
        elif hasattr(result, "mensajesList") and result.mensajesList:
            estado_paquete = "OBSERVADO"
        else:
            estado_paquete = "PENDIENTE"

        # Paso 4: Actualizar las tablas correspondientes
        try:
            from data_access import actualizar_estado_paquete, actualizar_estado_facturas
            actualizar_estado_paquete(evento_id, codigo_recepcion, estado_paquete)
            actualizar_estado_facturas(batch_numbers, codigo_recepcion, estado_paquete)
            logger.info(f"[📦] Paquete {codigo_recepcion} validado con estado: {estado_paquete}")
            return True
        except Exception as e:
            logger.error(f"[❌] Error al actualizar estados en base de datos: {e}")
            return False
