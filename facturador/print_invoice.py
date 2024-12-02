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
