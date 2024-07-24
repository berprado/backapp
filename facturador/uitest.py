import streamlit as st
from database import SessionLocal, engine, URL_DATABASE
import models
from config import ENDPOINT_URL
import os
from dotenv import load_dotenv
from models import FacturaCabecera, FacturaDetalle, SincronizarListaLeyendasFactura
from sqlalchemy import create_engine, Table, Column, Integer, String, DECIMAL, MetaData, TIMESTAMP, Text, BIGINT, ForeignKeyConstraint
from sqlalchemy.dialects.mysql import VARCHAR
from typing import Dict, Union
from sqlalchemy.exc import SQLAlchemyError
import logging
from business_logic import calculate_totals, collect_product_lines
from invoice_xml_generator import generate_xml_invoice
from decimal import Decimal

# Cargar variables de entorno
load_dotenv()

# Obtener valores de .env
ACTIVIDAD_ECONOMICA = os.getenv('ACTIVIDAD_ECONOMICA')
CODIGO_PRODUCTO_SIN = os.getenv('CODIGO_PRODUCTO_SIN')
DESCUENTO = os.getenv('DESCUENTO')
CODIGO_PUNTO_VENTA = os.getenv('CODIGO_PUNTO_VENTA')  # Punto de venta por defecto
CODIGO_SUCURSAL = os.getenv('CODIGO_SUCURSAL')  # Sucursal por defecto

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    filename='invoice_log.txt')

def validar_factura_cabecera(factura_cabecera_data):
    required_fields = [
        'nitEmisor', 'razonSocialEmisor', 'municipio', 'numeroFactura', 'cuf', 'cufd', 
        'codigoSucursal', 'direccion', 'fechaEmision', 'codigoTipoDocumentoIdentidad', 
        'numeroDocumento', 'codigoCliente', 'codigoMetodoPago', 'montoTotal', 'montoTotalSujetoIva', 
        'codigoMoneda', 'tipoCambio', 'montoTotalMoneda', 'leyenda', 'usuario', 'codigoDocumentoSector'
    ]
    
    for field in required_fields:
        if factura_cabecera_data.get(field) is None or factura_cabecera_data.get(field) == '':
            return False, f"El campo {field} es requerido y no puede estar vacío."
    
    return True, ""

def validar_factura_detalle(factura_detalle_data):
    required_fields = [
        'numeroFactura', 'actividadEconomica', 'codigoProductoSin', 'codigoProducto', 
        'descripcion', 'cantidad', 'unidadMedida', 'precioUnitario', 'subTotal'
    ]
    
    for field in required_fields:
        if factura_detalle_data.get(field) is None or factura_detalle_data.get(field) == '':
            return False, f"El campo {field} es requerido y no puede estar vacío."
    
    return True, ""

def guardar_factura_cabecera(cabecera_data):
    session = SessionLocal()
    try:
        nueva_factura_cabecera = FacturaCabecera(**cabecera_data)
        session.add(nueva_factura_cabecera)
        session.commit()
        return nueva_factura_cabecera.numeroFactura
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error al guardar la cabecera de la factura: {e}")
        st.error(f"Error al guardar la cabecera de la factura: {e}")
    finally:
        session.close()

def guardar_factura_detalle(detalle_data):
    session = SessionLocal()
    try:
        nuevo_factura_detalle = FacturaDetalle(**detalle_data)
        session.add(nuevo_factura_detalle)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error al guardar el detalle de la factura: {e}")
        st.error(f"Error al guardar el detalle de la factura: {e}")
    finally:
        session.close()

def obtener_siguiente_numero_factura():
    session = SessionLocal()
    try:
        ultimo_numero_factura = session.query(FacturaCabecera).order_by(FacturaCabecera.numeroFactura.desc()).first()
        if ultimo_numero_factura:
            return ultimo_numero_factura.numeroFactura + 1
        else:
            return 1  # Comienza desde 1 si no hay facturas previas
    except SQLAlchemyError as e:
        logging.error(f"Error al obtener el siguiente número de factura: {e}")
        st.error(f"Error al obtener el siguiente número de factura: {e}")
        return None
    finally:
        session.close()

