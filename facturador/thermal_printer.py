from escpos.printer import Usb
from bs4 import BeautifulSoup
import logging
from contextlib import contextmanager

class ThermalPrinter:
    def __init__(self, vendor_id=0x04B8, product_id=0x0E15):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.line_width = 48  # Ancho ajustado para fuente pequeña
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

    @contextmanager
    def printer_connection(self):
        """Contexto seguro para manejar la conexión de la impresora"""
        try:
            self._printer = Usb(self.vendor_id, self.product_id)
            self.logger.info("Impresora conectada exitosamente")
            yield self._printer
        except Exception as e:
            self.logger.error(f"Error al conectar con la impresora: {str(e)}")
            raise
        finally:
            if self._printer:
                try:
                    self._printer.close()
                except:
                    pass

    def _print_line(self, printer, text, align='left', font='b', width=1, bold=False):
        """Imprime una línea de texto con los atributos especificados"""
        printer.set(align=align, font=font, width=width, height=1, bold=bold)
        printer.text(f"{text}\n")

    def _print_separator(self, printer, char='-'):
        """Imprime una línea separadora"""
        self._print_line(printer, char * self.line_width, font='b')

    def _print_qr(self, printer, nit, cuf, numero_factura, size=6):
        """Imprime el código QR de la factura"""
        try:
            url = f'https://pilotosiat.impuestos.gob.bo/consulta/QR?nit={nit}&cuf={cuf}&numero={numero_factura}'
            printer.set(align='center')
            printer.qr(url, size=size, native=True)
            printer.text("\n")
        except Exception as e:
            self.logger.error(f"Error al imprimir código QR: {str(e)}")
            raise

    def print_invoice(self, html_content, nit, cuf, numero_factura):
        """Imprime la factura completa con código QR"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            with self.printer_connection() as printer:
                # Tipo Factura y Subtítulo
                tipo_factura = soup.find(id='tipo_factura_text')
                subtitulo = soup.find(id='subtitulo_text')
                if tipo_factura:
                    self._print_line(printer, tipo_factura.text.strip(), align='center', font='a', width=1, bold=True)
                if subtitulo:
                    self._print_line(printer, subtitulo.text.strip(), align='center', font='b')
                
                # Información de la empresa
                razon_social = soup.find(id='razon_social')
                nombre_sucursal = soup.find(id='nombre_sucursal')
                codigo_punto_venta = soup.find(id='codigo_punto_venta')
                if razon_social:
                    self._print_line(printer, razon_social.text.strip(), align='center', bold=True)
                if nombre_sucursal:
                    self._print_line(printer, nombre_sucursal.text.strip(), align='center')
                if codigo_punto_venta:
                    self._print_line(printer, codigo_punto_venta.text.strip(), align='center')
                
                # Dirección y contacto
                direccion = soup.find(id='direccion')
                municipio = soup.find(id='municipio')
                telefono = soup.find(id='telefono_empresa')
                if direccion:
                    self._print_line(printer, direccion.text.strip(), align='center')
                if municipio:
                    self._print_line(printer, municipio.text.strip(), align='center')
                if telefono:
                    self._print_line(printer, telefono.text.strip(), align='center')
                
                self._print_separator(printer)
                
                # NIT y Número de Factura
                nit = soup.find(id='nit')
                numero_factura = soup.find(id='numero_factura')
                if nit:
                    self._print_line(printer, f"NIT: {nit.text.strip()}", bold=True)
                if numero_factura:
                    self._print_line(printer, f"Factura N°: {numero_factura.text.strip()}", bold=True)
                
                # CUF
                cuf = soup.find(id='cuf')
                if cuf:
                    self._print_line(printer, "Código de Autorización:", align='center')
                    texto_cuf = cuf.text.strip()
                    while texto_cuf:
                        self._print_line(printer, texto_cuf[:self.line_width], align='center')
                        texto_cuf = texto_cuf[self.line_width:]
                
                self._print_separator(printer)
                
                # Información del cliente
                nombre = soup.find(id='nombre_mayusculas')
                documento = soup.find(id='numero_documento')
                cod_cliente = soup.find(id='cod_cliente')
                fecha = soup.find(id='fecha_emision')
                
                if nombre:
                    self._print_line(printer, f"Nombre/Razón Social: {nombre.text.strip()}", bold=True)
                if documento:
                    self._print_line(printer, f"NIT/CI/CEX: {documento.text.strip()}")
                if cod_cliente:
                    self._print_line(printer, f"Cod. Cliente: {cod_cliente.text.strip()}")
                if fecha:
                    self._print_line(printer, f"Fecha de Emisión: {fecha.text.strip()}")
                
                self._print_separator(printer)
                self._print_line(printer, "DETALLE", align='center', bold=True)
                self._print_separator(printer)
                
                # Productos
                for producto in soup.find_all('tr', class_='seccion_product-line'):
                    nombre_id = producto.find('strong')
                    unidad_id = producto.find('span', id=lambda x: x and x.endswith('_unidad'))
                    cantidad_id = producto.find('span', id=lambda x: x and x.endswith('_cantidad'))
                    monto_id = producto.find('td', class_='amount')
                    
                    if nombre_id:
                        self._print_line(printer, nombre_id.text.strip(), bold=True)
                    if unidad_id:
                        self._print_line(printer, unidad_id.text.strip())
                    if cantidad_id and monto_id:
                        cantidad_text = cantidad_id.text.strip()
                        monto_text = monto_id.text.strip()
                        spaces = self.line_width - len(cantidad_text) - len(monto_text)
                        self._print_line(printer, f"{cantidad_text}{' ' * spaces}{monto_text}")
                    self._print_separator(printer)
                
                # Totales
                totales_ids = ['subtotal', 'descuento_adicional', 'total', 'giftcard', 
                             'total_final', 'iva_base']
                totales_labels = {
                    'subtotal': 'Sub Total:',
                    'descuento_adicional': 'Descuento:',
                    'total': 'Total:',
                    'giftcard': 'Gift Card:',
                    'total_final': 'Monto a Pagar:',
                    'iva_base': 'Imp. Base Cred. Fiscal:'
                }
                
                for total_id in totales_ids:
                    elemento = soup.find(id=total_id)
                    if elemento:
                        label = totales_labels.get(total_id, total_id)
                        valor = elemento.text.strip()
                        spaces = self.line_width - len(label) - len(valor)
                        self._print_line(printer, f"{label}{' ' * spaces}{valor}", 
                                       bold=(total_id == 'total_final'))
                
                # Total en palabras
                total_palabras = soup.find(id='total_en_palabras_text')
                if total_palabras:
                    texto = f"Son: {total_palabras.text.strip()}"
                    while texto:
                        if len(texto) > self.line_width:
                            pos = texto[:self.line_width].rfind(' ')
                            if pos == -1:
                                pos = self.line_width
                            self._print_line(printer, texto[:pos])
                            texto = texto[pos:].strip()
                        else:
                            self._print_line(printer, texto)
                            break
                
                self._print_separator(printer)
                
                # Leyenda
                leyenda = soup.find(id='leyenda_text')
                if leyenda:
                    texto = leyenda.text.strip()
                    while texto:
                        if len(texto) > self.line_width:
                            pos = texto[:self.line_width].rfind(' ')
                            if pos == -1:
                                pos = self.line_width
                            self._print_line(printer, texto[:pos], align='center')
                            texto = texto[pos:].strip()
                        else:
                            self._print_line(printer, texto, align='center')
                            break
                
                printer.text("\n")  # Espacio antes del QR
                self._print_qr(printer, nit, cuf, numero_factura)
                printer.text("\n")  # Espacio después del QR
                
                printer.cut()
            
            self.logger.info("Impresión completada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante la impresión: {str(e)}")
            return False