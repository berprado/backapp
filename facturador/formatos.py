import os
from ui import fetch_random_leyenda
from ui import numero_a_palabras_con_decimales_como_fraccion
from ui import gift_card_codes



def generate_html_invoice_tabla(subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura, metodo_de_pago=None, codigo_clasificador_metodo_pago=None, tipo_documento=None, codigo_clasificador_documento=None, numero_documento=None, complemento=None, email=None, telefono=None, ultimos_digitos_tarjeta=None):
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
        <td class="tg-n17z" colspan="4"><span style="font-weight:bold">Fecha/Hora:</span> {fecha_emision}<br><span style="font-weight:bold">Nombre/Razón Social:</span> {nombre_cliente}</td>
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
        <td class="tg-n17z" colspan="5"><span class="tg-q5sf">ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS, EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE ACUERDO A LEY</span><br><br><span style="font-weight:bold">{leyenda}</span><br><br><span class="tg-q5sf">“Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido en una modalidad de facturación en línea”</span></td>
        <td class="tg-n17z" colspan="2">{{codigo_qr}}</td>
    </tr>
    </tbody></table>
    </body>
    </html>
    """
    return html_content


def generate_html_invoice_rollo(subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura, metodo_de_pago=None, codigo_clasificador_metodo_pago=None, tipo_documento=None, codigo_clasificador_documento=None, numero_documento=None, complemento=None, email=None, telefono=None, ultimos_digitos_tarjeta=None):
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
        <td class="tg-n17z" colspan="4"><span style="font-weight:bold">Fecha/Hora:</span> {fecha_emision}<br><span style="font-weight:bold">Nombre/Razón Social:</span> {nombre_cliente}</td>
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
        <td class="tg-n17z" colspan="5"><span class="tg-q5sf">ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS, EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE ACUERDO A LEY</span><br><br><span style="font-weight:bold">{leyenda}</span><br><br><span class="tg-q5sf">“Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido en una modalidad de facturación en línea”</span></td>
        <td class="tg-n17z" colspan="2">{{codigo_qr}}</td>
    </tr>
    </tbody></table>
    </body>
    </html>
    """
    return html_content