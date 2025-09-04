import os
import gzip
import base64
import hashlib
from datetime import datetime
from zeep import Client, Transport
from requests import Session
from logger_config import get_logger
from dotenv import load_dotenv

# IMPORTAR MÉTODOS ESPECÍFICOS DE LA FACTURACIÓN ONLINE QUE FUNCIONAN
from zeeper import comprimir_xml, obtener_hash  # Métodos probados de compresión y hash
from xml_signer import sign_xml  # Firma digital que funciona online
from invoice_xml_generator import generate_xml_invoice  # Generación de XML correcta

logger = get_logger('contingency')
load_dotenv()

class ContingencyPackager:
    """
    Clase para crear y enviar paquetes de contingencia siguiendo el flujo normativo correcto.
    Basada en el proceso de zeeper.py pero adaptada para paquetes de múltiples facturas.
    """
    
    def __init__(self):
        self.soap_session = Session()
        self.soap_session.headers.update({'apikey': os.getenv('API_KEY') or ''})
        self.wsdl_url = os.getenv('WSDL_URL_FACTURACION')
        
    # MÉTODO ELIMINADO: create_package_xml (wrapper XML)
    # Se mantiene únicamente el método normativo create_package_using_online_methods
    # que procesa cada factura individualmente como se requiere por normativa
    
    def compress_package(self, xml_path):
        """
        Comprime el paquete XML usando EXACTAMENTE el mismo método que zeeper.py
        que funciona correctamente en la facturación online.
        
        Args:
            xml_path (str): Ruta del archivo XML a comprimir
            
        Returns:
            str: Ruta del archivo comprimido o None si hay error
        """
        try:
            logger.info(f"[🗜️] Comprimiendo usando método de zeeper.py: {xml_path}")
            # Usar exactamente la función comprimir_xml de zeeper.py que funciona online
            gzip_path = comprimir_xml(xml_path)
            logger.info(f"[✅] Paquete comprimido con método zeeper: {gzip_path}")
            return gzip_path
            
        except Exception as e:
            logger.error(f"[❌] Error al comprimir paquete con método zeeper: {e}")
            return None
    
    def calculate_hash(self, gzip_path):
        """
        Calcula el hash SHA-256 usando EXACTAMENTE el mismo método que zeeper.py
        que funciona correctamente en la facturación online.
        
        Args:
            gzip_path (str): Ruta del archivo comprimido
            
        Returns:
            str: Hash SHA-256 en hexadecimal o None si hay error
        """
        try:
            logger.info(f"[#️⃣] Calculando hash usando método de zeeper.py: {gzip_path}")
            # Usar exactamente la función obtener_hash de zeeper.py que funciona online
            hash_result = obtener_hash(gzip_path)
            logger.info(f"[✅] Hash calculado con método zeeper: {hash_result}")
            return hash_result
            
        except Exception as e:
            logger.error(f"[❌] Error al calcular hash con método zeeper: {e}")
            return None
    
    def generate_invoice_xml(self, factura_data, cufd, numero_factura):
        """
        Genera XML de factura usando EXACTAMENTE el mismo método que 
        invoice_xml_generator.py para garantizar compatibilidad total.
        
        NOTA: Esta función debe ser adaptada según la estructura de datos
        disponible en las facturas offline almacenadas en la base de datos.
        Por ahora devuelve None para indicar que necesita implementación específica.
        
        Args:
            factura_data (dict): Datos de la factura desde base de datos
            cufd (str): CUFD del evento de contingencia
            numero_factura (int): Número de factura
            
        Returns:
            str: XML generado o None si hay error
        """
        try:
            logger.warning(f"[⚠️] generate_invoice_xml necesita implementación específica para datos offline")
            logger.info(f"[📄] Estructura de factura_data: {list(factura_data.keys()) if factura_data else 'None'}")
            
            # TODO: Implementar mapeo de datos offline a parámetros de generate_xml_invoice
            # Los datos offline tienen una estructura diferente a los datos online
            # Necesitamos mapear campos como:
            # - factura_data['nit_emisor'] -> nit_emisor
            # - factura_data['nombre_cliente'] -> nombre_razon_social
            # - etc.
            
            return None  # Temporal hasta completar la implementación
            
        except Exception as e:
            logger.error(f"[❌] Error al generar XML con invoice_xml_generator: {e}")
            return None

    def sign_xml_content(self, xml_content):
        """
        Firma el XML usando EXACTAMENTE el mismo método que xml_signer.py
        para garantizar compatibilidad total con el sistema online.
        
        Args:
            xml_content (str): Contenido XML a firmar
            
        Returns:
            str: XML firmado o None si hay error
        """
        try:
            logger.info(f"[✍️] Firmando XML usando xml_signer.py")
            
            # Usar exactamente la función sign_xml que funciona online
            signed_xml = sign_xml(xml_content)
            
            if signed_xml:
                logger.info(f"[✅] XML firmado correctamente con xml_signer")
            else:
                logger.error(f"[❌] No se pudo firmar XML con xml_signer")
            
            return signed_xml
            
        except Exception as e:
            logger.error(f"[❌] Error al firmar XML con xml_signer: {e}")
            return None

    def encode_to_base64(self, gzip_path):
        """
        Codifica el archivo comprimido en base64.
        
        Args:
            gzip_path (str): Ruta del archivo comprimido
            
        Returns:
            str: Contenido en base64 o None si hay error
        """
        try:
            logger.info(f"[📊] Codificando archivo a base64: {gzip_path}")
            
            with open(gzip_path, 'rb') as f:
                archivo_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            logger.info(f"[✅] Archivo codificado en base64 (tamaño: {len(archivo_base64)} caracteres)")
            return archivo_base64
            
        except Exception as e:
            logger.error(f"[❌] Error al codificar archivo: {e}")
            return None
    
    def create_package_using_online_methods(self, invoices_data, cufd, codigo_evento):
        """
        Crea un paquete de contingencia usando EXACTAMENTE los mismos métodos
        que funcionan en la facturación online: procesar cada factura INDIVIDUALMENTE.
        
        CORRECCIÓN CRÍTICA: NO crear wrapper XML, procesar cada factura como en línea.
        
        Args:
            invoices_data (list): Lista de datos de facturas offline
            cufd (str): CUFD del evento de contingencia
            codigo_evento (str): Código de recepción del evento significativo
            
        Returns:
            dict: Información del paquete creado o None si hay error
        """
        try:
            logger.info(f"[📦] Creando paquete NORMATIVO - procesando facturas INDIVIDUALES")
            logger.info(f"[📊] Total facturas a procesar: {len(invoices_data)}")
            
            # 1. CREAR DIRECTORIO TEMPORAL
            package_dir = f"contingency_packages/evento_{codigo_evento}"
            os.makedirs(package_dir, exist_ok=True)
            
            processed_files = []
            
            # 2. PROCESAR CADA FACTURA INDIVIDUALMENTE (como en línea)
            for i, factura_data in enumerate(invoices_data, 1):
                numero_factura = factura_data.get('numeroFactura')
                logger.info(f"[📄] Procesando factura {i}/{len(invoices_data)}: N° {numero_factura}")
                
                try:
                    # 2a. LEER XML EXISTENTE (facturas offline ya tienen XML guardado)
                    xml_path = factura_data.get('xml_path')  # Ruta del XML guardado
                    if not xml_path or not os.path.exists(xml_path):
                        logger.error(f"[❌] No se encuentra XML para factura {numero_factura}: {xml_path}")
                        continue
                    
                    # 2b. COMPRIMIR XML INDIVIDUAL (mismo método que online)
                    logger.info(f"[📦] Comprimiendo factura individual {numero_factura}")
                    gzip_path = comprimir_xml(xml_path)
                    
                    if not gzip_path or not os.path.exists(gzip_path):
                        logger.error(f"[❌] No se pudo comprimir XML para factura {numero_factura}")
                        continue
                    
                    # 2c. CALCULAR HASH INDIVIDUAL (mismo método que online)
                    hash_individual = obtener_hash(gzip_path)
                    if not hash_individual:
                        logger.error(f"[❌] No se pudo calcular hash para factura {numero_factura}")
                        continue
                    
                    # 2d. CODIFICAR A BASE64 INDIVIDUAL
                    with open(gzip_path, 'rb') as f:
                        archivo_base64 = base64.b64encode(f.read()).decode('utf-8')
                    
                    # 2e. AGREGAR A LISTA DE PROCESADOS
                    processed_files.append({
                        'numero_factura': numero_factura,
                        'xml_path': xml_path,
                        'gzip_path': gzip_path,
                        'hash_individual': hash_individual,
                        'archivo_base64': archivo_base64,
                        'cuf': factura_data.get('cuf')
                    })
                    
                    logger.info(f"[✅] Factura {numero_factura} procesada individualmente")
                    
                except Exception as e:
                    logger.error(f"[❌] Error procesando factura {numero_factura}: {e}")
                    continue
            
            if not processed_files:
                logger.error(f"[❌] No se procesó ninguna factura correctamente")
                return None
            
            # 3. CREAR PAQUETE NORMATIVO (múltiples archivos individuales)
            # NOTA: En paquetes de contingencia, el SIN espera recibir múltiples 
            # facturas individuales comprimidas, NO un archivo combinado
            
            package_info = {
                'facturas_procesadas': processed_files,
                'cantidad_facturas': len(processed_files),
                'tipo_paquete': 'individual_compressed',  # Cada factura comprimida individualmente
                'codigo_evento': codigo_evento,
                'package_dir': package_dir
            }
            
            logger.info(f"[✅] Paquete NORMATIVO creado correctamente")
            logger.info(f"[📊] Facturas procesadas individualmente: {len(processed_files)}")
            logger.info(f"[�] Cada factura tiene su propio .gz y hash")
            
            return package_info
            
        except Exception as e:
            logger.error(f"[❌] Error creando paquete normativo: {e}")
            return None
    
    def _create_multifile_gzip(self, xml_files, output_gz_path):
        """
        Crea un archivo .tar.gz que contiene múltiples archivos XML individuales.
        
        Al descomprimir este archivo se obtendrán los archivos XML originales separados,
        exactamente como se requiere normativamente.
        
        Args:
            xml_files (list): Lista de rutas de archivos XML a incluir
            output_gz_path (str): Ruta del archivo .tar.gz de salida
        """
        try:
            import tarfile
            
            logger.info(f"[📦] Creando archivo multi-XML: {output_gz_path}")
            
            with tarfile.open(output_gz_path, "w:gz") as tar:
                for xml_file in xml_files:
                    # Agregar cada XML al archivo comprimido manteniendo solo el nombre del archivo
                    arcname = os.path.basename(xml_file)
                    tar.add(xml_file, arcname=arcname)
                    logger.debug(f"[📄] Agregado: {arcname}")
            
            logger.info(f"[✅] Archivo multi-XML creado: {len(xml_files)} archivos incluidos")
            
        except Exception as e:
            logger.error(f"[❌] Error creando archivo multi-XML: {e}")
            raise

    def send_package_multiple_invoices(self, processed_files, cufd, codigo_evento):
        """
        Envía un paquete con múltiples facturas al SIN siguiendo la normativa.
        
        MÉTODO NORMATIVO CORRECTO: Envía hasta 500 facturas en un solo paquete,
        calculando automáticamente la cantidad real de facturas procesadas.
        
        Args:
            processed_files (list): Lista de facturas procesadas individualmente
            cufd (str): CUFD para el envío  
            codigo_evento (str): Código de recepción del evento significativo (del registro de evento)
            
        Returns:
            dict: Respuesta del envío del paquete completo
        """
        try:
            cantidad_facturas = len(processed_files)
            logger.info(f"[📦] Enviando PAQUETE con {cantidad_facturas} facturas al SIN")
            
            if cantidad_facturas > 500:
                logger.error(f"[❌] Paquete excede límite normativo: {cantidad_facturas} > 500")
                return None
            
            # 1. CREAR ARCHIVO COMBINADO CON TODAS LAS FACTURAS
            # Según normativa: "Formar paquetes de hasta 500 Facturas"
            combined_xml_path = f"contingency_packages/evento_{codigo_evento}/paquete_completo.xml"
            
            # Crear XML combinado de todas las facturas
            with open(combined_xml_path, 'w', encoding='utf-8') as combined_file:
                combined_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                
                for i, factura_info in enumerate(processed_files):
                    xml_path = factura_info['xml_path']
                    
                    with open(xml_path, 'r', encoding='utf-8') as xml_file:
                        xml_content = xml_file.read()
                        
                        # Eliminar declaración XML para evitar conflictos (excepto la primera)
                        if i > 0:
                            xml_content = xml_content.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
                            xml_content = xml_content.replace("<?xml version='1.0' encoding='UTF-8'?>", '')
                        
                        xml_content = xml_content.strip()
                        combined_file.write(xml_content + '\n')
            
            # 2. COMPRIMIR PAQUETE COMPLETO
            logger.info(f"[�️] Comprimiendo paquete completo con {cantidad_facturas} facturas")
            gzip_path = comprimir_xml(combined_xml_path)
            
            if not gzip_path or not os.path.exists(gzip_path):
                logger.error(f"[❌] No se pudo comprimir paquete completo")
                return None
            
            # 3. CALCULAR HASH DEL PAQUETE COMPLETO
            hash_paquete = obtener_hash(gzip_path)
            if not hash_paquete:
                logger.error(f"[❌] No se pudo calcular hash del paquete completo")
                return None
            
            # 4. CODIFICAR PAQUETE A BASE64
            with open(gzip_path, 'rb') as f:
                archivo_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            # 5. CREAR CLIENTE SOAP Y ENVIAR
            transport = Transport(session=self.soap_session)
            client = Client(self.wsdl_url, transport=transport)
            
            # 6. PREPARAR SOLICITUD CON CANTIDAD REAL DE FACTURAS
            solicitud = {
                'codigoAmbiente': int(os.getenv('CODIGO_AMBIENTE')),
                'codigoDocumentoSector': int(os.getenv('CODIGO_DOCUMENTO_SECTOR')),
                'codigoEmision': 2,  # offline según normativa
                'codigoModalidad': int(os.getenv('CODIGO_MODALIDAD')),
                'codigoPuntoVenta': int(os.getenv('CODIGO_PUNTO_VENTA', 0)),
                'codigoSistema': os.getenv('CODIGO_SISTEMA'),
                'codigoSucursal': int(os.getenv('CODIGO_SUCURSAL')),
                'cufd': cufd,
                'cuis': os.getenv('CUIS'),
                'nit': int(os.getenv('NIT')),
                'tipoFacturaDocumento': int(os.getenv('CODIGO_TIPO_FACTURA')),
                'archivo': archivo_base64,  # Paquete completo comprimido
                'fechaEnvio': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
                'hashArchivo': hash_paquete,  # Hash del paquete completo
                'cafc': '',  # Opcional: vacío para facturas normales de contingencia
                'cantidadFacturas': cantidad_facturas,  # ← CANTIDAD REAL Y DINÁMICA
                'codigoEvento': codigo_evento  # ← Código del registro de evento significativo
            }
            
            logger.info(f"[📡] Enviando paquete normativo:")
            logger.info(f"[📊] Cantidad facturas: {cantidad_facturas}")
            logger.info(f"[🔢] Código evento: {codigo_evento}")
            logger.info(f"[#️⃣] Hash paquete: {hash_paquete}")
            logger.info(f"[📦] Tamaño base64: {len(archivo_base64)} caracteres")
            
            # 7. ENVIAR PAQUETE COMPLETO
            response = client.service.RecepcionPaqueteFactura(solicitud)
            
            result = {
                'success': hasattr(response, 'transaccion') and response.transaccion,
                'response': response,
                'codigo_recepcion': getattr(response, 'codigoRecepcion', None),
                'cantidad_facturas_enviadas': cantidad_facturas,
                'codigo_evento_usado': codigo_evento,
                'hash_paquete': hash_paquete,
                'archivo_paquete': combined_xml_path,
                'archivo_comprimido': gzip_path
            }
            
            if result['success']:
                logger.info(f"[✅] PAQUETE enviado correctamente con {cantidad_facturas} facturas")
                logger.info(f"[📋] Código recepción paquete: {result['codigo_recepcion']}")
            else:
                logger.error(f"[❌] Error enviando paquete: {response}")
            
            return result
            
        except Exception as e:
            logger.error(f"[❌] Error en envío de paquete múltiple: {e}")
            return None

    def register_significant_event(self, cufd_contingencia, fecha_inicio, fecha_fin, descripcion="Contingencia por falta de conexión"):
        """
        Registra un evento significativo en el SIN y obtiene el codigo_evento necesario
        para posteriormente enviar los paquetes de facturas de contingencia.
        
        IMPORTANTE: Este método debe ejecutarse ANTES de enviar paquetes.
        El codigo_evento devuelto es lo que se usa en send_package_multiple_invoices().
        
        Args:
            cufd_contingencia (str): CUFD que se usó durante la contingencia
            fecha_inicio (str): Fecha inicio del evento formato "yyyy-MM-dd'T'HH:mm:ss.SSS"
            fecha_fin (str): Fecha fin del evento formato "yyyy-MM-dd'T'HH:mm:ss.SSS"
            descripcion (str): Descripción del evento significativo
            
        Returns:
            dict: Respuesta con codigo_evento o None si hay error
        """
        try:
            logger.info(f"[📋] Registrando evento significativo en el SIN")
            logger.info(f"[⏰] Período: {fecha_inicio} → {fecha_fin}")
            
            # Crear cliente SOAP
            transport = Transport(session=self.soap_session)
            client = Client(self.wsdl_url, transport=transport)
            
            # Preparar solicitud de registro de evento
            solicitud = {
                'codigoAmbiente': int(os.getenv('CODIGO_AMBIENTE')),
                'codigoSistema': os.getenv('CODIGO_SISTEMA'),
                'nit': int(os.getenv('NIT')),
                'cuis': os.getenv('CUIS'),
                'cufd': cufd_contingencia,  # CUFD que se usó en la contingencia
                'codigoSucursal': int(os.getenv('CODIGO_SUCURSAL')),
                'codigoPuntoVenta': int(os.getenv('CODIGO_PUNTO_VENTA', 0)),
                'codigoEvento': 1,  # Tipo de evento: 1 = Contingencia por falta de conexión
                'descripcion': descripcion,
                'fechaInicioEvento': fecha_inicio,
                'fechaFinEvento': fecha_fin,
                'cufdEvento': cufd_contingencia
            }
            
            logger.info(f"[📡] Enviando registro de evento al SIN")
            
            # Registrar evento significativo
            response = client.service.registroEventoSignificativo(solicitud)
            
            result = {
                'success': hasattr(response, 'transaccion') and response.transaccion,
                'response': response,
                'codigo_evento': getattr(response, 'codigoRecepcion', None),  # ← ESTE es el codigo_evento
                'cufd_usado': cufd_contingencia
            }
            
            if result['success']:
                logger.info(f"[✅] Evento significativo registrado correctamente")
                logger.info(f"[🔢] CÓDIGO EVENTO obtenido: {result['codigo_evento']}")
                logger.info(f"[💡] Usar este código en send_package_multiple_invoices()")
            else:
                logger.error(f"[❌] Error registrando evento: {response}")
            
            return result
            
        except Exception as e:
            logger.error(f"[❌] Error al registrar evento significativo: {e}")
            return None

    def validate_package_status(self, codigo_recepcion, cufd):
        """
        Valida el estado del paquete enviado usando validacionRecepcionPaqueteFactura.
        
        Args:
            codigo_recepcion (str): Código de recepción devuelto por el SIN
            cufd (str): CUFD usado en el envío
            
        Returns:
            response: Respuesta del servicio de validación o None si hay error
        """
        try:
            # Crear cliente SOAP
            transport = Transport(session=self.soap_session)
            client = Client(self.wsdl_url, transport=transport)
            
            # Preparar solicitud de validación usando diccionario
            # Estructura según SoapUI: SolicitudServicioValidacionRecepcionPaquete
            solicitud = {
                'codigoAmbiente': int(os.getenv('CODIGO_AMBIENTE')),
                'codigoDocumentoSector': int(os.getenv('CODIGO_DOCUMENTO_SECTOR')),
                'codigoEmision': 2,  # offline
                'codigoModalidad': int(os.getenv('CODIGO_MODALIDAD')),
                'codigoPuntoVenta': int(os.getenv('CODIGO_PUNTO_VENTA', 0)),
                'codigoSistema': os.getenv('CODIGO_SISTEMA'),
                'codigoSucursal': int(os.getenv('CODIGO_SUCURSAL')),
                'cufd': cufd,
                'cuis': os.getenv('CUIS'),
                'nit': int(os.getenv('NIT')),
                'tipoFacturaDocumento': int(os.getenv('CODIGO_TIPO_FACTURA')),
                'codigoRecepcion': codigo_recepcion
            }
            
            logger.info(f"[🔍] Validando estado del paquete: {codigo_recepcion}")
            
            # Llamar al servicio de validación con estructura SoapUI
            response = client.service.validacionRecepcionPaqueteFactura(solicitud)
            
            logger.info(f"[✅] Respuesta validación: {response}")
            return response
            
        except Exception as e:
            logger.error(f"[❌] Error al validar paquete: {e}")
            return None
