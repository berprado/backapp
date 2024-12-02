from escpos.printer import Usb
from pdf2image import convert_from_path

def print_pdf_as_image(pdf_path):
    """
    Convierte cada página del PDF a una imagen y la imprime.
    """
    # Crear conexión con la impresora
    printer = Usb(0x04B8, 0x0E15, 0, out_ep=0x01)  # Vendor ID y Product ID para Epson TM-T20II

    # Convertir PDF a imágenes
    images = convert_from_path(pdf_path)
    for img in images:
        # Imprimir imagen
        printer.image(img)
    
    printer.cut()
    print("Impresión completada.")

# Ruta al archivo PDF
pdf_path = "factura_325_178B43EFDB960B3F2395E8FCEFCCC35876F58C69269C5839CBD349E74_.pdf"

# Ejecutar la impresión
print_pdf_as_image(pdf_path)
