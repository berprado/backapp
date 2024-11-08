import pdfkit
from business_logic import generate_qr, generate_file_name
import os
from printer_utils import print_invoice_escpos

# Función en export.py que se integra con la impresión ESC/POS
def imprimir_recibo(html_content, cuf, nit, numero_factura):
    """
    Genera el HTML de la factura y lo envía a la impresora con formato ESC/POS.
    
    Args:
    - html_content: Contenido HTML de la factura.
    - cuf: Código único de la factura.
    - nit: Número de identificación tributaria.
    - numero_factura: Número de la factura.
    """
    print("Generando la impresión con formato ESC/POS...")

    # Llamar a la función de impresión
    print_invoice_escpos(html_content, cuf, nit, numero_factura)


def imprimir_recibo1(html_content, cuf, nit, numero_factura):
    qr_base64 = generate_qr(nit, cuf, numero_factura)
    html_content = html_content.replace("{cuf}", cuf)
    html_content = html_content.replace("{codigo_qr}", f'<img src="data:image/png;base64,{qr_base64}" alt="Backstage" width="150"/>')

    # Guardar el HTML final para inspección
    with open("final_factura_test.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("HTML final guardado en final_factura_test.html")
    # Usar la nueva función para generar el nombre del archivo
    file_name = generate_file_name(numero_factura, cuf, "pdf")
    file_path = os.path.join("pdfs", file_name)
    guardar_recibo_como_pdf(html_content, file_path)
    
    return file_path, qr_base64



def guardar_recibo_como_pdf(html_content, file_path):
    """
    Generates a PDF from the provided HTML content for 80mm thermal paper using pdfkit.
    """
    options = {
        'page-width': '80mm',  # Set page width to 80mm
        #'page-height': 'auto',  # REMOVE this line, wkhtmltopdf calculates height automatically
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
        'encoding': 'UTF-8',
        'no-outline': None
    }

    try:
        pdfkit.from_string(html_content, file_path, options=options)
        print(f"PDF saved successfully as {file_path}")
    except Exception as e:
        print(f"Error saving the PDF: {e}")


