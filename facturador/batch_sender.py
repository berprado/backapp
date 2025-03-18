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
from logger_config import get_contingency_logger
from dotenv import load_dotenv

logger = get_contingency_logger()
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
        Envía un lote de facturas al servicio de recepción de paquetes
        
        Args:
            xml_path (str): Ruta del archivo XML
            compressed_path (str): Ruta del archivo comprimido
            cufd_code (str): Código CUFD vigente
            
        Returns:
            tuple: (bool, dict) Éxito y datos de respuesta
        """
        try:
            # Calcular el hash del archivo comprimido
            hash_archivo = self.calculate_hash(compressed_path)
            if not hash_archivo:
                return False, {"error": "No se pudo calcular el hash del archivo"}
            
            # Codificar el archivo en base64
            archivo_base64 = self.encode_file_to_base64(compressed_path)
            if not archivo_base64:
                return False, {"error": "No se pudo codificar el archivo en base64"}
            
            # Crear el cliente SOAP
            client = Client(
                self.wsdl_url,
                transport=Transport(session=self.soap_session)
            )
            
            # Obtener el cafc si existe para las facturas
            cafc = None
            # Si se necesita CAFC, aquí se implementaría la lógica para obtenerlo
            
            # Preparar la solicitud
            solicitud = {
                'codigoAmbiente': os.getenv('CODIGO_AMBIENTE'),
                'codigoDocumentoSector': os.getenv('CODIGO_DOCUMENTO_SECTOR'),
                'codigoEmision': 2,  # Fuera de línea
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
                'cantidadFacturas': len(os.path.basename(xml_path).split('_')),
                'cafc': cafc
            }
            
            # Enviar la solicitud
            logger.info(f"Enviando lote de facturas al servicio web...")
            response = client.service.recepcionPaqueteFactura(**solicitud)
            
            # Procesar la respuesta
            if response and hasattr(response, 'transaccion') and response.transaccion:
                logger.info(f"Lote enviado exitosamente. Código de recepción: {response.codigoRecepcion}")
                return True, helpers.serialize_object(response)
            else:
                error_msg = "Error desconocido al enviar lote"
                if hasattr(response, 'mensajesList') and response.mensajesList:
                    error_msg = response.mensajesList[0].descripcion
                
                logger.error(f"Error al enviar lote: {error_msg}")
                return False, {"error": error_msg}
        
        except Exception as e:
            logger.error(f"Excepción al enviar lote: {str(e)}")
            return False, {"error": str(e)}
    
    def validate_batch(self, codigo_recepcion, cufd_code):
        """
        Valida el estado de un paquete enviado
        
        Args:
            codigo_recepcion (str): Código de recepción del paquete
            cufd_code (str): Código CUFD vigente
            
        Returns:
            tuple: (bool, dict) Éxito y datos de respuesta
        """
        try:
            # Crear el cliente SOAP
            client = Client(
                self.wsdl_url,
                transport=Transport(session=self.soap_session)
            )
            
            # Preparar la solicitud
            solicitud = {
                'codigoAmbiente': os.getenv('CODIGO_AMBIENTE'),
                'codigoSistema': os.getenv('CODIGO_SISTEMA'),
                'nit': os.getenv('NIT'),
                'cuis': os.getenv('CUIS'),
                'cufd': cufd_code,
                'codigoSucursal': os.getenv('CODIGO_SUCURSAL'),
                'codigoPuntoVenta': os.getenv('CODIGO_PUNTO_VENTA'),
                'codigoRecepcion': codigo_recepcion
            }
            
            # Enviar la solicitud
            logger.info(f"Validando estado del paquete {codigo_recepcion}...")
            response = client.service.validacionRecepcionPaqueteFactura(**solicitud)
            
            # Procesar la respuesta
            if response and hasattr(response, 'transaccion'):
                success = response.transaccion
                codigo_estado = getattr(response, 'codigoEstado', None)
                
                result = {
                    'success': success,
                    'codigo_estado': codigo_estado,
                    'full_response': helpers.serialize_object(response)
                }
                
                if success:
                    estado_text = ""
                    if codigo_estado == 901:
                        estado_text = "PENDIENTE"
                    elif codigo_estado == 902:
                        estado_text = "RECHAZADO"
                    elif codigo_estado == 903:
                        estado_text = "OBSERVADO"
                    elif codigo_estado == 904:
                        estado_text = "VALIDADO PARCIAL"
                    elif codigo_estado == 905:
                        estado_text = "VALIDADO"
                    
                    logger.info(f"Estado del paquete: {estado_text} ({codigo_estado})")
                    
                    # Procesar facturas validadas
                    if hasattr(response, 'listaCodigosRespuestas') and response.listaCodigosRespuestas:
                        self.process_validated_invoices(response.listaCodigosRespuestas)
                
                return True, result
            else:
                error_msg = "Error desconocido al validar paquete"
                if hasattr(response, 'mensajesList') and response.mensajesList:
                    error_msg = response.mensajesList[0].descripcion
                
                logger.error(f"Error al validar paquete: {error_msg}")
                return False, {"error": error_msg}
        
        except Exception as e:
            logger.error(f"Excepción al validar paquete: {str(e)}")
            return False, {"error": str(e)}
    
    def process_validated_invoices(self, lista_codigos):
        """
        Procesa la lista de códigos de respuesta de facturas
        
        Args:
            lista_codigos: Lista de códigos de respuesta de SIAT
        """
        try:
            for codigo_resp in lista_codigos:
                if hasattr(codigo_resp, 'codigoFactura') and hasattr(codigo_resp, 'codigoRecepcion'):
                    numero_factura = codigo_resp.codigoFactura
                    codigo_recepcion = codigo_resp.codigoRecepcion
                    
                    # Actualizar el estado de la factura en la base de datos
                    if codigo_recepcion:
                        success = update_invoice_status_after_sending(
                            numero_factura, 
                            codigo_recepcion, 
                            "VALIDADA"
                        )
                        
                        if success:
                            logger.info(f"Factura {numero_factura} actualizada con código {codigo_recepcion}")
                        else:
                            logger.warning(f"No se pudo actualizar la factura {numero_factura}")
        
        except Exception as e:
            logger.error(f"Error al procesar facturas validadas: {str(e)}")
    
    def send_all_pending_invoices(self):
        """
        Envía todas las facturas pendientes en lotes
        
        Returns:
            dict: Resultados del proceso de envío
        """
        try:
            # Preparar los lotes
            batches = self.prepare_batches()
            if not batches:
                return {
                    "success": True,
                    "message": "No hay facturas pendientes para enviar",
                    "batches_sent": 0,
                    "invoices_sent": 0
                }
            
            # Obtener el CUFD vigente
            cufd_record = self.session.query(Cufd).filter(Cufd.vigente == 1).first()
            if not cufd_record:
                return {
                    "success": False,
                    "message": "No se encontró un CUFD válido",
                    "batches_sent": 0,
                    "invoices_sent": 0
                }
            
            cufd_code = cufd_record.codigo
            
            # Resultados
            results = {
                "success": True,
                "batches_sent": 0,
                "batches_results": [],
                "invoices_sent": 0
            }
            
            # Procesar cada lote
            for i, batch in enumerate(batches):
                logger.info(f"Procesando lote {i+1} de {len(batches)} ({len(batch)} facturas)")
                
                # Crear el archivo de lote
                xml_path, compressed_path = self.create_batch_file(batch)
                if not xml_path or not compressed_path:
                    batch_result = {
                        "batch_number": i+1,
                        "success": False,
                        "message": "Error al crear el archivo de lote",
                        "invoices": len(batch)
                    }
                    results["batches_results"].append(batch_result)
                    continue
                
                # Enviar el lote
                success, response = self.send_batch(xml_path, compressed_path, cufd_code)
                
                batch_result = {
                    "batch_number": i+1,
                    "success": success,
                    "invoices": len(batch)
                }
                
                if success:
                    results["batches_sent"] += 1
                    results["invoices_sent"] += len(batch)
                    
                    # Obtener código de recepción
                    codigo_recepcion = response.get('codigoRecepcion')
                    batch_result["codigo_recepcion"] = codigo_recepcion
                    
                    # Validar el lote después de un breve tiempo
                    time.sleep(2)  # Esperar 2 segundos para dar tiempo al sistema
                    
                    validation_success, validation_response = self.validate_batch(codigo_recepcion, cufd_code)
                    batch_result["validation"] = {
                        "success": validation_success,
                        "codigo_estado": validation_response.get('codigo_estado') if validation_success else None,
                        "message": "Validación exitosa" if validation_success else validation_response.get('error')
                    }
                else:
                    batch_result["message"] = response.get('error', 'Error desconocido')
                
                results["batches_results"].append(batch_result)
            
            # Actualizar el resultado general
            if results["batches_sent"] == 0:
                results["success"] = False
                results["message"] = "No se pudo enviar ningún lote"
            else:
                results["message"] = f"Se enviaron {results['batches_sent']} de {len(batches)} lotes ({results['invoices_sent']} facturas)"
            
            return results
        
        except Exception as e:
            logger.error(f"Error general en send_all_pending_invoices: {str(e)}")
            return {
                "success": False,
                "message": f"Error general: {str(e)}",
                "batches_sent": 0,
                "invoices_sent": 0
            }
    
    def close(self):
        """Cierra la sesión de la base de datos"""
        if self.session:
            self.session.close()
