import os
import xml.etree.ElementTree as ET
from num2words import num2words
from dotenv import load_dotenv
from datetime import datetime
from escpos.printer import Usb  # Dependiendo del tipo de impresora, puede ser Network, File, etc.

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Función para convertir números a palabras con decimales
def numero_a_palabras_con_decimales(numero):
    parte_entera = int(numero)
    parte_decimal = int(round((numero - parte_entera) * 100))
    parte_entera_palabras = num2words(parte_entera, lang='es').capitalize()
    return f"{parte_entera_palabras} {parte_decimal:02d}/100 bolivianos."

# Parse XML file
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
        # Intentar con fracciones de segundo
        fecha_emision_dt = datetime.strptime(fecha_emision, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        # Si falla, intentar sin fracciones de segundo
        fecha_emision_dt = datetime.strptime(fecha_emision, '%Y-%m-%dT%H:%M:%S')
    
    fecha_emision_formateada = fecha_emision_dt.strftime('%d/%m/%Y %I:%M %p')
    monto_total = float(header.find('montoTotal').text)
    punto_venta = header.find('codigoPuntoVenta').text if header.find('codigoPuntoVenta') is not None else 'N/A'
    leyenda = header.find('leyenda').text if header.find('leyenda') is not None else 'N/A'
    
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
        'leyenda': leyenda
    }

# Función para generar la factura en texto para impresión ESC/POS
def generate_invoice_escpos(data):
    # Cargar variables adicionales desde el archivo .env
    direccion = os.getenv('DIRECCION', 'Dirección no disponible')
    municipio = os.getenv('MUNICIPIO', 'Municipio no disponible')
    telefono_empresa = os.getenv('TELEFONO', 'Teléfono no disponible')
    tipo_de_factura = os.getenv('DESCRIPCION_TIPO_FACTURA', 'FACTURA')
    subtitulo = os.getenv('SUBTITULO', 'CON DERECHO A CRÉDITO FISCAL')
    sucursal = os.getenv('NOMBRE_SUCURSAL', 'CASA MATRIZ')

    # Convertir el monto total a palabras
    total_en_palabras = numero_a_palabras_con_decimales(data['monto_total'])

    # Iniciar la impresora
    # Configuración de la impresora (debes ajustar los valores de vendor_id y product_id según tu impresora)
    printer = Usb(0x04B8, 0x0E15)  # Ejemplo para impresora Epson. Cambia los valores según tu impresora

    # Encabezado
    printer.set(align="center", bold=True, font="a")
    printer.text(f"{tipo_de_factura}\n")
    printer.text(f"{subtitulo}\n")
    printer.text(f"{data['razon_social']}\n")
    printer.text(f"{sucursal}\n")
    printer.text(f"Punto de Venta: {data['punto_venta']}\n")
    printer.text(f"{direccion}\n")
    printer.text(f"{municipio}\n")
    printer.text(f"Tel: {telefono_empresa}\n")
    printer.text(f"-----------------------------\n")

    # Información de la factura
    printer.set(align="left", bold=False, font="b")
    printer.text(f"NIT: {data['nit']}\n")
    printer.text(f"Factura N°: {data['numero_factura']}\n")
    printer.text(f"Fecha de Emisión: {data['fecha_emision']}\n")
    printer.text(f"-----------------------------\n")
    
    # Detalles de los productos
    printer.set(align="left", font="b")
    printer.text(f"DETALLE\n")
    printer.text(f"-----------------------------\n")
    for item in data['items']:
        printer.text(f"{item['descripcion']}\n")
        printer.text(f"{item['cantidad']} x {item['precio_unitario']} Bs\n")
        printer.text(f"Subtotal: {item['sub_total']} Bs\n")
        printer.text(f"-----------------------------\n")

    # Totales
    printer.text(f"Sub Total: {data['monto_total']:.2f} Bs\n")
    printer.text(f"Descuento: 0.00 Bs\n")
    printer.text(f"Total: {data['monto_total']:.2f} Bs\n")
    printer.text(f"Son: {total_en_palabras}\n")
    printer.text(f"-----------------------------\n")

    # Leyenda
    printer.text(f"{data['leyenda']}\n")
    printer.text(f"-----------------------------\n")
    
    # Corte del papel y finalizar
    printer.cut()

# Función principal para generar e imprimir la factura
def create_invoice(xml_file):
    data = parse_xml(xml_file)
    generate_invoice_escpos(data)

# Ejemplo de uso
create_invoice('C:/Users/Bernardo/Desktop/backapp/facturador/xmls/factura_172_178B43EFDB95D55D3DC4FD7604C220803B82A2F3822813CAF7B209E74_.xml')
