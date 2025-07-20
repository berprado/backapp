---
applyTo: '**'
---

### **Paso 4: Refactorizar `invoice_templates.py` y `thermal_printer.py`**

Este es el paso final de la refactorización del código. Aquí es donde todo el trabajo previo dará sus frutos y la lógica se conectará por completo.

#### **Parte A: Modificar `invoice_templates.py`**

**Tu Tarea:**

1.  Abre el archivo `invoice_templates.py`.
2.  Asegúrate de que importa `FacturaProcesada`: `from facturador.data_models import FacturaProcesada`.
3.  **Reemplaza por completo** la función `generate_html_invoice` (la que ahora usamos como `generate_html_for_pdf`) con esta nueva versión que acepta el objeto. La parte más importante es cambiar los placeholders para que accedan a los atributos del objeto `factura`.

**Código para `generate_html_invoice` en `invoice_templates.py`:**

```python
# Asumiendo que esta función está en invoice_templates.py

from facturador.data_models import FacturaProcesada # Asegúrate de que esta importación esté
from business_logic import generate_qr # Asumiendo que genera base64

def generate_html_invoice(factura: FacturaProcesada) -> str:
    """
    Genera el HTML completo para el PDF a partir de un objeto FacturaProcesada.
    """
    # Generamos el QR a partir de la URL que ya tenemos en nuestro objeto
    qr_base64 = generate_qr(factura.nit_emisor, factura.cuf, factura.numero_factura)
    qr_code_html = f'<img src="data:image/png;base64,{qr_base64}" alt="Codigo QR" style="width:100px;height:100px;">'

    # Construimos el detalle de los productos
    lineas_html = ""
    for linea in factura.lineas_productos:
        lineas_html += f"""
            <tr class="seccion_product-line">
                <td class="detail" id="detalle_{linea.codigo}_info">
                    <strong id="detalle_{linea.codigo}_nombre">{linea.codigo} - {linea.nombre}</strong><br>
                    <span id="detalle_{linea.codigo}_unidad">{linea.unidad}</span><br>
                    <span id="detalle_{linea.codigo}_cantidad">{linea.cantidad:.2f} x {linea.precio:.2f} {'- Desc: {:.2f}'.format(linea.montoDescuento) if linea.montoDescuento > 0 else ''}</span>
                </td>
                <td class="amount" id="detalle_{linea.codigo}_monto">
                    {linea.sub_total:.2f}
                </td>
            </tr>
        """

    # Plantilla principal
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Factura # {factura.numero_factura}</title>
        <style> /* Tu CSS aquí... */ </style>
    </head>
    <body>
        <table>
            <!-- Encabezado -->
            <tr><th class="header" colspan="2"><span id="tipo_factura_text">{factura.tipo_factura}</span><br><span id="subtitulo_text">{factura.subtitulo_factura}</span></th></tr>
            <tr><td class="header" colspan="2"><span id="razon_social">{factura.razon_social_emisor}</span><br>...</td></tr>
            <!-- ... Adapta todos los campos para usar el objeto 'factura' ... -->
            <tr><th class="header" colspan="2">Código de Autorización:<br><span class="header1" id="cuf">{factura.cuf}</span></th></tr>
            
            <!-- Productos -->
            {lineas_html}

            <!-- Totales -->
            <tr><td class="detail">Sub Total:</td><td class="amount" id="subtotal">{factura.subtotal_factura:.2f}</td></tr>
            <tr><td class="detail">Total:</td><td class="amount" id="total">{factura.monto_total:.2f}</td></tr>
            <!-- ... Resto de totales ... -->
            <tr><td colspan="2" class="header" id="total_en_palabras">Son: <span id="total_en_palabras_text">{factura.total_en_palabras}</span></td></tr>

            <!-- Pie de página y QR -->
            <tr><th colspan="2" class="header"><span id="leyenda_text">{factura.leyenda}</span></th></tr>
            <tr><td colspan="2" style="text-align:center;">{qr_code_html}</td></tr>
        </table>
    </body>
    </html>
    """
    return html_content
```
*Nota: Tendrás que completar la adaptación de todos los campos en la plantilla, pero te he dejado los ejemplos más importantes.*

