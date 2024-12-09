from escpos.printer import Usb
from bs4 import BeautifulSoup
import logging

def imprimir_factura_html(html_file_path):
    """
    Lee un archivo HTML de factura, formatea el contenido y lo imprime en una impresora térmica.

    Args:
    - html_file_path: Ruta al archivo HTML que contiene la factura.
    """
    try:
        # Leer el contenido del archivo HTML
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()

        # Procesar HTML para extraer texto relevante
        soup = BeautifulSoup(html_content, "html.parser")
        body = soup.body
        lines = []

        for element in body.find_all(["strong", "span", "td"]):
            text = element.get_text(strip=True)
            if text:
                lines.append(text)

        # Formatear texto para impresión
        formatted_text = "\n".join(lines)

        # Configurar conexión con la impresora
        VENDOR_ID = 0x04B8  # ID del proveedor (Vendor ID) para Epson
        PRODUCT_ID = 0x0E15  # ID del producto (Product ID) para TM-T20II
        printer = Usb(VENDOR_ID, PRODUCT_ID)

        # Enviar texto a la impresora
        printer.text("=========================\n")
        printer.text(formatted_text)
        printer.text("\n=========================\n")
        printer.cut()

        logging.info("✅ Impresión completada correctamente")
        return "✅ Factura impresa correctamente"

    except Exception as e:
        logging.error(f"❌ Error durante la impresión: {str(e)}")
        return f"❌ Error durante la impresión: {str(e)}"
from escpos.printer import Usb
from bs4 import BeautifulSoup
import logging

class ThermalPrinter:
    def __init__(self, vendor_id=0x04B8, product_id=0x0E15):
        self.printer = None
        self.vendor_id = vendor_id
        self.product_id = product_id
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

    def _connect_printer(self):
        try:
            self.printer = Usb(self.vendor_id, self.product_id)
            self.logger.info("Impresora conectada exitosamente")
        except Exception as e:
            self.logger.error(f"Error al conectar con la impresora: {str(e)}")
            raise

    def _print_separator(self):
        self.printer.text("-" * self.line_width + "\n")

    def _print_header(self, soup):
        tipo_factura = soup.find(id="tipo_factura").get_text(strip=True)
        empresa_info = soup.find(id="empresa_info").get_text(strip=True)
        direccion_info = soup.find(id="direccion_info").get_text(strip=True)
        codigo_autorizacion = soup.find(id="codigo_autorizacion").get_text(strip=True)

        self.printer.set(align='center', font='a', width=2)
        self.printer.text(tipo_factura + "\n\n")
        self.printer.set(align='center', font='a', width=1)
        self.printer.text(empresa_info + "\n")
        self.printer.text(direccion_info + "\n\n")
        self.printer.text("CÓDIGO DE AUTORIZACIÓN\n")
        self.printer.text(codigo_autorizacion + "\n\n")

    def _print_customer_info(self, soup):
        cliente_info = soup.find(id="cliente_info").get_text(separator="\n", strip=True)
        self.printer.set(align='left', font='a', width=1)
        self.printer.text("INFORMACIÓN DEL CLIENTE\n")
        self._print_separator()
        self.printer.text(cliente_info + "\n\n")

    def _print_products(self, soup):
        self.printer.set(align='center', font='a', width=1)
        self.printer.text("DETALLE DE PRODUCTOS\n")
        self._print_separator()
        for product_row in soup.select('tr.product-line'):
            nombre = product_row.find('strong').text.strip()
            unidad_cantidad = product_row.find('span').text.strip()
            monto = product_row.find('td', class_="amount").text.strip()

            self.printer.set(align='left')
            self.printer.text(f"{nombre}\n")
            self.printer.text(f"{unidad_cantidad}\n")
            self.printer.set(align='right')
            self.printer.text(f"{monto}\n")
            self._print_separator()

    def _print_totals(self, soup):
        self.printer.set(align='right', font='a', width=1)
        labels = {
            "subtotal": "Sub Total",
            "descuento": "Descuento",
            "total": "Total",
            "giftcard": "Gift Card",
            "total_final": "Monto a Pagar",
            "iva_base": "Imp. Base Cred. Fiscal"
        }

        for key, label in labels.items():
            value = soup.find(id=key).get_text(strip=True)
            self.printer.text(f"{label}: {value}\n")

        total_en_palabras = soup.find(id="total_en_palabras").get_text(strip=True)
        self.printer.set(align='center')
        self.printer.text("\n" + total_en_palabras + "\n")
        self._print_separator()

    def _print_legend(self, soup):
        leyenda = soup.find(id="leyenda").get_text(strip=True)
        self.printer.set(align='center', font='a', width=1)
        self.printer.text(leyenda + "\n\n")

    def print_invoice(self, html_content):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            self._connect_printer()
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

# Leer el archivo HTML cargado
with open("factura_actual.html", "r", encoding="utf-8") as file:
    html_content = file.read()

# Crear instancia e imprimir la factura
printer = ThermalPrinter()
printer.print_invoice(html_content)
