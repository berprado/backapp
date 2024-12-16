import os
import pdfkit
import logging
from datetime import datetime
from business_logic import generate_file_name

class CompactPDFGenerator:
    def __init__(self):
        self.logger = logging.getLogger('compact_pdf_generator')
        self._setup_logging()
        self._ensure_output_directory()
        self._setup_wkhtmltopdf()

    def _setup_logging(self):
        """Configura el sistema de logging"""
        if not self.logger.handlers:
            handler = logging.FileHandler('pdf_generation.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)

    def _ensure_output_directory(self):
        """Asegura que exista el directorio de salida"""
        if not os.path.exists('pdfs'):
            os.makedirs('pdfs')
            self.logger.info("Directorio 'pdfs' creado")

    def _setup_wkhtmltopdf(self):
        """Configura la ruta al ejecutable wkhtmltopdf"""
        if os.name == 'nt':  # Windows
            self.wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            if not os.path.exists(self.wkhtmltopdf_path):
                self.wkhtmltopdf_path = r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe'
        else:  # Linux/Unix
            self.wkhtmltopdf_path = '/usr/local/bin/wkhtmltopdf'
        
        if not os.path.exists(self.wkhtmltopdf_path):
            self.logger.error(f"wkhtmltopdf no encontrado en {self.wkhtmltopdf_path}")
            self.wkhtmltopdf_path = None

    def generate_pdf(self, html_content, numero_factura, cuf):
        """
        Genera un PDF a partir del contenido HTML proporcionado
        
        Args:
            html_content (str): Contenido HTML de la factura
            numero_factura (str): Número de la factura
            cuf (str): Código Único de Facturación
        
        Returns:
            bool: True si el PDF se generó correctamente, False en caso contrario
        """
        try:
            # Verificar que wkhtmltopdf esté configurado
            if not self.wkhtmltopdf_path:
                self.logger.error("wkhtmltopdf no está configurado correctamente")
                return False

            # Generar nombre de archivo
            pdf_filename = generate_file_name(numero_factura, cuf, 'pdf')
            pdf_path = os.path.join('pdfs', pdf_filename)
            
            # Configuración
            config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)
            
            # Opciones optimizadas para facturas
            options = {
                'page-height': '297mm',
                'page-width': '80mm',
                'margin-top': '2mm',
                'margin-right': '2mm',
                'margin-bottom': '2mm',
                'margin-left': '2mm',
                'encoding': 'UTF-8',
                'zoom': 1.0,
                'dpi': 300,
                'print-media-type': None,
                'disable-smart-shrinking': None,
                'quiet': ''
            }

            # Generar PDF directamente desde el contenido HTML
            self.logger.debug(f"Iniciando generación de PDF para factura {numero_factura}")
            pdfkit.from_string(
                html_content,
                pdf_path,
                options=options,
                configuration=config
            )

            # Verificar el resultado
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                self.logger.info(f"PDF generado exitosamente: {pdf_path}")
                return True
            else:
                self.logger.error("El PDF generado está vacío o no existe")
                return False

        except Exception as e:
            self.logger.error(f"Error al generar PDF: {str(e)}")
            self.logger.error(f"Detalles adicionales del error: {type(e).__name__}")
            return False

def generate_invoice_pdf(html_content, numero_factura, cuf):
    """
    Función de utilidad para generar el PDF de la factura
    """
    generator = CompactPDFGenerator()
    return generator.generate_pdf(html_content, numero_factura, cuf)