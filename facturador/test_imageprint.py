from thermal_printersito import ThermalPrinter
import os
# Ruta al archivo HTML
html_file_path = "final_facturita_test.html"

if not os.path.exists(html_file_path):
    print("El archivo HTML no existe. Verifica la ruta.")
else:
    # Leer el contenido del archivo HTML
    with open(html_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    # Crear una instancia de la impresora térmica
    printer = ThermalPrinter(vendor_id=0x04B8, product_id=0x0E15)

    # Imprimir la factura desde el contenido HTML
    try:
        success = printer.print_invoice(html_content)
        if success:
            print("La factura se imprimió correctamente.")
        else:
            print("Ocurrió un problema al imprimir la factura.")
    except Exception as e:
        print(f"Error durante la impresión: {str(e)}")
