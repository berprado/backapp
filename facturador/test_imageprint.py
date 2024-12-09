from thermal_printer import ThermalPrinter

# Leer el archivo HTML
html_file_path = "debug_factura_402.html"
with open(html_file_path, "r", encoding="utf-8") as file:
    html_content = file.read()

# Crear instancia de ThermalPrinter
printer = ThermalPrinter(vendor_id=0x04B8, product_id=0x0E15)

# Imprimir contenido del HTML como imagen
printer.print_html_as_image(html_content, font_path="arial.ttf", font_size=12)
