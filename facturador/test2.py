from escpos.printer import Usb
from bs4 import BeautifulSoup
import logging

class ThermalPrinter:
    def __init__(self, vendor_id=0x04B8, product_id=0x0E15):
        self.printer = Usb(vendor_id, product_id)
        self.line_width = 40  # Ancho ajustado para papel térmico
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger('thermal_printer')
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            fh = logging.FileHandler('thermal_printer.log')
            fh.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            logger.addHandler(fh)
            logger.addHandler(ch)
        return logger

    def _print_separator(self, style="solid"):
        if style == "dashed":
            self.printer.text("-" * self.line_width + "\n")
        elif style == "dotted":
            self.printer.text("." * self.line_width + "\n")
        else:
            self.printer.text("=" * self.line_width + "\n")

    def _print_header(self, soup):
        # Encabezado
        tipo_factura = soup.find(id="tipo_factura").get_text(strip=True)
        empresa_info = soup.find(id="razon_social").get_text(strip=True)
        direccion_info = soup.find(id="direccion").get_text(strip=True)
        codigo_autorizacion = soup.find(id="cuf").get_text(strip=True)

        self.printer.set(align='center', font='b', width=1, height=1)
        self.printer.text(f"{tipo_factura}\n")
        self.printer.text("(CON DERECHO A CRÉDITO FISCAL)\n\n")
        self.printer.text(f"{empresa_info}\n")
        self.printer.text("Casa Matriz\n")
        self.printer.text("No. Punto de Venta 0\n\n")
        self.printer.text(f"{direccion_info}\n\n")
        
        self.printer.text(f"{codigo_autorizacion}\n\n")

    def _print_customer_info(self, soup):
        cliente_info = soup.find(id="cliente_info").get_text(separator="\n", strip=True)
        self.printer.set(align='left', font='b', width=1, height=1)
        self.printer.text("INFORMACIÓN DEL CLIENTE\n")
        self._print_separator("dashed")
        self.printer.text(cliente_info + "\n\n")

    def _print_products(self, soup):
        self.printer.set(align='center', font='b', width=1, height=1)
        self.printer.text("DETALLE\n")
        self._print_separator("dotted")
        
        for product_row in soup.select('tr.product-line'):
            nombre = product_row.find('strong').text.strip()
            unidad_cantidad = product_row.find('span').text.strip()
            monto = product_row.find('td', class_="amount").text.strip()

            self.printer.set(align='left')
            self.printer.text(f"{nombre}\n")
            self.printer.text(f"   {unidad_cantidad}\n")
            self.printer.set(align='right')
            self.printer.text(f"{monto}\n")
            self._print_separator("dotted")

    def _print_totals(self, soup):
        self.printer.set(align='right', font='b', width=1, height=1)
        labels = {
            "subtotal": "SUBTOTAL",
            "descuento": "DESCUENTO",
            "giftcard": "MONTO GIFT CARD",
            "total": "TOTAL",
            "total_final": "MONTO A PAGAR",
            "iva_base": "IMPORTE BASE CRÉDITO FISCAL",
        }

        for key, label in labels.items():
            value = soup.find(id=key).get_text(strip=True)
            self.printer.text(f"{label} Bs {value}\n")

        total_en_palabras = soup.find(id="total_en_palabras").get_text(strip=True)
        self.printer.set(align='center')
        self.printer.text("\n" + total_en_palabras + "\n")
        self._print_separator()

    def _print_legend(self, soup):
        leyenda = soup.find(id="leyenda").get_text(strip=True)
        self.printer.set(align='center', font='b', width=1, height=1)
        self.printer.text("\nESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS,\n")
        self.printer.text("EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE\n")
        self.printer.text("ACUERDO A LEY\n\n")
        self.printer.text(leyenda + "\n")

    def print_invoice(self, html_content):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            self._print_header(soup)
            self._print_customer_info(soup)
            self._print_products(soup)
            self._print_totals(soup)
            self._print_legend(soup)
            self.printer.cut()
            self.logger.info("Impresión completada exitosamente")
        except Exception as e:
            self.logger.error(f"Error durante la impresión: {str(e)}")
            raise

# Leer el contenido del HTML cargado
with open("factura_actual.html", "r", encoding="utf-8") as file:
    html_content = file.read()

# Crear instancia de impresora e imprimir
printer = ThermalPrinter()
printer.print_invoice(html_content)
