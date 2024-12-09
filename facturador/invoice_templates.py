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

def generate_compact_html_invoice_xx(subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura, metodo_de_pago=None, codigo_clasificador_metodo_pago=None, tipo_documento=None, codigo_clasificador_documento=None, numero_documento=None, complemento=None, email=None, telefono=None, ultimos_digitos_tarjeta=None):
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
        width: 80mm;
        margin: 0;
        font-size: 10px;
      }}
      .tg {{
        border-collapse: collapse;
        border-spacing: 0;
        margin: 0px auto;
        width: 80mm !important;
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
        word-break: break-word;
        color: black;  /* Texto negro */
      }}

    
      .tg .tg-lboi{{text-align:right;vertical-align:middle}}
      .tg .tg-7rv2{{text-align:left;vertical-align:middle}}
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
        vertical-align: middle;
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

      @media screen and (max-width: 80mm) {{
        .tg {{
          width: 80mm !important;
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
            <td class="tg-eavw">{razon_social}<br>{nombre_sucursal}<br>Punttito de Venta: {codigo_punto_venta}</td>
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
            <td class="tg-eavw" >
              <span style="font-weight:bold">Nombre/Razón Social:</span>{nombre_mayusculas}<br>
              <span style="font-weight:bold">         NIT/CI/CEX:</span>{numero_documento}<br>
              <span style="font-weight:bold">       Cod. Cliente:</span>{numero_documento}<br>
              <span style="font-weight:bold">   Fecha de Emisión:</span>{fecha_emision}
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
                  <td>
                   <table style="width: 100%;">
                     <tr>
                      <td class="tg-7rv2" style="width: 85%;"><span style="font-weight:bold">{linea["codigo"]} - {linea["nombre"]}</span><br>     Unidad de Medida: {linea["unidad"]}<br>{linea["cantidad"]}x{linea["precio_venta"]} - {linea.get("montoDescuento", 0)}</td>
                      <td class="tg-lboi">{linea["sub_total"]:.2f}</td>
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


def generate_compact_html_invoice(
    subtotal, descuento_adicional, monto_giftcard, lineas_productos,
    nombre_cliente, fecha_emision, numero_factura, metodo_de_pago=None,
    codigo_clasificador_metodo_pago=None, tipo_documento=None, codigo_clasificador_documento=None,
    numero_documento=None, complemento=None, email=None, telefono=None, ultimos_digitos_tarjeta=None, cuf=None
):
    """Genera un HTML compacto para la factura."""
    
    # Calcular totales
    total = subtotal - descuento_adicional
    total_final = total - monto_giftcard
    
    if codigo_clasificador_metodo_pago in gift_card_codes:
        monto_total_sujeto_iva = total - monto_giftcard
    else:
        monto_total_sujeto_iva = total

    # Obtener representación en palabras
    total_en_palabras = numero_a_palabras_con_decimales_como_fraccion(total, lang='es') if total else ""

    # Obtener datos necesarios
    leyenda = fetch_random_leyenda()
    
    # Variables de entorno
    nit = os.getenv('NIT')
    razon_social = os.getenv('RAZON_SOCIAL')
    nombre_sucursal = os.getenv('NOMBRE_SUCURSAL')
    codigo_punto_venta = os.getenv('CODIGO_PUNTO_VENTA')
    direccion = os.getenv('DIRECCION')
    municipio = os.getenv('MUNICIPIO')
    telefono_empresa = os.getenv('TELEFONO')
    tipo_factura = os.getenv('DESCRIPCION_TIPO_FACTURA')
    subtitulo = os.getenv('SUBTITULO')

    nombre_mayusculas = nombre_cliente.upper() if nombre_cliente else ""

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Factura {numero_factura}</title>
        <style>
            body {{
                font-family: monospace;
                font-size: 10px;
                width: 80mm;
                margin: 0;
                padding: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 2px 3px;
            }}
            .header {{
                text-align: center;
                font-weight: bold;
            }}
            .detail {{
                text-align: left;
                border-bottom: 1px dotted #ccc;
            }}
            .amount {{
                text-align: right;
                font-weight: bold;
            }}
            .separator {{
                border-top: 1px dashed black;
                margin: 3px 0;
            }}
            .product-line {{
                border-bottom: 1px dotted #eee;
            }}
            .totals {{
                margin-top: 5px;
                border-top: 1px solid black;
            }}
        </style>
    </head>
    <body>
        <table>
            <!-- Encabezado -->
            <tr>
                <th class="header" colspan="2" id="seccion_tipo_factura">
                    <span id="tipo_factura_text">{tipo_factura}</span><br>
                    <span id="subtitulo_text">{subtitulo}</span>
                </th>
            </tr>
            <tr>
                <td class="header" colspan="2" id="seccion_empresa_info">
                    <span id="razon_social">{razon_social}</span><br>
                    <span id="nombre_sucursal">{nombre_sucursal}</span><br>
                    <span id="codigo_punto_venta">Punto de Venta: {codigo_punto_venta}</span>
                </td>
            </tr>
            <tr>
                <td class="header" colspan="2" id="seccion_direccion_info">
                    <span id="direccion">{direccion}</span><br>
                    <span id="municipio">{municipio}</span><br>
                    <span id="telefono_empresa">Tel: {telefono_empresa}</span>
                </td>
            </tr>
            <tr><td class="separator" colspan="2"></td></tr>
            
            <!-- Información de la factura -->
            <tr>
                <td class="header" colspan="2">
                    <strong id="texto_nit">NIT:</strong> <span id="nit">{nit}</span><br>
                    <strong id="texto_numero_factura">Factura N°:</strong> <span id="numero_factura">{numero_factura}</span>
                </td>
            </tr>
            <tr>
                <th class="header" colspan="2" id="texto_cuf">
                    Código de Autorización:<br><span id="cuf">{cuf}</span>
                </th>
            </tr>
            <tr><td class="separator" colspan="2"></td></tr>
            
            <!-- Información del cliente -->
            <tr>
                <td class="header" colspan="2" id="seccion_cliente_info">
                    <strong id="texto_nombre_mayusculas">Nombre/Razón Social:</strong> <span id="nombre_mayusculas">{nombre_mayusculas}</span><br>
                    <strong id="texto_numero_documento">NIT/CI/CEX:</strong> <span id="numero_documento">{numero_documento}</span><br>
                    <strong id="texto_cod_cliente">Cod. Cliente:</strong> <span id="cod_cliente">{numero_documento}</span><br>
                    <strong id="texto_fecha_emision">Fecha de Emisión:</strong> <span id="fecha_emision">{fecha_emision}</span>
                </td>
            </tr>
            <tr><td class="separator" colspan="2"></td></tr>
            
            <!-- Encabezado de productos -->
            <tr>
                <th class="header" colspan="2">DETALLE</th>
            </tr>
    """

    # Agregar detalles de productos
    for linea in lineas_productos:
        try:
            precio_unitario = float(linea["precio_venta"])
            cantidad = float(linea["cantidad"])
            subtotal_linea = float(linea["sub_total"])
            descuento = float(linea.get("montoDescuento", 0))
        except (ValueError, TypeError):
            precio_unitario = cantidad = subtotal_linea = descuento = 0.0

        html_content += f"""
            <tr class="seccion_product-line">
                <td class="detail" id="detalle_{linea['codigo']}_info">
                    <strong id="detalle_{linea['codigo']}_nombre">{linea["codigo"]} - {linea["nombre"]}</strong><br>
                    <span id="detalle_{linea['codigo']}_unidad">{linea["unidad"]}</span><br>
                    <span id="detalle_{linea['codigo']}_cantidad">{cantidad:.2f} x {precio_unitario:.2f}
                    {f'- Desc: {descuento:.2f}' if descuento > 0 else '0'}</span>
                </td>
                <td class="amount" id="detalle_{linea['codigo']}_monto">
                    {subtotal_linea:.2f}
                </td>
            </tr>
        """

    # Agregar sección de totales
    html_content += f"""
            <tr><td class="separator" colspan="2"></td></tr>
            <tr class="totals">
                <td class="detail">Sub Total:</td>
                <td class="amount" id="subtotal">{subtotal:.2f}</td>
            </tr>
            <tr>
                <td class="detail">Descuento:</td>
                <td class="amount" id="descuento_adicional">{descuento_adicional:.2f}</td>
            </tr>
            <tr>
                <td class="detail">Total:</td>
                <td class="amount" id="total">{total:.2f}</td>
            </tr>
            <tr>
                <td class="detail">Gift Card:</td>
                <td class="amount" id="giftcard">{monto_giftcard:.2f}</td>
            </tr>
            <tr>
                <td class="detail">Monto a Pagar:</td>
                <td class="amount" id="total_final">{total_final:.2f}</td>
            </tr>
            <tr>
                <td class="detail">Imp. Base Cred. Fiscal:</td>
                <td class="amount" id="iva_base">{monto_total_sujeto_iva:.2f}</td>
            </tr>
            <tr>
                <td colspan="2" class="header" id="total_en_palabras">
                    Son: <span id="total_en_palabras_text">{total_en_palabras}</span>
                </td>
            </tr>
            <tr><td class="separator" colspan="2"></td></tr>
            <tr>
                <th colspan="2" id="leyenda" class="header">
                    <span id="leyenda_text">{leyenda}</span>
                </th>
            </tr>
        </table>
    </body>
    </html>
    """
    return html_content

def generate_compact_invoice_text(subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura, metodo_de_pago=None, codigo_clasificador_metodo_pago=None, tipo_documento=None, codigo_clasificador_documento=None, numero_documento=None, complemento=None, email=None, telefono=None, ultimos_digitos_tarjeta=None):
    total = subtotal - descuento_adicional
    total_final = total - monto_giftcard
    
    if codigo_clasificador_metodo_pago in gift_card_codes:
        monto_total_sujeto_iva = total - monto_giftcard
    else:
        monto_total_sujeto_iva = total

    # Convertir el total a palabras para la impresión en la factura
    total_en_palabras = numero_a_palabras_con_decimales_como_fraccion(total, lang='es') if total else ""

    leyenda = fetch_random_leyenda()

    # Variables obtenidas desde el entorno
    nit = os.getenv('NIT')
    razon_social = os.getenv('RAZON_SOCIAL')
    nombre_sucursal = os.getenv('NOMBRE_SUCURSAL')
    codigo_punto_venta = os.getenv('CODIGO_PUNTO_VENTA')
    direccion = os.getenv('DIRECCION')
    municipio = os.getenv('MUNICIPIO')
    telefono_empresa = os.getenv('TELEFONO')
    tipo_factura = os.getenv('DESCRIPCION_TIPO_FACTURA')
    subtitulo = os.getenv('SUBTITULO')

    nombre_mayusculas = nombre_cliente.upper()

    
    # Generar el contenido de la factura en formato texto
    factura_texto = f"""
    {tipo_factura.center(40)}\n
    {subtitulo.center(40)}\n
    {razon_social.center(40)}\n
    {nombre_sucursal.center(40)}\n
    Punto de Venta: {codigo_punto_venta}\n
    {direccion}\n
    {municipio}\n
    Teléfono: {telefono_empresa}\n
    {"-"*40}\n
    NIT: {nit}\n
    Factura N°: {numero_factura}\n
    Código de Autorización:\n
    CUF: {codigo_clasificador_metodo_pago}\n
    {"-"*40}\n
    Fecha/Hora: {fecha_emision}\n
    Nombre/Razón Social: {nombre_mayusculas}\n
    NIT/CI/CEX: {numero_documento}\n
    Cod. Cliente: {numero_documento}\n
    {"-"*40}\n
    DETALLE\n
    {"-"*40}\n"""

    # Agregar cada producto con formato específico
    for linea in lineas_productos:
        factura_texto += f"{linea['codigo']} - {linea['nombre']}\n"
        factura_texto += f"{linea['cantidad']}x{linea['precio_venta']:.2f} Bs   SubTotal: {linea['sub_total']:.2f} Bs\n"

    # Totales
    factura_texto += f"""
    {"-"*40}
    Sub Total:      {subtotal:.2f} Bs\n
    Descuento:      {descuento_adicional:.2f} Bs\n
    Total:          {total:.2f} Bs\n
    Gift Card:      {monto_giftcard:.2f} Bs\n
    Monto a Pagar:  {total_final:.2f} Bs\n
    {"-"*40}
    Base Cred. Fiscal: {monto_total_sujeto_iva:.2f} Bs\n
    Son: {total_en_palabras}\n
    {"-"*40}
    ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS, EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE ACUERDO A LEY.
    \n{leyenda}\n
    "Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido en una modalidad de facturación en línea."
    """

    return factura_texto