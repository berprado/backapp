import xml.etree.ElementTree as ET
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from data_access import guardar_factura_cabecera, guardar_factura_detalle, fetch_random_leyenda
from logger_config import get_xml_logger

# Obtener el logger específico para XML
logger = get_xml_logger()

# Cargar variables de entorno
load_dotenv()

# Obtener valores de .env
ACTIVIDAD_ECONOMICA = os.getenv('ACTIVIDAD_ECONOMICA')
CODIGO_PRODUCTO_SIN = os.getenv('CODIGO_PRODUCTO_SIN')
DESCUENTO = os.getenv('DESCUENTO')
CODIGO_PUNTO_VENTA = os.getenv('CODIGO_PUNTO_VENTA')  # Punto de venta por defecto
CODIGO_SUCURSAL = os.getenv('CODIGO_SUCURSAL')  # Sucursal por defecto

# Mapeo de unidad de medida a códigos enteros
UNIDAD_MEDIDA_MAP = {
    "Unid": 57,
    "Litro": 2,
    "Kilogramo": 3,
    # Añade otros valores necesarios según el esquema XSD
}

XSD_PATH = "schemas/facturaElectronicaCompraVenta.xsd"  # Ruta del archivo XSD
XML_FOLDER_PATH = "xmls"  # Carpeta donde se guardarán los archivos XML    

def validate_and_format_datetime(value: str) -> str:
    try:
        # Intentar convertir la cadena en un objeto datetime
        logger.debug("Validando y formateando la fecha: %s", value)
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
        # Convertir de nuevo a cadena en el formato requerido
        formatted_date = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        logger.info("Fecha validada y formateada correctamente: %s", formatted_date)
        return formatted_date
    except ValueError:
        logger.error("Fecha inválida: %s. Formato esperado: YYYY-MM-DDTHH:MM:SS.sss", value)
        raise ValueError(f"Invalid dateTime value: {value}. Expected format: YYYY-MM-DDTHH:MM:SS.sss")

