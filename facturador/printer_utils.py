from escpos.printer import Usb
from bs4 import BeautifulSoup
import logging

# Create a custom logger for printing
printer_logger = logging.getLogger('printer')
printer_logger.setLevel(logging.DEBUG)

# Create handlers
file_handler = logging.FileHandler('printer_debug.log')
console_handler = logging.StreamHandler()

# Create formatters and add it to handlers
log_format = '%(asctime)s - %(levelname)s - %(message)s'
file_handler.setFormatter(logging.Formatter(log_format))
console_handler.setFormatter(logging.Formatter(log_format))

# Add handlers to the logger
printer_logger.addHandler(file_handler)
printer_logger.addHandler(console_handler)

def print_invoice_escpos(html_content, cuf, nit, numero_factura):
    """
    Imprime la factura con manejo mejorado de errores y logging.
    
    Args:
        html_content (str): Contenido HTML de la factura
        cuf (str): Código CUF
        nit (str): NIT de la empresa
        numero_factura (str): Número de factura
    
    Returns:
        bool: True si la impresión fue exitosa
    """
    try:
        logging.info(f"Iniciando impresión de factura #{numero_factura}")
        
        # Convert HTML to text format
        logging.info("Convirtiendo HTML a formato de impresión")
        invoice_text = html_to_escpos_text(html_content)
        logging.info("Conversión completada")
        
        # Add header info
        invoice_text = "\n".join([
            "=" * 48,
            "FACTURA",
            "=" * 48,
            invoice_text,
            "-" * 48,
            f"CUF: {cuf}",
            f"NIT: {nit}",
            f"Factura No: {numero_factura}",
            "=" * 48
        ])
        
        # Initialize printer
        logging.info("Inicializando conexión con la impresora")
        printer = Usb(0x04B8, 0x0E15, 0, out_ep=0x01)
        
        # Configurar impresora para papel de 80mm
        printer.set(
            font='a',
            height=1,
            width=1,
            density=8,
            smooth=True,
            align='center'
        )
        
        # Print content
        logging.info("Enviando datos a la impresora")
        printer.text(invoice_text)
        printer.cut()
        
        logging.info("Impresión completada exitosamente")
        return True
        
    except Exception as e:
        error_msg = f"Error al imprimir la factura: {str(e)}"
        logging.error(error_msg)
        raise Exception(error_msg)

def html_to_escpos_text(html_content):
    """
    Convierte el contenido HTML en formato de texto para impresora térmica de 80mm
    (aproximadamente 48 caracteres por línea)
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        printer_text = []
        
        # Constantes de formato
        LINE_WIDTH = 48
        SEPARATOR = "=" * LINE_WIDTH
        
        # Encabezado centrado y en negrita
        printer_text.append("\x1b\x61\x01")  # Centrar texto
        printer_text.append("\x1b\x45\x01")  # Iniciar negrita
        printer_text.append("FACTURA")
        printer_text.append("(CON DERECHO A CREDITO FISCAL)")
        printer_text.append(SEPARATOR)
        printer_text.append("\x1b\x45\x00")  # Finalizar negrita
        
        # Información de la empresa
        printer_text.append("BOLIVIAN FOODS & DRINKS S.R.L.")
        printer_text.append("CASA MATRIZ")
        printer_text.append("Punttito de Venta: 0")
        printer_text.append(SEPARATOR)
        
        # Dirección y contacto - Ajustado para 48 caracteres
        printer_text.append("\x1b\x61\x00")  # Alinear a la izquierda
        printer_text.append("AVENIDA MONTENEGRO NRO. SN EDIF.: ARACELY PISO: PB")
        printer_text.append("DEPTO.: BLOQUE E7")
        printer_text.append("ZONA/BARRIO: SAN MIGUEL")
        printer_text.append("LA PAZ")
        printer_text.append("Tel. 65560514")
        printer_text.append(SEPARATOR)
        
        # Información fiscal con formato ajustado
        nit_section = soup.find('td', text=lambda t: t and 'NIT' in t)
        if nit_section:
            printer_text.append("\x1b\x45\x01NIT:\x1b\x45\x00 ".ljust(15) + 
                              nit_section.find_next('td').get_text().strip())
            
        factura_section = soup.find('td', text=lambda t: t and 'Factura N°' in t)
        if factura_section:
            printer_text.append("\x1b\x45\x01Factura N°:\x1b\x45\x00 ".ljust(15) + 
                              factura_section.find_next('td').get_text().strip())
        
        printer_text.append(SEPARATOR)
        
        # Detalles de productos con formato tabular
        printer_text.append("\x1b\x45\x01DETALLE DE PRODUCTOS\x1b\x45\x00")
        productos = soup.find_all('tr', {'class': 'tg-1kjo'})
        for producto in productos:
            cells = producto.find_all('td')
            if len(cells) >= 7:
                # Formato para productos ajustado a 48 caracteres
                cod_prod = cells[0].get_text().strip()
                desc_prod = cells[3].get_text().strip()
                cant = cells[1].get_text().strip()
                precio = cells[4].get_text().strip()
                total = cells[6].get_text().strip()
                
                printer_text.append(f"\x1b\x45\x01{cod_prod} - {desc_prod}\x1b\x45\x00")
                printer_text.append(f"Cant: {cant}  Precio: {precio}  Total: {total}")
                printer_text.append("-" * LINE_WIDTH)
        
        # Totales alineados a la derecha
        printer_text.append("\x1b\x61\x02")  # Alinear a la derecha
        for total_label in ['Sub Total:', 'Descuento:', 'Total:', 'Gift Card:', 'Monto a Pagar:', 
                          'Imp. Base Cred. Fiscal:']:
            total_element = soup.find('td', text=total_label)
            if total_element:
                valor = total_element.find_next('td').get_text().strip()
                printer_text.append(f"{total_label.ljust(20)} {valor.rjust(10)}")
        
        printer_text.append(SEPARATOR)
        
        # Pie de factura centrado
        printer_text.append("\x1b\x61\x01")  # Centrar texto
        printer_text.append("ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS,")
        printer_text.append("EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE")
        printer_text.append("ACUERDO A LEY")
        printer_text.append(SEPARATOR)
        
        # Ley y aviso final
        leyenda = soup.find('span', text=lambda t: t and 'Ley N°' in t)
        if leyenda:
            printer_text.append(leyenda.get_text())
        
        printer_text.append('"Este documento es la Representación Gráfica de un')
        printer_text.append('Documento Fiscal Digital emitido en una modalidad')
        printer_text.append('de facturación en línea"')
        
        return "\n".join(printer_text)
        
    except Exception as e:
        logging.error(f"Error al convertir HTML a texto ESC/POS: {str(e)}")
        raise