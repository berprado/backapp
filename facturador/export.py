import pdfkit
from business_logic import generate_qr, generate_file_name
import os
import logging
from printer_utils import print_invoice_escpos

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    filename='logs/facturador.log'
)

def imprimir_recibo(html_content, cuf, nit, numero_factura):
    """
    Función principal que maneja la impresión y generación de PDF
    """
    try:
        logging.info(f"Iniciando proceso de factura {numero_factura}")
        
        # Generar QR
        qr_base64 = generate_qr(nit, cuf, numero_factura)
        
        # Preparar HTML con QR y CUF
        html_content = html_content.replace("{cuf}", cuf)
        html_content = html_content.replace("{codigo_qr}", 
            f'<img src="data:image/png;base64,{qr_base64}" alt="QR Code" width="150"/>')

        # Guardar HTML temporal
        html_path = "final_factura_test.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logging.info(f"HTML guardado en {html_path}")

        # Generar nombre y ruta del PDF
        file_name = generate_file_name(numero_factura, cuf, "pdf")
        pdf_path = os.path.join("pdfs", file_name)
        
        # Guardar PDF
        guardar_recibo_como_pdf(html_content, pdf_path)
        logging.info(f"PDF guardado en {pdf_path}")

        # Imprimir en impresora térmica
        print_invoice_escpos(html_content, cuf, nit, numero_factura)
        logging.info("Impresión térmica completada")
        
        return pdf_path, qr_base64

    except Exception as e:
        logging.error(f"Error en imprimir_recibo: {str(e)}")
        raise

def imprimir_recibo1(html_content, cuf, nit, numero_factura):
    """
    Función que solo genera PDF y QR, sin impresión térmica
    """
    try:
        # Generar QR
        qr_base64 = generate_qr(nit, cuf, numero_factura)
        
        # Preparar HTML con QR y CUF
        html_content = html_content.replace("{cuf}", cuf)
        html_content = html_content.replace("{codigo_qr}", 
            f'<img src="data:image/png;base64,{qr_base64}" alt="QR Code" width="150"/>')

        # Guardar HTML temporal
        html_path = "final_factura_test.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logging.info(f"HTML guardado en {html_path}")

        # Generar PDF
        file_name = generate_file_name(numero_factura, cuf, "pdf")
        pdf_path = os.path.join("pdfs", file_name)
        guardar_recibo_como_pdf(html_content, pdf_path)
        logging.info(f"PDF guardado en {pdf_path}")
        
        return pdf_path, qr_base64

    except Exception as e:
        logging.error(f"Error en imprimir_recibo1: {str(e)}")
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
        error_msg = f"Error al guardar PDF: {str(e)}"
        logging.error(error_msg)
        raise Exception(error_msg)