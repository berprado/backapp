import os
import logging
from datetime import datetime
import pdfkit
from facturador.thermal_printer import ThermalPrinter

class InvoiceExporter:
    def __init__(self):
        self.logger = logging.getLogger('invoice_exporter')
        self.html_path = 'factura_actual.html'  # Archivo HTML único
        self._ensure_directories()

    def _ensure_directories(self):
        """Asegura que exista el directorio para PDFs"""
        if not os.path.exists('pdfs'):
            os.makedirs('pdfs')
            self.logger.info("Directorio pdfs creado")

    def _generate_pdf_name(self, numero_factura, cuf):
        """Genera un nombre de archivo estandarizado para el PDF"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"factura_{numero_factura}_{cuf}_{timestamp}.pdf"

    def _save_html(self, html_content):
        """Guarda/sobreescribe el contenido HTML de la factura actual"""
        try:
            with open(self.html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"HTML actualizado en {self.html_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error al guardar HTML: {str(e)}")
            raise

    def _generate_pdf(self, numero_factura, cuf):
        """Genera el PDF de la factura desde el HTML guardado"""
        try:
            pdf_name = self._generate_pdf_name(numero_factura, cuf)
            pdf_path = os.path.join('pdfs', pdf_name)
            
            options = {
                'page-size': 'A4',
                'margin-top': '0mm',
                'margin-right': '0mm',
                'margin-bottom': '0mm',
                'margin-left': '0mm',
                'encoding': 'UTF-8'
            }
            
            pdfkit.from_file(self.html_path, pdf_path, options=options)
            self.logger.info(f"PDF generado en {pdf_path}")
            return pdf_path
        except Exception as e:
            self.logger.error(f"Error al generar PDF: {str(e)}")
            raise

    def _print_thermal(self, html_content):
        """Imprime en la impresora térmica"""
        try:
            printer = ThermalPrinter()
            success = printer.print_invoice(html_content)
            if success:
                self.logger.info("Impresión térmica completada")
            else:
                self.logger.warning("La impresión térmica no fue exitosa")
            return success
        except Exception as e:
            self.logger.error(f"Error en impresión térmica: {str(e)}")
            raise

    def export_invoice(self, html_content, cuf, nit, numero_factura):
        """
        Maneja el proceso completo de exportación de la factura.
        Retorna un diccionario con los resultados de cada operación.
        """
        results = {
            'success': False,
            'html_saved': False,
            'pdf_path': None,
            'printed': False,
            'errors': []
        }

        try:
            # Guardar/actualizar HTML
            self._save_html(html_content)
            results['html_saved'] = True
            
            # Generar PDF
            results['pdf_path'] = self._generate_pdf(numero_factura, cuf)
            
            # Imprimir en impresora térmica
            results['printed'] = self._print_thermal(html_content)
            
            results['success'] = True
            self.logger.info("Proceso de exportación completado exitosamente")
            
        except Exception as e:
            results['errors'].append(str(e))
            self.logger.error(f"Error en proceso de exportación: {str(e)}")

        return results