from thermal_printer import ThermalPrinter
import logging

def imprimir_factura_html(html_file_path: str, nit: str, cuf: str, numero_factura: str):
    """Imprime una factura térmica a partir de un archivo HTML."""
    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()

        printer = ThermalPrinter()
        return printer.print_invoice(html_content, nit, cuf, numero_factura)
    except Exception as e:
        logging.error(f"❌ Error durante la impresión: {str(e)}")
        return False
