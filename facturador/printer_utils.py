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
        bool: True si la impresión fue exitosa, False en caso contrario
    """
    try:
        logging.info(f"Iniciando impresión de factura #{numero_factura}")
        
        # Convert HTML to text format
        logging.info("Convirtiendo HTML a formato de impresión")
        invoice_text = html_to_escpos_text(html_content)
        logging.info("Conversión completada")
        
        # Add header info
        invoice_text = "\n".join([
            "=" * 32,
            "FACTURA",
            "=" * 32,
            invoice_text,
            "-" * 32,
            f"CUF: {cuf}",
            f"NIT: {nit}",
            f"Factura No: {numero_factura}",
            "=" * 32
        ])
        
        # Initialize printer
        logging.info("Inicializando conexión con la impresora")
        printer = Usb(0x04B8, 0x0E15, 0, out_ep=0x01)
        
        # Print content
        logging.info("Enviando datos a la impresora")
        printer.text(invoice_text)
        printer.cut()
        
        logging.info("Impresión completada exitosamente")
        return True
        
    except Exception as e:
        logging.error(f"Error durante la impresión: {str(e)}")
        raise Exception(f"Error al imprimir: {str(e)}")
        
        # Final separator and cut
        printer.text("\n" + "-" * 32 + "\n")
        printer.cut()
        
        logging.info("Factura impresa exitosamente")
        return True
        
    except Exception as e:
        error_msg = f"Error al imprimir la factura: {str(e)}"
        logging.error(error_msg)
        raise Exception(error_msg)

def html_to_escpos_text(html_content):
    """
    Convierte el contenido HTML de la factura en formato de texto para impresora térmica.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        invoice_text = ""
        
        # Process table rows
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            
            # Skip empty rows
            if not cells:
                continue
                
            # Process each cell in the row
            row_text = ""
            for cell in cells:
                cell_text = cell.get_text().strip()
                if cell_text:  # Only add non-empty cells
                    row_text += f"{cell_text}  "
            
            if row_text:  # Only add non-empty rows
                invoice_text += f"{row_text.strip()}\n"
                
        return invoice_text
        
    except Exception as e:
        logging.error(f"Error al convertir HTML a texto: {str(e)}")
        raise Exception(f"Error al procesar el contenido HTML: {str(e)}")