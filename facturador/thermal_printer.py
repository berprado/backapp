# thermal_printer.py
import logging
from escpos.printer import Usb
from bs4 import BeautifulSoup
import qrcode
from PIL import Image
import io
import re
import usb.core
import usb.util


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("printer_debug.log"),
        logging.StreamHandler()
    ]
)

class ThermalPrinter:
    def __init__(self, vendor_id=0x04b8, product_id=0x0e15):
        """
        Inicializa la impresora Epson TM-T20II
        vendor_id y product_id son específicos para la Epson TM-T20II
        """
        try:
            self.printer = Usb(vendor_id, product_id)
            logging.info("Impresora inicializada correctamente")
        except Exception as e:
            logging.error(f"Error al inicializar la impresora: {e}")
            raise

    def _clean_text(self, text):
        """Limpia el texto de caracteres especiales y ajusta el ancho"""
        if text is None:
            return ""
        # Eliminar caracteres especiales y HTML
        clean = re.sub(r'<[^>]+>', '', str(text))
        clean = clean.replace('&nbsp;', ' ').strip()
        return clean

    def _format_line(self, text, width=32):
        """Formatea una línea de texto al ancho especificado"""
        text = self._clean_text(text)
        if len(text) > width:
            return text[:width-3] + '...'
        return text

    def _print_header(self, soup):
        """Imprime el encabezado de la factura"""
        self.printer.set(align='center', font='a', width=2, height=2)
        self.printer.text("FACTURA\n")
        self.printer.set(align='center', font='a', width=1, height=1)
        self.printer.text("CON DERECHO A CREDITO FISCAL\n\n")

        # Información de la empresa
        self.printer.set(align='center')
        company_info = soup.find_all('td', limit=4)
        for info in company_info:
            self.printer.text(self._format_line(info.text) + "\n")
        self.printer.text("\n")

    def _print_invoice_details(self, soup):
        """Imprime los detalles de la factura"""
        self.printer.set(align='left')
        
        # NIT y número de factura
        nit_section = soup.find('td', text=re.compile('NIT', re.IGNORECASE))
        if nit_section:
            self.printer.text(f"NIT: {self._clean_text(nit_section.find_next('td').text)}\n")
        
        factura_section = soup.find('td', text=re.compile('Factura N°', re.IGNORECASE))
        if factura_section:
            self.printer.text(f"Factura N°: {self._clean_text(factura_section.find_next('td').text)}\n")

        # Información del cliente
        cliente_section = soup.find('td', text=re.compile('Nombre/Razón Social:', re.IGNORECASE))
        if cliente_section:
            self.printer.text(f"Cliente: {self._clean_text(cliente_section.find_next('td').text)}\n")

        self.printer.text("\n")

    def _print_products(self, soup):
        """Imprime la lista de productos"""
        self.printer.set(align='left')
        self.printer.text("DETALLE DE PRODUCTOS\n")
        self.printer.text("-" * 32 + "\n")

        products_section = soup.find_all('tr')
        for product in products_section:
            if "Producto" in product.text:
                name = self._format_line(product.find_all('td')[0].text)
                price = self._format_line(product.find_all('td')[1].text)
                self.printer.text(f"{name}\n")
                self.printer.text(f"Precio: {price}\n")
                self.printer.text("-" * 32 + "\n")

    def _print_totals(self, soup):
        """Imprime los totales"""
        self.printer.set(align='right')
        
        # Buscar y imprimir subtotal, descuento y total
        totals = {
            'Sub Total': None,
            'Descuento': None,
            'Total': None,
            'Gift Card': None,
            'Monto a Pagar': None
        }

        for label in totals.keys():
            section = soup.find('td', text=re.compile(label, re.IGNORECASE))
            if section:
                value = self._clean_text(section.find_next('td').text)
                totals[label] = value
                self.printer.text(f"{label}: {value}\n")

    def _print_qr(self, cuf):
        """Genera e imprime el código QR"""
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(cuf)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir la imagen QR a un formato que la impresora pueda manejar
        qr_buffer = io.BytesIO()
        qr_image.save(qr_buffer, format='PNG')
        self.printer.image(Image.open(qr_buffer))

    def _print_footer(self, soup):
        """Imprime el pie de página"""
        self.printer.set(align='center')
        self.printer.text("\n")
        footer_text = "GRACIAS POR SU COMPRA\n"
        self.printer.text(footer_text)
        self.printer.text("-" * 32 + "\n")

    def _validate_html_structure(self, soup):
        """
        Validates if the HTML has all required elements for printing.
        Raises ValueError if critical elements are missing.
        
        Args:
            soup: BeautifulSoup object of the HTML content
        """
        validation_results = {
            'header': bool(soup.find_all('td', limit=4)),
            'nit': bool(soup.find('td', text=re.compile('NIT', re.IGNORECASE))),
            'factura': bool(soup.find('td', text=re.compile('Factura N°', re.IGNORECASE))),
            'cliente': bool(soup.find('td', text=re.compile('Nombre/Razón Social:', re.IGNORECASE))),
            'productos': bool(soup.find_all('tr')),  # Verify product rows exist
            'totales': bool(soup.find('td', text=re.compile('Total:', re.IGNORECASE)))
        }
        
        # Log the validation results for debugging
        for element, found in validation_results.items():
            logging.debug(f"Elemento '{element}' encontrado: {found}")
        
        # Check for missing elements
        missing_elements = [k for k, v in validation_results.items() if not v]
        if missing_elements:
            error_msg = f"Elementos requeridos faltantes en el HTML: {', '.join(missing_elements)}"
            logging.error(error_msg)
            raise ValueError(error_msg)

    def print_invoice(self, html_content, cuf):
        """
        Imprime la factura completa con validación mejorada y manejo de errores.
        
        Args:
            html_content (str): Contenido HTML de la factura
            cuf (str): Código CUF para el QR
        """
        try:
            # Parse HTML and validate structure
            soup = BeautifulSoup(html_content, 'html.parser')
            logging.info("HTML parseado correctamente")
            
            # Validate HTML structure before printing
            self._validate_html_structure(soup)
            
            # Test printer connection
            logging.info("Probando conexión con la impresora...")
            self.printer.text("Test de conexión\n")
            self.printer.cut()
            logging.info("Prueba de conexión exitosa")
            
            # Continue with regular printing
            self._print_header(soup)
            self._print_invoice_details(soup)
            self._print_products(soup)
            self._print_totals(soup)
            self._print_qr(cuf)
            self._print_footer(soup)
            
            # Cut paper at the end
            self.printer.cut()
            
            logging.info("Factura impresa correctamente")
            return True
            
        except Exception as e:
            logging.error(f"Error detallado en print_invoice: {str(e)}")
            logging.error(f"Primeros 200 caracteres del HTML recibido: {html_content[:200]}...")
            raise

def print_invoice_thermal(html_content, cuf, nit, numero_factura):
    """
    Función principal para imprimir la factura con manejo mejorado de errores.
    
    Args:
        html_content (str): Contenido HTML de la factura
        cuf (str): Código CUF para el QR
        nit (str): NIT de la empresa
        numero_factura (str): Número de factura
    """
    try:
        # Log basic information
        logging.info(f"Iniciando impresión de factura #{numero_factura}")
        logging.debug(f"NIT: {nit}, CUF: {cuf}")
        
        # Initialize printer
        printer = ThermalPrinter()
        
        # Attempt to print
        result = printer.print_invoice(html_content, cuf)
        
        if result:
            logging.info(f"Factura #{numero_factura} impresa exitosamente")
            return True
        return False
        
    except usb.core.USBError as e:
        logging.error(f"Error de conexión USB: {str(e)}")
        raise Exception(f"Error de conexión con la impresora: {str(e)}")
    except ValueError as e:
        logging.error(f"Error de validación: {str(e)}")
        raise Exception(f"Error en el formato de la factura: {str(e)}")
    except Exception as e:
        logging.error(f"Error inesperado en la impresión: {str(e)}")
        raise Exception(f"Error al imprimir la factura: {str(e)}")