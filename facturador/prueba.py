from typing import Dict, List, Optional

def generate_txt_file(nit_emisor: int, razon_social_emisor: str, municipio: str, telefono: Optional[str],
                      numero_factura: int, cuf: str, cufd: str, codigo_sucursal: int, direccion: str,
                      codigo_punto_venta: Optional[int], fecha_emision: str, nombre_razon_social: str,
                      codigo_tipo_documento_identidad: int, numero_documento: str, complemento: Optional[str], 
                      codigo_cliente: str, codigo_metodo_pago: int, ultimos_digitos_tarjeta: Optional[str], 
                      monto_total: float, monto_total_sujeto_iva: float, codigo_moneda: int, tipo_cambio: float, 
                      monto_total_moneda: float, monto_giftcard: Optional[float], descuento_adicional: Optional[float], 
                      leyenda: str, usuario: str, codigo_documento_sector: int, lineas_productos: List[Dict[str, str]]) -> None:
    # Crear el contenido del archivo de texto
    content = f"""
    nit_emisor: {nit_emisor}
    razon_social_emisor: {razon_social_emisor}
    municipio: {municipio}
    telefono: {telefono}
    numero_factura: {numero_factura}
    cuf: {cuf}
    cufd: {cufd}
    codigo_sucursal: {codigo_sucursal}
    direccion: {direccion}
    codigo_punto_venta: {codigo_punto_venta}
    fecha_emision: {fecha_emision}
    nombre_razon_social: {nombre_razon_social}
    codigo_tipo_documento_identidad: {codigo_tipo_documento_identidad}
    numero_documento: {numero_documento}
    complemento: {complemento}
    codigo_cliente: {codigo_cliente}
    codigo_metodo_pago: {codigo_metodo_pago}
    ultimos_digitos_tarjeta: {ultimos_digitos_tarjeta}
    monto_total: {monto_total}
    monto_total_sujeto_iva: {monto_total_sujeto_iva}
    codigo_moneda: {codigo_moneda}
    tipo_cambio: {tipo_cambio}
    monto_total_moneda: {monto_total_moneda}
    monto_giftcard: {monto_giftcard}
    descuento_adicional: {descuento_adicional}
    leyenda: {leyenda}
    usuario: {usuario}
    codigo_documento_sector: {codigo_documento_sector}
    lineas_productos: {lineas_productos}
    """
    # Guardar el contenido en un archivo de texto
    with open("factura_datos.txt", "w", encoding="utf-8") as file:
        file.write(content.strip())
