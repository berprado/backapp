import pdfkit
import os
from business_logic import generate_qr  # Asegúrate de que esta función esté disponible

def imprimir_recibo(html_content, cuf, nit, numero_factura):
    """
    Genera un archivo PDF a partir del contenido HTML proporcionado, agrega el QR, y lo guarda en el sistema.
    """
    # Generar el código QR en base64
    qr_base64 = generate_qr(nit, cuf, numero_factura)

    # Incluir el código QR en el contenido HTML
    html_content = html_content.replace("{{codigo_qr}}", f'<img src="data:image/png;base64,{qr_base64}" alt="QR Code" />')
    
    # Guardar el HTML en un archivo para verificación
    with open("factura_test.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("HTML guardado en factura_test.html")

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
