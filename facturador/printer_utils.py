from escpos.printer import Usb
from bs4 import BeautifulSoup

def html_to_escpos_text(html_content):
    """
    Convierte el contenido HTML de la factura en un formato de texto listo para ESC/POS usando BeautifulSoup.
    
    Args:
    - html_content: Contenido HTML de la factura.
    
    Returns:
    - Texto formateado en formato ESC/POS listo para la impresora.
    """
    # Parsear el HTML con BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    invoice_text = ""

    # Extraer el título principal de la factura y aplicar formato de negrita
    titulo_factura = soup.find("strong")
    if titulo_factura:
        invoice_text += f"\x1b\x45\x01{titulo_factura.get_text()}\x1b\x45\x00\n"  # Negrita ESC/POS

    # Buscar todas las filas (<tr>) de la tabla y procesar cada celda (<td>)
    for row in soup.find_all("tr"):
        row_text = ""
        for cell in row.find_all("td"):
            cell_text = cell.get_text().strip()  # Obtener texto dentro de cada celda
            row_text += cell_text + "  "
        invoice_text += row_text.strip() + "\n"  # Añadir fila completa con salto de línea

    # Separar con línea divisoria al final de la tabla
    invoice_text += "-" * 32 + "\n"

    return invoice_text

def print_invoice_escpos(html_content):
    """
    Imprime la factura generada desde el HTML en la impresora Epson TM-T20II usando comandos ESC/POS.
    
    Args:
    - html_content: Contenido HTML de la factura.
    """
    # Convertir el HTML a formato de texto ESC/POS usando BeautifulSoup
    invoice_text = html_to_escpos_text(html_content)

    # Conectar a la impresora Epson TM-T20II (Vendor ID y Product ID específicos)
    printer = Usb(0x04B8, 0x0E15, 0, out_ep=0x01)

    # Imprimir el texto generado con formato ESC/POS
    printer.text(invoice_text)

    # Cortar el papel
    printer.cut()
    print("Factura impresa exitosamente en la Epson TM-T20II.")
