import base64
import os
from io import BytesIO
from PIL import Image
import qrcode

def generate_qr(nit, cuf, numero_factura):
    # Generar un código QR válido
    qr_data = f"NIT: {nit}, CUF: {cuf}, Número de Factura: {numero_factura}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    
    # Guardar la imagen en un buffer
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    
    # Convertir la imagen a base64
    qr_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return qr_base64

def guardar_recibo_como_pdf(html_content, file_path):
    # Esta función debe guardar el contenido HTML como un archivo PDF
    # Aquí deberías implementar la lógica para guardar el PDF
    pass

def imprimir_recibo(html_content, cuf, nit, numero_factura):
    """
    Genera un archivo PDF a partir del contenido HTML proporcionado, agrega el QR, y lo guarda en el sistema.
    También genera un archivo PNG del código QR.
    """
    # Generar el código QR en base64
    qr_base64 = generate_qr(nit, cuf, numero_factura)

    # Incluir el código QR en el contenido HTML
    html_content = html_content.replace("{{codigo_qr}}", f'<img src="data:image/png;base64,{qr_base64}" alt="QR Code" />')
    
    # Guardar el HTML en un archivo para verificación
    html_file_path = "factura_test.html"
    with open(html_file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML guardado en {html_file_path}")

    # Verificar si el archivo HTML se ha creado
    if os.path.exists(html_file_path):
        print(f"Archivo HTML creado correctamente en {html_file_path}")
    else:
        print(f"Error al crear el archivo HTML en {html_file_path}")

    # Decodificar el base64 y guardar la imagen como un archivo PNG
    qr_data = base64.b64decode(qr_base64)
    qr_image = Image.open(BytesIO(qr_data))
    qr_file_path = f"qr_{cuf}.png"
    qr_image.save(qr_file_path)
    print(f"QR guardado en {qr_file_path}")

    # Verificar si el archivo PNG se ha creado
    if os.path.exists(qr_file_path):
        print(f"Archivo PNG creado correctamente en {qr_file_path}")
    else:
        print(f"Error al crear el archivo PNG en {qr_file_path}")

    file_path = os.path.join("pdfs", f"factura_{cuf}.pdf")
    guardar_recibo_como_pdf(html_content, file_path)
    return file_path

# Ejemplo de uso
html_content = "<html><body><h1>Factura</h1><div>{{codigo_qr}}</div></body></html>"
cuf = "1234567890"
nit = "123456789"
numero_factura = "001"
imprimir_recibo(html_content, cuf, nit, numero_factura)