#### **Parte B: Modificar `thermal_printer.py`**

**Tu Tarea:**

1.  Abre `thermal_printer.py`.
2.  **Elimina `from bs4 import BeautifulSoup`**.
3.  Asegúrate de que importa `FacturaProcesada`: `from facturador.data_models import FacturaProcesada`.
4.  Reemplaza el método `print_invoice` con esta nueva versión que no usa HTML.

**Código para `print_invoice` en `thermal_printer.py`:**

```python
# En thermal_printer.py
from facturador.data_models import FacturaProcesada # IMPORTANTE

class ThermalPrinter:
    # ... __init__ y otros métodos auxiliares se mantienen ...

    def _print_qr(self, printer, url_qr: str, size=4):
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
        """Imprime la factura directamente desde el objeto FacturaProcesada."""
        try:
            printer_logger.info(f"Imprimiendo factura {factura.numero_factura} desde objeto de datos.")
            
            with self.printer_connection() as printer:
                # Encabezado
                self._print_line(printer, factura.tipo_factura, align='center', bold=True)
                self._print_line(printer, factura.subtitulo_factura, align='center')
                self._print_line(printer, factura.razon_social_emisor, align='center', bold=True)
                self._print_line(printer, factura.nombre_sucursal, align='center')
                # ... resto de datos del emisor ...
                self._print_separator(printer)
                
                # Datos fiscales
                self._print_line(printer, f"NIT: {factura.nit_emisor}", align='center')
                self._print_line(printer, f"Factura N°: {factura.numero_factura}", align='center', bold=True)
                self._print_line(printer, "Código de Autorización:", align='center')
                # Lógica para cortar el CUF
                texto_cuf = factura.cuf
                while texto_cuf:
                    self._print_line(printer, texto_cuf[:self.line_width], align='center', font='b')
                    texto_cuf = texto_cuf[self.line_width:]
                
                self._print_separator(printer)
                
                # Datos del cliente
                self._print_line(printer, f"Fecha: {factura.fecha_emision}")
                self._print_line(printer, f"Nombre: {factura.nombre_cliente}")
                self._print_line(printer, f"NIT/CI: {factura.numero_documento}")

                self._print_separator(printer)
                self._print_line(printer, "DETALLE", align='center', bold=True)

                # Productos
                for producto in factura.lineas_productos:
                    self._print_line(printer, f"{producto.codigo} {producto.nombre}", bold=True)
                    linea_detalle = f"{producto.cantidad:.2f} {producto.unidad} x {producto.precio:.2f}"
                    linea_subtotal = f"{producto.sub_total:.2f}"
                    espacios = self.line_width - len(linea_detalle) - len(linea_subtotal)
                    if espacios < 1: espacios = 1
                    self._print_line(printer, f"{linea_detalle}{' ' * espacios}{linea_subtotal}")

                self._print_separator(printer)

                # Totales
                self._print_line(printer, f"{'Sub Total:':<20}{factura.subtotal_factura:>10.2f}")
                self._print_line(printer, f"{'Descuento:':<20}{factura.descuento_adicional:>10.2f}")
                self._print_line(printer, f"{'Total:':<20}{factura.monto_total:>10.2f}", bold=True)
                self._print_line(printer, f"{'Monto a Pagar:':<20}{factura.monto_total_pagar:>10.2f}", bold=True)

                self._print_line(printer, f"Son: {factura.total_en_palabras}")
                
                self._print_separator(printer)
                
                # Pie de página
                self._print_line(printer, factura.leyenda, align='center')
                self._print_qr(printer, factura.url_qr)
                
                printer.cut()
            
            self.logger.info("Impresión desde objeto de datos completada.")
            return True
        except Exception as e:
            printer_logger.error(f"Error en print_invoice desde objeto: {e}", exc_info=True)
