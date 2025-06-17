import os
import sys
# Agregar la ruta del directorio padre al path de Python si no está ya
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from datetime import datetime
from database import SessionLocal
from sqlalchemy.exc import SQLAlchemyError
from facturador import models
import traceback
import logging
from logger_config import get_logger, get_facturacion_logger

# Obtener loggers para este módulo
logger = get_logger()
facturacion_logger = get_facturacion_logger()

def calcula_digito_mod11(cadena, num_dig=1, lim_mult=9, x10=False):
    if not x10:
        num_dig = 1

    for n in range(1, num_dig + 1):
        suma = 0
        mult = 2

        for i in range(len(cadena) - 1, -1, -1):
            suma += mult * int(cadena[i])
            mult += 1
            if mult > lim_mult:
                mult = 2

        if x10:
            dig = ((suma * 10) % 11) % 10
        else:
            dig = suma % 11

        if dig == 10:
            cadena += '1'
        elif dig == 11:
            cadena += '0'
        else:
            cadena += str(dig)

    return cadena[-num_dig:]

def generate_cuf(nit, fecha_emision, codigoSucursal, codigoModalidad, tipoEmision, tipoFactura, tipoDocumentoSector, numeroFactura, puntoVenta=None):
    try:
        facturacion_logger.info(f"Generando CUF para factura {numeroFactura}")
        # Completar cada campo según la longitud definida con ceros a la izquierda
        nit_emisor = f"{int(nit):013d}"
        
        # Asegurar que la fecha_hora esté en formato yyyyMMddHHmmssSSS
        if isinstance(fecha_emision, datetime):
            fecha_hora_str = fecha_emision.strftime("%Y%m%d%H%M%S%f")[:-3]
        else:
            fecha_hora_str = fecha_emision  # Asumiendo que se pasa un string formateado si no es datetime
        
        # Comprobar que fecha_hora tenga la longitud correcta
        if len(fecha_hora_str) != 17:
            raise ValueError("La fecha y hora deben estar en el formato yyyyMMddHHmmssSSS y tener 17 caracteres.")
        
        sucursal = f"{int(codigoSucursal):04d}"
        modalidad = f"{int(codigoModalidad):01d}"
        tipo_emision = f"{int(tipoEmision):01d}"
        tipo_factura = f"{int(tipoFactura):01d}"
        tipo_documento = f"{int(tipoDocumentoSector):02d}"
        numero_factura = f"{int(numeroFactura):010d}"
        punto_venta = f"{int(puntoVenta):04d}" if puntoVenta is not None else "0000"

        # Concatenar los campos
        cadena = f"{nit_emisor}{fecha_hora_str}{sucursal}{modalidad}{tipo_emision}{tipo_factura}{tipo_documento}{numero_factura}{punto_venta}"
        
        # Obtener el módulo 11 de la cadena y adjuntarlo al final
        verificador = calcula_digito_mod11(cadena)
        cadena += verificador

        # Aplicar la conversión a Base 16
        cuf_base16 = hex(int(cadena))[2:].upper()

        # Obtener el código de control desde la base de datos
        codigo_control = get_codigo_control_cufd()
        if not codigo_control:
            raise ValueError("No se pudo obtener el código de control CUFD.")
        
        # Concatenar el resultado con el código de control
        cuf = f"{cuf_base16}{codigo_control}"
        
        logging.info(f"El CUF generado es: {cuf}")
        
        return cuf
    except Exception as e:
        facturacion_logger.error(f"Error al generar CUF: {e}")
        facturacion_logger.error(traceback.format_exc())

def get_codigo_control_cufd():
    session = SessionLocal()
    try:
        cufd = session.query(models.Cufd).filter_by(vigente=1).first()
        return cufd.codigo_control if cufd else None
    except SQLAlchemyError as e:
        logging.error(f"Error al obtener el código de control CUFD: {e}")
        return None
    finally:
        session.close()
