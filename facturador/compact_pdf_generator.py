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

    def generate_pdf(self, html_content, numero_factura, cuf):
        """
        Genera un PDF a partir del HTML compacto de la factura
        
        Args:
            html_content (str): Contenido HTML de la factura
            numero_factura (str): Número de la factura
            cuf (str): Código Único de Facturación
            
        Returns:
            bool: True si el PDF se generó correctamente, False en caso contrario
        """
        try:
            # Generar nombre de archivo usando la función existente
            pdf_filename = generate_file_name(numero_factura, cuf, 'pdf')
            pdf_path = os.path.join('pdfs', pdf_filename)

            # Configurar opciones específicas para mantener el formato exacto
            options = {
                'page-height': '297mm',  # Altura A4
                'page-width': '80mm',    # Ancho de papel térmico
                'margin-top': '3mm',
                'margin-right': '2mm',
                'margin-bottom': '3mm',
                'margin-left': '2mm',
                'encoding': 'UTF-8',
                'no-outline': None,
                'zoom': 1.0,
                'dpi': 300,
                'enable-local-file-access': None,
                'print-media-type': None,
                'no-stop-slow-scripts': None,
                'disable-smart-shrinking': None,
                'load-error-handling': 'ignore'
            }

            # Guardar HTML temporalmente
            temp_html_path = os.path.join('pdfs', f'temp_{numero_factura}.html')
            with open(temp_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Generar PDF
            pdfkit.from_file(temp_html_path, pdf_path, options=options)

            # Verificar que el PDF se generó correctamente
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                self.logger.info(f"PDF generado exitosamente: {pdf_path}")
                return True
            else:
                self.logger.error("El PDF generado está vacío o no existe")
                return False

        except Exception as e:
            self.logger.error(f"Error al generar PDF: {str(e)}")
            return False

        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_html_path):
                os.remove(temp_html_path)
                self.logger.debug("Archivo HTML temporal eliminado")

def generate_invoice_pdf(html_content, numero_factura, cuf):
    """
    Función de utilidad para generar el PDF de la factura
    
    Args:
        html_content (str): Contenido HTML de la factura
        numero_factura (str): Número de la factura
        cuf (str): Código Único de Facturación
        
    Returns:
        bool: True si el PDF se generó correctamente, False en caso contrario
    """
    generator = CompactPDFGenerator()
    return generator.generate_pdf(html_content, numero_factura, cuf)