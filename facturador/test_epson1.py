from weasyprint import HTML

def html_to_pdf(html_content, output_path):
    HTML(string=html_content).write_pdf(output_path)

# Leer el contenido del archivo HTML
with open('debug_factura_.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# Generar el PDF
output_path = 'factura_84_247.pdf'
html_to_pdf(html_content, output_path)