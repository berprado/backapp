from escpos.printer import Usb
import logging

class ThermalPrinter:
    def __init__(self, vendor_id=0x04B8, product_id=0x0E15):
        self.vendor_id = vendor_id
        self.line_width = 57  # Ancho ajustado para fuente pequeña
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.line_width = 57  # Ancho ajustado para fuente pequeña
# Configura la impresora
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
p = Usb(0x04b8, 0x0202)
# Texto principal de la factura
p.set(align="center", font="a", width=2, height=2)  # Tamaño y alineación del texto
p.text("PACENA CHOPP 500ML\n")
p.text("---------------------\n")

# Texto detallado
p.set(align="left", font="a", width=1, height=1)
p.text("Detalle\n")
p.text("PACENA CHOPP 500ML     80.00\n")
p.text("VODKA 1825            70.00\n")
p.text("---------------------\n")
p.text("Sub Total:           150.00\n")
p.text("Descuento:            0.00\n")
p.text("Total:               150.00\n")
p.text("Gift Card:            0.00\n")
p.text("Monto a Pagar:       150.00\n")
p.text("Imp. Base Cred. Fiscal: 150.00\n")
p.text("\n")
p.text("Son: Ciento cincuenta 00/100 bolivianos.\n")
p.text("---------------------\n")
p.text("Nota: La interrupción del servicio...\n")

# Corta el papel
p.cut()
