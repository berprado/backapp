from datetime import datetime
from database import SessionLocal
from sqlalchemy.exc import SQLAlchemyError
import models
import logging


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

def generate_cuf(nit_emisor, fecha_hora, sucursal, modalidad, tipo_emision, tipo_factura, tipo_documento, numero_factura, punto_venta):
    # Completar cada campo según la longitud definida con ceros a la izquierda
    nit_emisor = f"{int(nit_emisor):013d}"
    
    # Asegurar que la fecha_hora esté en formato yyyyMMddHHmmssSSS
    if isinstance(fecha_hora, datetime):
        fecha_hora_str = fecha_hora.strftime("%Y%m%d%H%M%S%f")[:-3]
    else:
        fecha_hora_str = fecha_hora  # Asumiendo que se pasa un string formateado si no es datetime
    
    # Comprobar que fecha_hora tenga la longitud correcta
    if len(fecha_hora_str) != 17:
        raise ValueError("La fecha y hora deben estar en el formato yyyyMMddHHmmssSSS y tener 17 caracteres.")
    
    sucursal = f"{int(sucursal):04d}"
    modalidad = f"{int(modalidad):01d}"
    tipo_emision = f"{int(tipo_emision):01d}"
    tipo_factura = f"{int(tipo_factura):01d}"
    tipo_documento = f"{int(tipo_documento):02d}"
    numero_factura = f"{int(numero_factura):010d}"
    punto_venta = f"{int(punto_venta):04d}"

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

def generate_cuf(nit_emisor, fecha_hora, sucursal, modalidad, tipo_emision, tipo_factura, tipo_documento, numero_factura, punto_venta):
    # Completar cada campo según la longitud definida con ceros a la izquierda
    nit_emisor = f"{int(nit_emisor):013d}"
    
    # Asegurar que la fecha_hora esté en formato yyyyMMddHHmmssSSS
    if isinstance(fecha_hora, datetime):
        fecha_hora_str = fecha_hora.strftime("%Y%m%d%H%M%S%f")[:-3]
    else:
        fecha_hora_str = fecha_hora  # Asumiendo que se pasa un string formateado si no es datetime
    
    # Comprobar que fecha_hora tenga la longitud correcta
    if len(fecha_hora_str) != 17:
        raise ValueError("La fecha y hora deben estar en el formato yyyyMMddHHmmssSSS y tener 17 caracteres.")
    
    sucursal = f"{int(sucursal):04d}"
    modalidad = f"{int(modalidad):01d}"
    tipo_emision = f"{int(tipo_emision):01d}"
    tipo_factura = f"{int(tipo_factura):01d}"
    tipo_documento = f"{int(tipo_documento):02d}"
    numero_factura = f"{int(numero_factura):010d}"
    punto_venta = f"{int(punto_venta):04d}"

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