def generate_xml_invoice(nit_emisor: int, razon_social_emisor: str, municipio: str, telefono: Optional[str],
                         numero_factura: int, cuf: str, cufd: str, codigo_sucursal: int, direccion: str,
                         codigo_punto_venta: Optional[int], fecha_emision: str, nombre_razon_social: Optional[str],
                         codigo_tipo_documento_identidad: int, numero_documento: str, complemento: Optional[str], 
                         codigo_cliente: str, codigo_metodo_pago: int, ultimos_digitos_tarjeta: Optional[str], 
                         subtotal: float, total: float, codigo_moneda: int, tipo_cambio: float, 
                         monto_total_moneda: float, monto_giftcard: Optional[float], descuento_adicional: Optional[float], 
                         usuario: str, codigo_documento_sector: int, lineas_productos: List[Dict[str, str]],
                         actividad_economica: str, codigo_producto_sin: str) -> Tuple[str, Dict, List[Dict]]:

    logger.info("Iniciando la generación del XML de la factura.")
    logger.debug("Valores recibidos: nit_emisor=%s, razon_social_emisor=%s, municipio=%s, telefono=%s, numero_factura=%s, cuf=%s, cufd=%s, codigo_sucursal=%s, direccion=%s, codigo_punto_venta=%s, fecha_emision=%s, nombre_razon_social=%s, codigo_tipo_documento_identidad=%s, numero_documento=%s, complemento=%s, codigo_cliente=%s, codigo_metodo_pago=%s, ultimos_digitos_tarjeta=%s, subtotal=%s, total=%s, codigo_moneda=%s, tipo_cambio=%s, monto_total_moneda=%s, monto_giftcard=%s, descuento_adicional=%s, usuario=%s, codigo_documento_sector=%s, lineas_productos=%s", nit_emisor, razon_social_emisor, municipio, telefono, numero_factura, cuf, cufd, codigo_sucursal, direccion, codigo_punto_venta, fecha_emision, nombre_razon_social, codigo_tipo_documento_identidad, numero_documento, complemento, codigo_cliente, codigo_metodo_pago, ultimos_digitos_tarjeta, subtotal, total, codigo_moneda, tipo_cambio, monto_total_moneda, monto_giftcard, descuento_adicional, usuario, codigo_documento_sector, lineas_productos)

    # Validar y formatear fechaEmision
    fecha_emision = validate_and_format_datetime(fecha_emision)

    # Obtener leyenda aleatoria
    leyenda = fetch_random_leyenda()

    factura = ET.Element("facturaElectronicaCompraVenta", attrib={
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": XSD_PATH,
    })
    
    cabecera = ET.SubElement(factura, "cabecera")
    ET.SubElement(cabecera, "nitEmisor").text = str(nit_emisor)
    ET.SubElement(cabecera, "razonSocialEmisor").text = razon_social_emisor
    ET.SubElement(cabecera, "municipio").text = municipio
    
    # Manejo de nillable para telefono
    if telefono:
        ET.SubElement(cabecera, "telefono").text = telefono
    else:
        ET.SubElement(cabecera, "telefono", attrib={"xsi:nil": "true"})
    
    ET.SubElement(cabecera, "numeroFactura").text = str(numero_factura)
    ET.SubElement(cabecera, "cuf").text = cuf
    ET.SubElement(cabecera, "cufd").text = cufd
    ET.SubElement(cabecera, "codigoSucursal").text = str(codigo_sucursal)
    ET.SubElement(cabecera, "direccion").text = direccion
    
    # Manejo de nillable para codigoPuntoVenta
    if codigo_punto_venta is not None:
        ET.SubElement(cabecera, "codigoPuntoVenta").text = str(codigo_punto_venta)  # Punto de venta por defecto
    else:
        ET.SubElement(cabecera, "codigoPuntoVenta", attrib={"xsi:nil": "true"})
    
    ET.SubElement(cabecera, "fechaEmision").text = fecha_emision
    
    # Manejo de nillable para nombreRazonSocial
    if nombre_razon_social:
        ET.SubElement(cabecera, "nombreRazonSocial").text = nombre_razon_social.upper()
    else:
        ET.SubElement(cabecera, "nombreRazonSocial", attrib={"xsi:nil": "true"})
    
    ET.SubElement(cabecera, "codigoTipoDocumentoIdentidad").text = str(codigo_tipo_documento_identidad)
    ET.SubElement(cabecera, "numeroDocumento").text = numero_documento
    
    # Manejo de nillable para complemento
    if complemento:
        ET.SubElement(cabecera, "complemento").text = complemento
    else:
        ET.SubElement(cabecera, "complemento", attrib={"xsi:nil": "true"})
    
    ET.SubElement(cabecera, "codigoCliente").text = codigo_cliente
    ET.SubElement(cabecera, "codigoMetodoPago").text = str(codigo_metodo_pago)
    
    # Manejo de nillable para numeroTarjeta
    if ultimos_digitos_tarjeta:
        ET.SubElement(cabecera, "numeroTarjeta").text = ultimos_digitos_tarjeta
    else:
        ET.SubElement(cabecera, "numeroTarjeta", attrib={"xsi:nil": "true"})
    
    ET.SubElement(cabecera, "montoTotal").text = "{:.2f}".format(float(total))  # montoTotal original antes de aplicar la gift card
    ET.SubElement(cabecera, "montoTotalSujetoIva").text = "{:.2f}".format(float(total) - float(monto_giftcard) if monto_giftcard else float(total))
    ET.SubElement(cabecera, "codigoMoneda").text = str(codigo_moneda)
    ET.SubElement(cabecera, "tipoCambio").text = "{:.2f}".format(float(tipo_cambio))
    ET.SubElement(cabecera, "montoTotalMoneda").text = "{:.2f}".format(float(total) / float(tipo_cambio))  # montoTotalMoneda = montoTotal / tipoCambio
    
    # Manejo de nillable para montoGiftCard
    if monto_giftcard is not None:
        ET.SubElement(cabecera, "montoGiftCard").text = "{:.2f}".format(float(monto_giftcard))
    else:
        ET.SubElement(cabecera, "montoGiftCard", attrib={"xsi:nil": "true"})
    
    # Manejo de nillable para descuentoAdicional
    if descuento_adicional is not None:
        ET.SubElement(cabecera, "descuentoAdicional").text = "{:.2f}".format(float(descuento_adicional))
    else:
        ET.SubElement(cabecera, "descuentoAdicional", attrib={"xsi:nil": "true"})
    
    ET.SubElement(cabecera, "codigoExcepcion", attrib={"xsi:nil": "true"})
    ET.SubElement(cabecera, "cafc", attrib={"xsi:nil": "true"})
    ET.SubElement(cabecera, "leyenda").text = leyenda
    ET.SubElement(cabecera, "usuario").text = usuario
    ET.SubElement(cabecera, "codigoDocumentoSector").text = str(codigo_documento_sector)

    cabecera_data = {
        'nitEmisor': nit_emisor,
        'razonSocialEmisor': razon_social_emisor,
        'municipio': municipio,
        'telefono': telefono,
        'numeroFactura': numero_factura,
        'cuf': cuf,
        'cufd': cufd,
        'codigoSucursal': codigo_sucursal,
        'direccion': direccion,
        'codigoPuntoVenta': codigo_punto_venta,
        'fechaEmision': fecha_emision,
        'nombreRazonSocial': nombre_razon_social,
        'codigoTipoDocumentoIdentidad': codigo_tipo_documento_identidad,
        'numeroDocumento': numero_documento,
        'complemento': complemento,
        'codigoCliente': codigo_cliente,
        'codigoMetodoPago': codigo_metodo_pago,
        'numeroTarjeta': ultimos_digitos_tarjeta,
        'montoTotal': total,
        'montoTotalSujetoIva': total - monto_giftcard if monto_giftcard else total,
        'codigoMoneda': codigo_moneda,
        'tipoCambio': tipo_cambio,
        'montoTotalMoneda': total / tipo_cambio,
        'montoGiftCard': monto_giftcard,
        'descuentoAdicional': descuento_adicional,
        'codigoExcepcion': None,
        'cafc': None,
        'leyenda': leyenda,
        'usuario': usuario,
        'codigoDocumentoSector': codigo_documento_sector
    }

    detalles_data = []

    for linea in lineas_productos:
        logger.debug("Procesando la línea de producto: %s", linea)
        detalle = ET.SubElement(factura, "detalle")
        ET.SubElement(detalle, "actividadEconomica").text = str(actividad_economica)
        ET.SubElement(detalle, "codigoProductoSin").text = str(codigo_producto_sin)
        ET.SubElement(detalle, "codigoProducto").text = str(linea["codigo"])
        ET.SubElement(detalle, "descripcion").text = str(linea["nombre"])
        ET.SubElement(detalle, "cantidad").text = "{:.2f}".format(float(linea["cantidad"]))
        unidad_medida_codigo = UNIDAD_MEDIDA_MAP.get(linea["unidad"], 57)  # Usa 1 (Unid) como valor predeterminado
        ET.SubElement(detalle, "unidadMedida").text = str(unidad_medida_codigo)
        ET.SubElement(detalle, "precioUnitario").text = "{:.2f}".format(float(linea["precio_venta"]))
        
        # Manejo de nillable para montoDescuento
        if linea.get("montoDescuento") is not None:
            ET.SubElement(detalle, "montoDescuento").text = "{:.2f}".format(float(linea["montoDescuento"]))
        else:
            ET.SubElement(detalle, "montoDescuento", attrib={"xsi:nil": "true"})
        
        ET.SubElement(detalle, "subTotal").text = "{:.2f}".format(float(linea["sub_total"]))
        
        # Manejo de nillable para numeroSerie
        if linea.get("numeroSerie"):
            ET.SubElement(detalle, "numeroSerie").text = str(linea["numeroSerie"])
        else:
            ET.SubElement(detalle, "numeroSerie", attrib={"xsi:nil": "true"})
        
        # Manejo de nillable para numeroImei
        if linea.get("numeroImei"):
            ET.SubElement(detalle, "numeroImei").text = str(linea["numeroImei"])
        else:
            ET.SubElement(detalle, "numeroImei", attrib={"xsi:nil": "true"})

        detalles_data.append({
            'numeroFactura': numero_factura,  # Asegurando el número de factura en el detalle
            'actividadEconomica': actividad_economica,
            'codigoProductoSin': codigo_producto_sin,
            'codigoProducto': linea["codigo"],
            'descripcion': linea["nombre"],
            'cantidad': float(linea["cantidad"]),
            'unidadMedida': unidad_medida_codigo,
            'precioUnitario': float(linea["precio_venta"]),
            'montoDescuento': float(linea.get("montoDescuento", 0.00)),
            'subTotal': float(linea["sub_total"]),
            'numeroSerie': linea.get("numeroSerie"),
            'numeroImei': linea.get("numeroImei")
        })

    xml_string = ET.tostring(factura, encoding='utf-8', method='xml').decode('utf-8')
    logger.info("XML generado exitosamente para la factura #%s", numero_factura)
    return xml_string, cabecera_data, detalles_data