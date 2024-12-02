import pdfkit
from business_logic import generate_qr, generate_file_name
import os
import logging
from printer_utils import print_invoice_escpos

logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    filename='facturador.log'
)

def imprimir_recibo(html_content, cuf, nit, numero_factura):
    """
    Función principal que maneja la impresión y generación de PDF
    """
    try:
        # Generar QR y preparar HTML
        qr_base64 = generate_qr(nit, cuf, numero_factura)
        html_content = html_content.replace("{cuf}", cuf)
        html_content = html_content.replace("{codigo_qr}", 
            f'<img src="data:image/png;base64,{qr_base64}" alt="QR Code" width="150"/>')

        # Guardar HTML para referencia
        with open("final_factura_test.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        logging.info("HTML guardado como final_factura_test.html")

        # Generar PDF
        file_name = generate_file_name(numero_factura, cuf, "pdf")
        file_path = os.path.join("pdfs", file_name)
        guardar_recibo_como_pdf(html_content, file_path)

        # Imprimir en impresora térmica
        print_invoice_escpos(html_content, cuf, nit, numero_factura)
        
        return file_path, qr_base64

    except Exception as e:
        logging.error(f"Error en imprimir_recibo: {str(e)}")
        raise

def guardar_recibo_como_pdf(html_content, file_path):
    """
    Genera PDF optimizado para papel térmico de 80mm
    """
    options = {
        'page-width': '80mm',
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
        'encoding': 'UTF-8',
        'no-outline': None
    }

    try:
        pdfkit.from_string(html_content, file_path, options=options)
        logging.info(f"PDF guardado exitosamente en {file_path}")
    except Exception as e:
        logging.error(f"Error al guardar PDF: {e}")
        raise