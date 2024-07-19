import xml.etree.ElementTree as ET
import os
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

import logging

# Configure logging level
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    filename='invoice_log.txt')

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
    "Unid": 1,
    "Litro": 2,
    "Kilogramo": 3,
    # Añade otros valores necesarios según el esquema XSD
}

XSD_PATH = "schemas/facturaElectronicaCompraVenta.xsd"  # Ruta del archivo XSD
XML_FOLDER_PATH = "xmls"  # Carpeta donde se guardarán los archivos XML    

def validate_and_format_datetime(value: str) -> str:
    try:
        # Intentar convertir la cadena en un objeto datetime
        logging.debug("Validando y formateando la fecha: %s", value)
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
        # Convertir de nuevo a cadena en el formato requerido
        formatted_date = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        logging.info("Fecha validada y formateada correctamente: %s", formatted_date)
        return formatted_date
    except ValueError:
        logging.error("Fecha inválida: %s. Formato esperado: YYYY-MM-DDTHH:MM:SS.sss", value)
        raise ValueError(f"Invalid dateTime value: {value}. Expected format: YYYY-MM-DDTHH:MM:SS.sss")

def generate_xml_invoice(nit_emisor: int, razon_social_emisor: str, municipio: str, telefono: Optional[str],
                         numero_factura: int, cuf: str, cufd: str, codigo_sucursal: int, direccion: str,
                         codigo_punto_venta: Optional[int], fecha_emision: str, nombre_razon_social: Optional[str],
                         codigo_tipo_documento_identidad: int, numero_documento: str, complemento: Optional[str], 
                         codigo_cliente: str, codigo_metodo_pago: int, ultimos_digitos_tarjeta: Optional[str], 
                         subtotal: float, total: float, codigo_moneda: int, tipo_cambio: float, 
                         monto_total_moneda: float, monto_giftcard: Optional[float], descuento_adicional: Optional[float], 
                         leyenda: str, usuario: str, codigo_documento_sector: int, lineas_productos: List[Dict[str, str]]) -> str:

    logging.info("Iniciando la generación del XML de la factura.")
    logging.debug("Valores recibidos: nit_emisor=%s, razon_social_emisor=%s, municipio=%s, telefono=%s, numero_factura=%s, cuf=%s, cufd=%s, codigo_sucursal=%s, direccion=%s, codigo_punto_venta=%s, fecha_emision=%s, nombre_razon_social=%s, codigo_tipo_documento_identidad=%s, numero_documento=%s, complemento=%s, codigo_cliente=%s, codigo_metodo_pago=%s, ultimos_digitos_tarjeta=%s, subtotal=%s, total=%s, codigo_moneda=%s, tipo_cambio=%s, monto_total_moneda=%s, monto_giftcard=%s, descuento_adicional=%s, leyenda=%s, usuario=%s, codigo_documento_sector=%s, lineas_productos=%s", nit_emisor, razon_social_emisor, municipio, telefono, numero_factura, cuf, cufd, codigo_sucursal, direccion, codigo_punto_venta, fecha_emision, nombre_razon_social, codigo_tipo_documento_identidad, numero_documento, complemento, codigo_cliente, codigo_metodo_pago, ultimos_digitos_tarjeta, subtotal, total, codigo_moneda, tipo_cambio, monto_total_moneda, monto_giftcard, descuento_adicional, leyenda, usuario, codigo_documento_sector, lineas_productos)

    # Validar y formatear fechaEmision
    fecha_emision = validate_and_format_datetime(fecha_emision)

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
    
    ET.SubElement(cabecera, "montoTotal").text = "{:.2f}".format(total)  # montoTotal original antes de aplicar la gift card
    ET.SubElement(cabecera, "montoTotalSujetoIva").text = "{:.2f}".format(total - monto_giftcard if monto_giftcard else total)
    ET.SubElement(cabecera, "codigoMoneda").text = str(codigo_moneda)
    ET.SubElement(cabecera, "tipoCambio").text = "{:.2f}".format(tipo_cambio)
    ET.SubElement(cabecera, "montoTotalMoneda").text = "{:.2f}".format(total / tipo_cambio)  # montoTotalMoneda = montoTotal / tipoCambio
    
    # Manejo de nillable para montoGiftCard
    if monto_giftcard is not None:
        ET.SubElement(cabecera, "montoGiftCard").text = str(monto_giftcard)
    else:
        ET.SubElement(cabecera, "montoGiftCard", attrib={"xsi:nil": "true"})
    
    # Manejo de nillable para descuentoAdicional
    if descuento_adicional is not None:
        ET.SubElement(cabecera, "descuentoAdicional").text = str(descuento_adicional)
    else:
        ET.SubElement(cabecera, "descuentoAdicional", attrib={"xsi:nil": "true"})
    
    ET.SubElement(cabecera, "codigoExcepcion", attrib={"xsi:nil": "true"})
    ET.SubElement(cabecera, "cafc", attrib={"xsi:nil": "true"})
    ET.SubElement(cabecera, "leyenda").text = leyenda
    ET.SubElement(cabecera, "usuario").text = usuario
    ET.SubElement(cabecera, "codigoDocumentoSector").text = str(codigo_documento_sector)

    for linea in lineas_productos:
        logging.debug("Procesando la línea de producto: %s", linea)
        detalle = ET.SubElement(factura, "detalle")
        ET.SubElement(detalle, "actividadEconomica").text = str(ACTIVIDAD_ECONOMICA)
        ET.SubElement(detalle, "codigoProductoSin").text = str(CODIGO_PRODUCTO_SIN)
        ET.SubElement(detalle, "codigoProducto").text = str(linea["codigo"])
        ET.SubElement(detalle, "descripcion").text = str(linea["nombre"])
        ET.SubElement(detalle, "cantidad").text = str(linea["cantidad"])
        unidad_medida_codigo = UNIDAD_MEDIDA_MAP.get(linea["unidad"], 1)  # Usa 1 (Unid) como valor predeterminado
        ET.SubElement(detalle, "unidadMedida").text = str(unidad_medida_codigo)
        ET.SubElement(detalle, "precioUnitario").text = str(linea["precio_venta"])
        
        # Manejo de nillable para montoDescuento
        if linea.get("montoDescuento") is not None:
            ET.SubElement(detalle, "montoDescuento").text = str(linea["montoDescuento"])
        else:
            ET.SubElement(detalle, "montoDescuento", attrib={"xsi:nil": "true"})
        
        ET.SubElement(detalle, "subTotal").text = str(linea["sub_total"])
        
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

    xml_string = ET.tostring(factura, encoding='utf-8', method='xml').decode('utf-8')
    
    # Guardar el XML antes de ser canonicalizado
    initial_xml_filename = f"{XML_FOLDER_PATH}/factura_{cuf}_antes_de_canonicalizar.xml"
    with open(initial_xml_filename, "w", encoding='utf-8') as initial_xml_file:
        initial_xml_file.write(xml_string)
    logging.info(f"XML inicial guardado en {initial_xml_filename}")

    logging.info("XML de la factura generado correctamente.")
    logging.debug(f"XML Generado:\n{xml_string}")
    return xml_string