import pdfkit
import os

def imprimir_recibo(html_content, cuf):
    """
    Genera un archivo PDF a partir del contenido HTML proporcionado y lo guarda en el sistema.
    """
    file_path = os.path.join("pdfs", f"factura_{cuf}.pdf")
    guardar_recibo_como_pdf(html_content, file_path)
    return file_path
def guardar_recibo_como_pdf(html_content, file_path):
    """
    Genera un archivo PDF a partir del contenido HTML proporcionado usando pdfkit.
    """
    try:
        pdfkit.from_string(html_content, file_path)
        print(f"Recibo guardado exitosamente como {file_path}")
    except Exception as e:
        print(f"Error al guardar el recibo como PDF: {e}")

