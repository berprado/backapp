# Description: Lógica de negocio para el cálculo de totales y agrupación de productos

import pandas as pd

def calculate_totals(comandas_seleccionadas):
    total = sum(float(comanda["sub_total"]) for comanda in comandas_seleccionadas)
    descuento = 0 # Implementar la lógica de cálculo de descuentos
    total_final = total - descuento
    return total, descuento, total_final

def collect_product_lines(comandas, selected_id_comanda):
    lineas_productos = []
    for comanda in comandas:
        if comanda["id_comanda"] in selected_id_comanda:
            linea_producto = {
                "nombre": comanda["nombre"],
                "precio_venta": "{:.2f}".format(float(comanda["precio_venta"])),
                "cantidad": int(comanda["cantidad"]),
                "sub_total":(float(comanda["precio_venta"]) * int(comanda["cantidad"])),
                "codigo": comanda["id_producto_combo"],  # Agregar el campo 'codigo'
                "unidad": comanda.get("unidad", "Unid")  # Asegurarse de incluir 'unidad' si existe
            }
            lineas_productos.append(linea_producto)

    # Agrupar productos repetidos
    df = pd.DataFrame(lineas_productos)
    df_grouped = df.groupby(['nombre', 'precio_venta', 'codigo', 'unidad']).agg({
        'cantidad': 'sum',
        'sub_total': 'sum'
    }).reset_index()
    return df_grouped.to_dict(orient='records')



