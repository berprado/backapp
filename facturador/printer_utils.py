# printer_utils.py
from escpos.printer import Usb
from bs4 import BeautifulSoup
import streamlit as st
import logging
import re

# Configuración del logger
printer_logger = logging.getLogger('printer_utils')
printer_logger.setLevel(logging.DEBUG)

if not printer_logger.handlers:
    # Crear manejadores
    file_handler = logging.FileHandler('printer_debug.log')
    console_handler = logging.StreamHandler()

    # Crear formato
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Agregar manejadores al logger
    printer_logger.addHandler(file_handler)
    printer_logger.addHandler(console_handler)

def verificar_impresora():
    """
    Verifica la conexión con la impresora térmica
    Returns:
        bool: True si la impresora está conectada y lista
    """
    try:
        printer = Usb(0x04B8, 0x0E15, 0, out_ep=0x01)
        printer_logger.info("Impresora verificada y conectada correctamente")
        return True
    except Exception as e:
        error_msg = f"Error al conectar con la impresora: {str(e)}"
        printer_logger.error(error_msg)
        st.error(error_msg)
        return False

def guardar_factura_actual(html_content, cuf, nit, numero_factura):
    """
    Guarda los datos de la factura actual en el session_state
    """
    st.session_state['factura_actual'] = {
        'html_content': html_content,
        'cuf': cuf,
        'nit': nit,
        'numero_factura': numero_factura,
        'impresa': False
    }
    printer_logger.info(f"Factura {numero_factura} guardada en session_state")

def obtener_factura_actual():
    """
    Obtiene los datos de la factura actual del session_state
    Returns:
        dict: Datos de la factura o None si no hay factura
    """
    return st.session_state.get('factura_actual')

def marcar_factura_impresa():
    """
    Marca la factura actual como impresa en el session_state
    """
    if 'factura_actual' in st.session_state:
        st.session_state['factura_actual']['impresa'] = True
        printer_logger.info(f"Factura {st.session_state['factura_actual']['numero_factura']} marcada como impresa")

def html_to_escpos_text(html_content):
    """
    Convierte el contenido HTML en formato de texto para impresora térmica de 80mm
    (aproximadamente 48 caracteres por línea)
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        printer_text = []
        
        LINE_WIDTH = 48
        SEPARATOR = "-" * LINE_WIDTH

        # Encabezado
        printer_text.extend([
            "\x1b\x61\x01",  # Centrar texto
            "\x1b\x21\x00",  # Tamaño normal
            "\x1b\x45\x01",  # Iniciar negrita
            "FACTURA",
            "(CON DERECHO A CREDITO FISCAL)",
            "\x1b\x45\x00",  # Finalizar negrita
            SEPARATOR
        ])
        
        # Información de la empresa
        empresa_info = soup.find('td', {'class': 'tg-n17z', 'colspan': '4'})
        if empresa_info:
            for line in empresa_info.stripped_strings:
                printer_text.append(line)
        printer_text.append(SEPARATOR)
        
        # Información fiscal y datos del cliente
        fiscal_info = [
            ('NIT', 'NIT'),
            ('Factura', 'Factura N°'),
            ('Código de Autorización', 'CUF'),
            ('Nombre/Razón Social:', 'Cliente'),
            ('NIT/CI/CEX:', 'Doc. Identidad'),
            ('Fecha de Emisión:', 'Fecha')
        ]

        for search_text, label in fiscal_info:
            element = soup.find('td', string=re.compile(search_text, re.IGNORECASE))
            if element and element.find_next('td'):
                value = element.find_next('td').get_text().strip()
                printer_text.append(f"{label}: {value}")
        
        printer_text.append(SEPARATOR)
        
        # Detalles de productos
        printer_text.extend([
            "DETALLE DE PRODUCTOS",
            SEPARATOR
        ])
        
        productos = soup.find_all('tr', {'class': 'tg-1kjo'})
        for producto in productos:
            cells = producto.find_all('td')
            if len(cells) >= 7:
                printer_text.extend([
                    f"{cells[0].get_text().strip()} - {cells[3].get_text().strip()}",
                    f"Cant: {cells[1].get_text().strip()} x {cells[4].get_text().strip()}",
                    f"Total: {cells[6].get_text().strip()}",
                    "-" * 24
                ])
        
        # Totales
        totales_labels = [
            'Sub Total:', 'Descuento:', 'Total:', 
            'Gift Card:', 'Monto a Pagar:', 'Imp. Base Cred. Fiscal:'
        ]
        for label in totales_labels:
            element = soup.find('td', string=re.compile(label, re.IGNORECASE))
            if element and element.find_next('td'):
                valor = element.find_next('td').get_text().strip()
                printer_text.append(f"{label.ljust(25)}{valor.rjust(10)}")
        
        printer_text.append(SEPARATOR)
        
        # Son
        son_element = soup.find('td', string=re.compile('Son:', re.IGNORECASE))
        if son_element:
            printer_text.append(son_element.get_text().strip())
        
        printer_text.append(SEPARATOR)
        
        # Pie de factura
        printer_text.extend([
            "ESTA FACTURA CONTRIBUYE AL DESARROLLO",
            "DEL PAIS, EL USO ILICITO SERA",
            "SANCIONADO PENALMENTE DE ACUERDO A LEY"
        ])
        
        return "\n".join(printer_text)
        
    except Exception as e:
        printer_logger.error(f"Error al convertir HTML a texto ESC/POS: {str(e)}")
        raise

def print_invoice_escpos(html_content, cuf, nit, numero_factura):
    """
    Imprime la factura usando la impresora térmica
    """
    try:
        printer_logger.info(f"Iniciando impresión de factura #{numero_factura}")
        
        # Convertir HTML a texto
        printer_logger.info("Convirtiendo HTML a formato de impresión")
        invoice_text = html_to_escpos_text(html_content)
        printer_logger.info("Conversión completada")
        
        # Agregar información adicional
        invoice_text = "\n".join([
            "=" * 48,
            invoice_text,
            "-" * 48,
            f"CUF: {cuf}",
            f"NIT: {nit}",
            f"Factura No: {numero_factura}",
            "=" * 48
        ])
        
        # Inicializar impresora
        printer_logger.info("Inicializando impresora")
        printer = Usb(0x04B8, 0x0E15, 0, out_ep=0x01)
        
        # Configurar impresora
        printer.set(
            font='a',
            height=1,
            width=1,
            density=8,
            smooth=True,
            align='center'
        )
        
        # Imprimir
        printer_logger.info("Enviando datos a la impresora")
        printer.text(invoice_text)
        printer.cut()
        
        printer_logger.info("Impresión completada exitosamente")
        return True
        
    except Exception as e:
        error_msg = f"Error al imprimir la factura: {str(e)}"
        printer_logger.error(error_msg)
        raise