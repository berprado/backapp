from escpos.printer import Usb

def print_invoice_with_format(data):
    """
    Imprime la factura con formato basado en la estructura del HTML usando comandos ESC/POS.
    
    Args:
    - data: Diccionario con los datos de la factura (razón social, NIT, detalles de productos, etc.).
    """

    # Generar el texto con estructura similar al HTML
    invoice_text = f"""
\x1b\x45\x01{data['tipo_factura']}\x1b\x45\x00
\x1b\x45\x01{data['subtitulo']}\x1b\x45\x00
\x1b\x45\x01{data['razon_social']}\x1b\x45\x00
Sucursal: {data['sucursal']}
Punto de Venta: {data['punto_venta']}
Dirección: {data['direccion']}
Municipio: {data['municipio']}
Tel: {data['telefono']}
-----------------------------
\x1b\x45\x01NIT: {data['nit']}\x1b\x45\x00
Factura N°: {data['numero_factura']}
Fecha de Emisión: {data['fecha_emision']}
-----------------------------
\x1b\x45\x01DETALLE\x1b\x45\x00
-----------------------------
"""
    # Recorrer los items de la factura y formatear cada uno
    for item in data['items']:
        invoice_text += f"{item['descripcion']}\n{item['cantidad']} x {item['precio_unitario']} Bs\nSubtotal: {item['sub_total']} Bs\n-----------------------------\n"

    # Añadir totales y leyenda
    invoice_text += f"""
Sub Total: {data['monto_total']:.2f} Bs
Descuento: {data['descuento']:.2f} Bs
Total: {data['monto_total'] - data['descuento']:.2f} Bs
Son: {data['total_en_palabras']}
-----------------------------
\x1b\x45\x01{data['leyenda']}\x1b\x45\x00
-----------------------------
“Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido en una modalidad de facturación en línea”
"""

    # Conectar a la impresora y enviar el texto a imprimir
    printer = Usb(0x04B8, 0x0E15, 0, out_ep=0x01)  # Conectar a la impresora Epson TM-T20II con Vendor ID y Product ID
    printer.text(invoice_text)
    printer.cut()

# Definir los datos de la factura en el mismo formato de `generate_compact_html_invoice`
data = {
    'tipo_factura': 'FACTURA',
    'subtitulo': 'CON DERECHO A CRÉDITO FISCAL',
    'razon_social': 'Mi Empresa S.A.',
    'sucursal': 'CASA MATRIZ',
    'direccion': 'Av. Principal #123',
    'municipio': 'Ciudad',
    'telefono': '555-1234',
    'nit': '344096024',
    'numero_factura': '237',
    'fecha_emision': '2023-09-28',
    'items': [
        {'descripcion': 'Producto A', 'cantidad': '2', 'precio_unitario': '20.00', 'sub_total': '40.00'},
        {'descripcion': 'Producto B', 'cantidad': '3', 'precio_unitario': '20.00', 'sub_total': '60.00'},
    ],
    'monto_total': 100.00,
    'descuento': 0.00,
    'total_en_palabras': 'CIEN 00/100 BOLIVIANOS',
    'leyenda': 'Gracias por su compra.',
    'punto_venta': '001'
}

# Ejecutar la impresión con el formato ajustado
print_invoice_with_format(data)
