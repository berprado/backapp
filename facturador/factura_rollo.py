import streamlit as st
import streamlit.components.v1 as components  # Importar el módulo components
from invoice_templates import generate_compact_invoice_text
import os
from escpos.printer import Usb
# Función para convertir número a palabras (puede mejorarse)
def numero_a_palabras_con_decimales_como_fraccion(numero, lang='es'):
    return "Trescientos diez"

# Datos de ejemplo para generar la factura
subtotal = 90.00
descuento_adicional = 0.00
monto_giftcard = 0.00
lineas_productos = [
    {"codigo": "001", "nombre": "Producto A", "cantidad": 2, "precio_venta": 30.00, "sub_total": 60.00},
    {"codigo": "002", "nombre": "Producto B", "cantidad": 1, "precio_venta": 30.00, "sub_total": 30.00}
]
nombre_cliente = "PRADO"
fecha_emision = "05/08/2024 01:20 AM"
numero_factura = "565"
metodo_de_pago = "Efectivo"
codigo_clasificador_metodo_pago = "1"
tipo_documento = "CI"
codigo_clasificador_documento = "1"
numero_documento = "344096024"
complemento = None
email = "cliente@example.com"
telefono = "65560514"
ultimos_digitos_tarjeta = None
# Generar el contenido de la factura en formato texto
factura_texto = generate_compact_invoice_text(
    subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura,
    metodo_de_pago, codigo_clasificador_metodo_pago, tipo_documento, codigo_clasificador_documento, numero_documento,
    complemento, email, telefono, ultimos_digitos_tarjeta
)

# Mostrar la factura en formato texto
print(factura_texto)

st.write(factura_texto)
    # Conectar a la impresora y enviar el texto a imprimir
