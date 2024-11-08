import os
from data_access import fetch_random_leyenda
from num2words import num2words

def numero_a_palabras_con_decimales_como_fraccion(numero, lang='es'):
    if not numero:
        return ""
    
    parte_entera = int(numero)
    parte_decimal = int(round((numero - parte_entera) * 100))
    parte_entera_palabras = num2words(parte_entera, lang=lang).capitalize()
    
    if parte_decimal > 0:
        return f" {parte_entera_palabras} {parte_decimal:02d}/100 bolivianos."
    else:
        return f" {parte_entera_palabras} 00/100 bolivianos."

# Lista de códigos permitidos para gift cards
gift_card_codes = [
    102, 109, 115, 120, 124, 128, 129, 130, 138, 146, 153, 159, 164, 168,
    172, 173, 174, 182, 189, 195, 200, 204, 208, 209, 210, 217, 221, 222,
    223, 224, 225, 226, 228, 232, 241, 246, 250, 254, 255, 256, 261, 265,
    269, 270, 271, 275, 279, 280, 281, 285, 286, 287, 291, 292, 293, 30,
    304, 35, 40, 49, 53, 60, 64, 68, 72, 76, 77, 78, 86, 94, 27
]

def generate_html_invoice(subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura, metodo_de_pago=None, codigo_clasificador_metodo_pago=None, tipo_documento=None, codigo_clasificador_documento=None, numero_documento=None, complemento=None, email=None, telefono=None, ultimos_digitos_tarjeta=None):
    total = subtotal - descuento_adicional
    total_final = total - monto_giftcard
    
    if codigo_clasificador_metodo_pago in gift_card_codes:
        monto_total_sujeto_iva = total - monto_giftcard
    else:
        monto_total_sujeto_iva = total

    total_en_palabras = numero_a_palabras_con_decimales_como_fraccion(total, lang='es') if total else ""

    leyenda = fetch_random_leyenda()
    
    nit = os.getenv('NIT') # NIT del emisor
    razon_social = os.getenv('RAZON_SOCIAL') # Razón social del emisor
    nombre_sucursal = os.getenv('NOMBRE_SUCURSAL')  # Nombre de la sucursal
    codigo_punto_venta = os.getenv('CODIGO_PUNTO_VENTA')  # Código del punto de venta
    direccion = os.getenv('DIRECCION')  # Dirección de la empresa
    municipio = os.getenv('MUNICIPIO')  # Municipio de la empresa
    telefono_empresa = os.getenv('TELEFONO')  # Teléfono de la empresa
    tipo_factura = os.getenv('DESCRIPCION_TIPO_FACTURA')  # Tipo de factura (original, copia, etc.)
    subtitulo = os.getenv('SUBTITULO')    # Generar el código QR si el CUF está disponible

    nombre_mayusculas = nombre_cliente.upper()

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Factura</title>
        <style type="text/css">
        .tg  {{border-collapse:collapse;border-spacing:0;margin:0px auto;}}
        .tg td{{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
        overflow:hidden;padding:10px 5px;word-break:normal;}}
        .tg th{{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
        font-weight:normal;overflow:hidden;padding:10px 5px;word-break:normal;}}
        .tg .tg-4pi9{{background-color:#ffffff;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:left;vertical-align:middle;word-break:break-all;}}
        .tg .tg-tdlr{{background-color:#ffffff;border-color:#ffffff;font-size:12px;text-align:left;vertical-align:top;}}
        .tg .tg-c01i{{background-color:#9b9b9b;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;font-weight:bold;text-align:right;vertical-align:middle;}}
        .tg .tg-n17z{{background-color:#ffffff;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:center;vertical-align:middle;}}
        .tg .tg-i6l2{{background-color:#ffffff;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:right;vertical-align:middle;}}
        .tg .tg-gayi{{background-color:#9b9b9b;border-color:#efefef;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;font-weight:bold;text-align:center;vertical-align:middle;}}
        .tg .tg-1kjo{{background-color:#c0c0c0c0;border-color:#efefef;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:center;vertical-align:middle;}}
        .tg .tg-tm6e{{background-color:#c0c0c0;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:left;vertical-align:middle;}}
        .tg .tg-q5sf{{background-color:#ffffff;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:9px;text-align:center;vertical-align:middle;}}
        .tg .tg-e8cb{{background-color:#9b9b9b;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:right;vertical-align:middle;}}
        .tg .tg-6l70{{background-color:#9b9b9b;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:center;vertical-align:middle;}}
        </style>
    </head>
    <body>
    <table class="tg"><tbody>
    <tr>
        <td class="tg-n17z" colspan="4"><span style="font-weight:bold">{razon_social}</span><br><span style="font-weight:bold">{nombre_sucursal}</span><br><span style="font-weight:bold">Punto de Venta:</span> {codigo_punto_venta}</td>
        <td class="tg-n17z"></td>
        <td class="tg-i6l2"><span style="font-weight:bold">NIT:</span><br><span style="font-weight:bold">Factura N°:</span></td>
        <td class="tg-4pi9">{nit}<br>{numero_factura}</td>
    </tr>
    <tr>
        <td class="tg-n17z" colspan="4">{direccion}<br><span style="font-weight:bold">{municipio}</span><br><span style="font-weight:bold">Teléfono:</span> {telefono_empresa}</td>
        <td class="tg-n17z"></td>
        <td class="tg-i6l2"><span style="font-weight:bold">Código de</span><br><span style="font-weight:bold">Autorización</span></td>
        <td class="tg-4pi9">{{cuf}}</td>
    </tr>
    <tr>
        <td class="tg-n17z" colspan="7"><span style="font-weight:bold">{tipo_factura}</span><br>{subtitulo}</td>
    </tr>
    <tr>
        <td class="tg-n17z" colspan="4"><span style="font-weight:bold">Fecha/Hora:</span> {fecha_emision}<br><span style="font-weight:bold">Nombre/Razón Social:</span> {nombre_mayusculas}</td>
        <td class="tg-n17z"></td>
        <td class="tg-i6l2"><span style="font-weight:bold">NIT/CI/CEX:</span><br><span style="font-weight:bold">Cod. Cliente:</span></td>
        <td class="tg-4pi9">{numero_documento}<br>{numero_documento}</td>
    </tr>
    <tr>
        <td class="tg-tdlr" colspan="7"></td>
    </tr>
    <tr>
        <td class="tg-gayi" width="10%">CODIGO</td>
        <td class="tg-gayi" width="5%">CANTIDAD</td>
        <td class="tg-gayi" width="10%">UNIDAD</td>
        <td class="tg-gayi" width="35%">DESCRIPCIÓN</td>
        <td class="tg-gayi" width="10%">PRECIO UNIT.</td>
        <td class="tg-gayi" width="15%">DESCUENTO</td>
        <td class="tg-gayi" width="15%">SUBTOTAL</td>
    </tr>
    """

    for linea in lineas_productos:
        html_content += f"""
        <tr>
            <td class="tg-1kjo">{linea["codigo"]}</td>
            <td class="tg-1kjo">{linea["cantidad"]}</td>
            <td class="tg-1kjo">{linea["unidad"]}</td>
            <td class="tg-1kjo">{linea["nombre"]}</td>
            <td class="tg-1kjo">{linea["precio_venta"]}</td>
            <td class="tg-1kjo">{linea.get("montoDescuento", 0)}</td>
            <td class="tg-1kjo">{linea["sub_total"]}</td>
        </tr>
        """

    html_content += f"""
    <tr>
        <td class="tg-n17z" colspan="5"></td>
        <td class="tg-c01i">Sub Total:</td>
        <td class="tg-tm6e"><span style="font-weight:bold">{subtotal:.2f}</span></td>
    </tr>
    <tr>
        <td class="tg-q5sf" colspan="5"></td>
        <td class="tg-c01i">Descuento:</td>
        <td class="tg-tm6e"><span style="font-weight:bold">{descuento_adicional:.2f}</span></td>
    </tr>
    <tr>
        <td class="tg-n17z" colspan="5"><span style="font-weight:bold">Son: {total_en_palabras}</span></td>
        <td class="tg-e8cb"><span style="font-weight:bold">Total:</span></td>
        <td class="tg-tm6e"><span style="font-weight:bold">{total:.2f}</span></td>
    </tr>
    <tr>
        <td class="tg-q5sf" colspan="5"></td>
        <td class="tg-e8cb"><span style="font-weight:bold">Gift Card:</span></td>
        <td class="tg-tm6e"><span style="font-weight:bold">{monto_giftcard:.2f}</span></td>
    </tr>
    <tr>
        <td class="tg-q5sf" colspan="5"></td>
        <td class="tg-e8cb"><span style="font-weight:bold">Monto a Pagar:</span></td>
        <td class="tg-tm6e"><span style="font-weight:bold">{total_final:.2f}</span></td>
    </tr>
    <tr>
        <td class="tg-q5sf" colspan="5"></td>
        <td class="tg-6l70"><span style="font-weight:bold">Imp. Base Cred. Fiscal:</span></td>
        <td class="tg-tm6e"><span style="font-weight:bold">{monto_total_sujeto_iva:.2f}</span></td>
    </tr>
    <tr>
        <td class="tg-n17z" colspan="5"><span class="tg-q5sf">ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS, EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE ACUERDO A LEY</span><br><br><span style="font-weight:bold">{leyenda}</span><br><br><span class="tg-q5sf">"Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido en una modalidad de facturación en línea"</span></td>
        <td class="tg-n17z" colspan="2">{{codigo_qr}}</td>
    </tr>
    </tbody></table>
    </body>
    </html>
    """
    return html_content

def generate_compact_html_invoice(subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura, metodo_de_pago=None, codigo_clasificador_metodo_pago=None, tipo_documento=None, codigo_clasificador_documento=None, numero_documento=None, complemento=None, email=None, telefono=None, ultimos_digitos_tarjeta=None):
    total = subtotal - descuento_adicional
    total_final = total - monto_giftcard
    
    if codigo_clasificador_metodo_pago in gift_card_codes:
        monto_total_sujeto_iva = total - monto_giftcard
    else:
        monto_total_sujeto_iva = total

    total_en_palabras = numero_a_palabras_con_decimales_como_fraccion(total, lang='es') if total else ""

    leyenda = fetch_random_leyenda()
    
    nit = os.getenv('NIT') # NIT del emisor
    razon_social = os.getenv('RAZON_SOCIAL') # Razón social del emisor
    nombre_sucursal = os.getenv('NOMBRE_SUCURSAL')  # Nombre de la sucursal
    codigo_punto_venta = os.getenv('CODIGO_PUNTO_VENTA')  # Código del punto de venta
    direccion = os.getenv('DIRECCION')  # Dirección de la empresa
    municipio = os.getenv('MUNICIPIO')  # Municipio de la empresa
    telefono_empresa = os.getenv('TELEFONO')  # Teléfono de la empresa
    tipo_factura = os.getenv('DESCRIPCION_TIPO_FACTURA')  # Tipo de factura (original, copia, etc.)
    subtitulo = os.getenv('SUBTITULO')    # Generar el código QR si el CUF está disponible

    nombre_mayusculas = nombre_cliente.upper()

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Factura</title>
        <style type="text/css">
      body {{
        background-color: white; /* Fondo blanco */
        color: black;  /* Texto negro */
      }}
      .tg {{
        border-collapse: collapse;
        border-spacing: 0;
        margin: 0px auto;
        width: 100% !important;
        background-color: white;  /* Fondo blanco para la tabla */
      }}

      .tg td, .tg th {{
        border-color: white;
        border-style: solid;
        border-width: 1px;
        font-family: "Lucida Console", Monaco, monospace !important;
        font-size: 10px;
        overflow: hidden;
        padding: 1px 1px;
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
        margin: 1px 0;
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
    </head>
    <body>
    <div class="tg-wrap">
      <table class="tg" style="width: 100%;">
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
              <span style="font-weight:bold">Nombre/Razón Social:</span> {nombre_mayusculas}<br>
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
                        <td >
                        <table style="width: 100%;">
                            <tr>
                            <td colspan=2><strong>{linea["codigo"]} - {linea["nombre"]}</strong></td>
                            </tr>
                            <tr>
                            <td colspan=2>Unidad de Medida: {linea["unidad"]}</td>
                            </tr>
                            <tr>
                            <td>{linea["cantidad"]}x{linea["precio_venta"]} - {linea.get("montoDescuento", 0)}</td>
                            <td style:"text-align: right;">{linea["sub_total"]}</td>
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
            <td class="tg-sz8q">Son: {total_en_palabras}</td>
          </tr>

          <tr><td class="separator"></td></tr>

          <tr>
            <td class="tg-eavw">
              ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS, EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE ACUERDO A LEY.
            </td>
          </tr>
          <tr>
            <td class="tg-eavw"><br>{leyenda}<br></td>
          </tr>
          <tr>
            <td class="tg-eavw">
              “Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido en una modalidad de facturación en línea”
            </td>
          </tr>
          <tr>
            <td class="tg-8jgo">{{codigo_qr}}</td>
          </tr>
        </tbody>
      </table>
    </div>
    """
    return html_content
