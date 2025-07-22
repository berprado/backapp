import os
import sys
# Agregar la ruta del directorio padre al path de Python si no está ya
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logger_config import get_logger, get_printer_logger
import traceback  # Añadir la importación de traceback
from datetime import datetime  # Importar datetime para la marca de tiempo

# Obtener loggers para este módulo
logger = get_logger()
printer_logger = get_printer_logger()

from escpos.printer import Usb
from facturador.data_models import FacturaProcesada  # IMPORTANTE
import logging
from contextlib import contextmanager

class ThermalPrinter:
    def __init__(self, vendor_id=0x04B8, product_id=0x0E15):
        printer_logger.info("Inicializando ThermalPrinter")
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.line_width = 64  # Ancho ajustado para fuente pequeña
        self.logger = self._setup_logger()
        self._printer = None  # NUEVO: Atributo para mantener la conexión

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

    def connect(self):
        """Se conecta a la impresora si no está ya conectada."""
        if self._printer is None:
            try:
                self.logger.info("Intentando conectar con la impresora USB...")
                self._printer = Usb(self.vendor_id, self.product_id)
                self.logger.info("Impresora conectada exitosamente.")
            except Exception as e:
                self.logger.error(f"Error al conectar con la impresora: {str(e)}")
                self._printer = None  # Asegurarse de que sigue siendo None si falla
                raise  # Lanzar la excepción para que el worker la maneje
        else:
            self.logger.info("Ya se encuentra conectado a la impresora.")

    def disconnect(self):
        """Cierra la conexión con la impresora."""
        if self._printer is not None:
            try:
                self.logger.info("Cerrando conexión con la impresora.")
                self._printer.close()
            except Exception as e:
                self.logger.error(f"Error al cerrar la conexión: {str(e)}")
            finally:
                self._printer = None

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

    def _print_line(self, printer, text, align='left', font='b', width=1, height=1, bold=False):
        """Imprime una línea de texto con los atributos especificados"""
        printer.set(align=align, font=font, width=width, height=height, bold=bold)
        printer.text(f"{text}\n")

    def _print_separator(self, printer, char='-'):
        """Imprime una línea separadora"""
        self._print_line(printer, char * self.line_width, font='b')

    def _print_qr(self, printer, url_qr: str, size=4):
        """Imprime el código QR de la factura usando la URL del objeto FacturaProcesada"""
        try:
            self.logger.info(f"Generando QR nativo con URL: {url_qr}")
            printer.set(align='center')
            printer.qr(url_qr, size=size, native=True)
            printer.text("\n")
            self.logger.info("QR impreso exitosamente.")
        except Exception as e:
            self.logger.error(f"Error al imprimir código QR: {str(e)}")
            raise

    def print_invoice(self, factura: FacturaProcesada) -> bool:
        """Imprime la factura usando una conexión existente."""
        try:
            if self._printer is None:
                raise Exception("La impresora no está conectada. Se debe llamar a connect() primero.")
            
            printer_logger.info(f"Imprimiendo factura {factura.numero_factura} en conexión existente.")
            
            # Encabezado
            self._print_line(self._printer, factura.tipo_factura, align='center', bold=True)
            self._print_line(self._printer, factura.subtitulo_factura, align='center')
            self._print_line(self._printer, factura.razon_social_emisor, align='center', bold=True)
            self._print_line(self._printer, factura.nombre_sucursal, align='center')
            self._print_line(self._printer, f"Punto de Venta: {factura.punto_venta}", align='center')
            
            # Dirección y contacto
            self._print_line(self._printer, factura.direccion_emisor, align='center')
            self._print_line(self._printer, factura.municipio_emisor, align='center')
            self._print_line(self._printer, factura.telefono_emisor, align='center')
            
            self._print_separator(self._printer)
            
            # Datos fiscales
            self._print_line(self._printer, f"NIT: {factura.nit_emisor}", align='center')
            self._print_line(self._printer, f"Factura N°: {factura.numero_factura}", align='center', bold=True)
            self._print_line(self._printer, "Código de Autorización:", align='center')
            # Lógica para cortar el CUF
            texto_cuf = factura.cuf
            while texto_cuf:
                self._print_line(self._printer, texto_cuf[:self.line_width], align='center', font='b')
                texto_cuf = texto_cuf[self.line_width:]
            
            self._print_separator(self._printer)
            
            # Datos del cliente
            self._print_line(self._printer, f"Fecha: {factura.fecha_emision}")
            self._print_line(self._printer, f"Nombre: {factura.nombre_cliente}")
            self._print_line(self._printer, f"NIT/CI: {factura.numero_documento}")

            self._print_separator(self._printer)
            self._print_line(self._printer, "DETALLE", align='center', bold=True)

            # Productos
            for producto in factura.lineas_productos:
                self._print_line(self._printer, f"{producto.codigo} - {producto.nombre}", bold=True)
                linea_detalle = f"{producto.cantidad:.2f} {producto.unidad} x {producto.precio:.2f}"
                linea_subtotal = f"{producto.sub_total:.2f}"
                espacios = self.line_width - len(linea_detalle) - len(linea_subtotal)
                if espacios < 1: espacios = 1
                self._print_line(self._printer, f"{linea_detalle}{' ' * espacios}{linea_subtotal}")

            self._print_separator(self._printer)

            # Totales
            self._print_line(self._printer, f"{'Sub Total:':<20}{factura.subtotal_factura:>10.2f}")
            self._print_line(self._printer, f"{'Descuento:':<20}{factura.descuento_adicional:>10.2f}")
            self._print_line(self._printer, f"{'Total:':<20}{factura.monto_total:>10.2f}", bold=True)
            self._print_line(self._printer, f"{'Monto a Pagar:':<20}{factura.monto_total_pagar:>10.2f}", bold=True)

            self._print_line(self._printer, f"Son: {factura.total_en_palabras}")
            
            self._print_separator(self._printer)
            
            # Pie de página
            self._print_line(self._printer, factura.leyenda, align='center')
            self._print_qr(self._printer, factura.url_qr)
            
            self._printer.cut()
            
            self.logger.info("Impresión desde objeto de datos completada.")
            return True
        except Exception as e:
            printer_logger.error(f"Error en print_invoice desde objeto: {e}", exc_info=True)
            # Si hay un error de impresión, es buena idea cerrar la conexión
            # para forzar una reconexión en el siguiente intento.
            self.disconnect()
            return False

    def process_and_print_invoice_legacy(self, html_content, nit, cuf, numero_factura):
        """
        MÉTODO LEGACY: Procesa el contenido HTML y realiza la impresión térmica.
        
        NOTA: Este método se mantiene solo para retrocompatibilidad.
        Se recomienda usar print_invoice(factura_obj) con objetos FacturaProcesada.

        Args:
            html_content (str): Contenido HTML de la factura.
            nit (str): NIT del emisor.
            cuf (str): Código Único de Facturación.
            numero_factura (str): Número de la factura.

        Returns:
            bool: True si la impresión fue exitosa, False en caso de error.
        """
        try:
            self.logger.warning("Usando método legacy process_and_print_invoice_legacy. Se recomienda migrar a print_invoice con FacturaProcesada.")
            
            # Para el método legacy, necesitaríamos parsear el HTML aquí
            # Por ahora, retornamos False y loggeamos que se debe usar el nuevo método
            self.logger.error("Método legacy no implementado completamente. Use print_invoice con objeto FacturaProcesada.")
            return False
            
        except Exception as e:
            self.logger.error(f"Error en el proceso de impresión legacy: {str(e)}")
            return False