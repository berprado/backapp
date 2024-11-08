from escpos.printer import Usb
from num2words import num2words
from string import Template

def numero_a_palabras_con_decimales(numero):
    parte_entera = int(numero)
    parte_decimal = int(round((numero - parte_entera) * 100))
    parte_entera_palabras = num2words(parte_entera, lang='es').capitalize()
    return f"{parte_entera_palabras} {parte_decimal:02d}/100 bolivianos."

def generate_invoice_text(data):
    template_str = '''
    ${tipo_factura}
    ${subtitulo}
    ${razon_social}
    Sucursal: ${sucursal}
    Punto de Venta: ${punto_venta}
    Dirección: ${direccion}
    Municipio: ${municipio}
    Tel: ${telefono}
    -----------------------------
    NIT: ${nit}
    Factura N°: ${numero_factura}
    Fecha de Emisión: ${fecha_emision}
    -----------------------------
    DETALLE
    -----------------------------
    $items
    -----------------------------
    Sub Total: ${sub_total} Bs
    Descuento: ${descuento} Bs
    Total: ${monto_total} Bs
    Son: ${total_en_palabras}
    -----------------------------
    ${leyenda}
    -----------------------------
    '''
    # Generar detalles de los productos
    items_str = ''
    for item in data['items']:
        items_str += f"{item['descripcion']}\n"
        items_str += f"{item['cantidad']} x {item['precio_unitario']} Bs\n"
        items_str += f"Subtotal: {item['sub_total']} Bs\n"
        items_str += "-----------------------------\n"

    template = Template(template_str)
    invoice_text = template.substitute(
        tipo_factura=data.get('tipo_factura', 'FACTURA'),
        subtitulo=data.get('subtitulo', 'CON DERECHO A CRÉDITO FISCAL'),
        razon_social=data['razon_social'],
        sucursal=data.get('sucursal', 'CASA MATRIZ'),
        punto_venta=data.get('punto_venta', 'N/A'),
        direccion=data.get('direccion', 'Dirección no disponible'),
        municipio=data.get('municipio', 'Municipio no disponible'),
        telefono=data.get('telefono', 'Teléfono no disponible'),
        nit=data['nit'],
        numero_factura=data['numero_factura'],
        fecha_emision=data['fecha_emision'],
        items=items_str,
        sub_total=f"{data['monto_total']:.2f}",
        descuento="0.00",
        monto_total=f"{data['monto_total']:.2f}",
        total_en_palabras=numero_a_palabras_con_decimales(data['monto_total']),
        leyenda=data.get('leyenda', '')
    )
    return invoice_text

def print_invoice(data):
    invoice_text = generate_invoice_text(data)
    printer = Usb(0x04B8, 0x0E15, 0, out_ep=0x01)
    printer.text(invoice_text)
    printer.cut()

# Datos de ejemplo
data = {
    'razon_social': 'Mi Empresa S.A.',
    'nit': '123456789',
    'numero_factura': '001',
    'fecha_emision': '01/01/2023 12:00 PM',
    'monto_total': 100.00,
    'items': [
        {'descripcion': 'Producto A', 'cantidad': '2', 'precio_unitario': '20.00', 'sub_total': '40.00'},
        {'descripcion': 'Producto B', 'cantidad': '3', 'precio_unitario': '20.00', 'sub_total': '60.00'},
    ],
    'punto_venta': '001',
    'leyenda': 'Gracias por su compra.',
    'tipo_factura': 'FACTURA',
    'subtitulo': 'CON DERECHO A CRÉDITO FISCAL',
    'sucursal': 'CASA MATRIZ',
    'direccion': 'Av. Principal #123',
    'municipio': 'Ciudad',
    'telefono': '555-1234'
}

print_invoice(data)