def main():
    st.title("Generación de Factura Electrónica")
    
    # Cargar datos de la factura
    # Aquí puedes obtener los datos desde la interfaz o desde otro origen de datos
    comandas = [
        {"id_comanda": 1, "nombre": "Producto A", "precio_venta": 100, "cantidad": 2, "id_producto_combo": 101, "unidad": "Unid", "sub_total": 200},
        {"id_comanda": 2, "nombre": "Producto B", "precio_venta": 200, "cantidad": 1, "id_producto_combo": 102, "unidad": "Unid", "sub_total": 200}
    ]  # Lista de comandas
    selected_id_comanda = [1, 2]  # Lista de ID de comandas seleccionadas
    
    # Obtener el número de factura
    numero_factura = obtener_siguiente_numero_factura()
    if numero_factura is None:
        st.error("No se pudo obtener el número de factura.")
        return

    # Calcular los totales de la factura
    subtotal, descuento_adicional, monto_giftcard, total, monto_total_sujeto_iva, monto_total_moneda = calculate_totals(
        comandas_seleccionadas=comandas, 
        descuento_adicional=Decimal(0), 
        monto_giftcard=Decimal(0), 
        codigo_clasificador_metodo_pago=None, 
        tipo_cambio=1
    )

    # Recoger las líneas de productos
    lineas_productos = collect_product_lines(comandas, selected_id_comanda, numero_factura)

    # Asegurarse de que hay líneas de productos
    if not lineas_productos:
        st.error("No hay líneas de productos para la factura.")
        return

    # Generar el XML de la factura
    xml_string, cabecera_data, detalles_data = generate_xml_invoice(
        nit_emisor=344096024, razon_social_emisor="BOLIVIAN FOODS & DRINKS S.R.L.", municipio="LA PAZ", 
        telefono="65560514", numero_factura=numero_factura, cuf="178B4ssqq3EFDB9wsdd5AF31DCEA48D0FB0219B1A7C1A6B2C567A444B094D8E74", 
        cufd="BQW9Dfm9pQUE=N0jIwOUI5RDBENjY=Qnx6QXhBWUhZVUFM0OEY3NkRBRkU0R", codigo_sucursal=0, 
        direccion="AVENIDA MONTENEGRO NRO. SN EDIF.: ARACELY PISO: PB DEPTO.: BLOQUE E7 ZONA/BARRIO: SAN MIGUEL", 
        codigo_punto_venta=0, fecha_emision="2024-07-23T05:15:12.805", nombre_razon_social="prado", 
        codigo_tipo_documento_identidad=5, numero_documento="344096024", complemento=None, 
        codigo_cliente="344096024", codigo_metodo_pago=1, ultimos_digitos_tarjeta=None, 
        subtotal=subtotal, total=total, codigo_moneda=1, tipo_cambio=1, monto_total_moneda=monto_total_moneda, 
        monto_giftcard=monto_giftcard, descuento_adicional=descuento_adicional, usuario="don_bercho", 
        codigo_documento_sector=1, lineas_productos=lineas_productos, 
        actividad_economica="561110", codigo_producto_sin="99100"
    )

    # Validar la factura
    is_valid, error_message = validar_factura_cabecera(cabecera_data)
    if is_valid:
        guardar_factura_cabecera(cabecera_data)
    else:
        st.error(error_message)
        return

    # Validar y guardar detalles de la factura
    for detalle in detalles_data:
        is_valid, error_message = validar_factura_detalle(detalle)
        if is_valid:
            guardar_factura_detalle(detalle)
        else:
            st.error(error_message)
            return

if __name__ == "__main__":
    main()
