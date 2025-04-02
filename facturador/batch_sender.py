import os
import gzip
import base64
import hashlib
import logging
import time
from datetime import datetime
from zeep import Client, Transport, helpers
from requests import Session
from database import SessionLocal
from facturador.models import FacturaCabecera, Cufd
from facturador.offline_billing import update_invoice_status_after_sending
from facturador.logger_config import get_logger  # Cambiar esta importación
from dotenv import load_dotenv

logger = get_logger('contingency')  # Usar el logger general con nombre específico
load_dotenv()

class BatchSender:
    """Clase para el envío de facturas en lotes"""
    
    def __init__(self):
        self.session = SessionLocal()
        self.max_batch_size = 500  # Máximo 500 facturas por paquete según normativa
        self.soap_session = Session()
        self.soap_session.headers.update({'apikey': os.getenv('API_KEY')})
        self.wsdl_url = os.getenv('WSDL_URL_OPERACIONES')
        
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
        Crea un archivo XML con todas las facturas del lote
        
        Args:
            batch_numbers (list): Lista de números de factura en el lote
            
        Returns:
            tuple: (str, str) Ruta del archivo XML generado y del archivo comprimido
        """
        try:
            # Nombre del archivo basado en timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_file_path = f"xmls_batch/batch_{timestamp}.xml"
            
            # Crear el archivo XML principal que contendrá todas las facturas
            with open(batch_file_path, "w", encoding="utf-8") as batch_file:
                batch_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                batch_file.write('<facturas>\n')
                
                for numero_factura in batch_numbers:
                    # Buscar la factura en la base de datos
                    factura = self.session.query(FacturaCabecera).filter(
                        FacturaCabecera.numeroFactura == numero_factura
                    ).first()
                    
                    if factura:
                        # Buscar el XML almacenado de la factura
                        xml_path = f"xmls_offline/factura_{factura.numeroFactura}_{factura.cuf}.xml"
                        
                        if os.path.exists(xml_path):
                            with open(xml_path, "r", encoding="utf-8") as xml_file:
                                xml_content = xml_file.read()
                                
                                # Eliminar la declaración XML para evitar conflictos
                                xml_content = xml_content.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
                                
                                # Agregar el contenido al archivo de lote
                                batch_file.write(xml_content)
                        else:
                            logger.warning(f"No se encontró el XML para la factura {numero_factura}")
                    else:
                        logger.warning(f"No se encontró la factura {numero_factura} en la base de datos")
                
                batch_file.write('</facturas>\n')
            
            # Comprimir el archivo
            compressed_file_path = f"{batch_file_path}.gz"
            with open(batch_file_path, 'rb') as f_in:
                with gzip.open(compressed_file_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            logger.info(f"Archivo de lote creado: {compressed_file_path}")
            return batch_file_path, compressed_file_path
        
        except Exception as e:
            logger.error(f"Error al crear archivo de lote: {str(e)}")
            return None, None
    
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
    
    def send_batch(self, xml_path, compressed_path, cufd_code):
        """
        Sends a batch of invoices to the SIAT system.

        Args:
            xml_path (str): Path to the XML file.
            compressed_path (str): Path to the compressed file.
            cufd_code (str): Current CUFD code.

        Returns:
            tuple: (bool, dict) Success and response data.
        """
        try:
            # Validate inputs
            if not os.path.exists(xml_path):
                logger.error(f"XML file not found: {xml_path}")
                return False, {"error": "XML file not found."}

            if not os.path.exists(compressed_path):
                logger.error(f"Compressed file not found: {compressed_path}")
                return False, {"error": "Compressed file not found."}

            if not cufd_code:
                logger.error("CUFD code is required but not provided.")
                return False, {"error": "CUFD code is missing."}

            # Calculate the hash of the compressed file
            hash_archivo = self.calculate_hash(compressed_path)
            if not hash_archivo:
                return False, {"error": "Failed to calculate file hash."}

            # Encode the file in base64
            archivo_base64 = self.encode_file_to_base64(compressed_path)
            if not archivo_base64:
                return False, {"error": "Failed to encode file to base64."}

            # Create the SOAP client
            client = Client(
                self.wsdl_url,
                transport=Transport(session=self.soap_session)
            )

            # Prepare the request
            solicitud = {
                'codigoAmbiente': os.getenv('CODIGO_AMBIENTE'),
                'codigoDocumentoSector': os.getenv('CODIGO_DOCUMENTO_SECTOR'),
                'codigoEmision': 2,  # Offline mode
                'codigoModalidad': os.getenv('CODIGO_MODALIDAD'),
                'codigoPuntoVenta': os.getenv('CODIGO_PUNTO_VENTA'),
                'codigoSistema': os.getenv('CODIGO_SISTEMA'),
                'codigoSucursal': os.getenv('CODIGO_SUCURSAL'),
                'cufd': cufd_code,
                'cuis': os.getenv('CUIS'),
                'nit': os.getenv('NIT'),
                'tipoFacturaDocumento': os.getenv('TIPO_FACTURA_DOCUMENTO'),
                'archivo': archivo_base64,
                'hashArchivo': hash_archivo,
                'cantidadFacturas': len(os.path.basename(xml_path).split('_'))
            }

            # Retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempt {attempt + 1} to send batch...")
                    response = client.service.recepcionPaqueteFactura(**solicitud)

                    # Process the response
                    if response and hasattr(response, 'transaccion') and response.transaccion:
                        logger.info(f"Batch sent successfully. Reception code: {response.codigoRecepcion}")
                        return True, helpers.serialize_object(response)
                    else:
                        error_msg = "Unknown error while sending batch."
                        if hasattr(response, 'mensajesList') and response.mensajesList:
                            error_msg = response.mensajesList[0].descripcion

                        logger.error(f"Error sending batch: {error_msg}")
                        return False, {"error": error_msg}

                except Exception as e:
                    logger.error(f"Exception during batch sending attempt {attempt + 1}: {str(e)}")

            return False, {"error": "Failed to send batch after multiple attempts."}

        except Exception as e:
            logger.error(f"Exception in send_batch: {str(e)}")
            return False, {"error": str(e)}
