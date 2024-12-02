# generate_pdf.py
import pdfkit
from ui_copy import generate_html_invoice  # Importar desde donde esté definida

def generate_pdf_from_invoice(subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura, metodo_de_pago=None, codigo_clasificador_metodo_pago=None, tipo_documento=None, codigo_clasificador_documento=None, numero_documento=None, complemento=None, email=None, telefono=None, ultimos_digitos_tarjeta=None):
    # Generar el HTML utilizando la función existente
    html_content = generate_html_invoice(
        subtotal=subtotal, 
        descuento_adicional=descuento_adicional, 
        monto_giftcard=monto_giftcard, 
        lineas_productos=lineas_productos, 
        nombre_cliente=nombre_cliente, 
        fecha_emision=fecha_emision, 
        numero_factura=numero_factura, 
        metodo_de_pago=metodo_de_pago, 
        codigo_clasificador_metodo_pago=codigo_clasificador_metodo_pago, 
        tipo_documento=tipo_documento, 
        codigo_clasificador_documento=codigo_clasificador_documento, 
        numero_documento=numero_documento, 
        complemento=complemento, 
        email=email, 
        telefono=telefono, 
        ultimos_digitos_tarjeta=ultimos_digitos_tarjeta
    )

    # Ruta de salida del PDF
    file_path = f'pdfs/factura_{numero_factura}.pdf'

    # Convertir el HTML a PDF
    pdfkit.from_string(html_content, file_path)

    return file_path
