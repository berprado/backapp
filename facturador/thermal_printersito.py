from escpos.printer import Usb
from bs4 import BeautifulSoup
import logging
import re

class ThermalPrinter:
    def __init__(self, vendor_id=0x04B8, product_id=0x0E15):
        self.printer = None
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.line_width = 57  # Ajustado para papel de 88mm
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logger = logging.getLogger('thermal_printer')
        logger.setLevel(logging.DEBUG)
        
        if not logger.handlers:
            # Crear manejador de archivo
            fh = logging.FileHandler('thermal_printer.log')
            fh.setLevel(logging.DEBUG)
            
            # Crear manejador de consola
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            
            # Crear formato
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            
            # Agregar manejadores al logger
            logger.addHandler(fh)
            logger.addHandler(ch)
        
        return logger

    def _connect_printer(self):
        try:
            self.printer = Usb(self.vendor_id, self.product_id)
            self.logger.info("Impresora conectada exitosamente")
        except Exception as e:
            self.logger.error(f"Error al conectar con la impresora: {str(e)}")
            raise

    def _format_line(self, text, width=None):
        """Formatea una línea de texto para el ancho del papel"""
        if width is None:
            width = self.line_width
        if len(text) > width:
            return text[:width-3] + '...'
        return text.ljust(width)

    def _extract_header_info(self, soup):
        """Extrae la información del encabezado"""
        header_info = []
        
        # Información de la empresa
        empresa_info = soup.find('td', {'class': 'tg-n17z', 'colspan': '4'})
        if empresa_info:
            for line in empresa_info.stripped_strings:
                header_info.append(line)
        
        return header_info

    def _extract_customer_info(self, soup):
        """Extrae la información del cliente"""
        customer_info = []
        
        # Información del cliente
        cliente_cell = soup.find('td', string=re.compile('Nombre/Razón Social'))
        if cliente_cell:
            cliente_text = cliente_cell.get_text()
            nombre = cliente_text.split(':')[1].strip() if ':' in cliente_text else cliente_text
            customer_info.append(f"Cliente: {nombre}")

        # NIT/CI/CEX
        doc_cell = soup.find('td', string=re.compile('NIT/CI/CEX'))
        if doc_cell:
            doc = doc_cell.find_next('td').get_text().strip()
            customer_info.append(f"Doc. Identidad: {doc}")

        # Fecha de emisión
        fecha_cell = soup.find('td', string=re.compile('Fecha'))
        if fecha_cell:
            fecha = fecha_cell.get_text().split(':')[1].strip()
            customer_info.append(f"Fecha: {fecha}")
        
        return customer_info

    def _extract_products(self, soup):
        """Extrae los productos del HTML"""
        products = []
        try:
            # Buscar la tabla de productos
            product_rows = soup.find_all('tr', {'class': 'tg-1kjo'})
            for row in product_rows:
                cells = row.find_all('td')
                if len(cells) >= 7:
                    product = {
                        'codigo': cells[0].get_text().strip(),
                        'cantidad': float(cells[1].get_text().strip()),
                        'unidad': cells[2].get_text().strip(),
                        'descripcion': cells[3].get_text().strip(),
                        'precio_unit': float(cells[4].get_text().strip()),
                        'descuento': float(cells[5].get_text().strip() or '0'),
                        'subtotal': float(cells[6].get_text().strip())
                    }
                    products.append(product)
            
            return products
        except Exception as e:
            self.logger.error(f"Error extrayendo productos: {str(e)}")
            return []

    def _extract_totals(self, soup):
        """Extrae y formatea los totales"""
        totals = []
        labels = [
            'Sub Total:', 'Descuento:', 'Total:', 
            'Gift Card:', 'Monto a Pagar:', 'Imp. Base Cred. Fiscal:'
        ]
        
        for label in labels:
            cell = soup.find('td', string=re.compile(label))
            if cell and cell.find_next('td'):
                value = cell.find_next('td').get_text().strip()
                formatted = f"{label.ljust(25)}{value.rjust(self.line_width - 25)}"
                totals.append(formatted)
        
        return totals

    def _print_header(self):
        """Imprime el encabezado"""
        self.printer.set(align='center', font='a')
        header = [
            "=" * self.line_width,
            "FACTURA",
            "(CON DERECHO A CREDITO FISCAL)",
            "=" * self.line_width
        ]
        self.printer.text("\n".join(header) + "\n\n")

    def _print_product_line(self, product):
        """Formatea una línea de producto"""
        self.printer.set(align='left')
        
        # Descripción del producto
        desc_line = f"{product['codigo']} - {product['descripcion']}"
        self.printer.text(self._format_line(desc_line) + "\n")
        
        # Cantidad y precio
        qty_price = f"{product['cantidad']} x {product['precio_unit']:,.2f}"
        subtotal = f"= {product['subtotal']:,.2f}"
        space = self.line_width - len(qty_price) - len(subtotal)
        self.printer.text(f"{qty_price}{' ' * space}{subtotal}\n")
        
        # Unidad de medida
        self.printer.text(f"Unidad: {product['unidad']}\n")
        
        if product['descuento'] > 0:
            self.printer.text(f"Descuento: {product['descuento']:,.2f}\n")
        
        self.printer.text("-" * self.line_width + "\n")

    def _extract_cuf(self, soup):
        """Extrae el CUF del HTML"""
        cuf_element = soup.find('td', string=re.compile('Código de Autorización', re.IGNORECASE))
        if cuf_element and cuf_element.find_next('td'):
            return cuf_element.find_next('td').get_text().strip()
        return ""

    def _extract_nit(self, soup):
        """Extrae el NIT del HTML"""
        nit_element = soup.find('td', class_='tg-i6l2', string=re.compile('NIT', re.IGNORECASE))
        if nit_element and nit_element.find_next('td'):
            return nit_element.find_next('td').get_text().strip()
        return ""

    def _extract_invoice_number(self, soup):
        """Extrae el número de factura del HTML"""
        invoice_element = soup.find('td', string=re.compile('Factura N°', re.IGNORECASE))
        if invoice_element and invoice_element.find_next('td'):
            return invoice_element.find_next('td').get_text().strip()
        return ""

    def print_invoice(self, html_content):
        """Método principal para imprimir la factura"""
        try:
            self.logger.info("Iniciando impresión")
            soup = BeautifulSoup(html_content, 'html.parser')
            self._connect_printer()
            
            # Encabezado
            self._print_header()
            
            # Información de la empresa
            self.printer.set(align='center')
            empresa_info = self._extract_header_info(soup)
            for line in empresa_info:
                self.printer.text(self._format_line(line) + "\n")
            
            self.printer.text("-" * self.line_width + "\n")
            
            # Información de documento
            self.printer.set(align='left')
            self.printer.text(f"NIT: {self._extract_nit(soup)}\n")
            self.printer.text(f"Factura N°: {self._extract_invoice_number(soup)}\n")
            
            # Información del cliente
            self.printer.text("\n")
            cliente_info = self._extract_customer_info(soup)
            for line in cliente_info:
                self.printer.text(self._format_line(line) + "\n")
            
            # Detalle de productos
            self.printer.text("\nDETALLE DE PRODUCTOS\n")
            self.printer.text("-" * self.line_width + "\n")
            
            productos = self._extract_products(soup)
            for producto in productos:
                self._print_product_line(producto)
            
            # Totales
            self.printer.set(align='right')
            totales = self._extract_totals(soup)
            self.printer.text("\n")
            for total in totales:
                self.printer.text(self._format_line(total) + "\n")
            
            # Son (en palabras)
            son_element = soup.find('td', string=re.compile('Son:', re.IGNORECASE))
            if son_element:
                self.printer.set(align='left')
                self.printer.text("\n" + self._format_line(son_element.get_text().strip()) + "\n")
            
            # Mensaje legal y pie
            self.printer.set(align='center')
            footer = [
                "",
                "ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS,",
                "EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE",
                "DE ACUERDO A LEY",
                "",
                f"CUF: {self._extract_cuf(soup)}",
                f"NIT: {self._extract_nit(soup)}",
                f"Factura No: {self._extract_invoice_number(soup)}",
                "=" * self.line_width
            ]
            self.printer.text("\n".join(footer))
            
            # Cortar papel
            self.printer.cut()
            
            self.logger.info("Impresión completada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante la impresión: {str(e)}")
            raise

def print_invoice_thermal(html_content, cuf, nit, numero_factura):
    """
    Función principal para imprimir la factura térmica
    Args:
        html_content (str): Contenido HTML de la factura
        cuf (str): Código CUF para el QR
        nit (str): NIT de la empresa
        numero_factura (str): Número de factura
    Returns:
        bool: True si la impresión fue exitosa
    """
    try:
        printer = ThermalPrinter()
        return printer.print_invoice(html_content)
    except Exception as e:
        logging.error(f"Error al imprimir factura: {str(e)}")
        raise