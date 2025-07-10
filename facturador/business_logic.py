
import pandas as pd
from decimal import Decimal
from data_access import obtener_nombre_unidad_medida  # Asegúrate de importar la función
import qrcode
import base64
from io import BytesIO
from datetime import datetime
from zeep.exceptions import Fault
import os
import requests
from dotenv import load_dotenv


# Desactivar advertencias de seguridad SSL en desarrollo


def calculate_totals(comandas_seleccionadas, descuento_adicional=Decimal(0), monto_giftcard=Decimal(0), codigo_clasificador_metodo_pago=None, tipo_cambio=1):
    gift_card_codes = [
        102, 109, 115, 120, 124, 128, 129, 130, 138, 146, 153, 159, 164, 168,
        172, 173, 174, 182, 189, 195, 200, 204, 208, 209, 210, 217, 221, 222,
        223, 224, 225, 226, 228, 232, 241, 246, 250, 254, 255, 256, 261, 265,
        269, 270, 271, 275, 279, 280, 281, 285, 286, 287, 291, 292, 293, 30,
        304, 35, 40, 49, 53, 60, 64, 68, 72, 76, 77, 78, 86, 94, 27
    ]
    
    subtotal = sum(Decimal(comanda["sub_total"]) for comanda in comandas_seleccionadas)
    descuento_adicional = Decimal(descuento_adicional)
    monto_giftcard = Decimal(monto_giftcard)
    total = subtotal - descuento_adicional  # Este es el montoTotal original
    
    if codigo_clasificador_metodo_pago in gift_card_codes:
        monto_total_sujeto_iva = total - monto_giftcard
    else:
        monto_total_sujeto_iva = total

    monto_total_moneda = total / Decimal(tipo_cambio)  # Calcular montoTotalMoneda

    return subtotal, descuento_adicional, monto_giftcard, total, monto_total_sujeto_iva, monto_total_moneda

def collect_product_lines(comandas, selected_id_comanda, db):
    lineas_productos = []
    for comanda in comandas:
        if comanda["id_comanda"] in selected_id_comanda:
            codigo_producto = comanda["id_producto_combo"]
            # Obtener el nombre de la unidad de medida usando el código de producto
            unidad_medida = obtener_nombre_unidad_medida(codigo_producto, db)
            linea_producto = {
                "nombre": comanda["nombre"],
                "precio": "{:.2f}".format(float(comanda["precio_venta"])),
                "cantidad": int(comanda["cantidad"]),
                "sub_total": (float(comanda["precio_venta"]) * int(comanda["cantidad"])),
                "codigo": codigo_producto,
                "unidad": unidad_medida  # Asignar el nombre de la unidad de medida
            }
            lineas_productos.append(linea_producto)

    # Agrupar productos repetidos
    df = pd.DataFrame(lineas_productos)
    df_grouped = df.groupby(['nombre', 'precio', 'codigo', 'unidad']).agg({
        'cantidad': 'sum',
        'sub_total': 'sum'
    }).reset_index()
    return df_grouped.to_dict(orient='records')

def generate_invoice_link(nit, cuf, numero_factura):
    """
    Genera el enlace de consulta de la factura basado en el NIT, CUF y número de factura.
    """
    enlace = f"https://pilotosiat.impuestos.gob.bo/consulta/QR?nit={nit}&cuf={cuf}&numero={numero_factura}"
    return enlace


def generate_qr(nit, cuf, numero_factura, tamano=1):
    """Genera un código QR para la factura."""
    url_qr = f'https://pilotosiat.impuestos.gob.bo/consulta/QR?nit={nit}&cuf={cuf}&numero={numero_factura}&t={tamano}'
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, "PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    return img_base64


# business_logic.py

def registrar_punto_de_venta(client, connection, solicitud):
    try:
        response = client.service.registroPuntoVenta(SolicitudRegistroPuntoVenta=solicitud)
        if response:
            codigo_punto_venta = response['codigoPuntoVenta']
            transaccion = response['transaccion']

            if transaccion:
                cursor = connection.cursor()
                cursor.execute('''
                INSERT INTO punto_venta (codigoPuntoVenta, nombrePuntoVenta, descripcion, codigoAmbiente, codigoModalidad, codigoSistema, codigoSucursal, codigoTipoPuntoVenta, cuis, nit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (codigo_punto_venta, solicitud['nombrePuntoVenta'], solicitud['descripcion'], solicitud['codigoAmbiente'], 
                      solicitud['codigoModalidad'], solicitud['codigoSistema'], solicitud['codigoSucursal'], solicitud['codigoTipoPuntoVenta'], 
                      solicitud['cuis'], solicitud['nit']))
                connection.commit()
                return {"success": True, "message": f"Punto de venta registrado exitosamente con código {codigo_punto_venta}."}
            else:
                return {"success": False, "message": "La transacción no se pudo completar."}
    except Exception as e:
        return {"success": False, "message": f"Error al registrar el punto de venta: {e}"}
    

#verifica las comunicaciones con los servicios de facturación
    
# Cargar las variables desde el archivo .env
load_dotenv()

# Extraer los endpoints y el API_KEY del .env
ENDPOINTS = {
    "Facturación Códigos": os.getenv("WSDL_URL_CODIGOS"),
    "Facturación Operaciones": os.getenv("WSDL_URL_OPERACIONES"),
    "Facturación Sincronización": os.getenv("WSDL_URL_SYNC"),
    "Documentos de Ajuste": os.getenv("WSDL_URL_AJUSTE"),
    "Facturación Compra-Venta": os.getenv("WSDL_URL_FACTURACION")
}

API_KEY = os.getenv("API_KEY")

# Plantilla de solicitud SOAP
SOAP_REQUEST_TEMPLATE = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
   <soapenv:Header/>
   <soapenv:Body>
      <siat:verificarComunicacion/>
   </soapenv:Body>
</soapenv:Envelope>"""

# Función para verificar la comunicación con un servicio
def verificar_comunicacion(servicio):
    url = ENDPOINTS[servicio]
    if url is None:
        return False, f"Error: URL no configurada para el servicio {servicio}"
        
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": "",
        "apikey": API_KEY
    }

    try:
        response = requests.post(url, data=SOAP_REQUEST_TEMPLATE, headers=headers)
        response.raise_for_status()  # Verifica si la respuesta es exitosa (código 200)

        if servicio in ["Documentos de Ajuste", "Facturación Compra-Venta"]:
            # Estructura para Facturación Compra-Venta y Documentos de Ajuste
            if "<transaccion>true</transaccion>" in response.text:
                return True, "Comunicación exitosa"
            else:
                return False, "Fallo en la comunicación"
        else:
            # Estructura para otros servicios
            if "<codigo>926</codigo>" in response.text:
                return True, "Comunicación exitosa con código 926"
            else:
                return False, "Fallo en la comunicación"
    except requests.exceptions.RequestException as e:
        return False, f"Error de comunicación: {e}"

# Función para verificar todos los servicios
def verificar_todos_los_servicios():
    resultados = {}
    for servicio in ENDPOINTS:
        exito, mensaje = verificar_comunicacion(servicio)
        resultados[servicio] = mensaje if exito else f"Error: {mensaje}"
    return resultados


def generate_file_name(numero_factura, cuf, extension):
    """
    Genera un nombre de archivo consistente para facturas XML y PDF.
    
    :param numero_factura: El número de la factura
    :param cuf: El Código Único de Facturación
    :param extension: La extensión del archivo ('xml' o 'pdf')
    :return: El nombre del archivo generado
    """
    return f"factura_{numero_factura}_{cuf}_.{extension}"


