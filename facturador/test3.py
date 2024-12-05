from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generar_factura_pdf(datos_factura, archivo_salida):
    c = canvas.Canvas(archivo_salida, pagesize=letter)
    
    # Título de la factura
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Factura")

    # Información básica
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"Cliente: {datos_factura['cliente']}")
    c.drawString(50, 700, f"Fecha: {datos_factura['fecha']}")
    c.drawString(50, 680, f"Número de factura: {datos_factura['numero_factura']}")

    # Detalles del pedido
    y = 650
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Detalles del pedido:")
    y -= 20
    c.setFont("Helvetica", 10)

    for item in datos_factura['items']:
        c.drawString(60, y, f"{item['cantidad']} x {item['producto']} @ {item['precio']} = {item['total']}")
        y -= 20
    
    # Total
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Total: {datos_factura['total']}")

    # Guardar archivo
    c.save()

# Datos de ejemplo
datos = {
    "cliente": "Juan Pérez",
    "fecha": "2024-12-04",
    "numero_factura": "000123",
    "items": [
        {"producto": "Producto A", "cantidad": 2, "precio": 50.00, "total": 100.00},
        {"producto": "Producto B", "cantidad": 1, "precio": 75.00, "total": 75.00},
    ],
    "total": 175.00
}

generar_factura_pdf(datos, "factura_ejemplo.pdf")
