import pandas as pd
from decimal import Decimal
from data_access import obtener_nombre_unidad_medida  # Asegúrate de importar la función

def calculate_totals(comandas_seleccionadas, descuento_adicional=Decimal(0), monto_giftcard=Decimal(0), codigo_clasificador_metodo_pago=None, tipo_cambio=1):
    gift_card_codes = [
        102, 109, 115, 120, 124, 128, 129, 130, 138, 146, 153, 159, 164, 168,
        172, 173, 174, 182, 189, 195, 200, 204, 208, 209, 210, 217, 221, 222,
        223, 224, 225, 226, 228, 232, 241, 246, 250, 254, 255, 256, 261, 265,
        269, 270, 271, 275, 279, 280, 281, 285, 286, 287, 291, 292, 293, 30,
        304, 35, 40, 49, 53, 60, 64, 68, 72, 76, 77, 78, 86, 94
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
                "precio_venta": "{:.2f}".format(float(comanda["precio_venta"])),
                "cantidad": int(comanda["cantidad"]),
                "sub_total": (float(comanda["precio_venta"]) * int(comanda["cantidad"])),
                "codigo": codigo_producto,
                "unidad": unidad_medida  # Asignar el nombre de la unidad de medida
            }
            lineas_productos.append(linea_producto)

    # Agrupar productos repetidos
    df = pd.DataFrame(lineas_productos)
    df_grouped = df.groupby(['nombre', 'precio_venta', 'codigo', 'unidad']).agg({
        'cantidad': 'sum',
        'sub_total': 'sum'
    }).reset_index()
    return df_grouped.to_dict(orient='records')