printer = Usb(0x04B8, 0x0E15, 0, out_ep=0x01)  # Conectar a la impresora Epson TM-T20II con Vendor ID y Product ID
printer.text(factura_texto)
printer.cut()
# Función para generar la factura en HTML con el formato proporcionado
def generate_html_invoice_80mm(subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura, metodo_de_pago=None, codigo_clasificador_metodo_pago=None, tipo_documento=None, codigo_clasificador_documento=None, numero_documento=None, complemento=None, email=None, telefono=None, ultimos_digitos_tarjeta=None):
    total = subtotal - descuento_adicional
    total_final = total - monto_giftcard
    
    if codigo_clasificador_metodo_pago in ['gift_card_codes']:  # Aquí debes tener los códigos válidos
        monto_total_sujeto_iva = total - monto_giftcard
    else:
        monto_total_sujeto_iva = total

    total_en_palabras = numero_a_palabras_con_decimales_como_fraccion(total, lang='es') if total else ""

    leyenda = "ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS, EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE ACUERDO A LEY"
    
    nit = os.getenv('NIT', '344096024')
    razon_social = os.getenv('RAZON_SOCIAL', 'BOLIVIAN FOODS & DRINKS S.R.L.')
    nombre_sucursal = os.getenv('NOMBRE_SUCURSAL', 'Casa Matriz')
    codigo_punto_venta = os.getenv('CODIGO_PUNTO_VENTA', '0')
    direccion = os.getenv('DIRECCION', 'AVENIDA MONTENEGRO NRO. SN')
    municipio = os.getenv('MUNICIPIO', 'LA PAZ')
    telefono_empresa = os.getenv('TELEFONO', '65560514')
    tipo_factura = os.getenv('DESCRIPCION_TIPO_FACTURA', 'FACTURA')
    subtitulo = os.getenv('SUBTITULO', '(CON DERECHO A CRÉDITO FISCAL)')
    cuf = "178B43EFDB95BEFB21CB1FD7A00C416FFFC5FA9F"
    codigo_qr = "Aquí va el código QR"

    # HTML con la estructura proporcionada y el fondo blanco añadido
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <style type="text/css">
      body {{
        background-color: white; /* Fondo blanco */
        color: black;  /* Texto negro */
      }}
      .tg {{
        border-collapse: collapse;
        border-spacing: 0;
        margin: 0px auto;
        width: 8cm !important;
        background-color: white;  /* Fondo blanco para la tabla */
      }}

      .tg td, .tg th {{
        border-color: white;
        border-style: solid;
        border-width: 1px;
        font-family: "Lucida Console", Monaco, monospace !important;
        font-size: 10px;
        overflow: hidden;
        padding: 5px 2px;
        word-break: normal;
        color: black;  /* Texto negro */
      }}

    

      .tg-9k97 {{
        border-color: #ffffff;
        font-family: "Lucida Console", Monaco, monospace !important;
        text-align: right;
        vertical-align: top;
        color: black;
      }}

      .tg-8jgo {{
        border-color: #ffffff;
        text-align: center;
        vertical-align: top;
        color: black;
      }}

      .tg-eavw {{
        border-color: #ffffff;
        font-family: "Lucida Console", Monaco, monospace !important;
        text-align: center;
        vertical-align: top;
        color: black;
      }}

      .tg-sz8q {{
        border-color: #ffffff;
        font-family: "Lucida Console", Monaco, monospace !important;
        text-align: left;
        vertical-align: top;
        color: black;
      }}

      .tg-02er {{
        border-color: #ffffff;
        font-family: "Lucida Console", Monaco, monospace !important;
        font-weight: bold;
        text-align: center;
        vertical-align: top;
        color: black;
      }}

      .separator {{
        border: none;
        height: 1px;
        background: black;
        margin: 10px 0;
      }}

      @media screen and (max-width: 8cm) {{
        .tg {{
          width: 100% !important;
        }}

        .tg-wrap {{
          overflow-x: auto;
          -webkit-overflow-scrolling: touch;
          margin: auto 0px;
        }}

        .separator {{
          background: #ccc;
        }}
      }}
    </style>

    <div class="tg-wrap">
      <table class="tg">
        <tbody>
          <tr>
            <td class="tg-eavw">
              <strong>{tipo_factura}</strong><br>
              <strong>{subtitulo}</strong>
            </td>
          </tr>
          <tr>
            <td class="tg-eavw">{razon_social}<br>{nombre_sucursal}<br>Punto de Venta: {codigo_punto_venta}</td>
          </tr>
          <tr>
            <td class="tg-eavw">{direccion}<br>{municipio}<br>Tel. {telefono_empresa}</td>
          </tr>

          <tr><td class="separator"></td></tr>

          <tr>
            <td class="tg-eavw">
              <span style="font-weight:bold">NIT</span><br>{nit}<br>
              <span style="font-weight:bold">Factura N°</span><br>{numero_factura}
            </td>
          </tr>
          <tr>
            <td class="tg-eavw">
              <span style="font-weight:bold">Código de Autorización</span><br>{{cuf}}
            </td>
          </tr>

          <tr><td class="separator"></td></tr>

          <tr>
            <td class="tg-eavw">
              <span style="font-weight:bold">Nombre/Razón Social:</span> {nombre_cliente}<br>
              <span style="font-weight:bold">NIT/CI/CEX:</span> {numero_documento}<br>
              <span style="font-weight:bold">Cod. Cliente:</span> {numero_documento}<br>
              <span style="font-weight:bold">Fecha de Emisión: </span>{fecha_emision}
            </td>
          </tr>

          <tr><td class="separator"></td></tr>
        
        
          <tr>
            <td class="tg-eavw"><span style="font-weight:bold">DETALLE</span></td>
          </tr>
        """
    for linea in lineas_productos:
        html_content += f""" 
        <tr>
                <td class="tg-sz8q">
                <table style="width: 100%;">
                    <tr>
                    <td colspan=2><strong>{linea["codigo"]} - {linea["nombre"]}</strong></td>
                    </tr>
                    <tr>
                    <td colspan=2>Unidad de Medida:{linea["unidad"]}</td>
                    </tr>
                    <tr>
                    <td>{linea["cantidad"]} x {linea["precio_venta"]} - {linea.get("montoDescuento", 0)}</td>
                    <td align=leftright>{linea["sub_total"]}</td>
                    </tr>
                   </table>
                </td>
            </tr>
        """
    html_content += f"""
          <tr><td class="separator"></td></tr>

          <tr>
            <td class="tg-9k97">Sub Total: {subtotal:.2f}</td>
          </tr>
          <tr>
            <td class="tg-9k97">Descuento: {descuento_adicional:.2f}</td>
          </tr>
          <tr>
            <td class="tg-9k97">Total: {total:.2f}</td>
          </tr>
          <tr>
            <td class="tg-9k97">Gift Card: {monto_giftcard:.2f}</td>
          </tr>
          <tr>
            <td class="tg-9k97">
              <span style="font-weight:bold">Monto a Pagar:</span> {total_final:.2f}
            </td>
          </tr>
          <tr>
            <td class="tg-9k97">
              <span style="font-weight:bold">Imp. Base Cred. Fiscal:</span> {monto_total_sujeto_iva:.2f}
            </td>
          </tr>
          <tr>
            <td class="tg-sz8q">Son: {total_en_palabras} 00/100 Bolivianos.</td>
          </tr>

          <tr><td class="separator"></td></tr>

          <tr>
            <td class="tg-eavw">
              ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS, EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE ACUERDO A LEY.
            </td>
          </tr>
          <tr>
            <td class="tg-eavw">{leyenda}</td>
          </tr>
          <tr>
            <td class="tg-eavw">
              “Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido en una modalidad de facturación en línea”
            </td>
          </tr>
          <tr>
            <td class="tg-8jgo">{codigo_qr}</td>
          </tr>
        </tbody>
      </table>
    </div>
    """
    return html_content

# Datos de ejemplo para productos
lineas_productos = [
    {"codigo": "7", "cantidad": "2", "unidad": "Unidades", "nombre": "COSMOPOLITAN", "precio_venta": 45.00, "sub_total": 90.00}
]

# Renderizar en Streamlit
st.title("Vista previa de la Factura")
factura_texto = generate_compact_invoice_text(
    subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura,
    metodo_de_pago, codigo_clasificador_metodo_pago, tipo_documento, codigo_clasificador_documento, numero_documento,
    complemento, email, telefono, ultimos_digitos_tarjeta
)
components.html(factura_texto, height=800, scrolling=True)
