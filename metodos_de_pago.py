import streamlit as st
import requests
from num2words import num2words
import datetime
import pdfkit
from sqlalchemy import Column, Integer, String, DateTime
import xml.etree.ElementTree as ET

# Constantes
ENDPOINT_URL = "http://127.0.0.1:8000/"
PDF_FILE_NAME = 'reporte.pdf'
XML_FILE_NAME = 'factura.xml'

@st.cache_resource


def fetch_comandas():
    """Obtiene los id de las comandas desde la API y maneja posibles errores."""
    try:
        response = requests.get(ENDPOINT_URL)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return [], f"Error al obtener los id_comanda: {e}"
    

def main():
    # Obtener comandas y manejar posibles errores
    comandas, mensaje_error = fetch_comandas()
    if mensaje_error:
        st.error(mensaje_error)

    # Asegurar id_comandas únicos y ordenarlos
    id_comanda_set = set(comanda["id_comanda"] for comanda in comandas)
    id_comandas = sorted(id_comanda_set, reverse=True)



    # Entradas de la barra lateral
    cliente = st.sidebar.text_input("CLIENTE")
    nit = st.sidebar.text_input("NIT")
    

    opciones = ["Efectivo", "Tarjeta", "QR"]

    # Crear un selectbox en el sidebar
    seleccion = st.sidebar.selectbox("Tipo de Pago:", opciones)

    # Condición para mostrar un campo de entrada si se selecciona "Tarjeta"
    if seleccion == "Tarjeta":
        # Campo de entrada para un número de 4 caracteres
        numero_4_digitos = st.sidebar.text_input("Ingresa el número de Tarjeta:", max_chars=4)

        # Verificar si el usuario ingresó algo
        if numero_4_digitos:
            st.write(f"Has ingresado: {numero_4_digitos}")
        else:
            st.write("Selecciona el Método de Pago")  # Mensaje por defecto cuando no se ingresa nada

    # Condición para mostrar un mensaje si se selecciona "QR"
    elif seleccion == "QR":
        st.write("Elegiste el método de pago QR")

    # Condición para mostrar un mensaje si se selecciona "Efectivo"
    elif seleccion == "Efectivo":
        st.write("Elegiste el método de pago Efectivo")



#Input de descuento
    descuento_input = st.sidebar.text_input("DESCUENTO", value="0", placeholder="Presiona Enter para aplicar el descuento")


#Selección de comandas
    selected_id_comanda = st.sidebar.multiselect("Detalle de la Factura", list(id_comandas), placeholder="Selecciona la(s) comandas")
    
    try:
        descuento = float(descuento_input)
    except ValueError:
        st.error("Por favor, ingresa un número válido para el descuento.")
        descuento = 0

    # Diseño de la página principal
    display_invoice_header(cliente, nit)

    # Mostrar productos y calcular totales
    total, lineas_productos = calculate_totals(comandas, selected_id_comanda)
    display_totals(total, descuento)

    # Botones de generación de PDF y XML
    generate_pdf_button(total, lineas_productos, cliente, nit, descuento)
    generate_xml_button(comandas, selected_id_comanda, total, descuento)

