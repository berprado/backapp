import pdfkit
from business_logic import generate_qr, generate_file_name
import os

def imprimir_recibo(html_content, cuf, nit, numero_factura):
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
    Genera un archivo PDF a partir del contenido HTML proporcionado usando pdfkit.
    """
    try:
        pdfkit.from_string(html_content, file_path)
        print(f"Factura guardada exitosamente como {file_path}")
    except Exception as e:
        print(f"Error al guardar la factura como PDF: {e}")
