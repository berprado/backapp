import logging
from escpos.printer import Usb

def test_printer():
    """
    Función de prueba para verificar la comunicación con la impresora Epson TM-T20II
    """
    try:
        # Configuración de logging
        logging.basicConfig(level=logging.INFO)
        
        # ID de Vendedor (Vendor ID) y ID de Producto (Product ID) para Epson TM-T20II
        VENDOR_ID = 0x04b8   # ID típico para Epson
        PRODUCT_ID = 0x0e15  # ID típico para TM-T20II
        
        logging.info(f"Intentando conectar con la impresora (Vendor ID: {VENDOR_ID}, Product ID: {PRODUCT_ID})...")
        
        # Intenta conectar con la impresora
        printer = Usb(VENDOR_ID, PRODUCT_ID)
        
        logging.info("✅ Conexión exitosa con la impresora")
        
        # Imprimir texto de prueba
        printer.set(align='center')
        printer.text("=========================\n")
        printer.text("PRUEBA DE IMPRESIÓN\n")
        printer.text("=========================\n\n")
        
        # Probar diferentes estilos
        printer.set(align='left')
        printer.text("Texto normal\n")
        printer.set(bold=True)
        printer.text("Texto en negrita\n")
        printer.set(bold=False)
        printer.set(double_height=True)
        printer.text("Texto alto\n")
        printer.set(double_height=False)
        printer.set(double_width=True)
        printer.text("Texto ancho\n")
        printer.set(double_width=False)
        
        # Probar corte de papel
        printer.text("\n\n")
        printer.text("Si puedes leer esto, ¡la prueba fue exitosa!\n")
        printer.text("\n\n")
        printer.cut()
        
        logging.info("✅ Prueba de impresión completada con éxito")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error durante la prueba: {str(e)}")
        
        # Mostrar información adicional si hay error de conexión USB
        if "USBError" in str(type(e)):
            logging.error("""
            Posibles soluciones:
            1. Verifica que la impresora esté encendida y conectada
            2. Comprueba los IDs de Vendor y Product
            3. En Windows, es posible que necesites usar Zadig
            4. En Linux, verifica los permisos udev
            """)
        return False

if __name__ == "__main__":
    print("Iniciando prueba de impresora...")
    test_printer()
    input("Presiona Enter para salir...")