def display_invoice_header(cliente, nit):
    """Muestra la cabecera de la factura."""
    #nitEmisor
    st.markdown("<center><b>nitEmisor</b></center>", unsafe_allow_html=True)
    #razonSocialEmisor
    st.markdown("<center><b>BACKSTAGE BAR & KARAOKE</b></center>", unsafe_allow_html=True)
    #municipio 
    st.markdown("<center><b>municipio</b></center>", unsafe_allow_html=True)
    #telefono 
    st.markdown("<center><b>telefono</b></center>", unsafe_allow_html=True)
    #numeroFactura  
    st.markdown("<center><b>numeroFactura</b></center>", unsafe_allow_html=True)
    #cuf
    st.markdown("<center><b>cuf</b></center>", unsafe_allow_html=True)
    #cufd
    st.markdown("<center><b>cufd</b></center>", unsafe_allow_html=True)
    #codigoSucursal
    st.markdown("<center><b>codigoSucursal</b></center>", unsafe_allow_html=True)
    #direccion
    st.markdown("<center><b>direccion</b></center>", unsafe_allow_html=True)
    #codigoPuntoVenta
    st.markdown("<center>codigoPuntoVenta</center>", unsafe_allow_html=True)
    #fechaEmision
    st.markdown(f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    #nombreRazonSocial
    st.markdown(f"Señor(es): {cliente.upper()}")
    #codigoTipoDocumentoIdentidad
    st.markdown(f"NIT/CI/RUE: {nit}")
    #numeroDocumento
    st.markdown("<center>numeroDocumento</center>", unsafe_allow_html=True)
    #complemento
    st.markdown("<center>complemento</center>", unsafe_allow_html=True)
    #codigoCliente
    st.markdown("<center>codigoCLiente</center>", unsafe_allow_html=True)
    #codigoMetodoPago
    st.markdown("<center>codigoCLiente</center>", unsafe_allow_html=True)
    st.markdown("**PRODUCTO | PRECIO | CANTIDAD | SUBTOTAL**")

def calculate_totals(comandas, selected_id_comanda):
    """Calcula el total y prepara las líneas de productos para mostrar."""
    total = 0
    lineas_productos = ""
    for comanda in comandas:
        if comanda["id_comanda"] in selected_id_comanda:
            nombre = comanda["nombre"]
            precio_venta = float(comanda["precio_venta"])
            cantidad = int(comanda["cantidad"])
            sub_total = precio_venta * cantidad
            linea = f"{nombre} {precio_venta}x{cantidad} >>> Bs {sub_total}"
            st.text(linea)
            lineas_productos += f"<p>{linea}</p>"
            total += sub_total
    return total, lineas_productos

def display_totals(total, descuento):
    """Muestra el subtotal, descuento y total después del descuento."""
    total_final = total - descuento
    st.markdown(f"SubTotal: Bs {total:.2f}")
    st.markdown(f"Descuento: Bs {descuento:.2f}")
    st.markdown(f"**Total: Bs {total_final:.2f}**")
    st.write(f"Son: {num2words(total_final, lang='es').title()} 00/100 Bolivianos")

def generate_pdf_button(total, lineas_productos, cliente, nit, descuento):
    """Genera un PDF a partir de una plantilla HTML y proporciona un botón de descarga."""
    if st.button("Generar Factura en PDF", key="generar_pdf"):
        total_final = total - descuento  # Calcula el total final aquí para el PDF
        reporte_html = create_pdf_html(total, lineas_productos, cliente, nit, descuento, total_final)
        pdfkit.from_string(reporte_html, PDF_FILE_NAME)
        with open(PDF_FILE_NAME, 'rb') as archivo:
            st.download_button("Ver Factura", archivo, file_name=PDF_FILE_NAME)

def create_pdf_html(total, lineas_productos, cliente, nit, descuento, total_final):
    """Crea el contenido HTML para el informe en PDF."""
    return f"""
    <html>
    <head>
        <title>Informe de Venta</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: "DejaVu Sans", Arial, sans-serif; }}
        </style>
    </head>
    <body>
        <center><h1>BACKSTAGE BAR & KARAOKE</h1></center>
        <center><h2>Sucursal N° 0 - Casa Matriz</h2></center>
        <center><h3>Factura N° 001-001-0000001</h3></center>
        <p>Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Señor(es): {cliente.upper()}</p>
        <p>NIT/CI/RUE: {nit}</p>
        <h4>-------------------------</h4>
        {lineas_productos}
        <p style='text-align: right;'>SubTotal: Bs {total:.2f}</p>
        <p style='text-align: right;'>Descuento: Bs {descuento:.2f}</p>
        <p style='text-align: right;'><b>Total: Bs {total_final:.2f}</b></p>
        <p style='text-align: right;'>Son: {num2words(total_final, lang='es').title()} 00/100 Bolivianos</p>
    </body>
    </html>
    """

def generate_xml_button(comandas, selected_id_comanda, total, descuento):
    """Genera un archivo XML de la factura al presionar el botón."""
    if st.button("Generar Factura en XML", key="generar_xml"):
        lineas_productos = collect_product_lines(comandas, selected_id_comanda)
        generate_xml_invoice(lineas_productos, total, descuento)

def collect_product_lines(comandas, selected_id_comanda):
    """Recopila las líneas de productos para generar la factura XML."""
    lineas_productos = []
    for comanda in comandas:
        if comanda["id_comanda"] in selected_id_comanda:
            linea_producto = {
                "nombre": comanda["nombre"],
                "precio_venta": float(comanda["precio_venta"]),
                "cantidad": int(comanda["cantidad"]),
                "sub_total": float(comanda["precio_venta"]) * int(comanda["cantidad"])
            }
            lineas_productos.append(linea_producto)
    return lineas_productos

def generate_xml_invoice(total, descuento, lineas_productos):
    """Genera un archivo XML para la factura."""
    total_final = total - descuento  # Calcula el total final aquí para el XML
    factura = ET.Element("factura")
    ET.SubElement(factura, "total").text = str(total)
    ET.SubElement(factura, "descuento").text = str(descuento)
    ET.SubElement(factura, "total_final").text = str(total_final)
    productos = ET.SubElement(factura, "productos")
    for linea in lineas_productos:
        producto = ET.SubElement(productos, "producto")
        ET.SubElement(producto, "nombre").text = linea["nombre"]
        ET.SubElement(producto, "precio_venta").text = str(linea["precio_venta"])
        ET.SubElement(producto, "cantidad").text = str(linea["cantidad"])
        ET.SubElement(producto, "sub_total").text = str(linea["sub_total"])
    arbol = ET.ElementTree(factura)
    try:
        arbol.write(XML_FILE_NAME)
        st.success(f"Archivo XML Generado: {XML_FILE_NAME}")
    except Exception as e:
        st.error(f"Error al generar la factura en XML: {e}")

if __name__ == "__main__":
    main()
