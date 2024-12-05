from escpos.printer import Usb
from bs4 import BeautifulSoup

def parse_and_print(html_content):
    try:
        # Configuración de la impresora USB para Epson TM-T20II
        printer = Usb(0x04B8, 0x0E15)  # Ajusta los valores si son diferentes para tu impresora

        # Analizar el contenido HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extraer encabezado
        tipo_factura = soup.find(id="tipo_factura").text.strip()
        subtitulo = soup.find(id="subtitulo").text.strip()
        empresa_info = soup.find(id="empresa_info").text.strip()
        direccion = soup.find(id="direccion").text.strip()

        # Extraer información del cliente
        cliente_info = soup.find(id="cliente_info").text.strip()

        # Extraer productos
        productos = []
        for producto in soup.select('td[id^="producto_"]'):
            codigo = producto['id'].replace("producto_", "")
            nombre = producto.text.strip()
            subtotal = soup.find(id=f"subtotal_producto_{codigo}").text.strip()
            productos.append({
                "codigo": codigo,
                "nombre": nombre,
                "subtotal": subtotal
            })

        # Extraer totales
        subtotal = soup.find(id="subtotal").text.replace("Sub Total: ", "").strip()
        descuento = soup.find(id="descuento").text.replace("Descuento: ", "").strip()
        total = soup.find(id="total").text.replace("Total: ", "").strip()
        giftcard = soup.find(id="giftcard").text.replace("Gift Card: ", "").strip()
        total_final = soup.find(id="total_final").text.replace("Monto a Pagar:", "").strip()
        iva_base = soup.find(id="iva_base").text.replace("Imp. Base Cred. Fiscal:", "").strip()
        total_en_palabras = soup.find(id="total_en_palabras").text.replace("Son: ", "").strip()
        leyenda = soup.find(id="leyenda").text.strip()
        leyenda_legal = soup.find(id="leyenda_legal").text.strip()
        representacion_grafica = soup.find(id="representacion_grafica").text.strip()

        # Iniciar impresión
        printer.set(align='center', font='a', width=2)
        printer.text(tipo_factura + "\n")
        printer.text(subtitulo + "\n\n")

        printer.set(align='left', font='a', width=1)
        printer.text(empresa_info + "\n")
        printer.text(direccion + "\n\n")
        printer.text(cliente_info + "\n\n")

        printer.set(align='center')
        printer.text("DETALLE DE PRODUCTOS\n")
        printer.text("-" * 40 + "\n")

        # Imprimir detalles de productos
        for producto in productos:
            printer.text(f"{producto['codigo']} - {producto['nombre']}\n")
            printer.text(f"Subtotal: {producto['subtotal']}\n")
            printer.text("-" * 40 + "\n")

        # Imprimir totales
        printer.set(align='right')
        printer.text(f"Sub Total: {subtotal}\n")
        printer.text(f"Descuento: {descuento}\n")
        printer.text(f"Total: {total}\n")
        printer.text(f"Gift Card: {giftcard}\n")
        printer.text(f"Monto a Pagar: {total_final}\n")
        printer.text(f"Imp. Base Cred. Fiscal: {iva_base}\n")
        printer.text(f"Son: {total_en_palabras}\n")
        printer.text("-" * 40 + "\n")

        # Imprimir leyendas
        printer.set(align='center')
        printer.text(leyenda + "\n\n")
        printer.text(leyenda_legal + "\n\n")
        printer.text(representacion_grafica + "\n\n")

        # Cortar papel
        printer.cut()
        print("Impresión completada exitosamente.")

    except Exception as e:
        print(f"Error durante la impresión: {e}")


# Leer el contenido del archivo HTML
with open("final_factura_test.html", "r", encoding="utf-8") as file:
    html_content = file.read()

# Parsear e imprimir el contenido
parse_and_print(html_content)
