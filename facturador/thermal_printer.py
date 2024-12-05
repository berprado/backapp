from escpos.printer import Usb
from bs4 import BeautifulSoup
import logging


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

    def _extract_header_info(self, soup):
        """Extrae la información del encabezado"""
        try:
            tipo_factura = soup.find(id="tipo_factura").text.strip()
            subtitulo = soup.find(id="subtitulo").text.strip()
            empresa_info = soup.find(id="razon_social").text.strip()
            nombre_sucursal = soup.find(id="nombre_sucursal").text.strip()
            direccion = soup.find(id="direccion").text.strip()
            municipio = soup.find(id="municipio").text.strip()
            telefono = soup.find(id="telefono_empresa").text.strip()
            return {
                "tipo_factura": tipo_factura,
                "subtitulo": subtitulo,
                "empresa_info": empresa_info,
                "nombre_sucursal": nombre_sucursal,
                "direccion": direccion,
                "municipio": municipio,
                "telefono": telefono
            }
        except Exception as e:
            self.logger.error(f"Error al extraer el encabezado: {str(e)}")
            return {}

    def _extract_customer_info(self, soup):
        """Extrae la información del cliente"""
        try:
            nombre = soup.find(id="nombre_razon_social").text.strip()
            nit = soup.find(id="nit_ci").text.strip()
            cod_cliente = soup.find(id="cod_cliente").text.strip()
            fecha_emision = soup.find(id="fecha_emision").text.strip()
            return {
                "nombre": nombre,
                "nit": nit,
                "cod_cliente": cod_cliente,
                "fecha_emision": fecha_emision
            }
        except Exception as e:
            self.logger.error(f"Error al extraer información del cliente: {str(e)}")
            return {}

    def _extract_products(self, soup):
        """Extrae los productos del HTML"""
        products = []
        try:
            product_elements = soup.select('td[id^="producto_"]')
            for product_element in product_elements:
                codigo = product_element['id'].replace("producto_", "")
                nombre = product_element.text.strip()
                subtotal = soup.find(id=f"subtotal_producto_{codigo}").text.strip()
                products.append({
                    "codigo": codigo,
                    "nombre": nombre,
                    "subtotal": subtotal
                })
        except Exception as e:
            self.logger.error(f"Error al extraer productos: {str(e)}")
        return products

    def _extract_totals(self, soup):
        """Extrae y formatea los totales"""
        try:
            totals = {
                "subtotal": soup.find(id="subtotal").text.replace("Sub Total: ", "").strip(),
                "descuento": soup.find(id="descuento").text.replace("Descuento: ", "").strip(),
                "total": soup.find(id="total").text.replace("Total: ", "").strip(),
                "giftcard": soup.find(id="giftcard").text.replace("Gift Card: ", "").strip(),
                "total_final": soup.find(id="total_final").text.replace("Monto a Pagar: ", "").strip(),
                "iva_base": soup.find(id="iva_base").text.replace("Imp. Base Cred. Fiscal:", "").strip(),
                "total_en_palabras": soup.find(id="total_en_palabras").text.replace("Son: ", "").strip(),
                "leyenda": soup.find(id="leyenda").text.strip()
            }
            return totals
        except Exception as e:
            self.logger.error(f"Error al extraer los totales: {str(e)}")
            return {}

    def print_invoice(self, html_content):
        """Método principal para imprimir la factura"""
        try:
            self.logger.info("Iniciando impresión")
            soup = BeautifulSoup(html_content, 'html.parser')
            self._connect_printer()

            # Imprimir encabezado
            header = self._extract_header_info(soup)
            self.printer.set(align='center', font='a', width=2)
            self.printer.text(f"{header['tipo_factura']}\n")
            self.printer.text(f"{header['subtitulo']}\n\n")

            self.printer.set(align='left', font='a', width=1)
            self.printer.text(f"{header['empresa_info']}\n")
            self.printer.text(f"{header['nombre_sucursal']}\n")
            self.printer.text(f"{header['direccion']}, {header['municipio']}\n")
            self.printer.text(f"Tel: {header['telefono']}\n\n")

            # Imprimir información del cliente
            customer = self._extract_customer_info(soup)
            self.printer.text(f"Cliente: {customer['nombre']}\n")
            self.printer.text(f"NIT: {customer['nit']}\n")
            self.printer.text(f"Código Cliente: {customer['cod_cliente']}\n")
            self.printer.text(f"Fecha Emisión: {customer['fecha_emision']}\n\n")

            # Imprimir detalle de productos
            self.printer.text("DETALLE DE PRODUCTOS\n")
            self.printer.text("-" * self.line_width + "\n")
            products = self._extract_products(soup)
            for product in products:
                self.printer.text(f"{product['codigo']} - {product['nombre']}\n")
                self.printer.text(f"Subtotal: {product['subtotal']}\n")
                self.printer.text("-" * self.line_width + "\n")

            # Imprimir totales
            totals = self._extract_totals(soup)
            self.printer.text(f"Sub Total: {totals['subtotal']}\n")
            self.printer.text(f"Descuento: {totals['descuento']}\n")
            self.printer.text(f"Total: {totals['total']}\n")
            self.printer.text(f"Gift Card: {totals['giftcard']}\n")
            self.printer.text(f"Monto a Pagar: {totals['total_final']}\n")
            self.printer.text(f"Imp. Base Cred. Fiscal: {totals['iva_base']}\n")
            self.printer.text(f"Son: {totals['total_en_palabras']}\n\n")

            # Imprimir leyenda
            self.printer.set(align='center')
            self.printer.text(f"{totals['leyenda']}\n")
            self.printer.cut()

            self.logger.info("Impresión completada exitosamente")
            return True

        except Exception as e:
            self.logger.error(f"Error durante la impresión: {str(e)}")
            return False
