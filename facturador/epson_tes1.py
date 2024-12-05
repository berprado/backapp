from bs4 import BeautifulSoup
import streamlit as st
from thermal_printer import ThermalPrinter

def html_to_escpos_text(html_content):
    """
    Convierte el HTML de la factura a texto ESC/POS para impresión.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Obtener datos clave
        header = soup.find('strong').get_text(strip=True)
        company_details = soup.find_all('td', class_='tg-eavw')[:3]
        nit = soup.find(text="NIT").find_next().get_text(strip=True)
        factura_numero = soup.find(text="Factura N°").find_next().get_text(strip=True)
        monto_total = soup.find(text="Monto a Pagar:").find_next().get_text(strip=True)
        qr_data = soup.find('img')['src']  # Suponiendo que QR ya está en formato base64

        # Construir el contenido de impresión
        escpos_text = f"""
        {header}
        {"-" * 32}
        {company_details[0].get_text(strip=True)}
        {company_details[1].get_text(strip=True)}
        {"-" * 32}
        NIT: {nit}
        Factura N°: {factura_numero}
        {"-" * 32}
        TOTAL: {monto_total}
        {"-" * 32}
        """
        return escpos_text

    except Exception as e:
        st.error(f"Error al procesar HTML: {e}")
        return None

def imprimir_factura(html_file_path):
    """
    Imprime la factura en formato ESC/POS utilizando una impresora térmica.
    """
    try:
        # Cargar HTML
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # Convertir a ESC/POS
        escpos_text = html_to_escpos_text(html_content)

        if escpos_text:
            # Enviar a la impresora térmica
            printer = ThermalPrinter()  # Asegúrate de que `ThermalPrinter` esté configurado correctamente
            printer.print_text(escpos_text)
            st.success("Factura impresa correctamente.")
        else:
            st.error("No se pudo procesar el contenido para impresión.")

    except Exception as e:
        st.error(f"Error al imprimir la factura: {e}")

# Interfaz de usuario
if st.button("Imprimir Factura"):
    # Ajusta la ruta al archivo HTML
    html_file_path = "final_factura_test.html"
    imprimir_factura(html_file_path)

