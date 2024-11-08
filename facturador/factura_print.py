import os
import sys
import xml.etree.ElementTree as ET
from num2words import num2words
from dotenv import load_dotenv
from datetime import datetime
from escpos.printer import Usb  # Dependiendo del tipo de impresora, puede ser Network, File, etc.
from string import Template

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Función para convertir números a palabras con decimales
def numero_a_palabras_con_decimales(numero):
    parte_entera = int(numero)
    parte_decimal = int(round((numero - parte_entera) * 100))
    parte_entera_palabras = num2words(parte_entera, lang='es').capitalize()
    return f"{parte_entera_palabras} {parte_decimal:02d}/100 bolivianos."

# Función para generar el texto de la factura en formato ESC/POS
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

# Función para imprimir la factura en la impresora ESC/POS
def print_invoice(data):
    invoice_text = generate_invoice_text(data)
    printer = Usb(0x04B8, 0x0E15, 0, out_ep=0x01)
    printer.text(invoice_text)
    printer.cut()

# Parsear el archivo XML para extraer los datos
def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Extraer datos desde el XML
    header = root.find('cabecera')
    razon_social = header.find('razonSocialEmisor').text
    nit = header.find('nitEmisor').text
    numero_factura = header.find('numeroFactura').text
    fecha_emision = header.find('fechaEmision').text
    try:
        fecha_emision_dt = datetime.strptime(fecha_emision, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        fecha_emision_dt = datetime.strptime(fecha_emision, '%Y-%m-%dT%H:%M:%S')
    
    fecha_emision_formateada = fecha_emision_dt.strftime('%d/%m/%Y %I:%M %p')
    monto_total = float(header.find('montoTotal').text)
    punto_venta = header.find('codigoPuntoVenta').text if header.find('codigoPuntoVenta') is not None else 'N/A'
    leyenda = header.find('leyenda').text if header.find('leyenda') is not None else 'N/A'
    nombre_cliente = header.find('nombreRazonSocial').text if header.find('nombreRazonSocial') is not None else 'N/A'
    numero_documento = header.find('numeroDocumento').text if header.find('numeroDocumento') is not None else 'N/A'
    
    # Extraer detalles de los productos
    items = []
    for detalle in root.findall('detalle'):
        descripcion = detalle.find('descripcion').text
        cantidad = detalle.find('cantidad').text
        precio_unitario = detalle.find('precioUnitario').text
        sub_total = detalle.find('subTotal').text
        items.append({
            'descripcion': descripcion,
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'sub_total': sub_total
        })
    
    return {
        'razon_social': razon_social,
        'nit': nit,
        'numero_factura': numero_factura,
        'fecha_emision': fecha_emision_formateada,
        'monto_total': monto_total,
        'items': items,
        'punto_venta': punto_venta,
        'leyenda': leyenda,
        'nombre_cliente': nombre_cliente,
        'numero_documento': numero_documento
    }

# Generar la factura e imprimirla usando los datos del XML
def generate_invoice_escpos(data):
    print_invoice(data)

# Función principal para generar e imprimir la factura
def create_invoice(xml_file):
    data = parse_xml(xml_file)
    generate_invoice_escpos(data)

# Punto de entrada del script
def main():
    if len(sys.argv) != 2:
        print("Uso: python factura_print.py <ruta_xml>")
        sys.exit(1)

    xml_file = sys.argv[1]
    create_invoice(xml_file)

if __name__ == "__main__":
    main()
