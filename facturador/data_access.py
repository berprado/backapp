import random
import requests
import streamlit as st
from database import SessionLocal, engine, URL_DATABASE
import models
from config import ENDPOINT_URL
import os
from dotenv import load_dotenv
from models import FacturaCabecera, FacturaDetalle, SincronizarListaLeyendasFactura
from sqlalchemy import create_engine, Table, Column, Integer, String, DECIMAL, MetaData, TIMESTAMP, Text, BIGINT, ForeignKeyConstraint
from sqlalchemy.dialects.mysql import VARCHAR
from typing import List, Dict, Union
from sqlalchemy.exc import SQLAlchemyError
import logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    filename='invoice_log.txt')
load_dotenv()
metadata = MetaData()

# Create the engine to connect to the database
engine = create_engine(URL_DATABASE)

@st.cache_resource
def fetch_comandas():
    try:
        response = requests.get(f"{ENDPOINT_URL}")
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return [], f"Error al obtener los id_comanda: {e}"

@st.cache_resource
def fetch_metodos_pago():
    session = SessionLocal()
    try:
        metodos = session.query(models.SincronizarParametricaTipoMetodoPago).all()
        if not metodos:
            return [], "No se encontraron métodos de pago"
        return [metodo.to_dict() for metodo in metodos], None
    except Exception as e:
        return [], f"Error al obtener los métodos de pago: {e}"
    finally:
        session.close()

@st.cache_resource
def fetch_tipos_documento():
    session = SessionLocal()
    try:
        documentos = session.query(models.SincronizarParametricaTipoDocumentoIdentidad).all()
        if not documentos:
            return [], "No se encontraron tipos de documento"
        return [documento.to_dict() for documento in documentos], None
    except Exception as e:
        return [], f"Error al obtener los tipos de documento: {e}"
    finally:
        session.close()

def fetch_cliente(numero_documento):
    session = SessionLocal()
    try:
        cliente = session.query(models.Cliente).filter(models.Cliente.codigo_cliente == numero_documento).first()
        if not cliente:
            return None, "Cliente no encontrado"
        return cliente.to_dict(), None
    except Exception as e:
        return None, f"Error al obtener el cliente: {e}"
    finally:
        session.close()

# Código de actividad económica desde el archivo .env
ACTIVIDAD_ECONOMICA = os.getenv('ACTIVIDAD_ECONOMICA')

# IDs de leyendas permitidos
LEYENDA_IDS = [2, 6, 9, 13, 19, 22, 27, 31]

def fetch_random_leyenda():
    session = SessionLocal()
    try:
        leyendas = session.query(SincronizarListaLeyendasFactura).filter(
            SincronizarListaLeyendasFactura.codigoActividad == ACTIVIDAD_ECONOMICA,
            SincronizarListaLeyendasFactura.id.in_(LEYENDA_IDS)
        ).all()
        if leyendas:
            return random.choice(leyendas).descripcionLeyenda
        return "Leyenda no encontrada"
    except Exception as e:
        return f"Error al obtener la leyenda: {e}"
    finally:
        session.close()

metadata = MetaData()

# Crear el motor de conexión a la base de datos
engine = create_engine(URL_DATABASE)

# Reflejar las tablas en la base de datos
metadata.create_all(engine)

def guardar_factura_cabecera(cabecera: Dict[str, Union[str, float, int]]) -> None:
    logging.debug(f"Preparando para almacenar la cabecera: {cabecera}")

    session = SessionLocal()
    try:
        query = models.FacturaCabecera.__table__.insert().values(
            nitEmisor=cabecera['nitEmisor'],
            razonSocialEmisor=cabecera['razonSocialEmisor'],
            municipio=cabecera['municipio'],
            telefono=cabecera['telefono'],
            numeroFactura=cabecera['numeroFactura'],
            cuf=cabecera['cuf'],
            cufd=cabecera['cufd'],
            codigoSucursal=cabecera['codigoSucursal'],
            direccion=cabecera['direccion'],
            codigoPuntoVenta=cabecera['codigoPuntoVenta'],
            fechaEmision=cabecera['fechaEmision'],
            nombreRazonSocial=cabecera['nombreRazonSocial'],
            codigoTipoDocumentoIdentidad=cabecera['codigoTipoDocumentoIdentidad'],
            numeroDocumento=cabecera['numeroDocumento'],
            complemento=cabecera['complemento'],
            codigoCliente=cabecera['codigoCliente'],
            codigoMetodoPago=cabecera['codigoMetodoPago'],
            numeroTarjeta=cabecera['numeroTarjeta'],
            montoTotal=cabecera['montoTotal'],
            montoTotalSujetoIva=cabecera['montoTotalSujetoIva'],
            codigoMoneda=cabecera.get('codigoMoneda', 1),
            tipoCambio=cabecera.get('tipoCambio', 1.00),
            montoTotalMoneda=cabecera['montoTotalMoneda'],
            montoGiftCard=cabecera.get('montoGiftCard'),
            descuentoAdicional=cabecera.get('descuentoAdicional', 0.00),
            codigoExcepcion=cabecera.get('codigoExcepcion'),
            cafc=cabecera.get('cafc'),
            leyenda=cabecera['leyenda'],
            usuario=cabecera['usuario'],
            codigoDocumentoSector=cabecera.get('codigoDocumentoSector', 1),
            estadoValidacion=cabecera.get('estadoValidacion', 'VALIDADA'),
            fechaCreacion=cabecera.get('fechaCreacion', 'CURRENT_TIMESTAMP'),
            creadoPor=cabecera.get('creadoPor', 'ADMIN'),
            fechaActualizacion=cabecera.get('fechaActualizacion', 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
            actualizadoPor=cabecera.get('actualizadoPor', 'ADMIN'),
            detallesFirmaDigital=cabecera.get('detallesFirmaDigital'),
            mensajeError=cabecera.get('mensajeError'),
            fechaValidacion=cabecera.get('fechaValidacion'),
            resultadoValidacion=cabecera.get('resultadoValidacion'),
            estadoFirma=cabecera.get('estadoFirma', 'Pendiente'),
            mensajeErrorFirma=cabecera.get('mensajeErrorFirma'),
            fechaErrorFirma=cabecera.get('fechaErrorFirma'),
            intentosFirma=cabecera.get('intentosFirma', 0),
            estado=cabecera.get('estado', 'Activa'),
            fechaAnulacion=cabecera.get('fechaAnulacion'),
            anuladaPor=cabecera.get('anuladaPor'),
            motivoAnulacion=cabecera.get('motivoAnulacion')
        )
        session.execute(query)
        session.commit()
        logging.info(f"Cabecera almacenada exitosamente: {cabecera}")
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error al guardar la cabecera de la factura: {e}")
        raise e
    finally:
        session.close()

# Metadatos y tabla de factura_detalle
metadata = MetaData()
factura_detalle_table = Table('factura_detalle', metadata, autoload_with=engine)

def guardar_factura_detalle(detalle: Dict[str, Union[str, float, int]]) -> None:
    logging.debug(f"Preparando para almacenar el detalle: {detalle}")
    
    # Crear una nueva sesión
    session = SessionLocal()
    try:
        query = factura_detalle_table.insert().values(
            numeroFactura=detalle['numeroFactura'],
            actividadEconomica=detalle.get('actividadEconomica', '56110'),
            codigoProductoSin=detalle.get('codigoProductoSin', 99100),
            codigoProducto=detalle['codigoProducto'],
            descripcion=detalle['descripcion'],
            cantidad=detalle['cantidad'],
            unidadMedida=detalle['unidadMedida'],
            precioUnitario=detalle['precioUnitario'],
            montoDescuento=detalle.get('montoDescuento', 0.00),
            subTotal=detalle['subTotal'],
            numeroSerie=detalle['numeroSerie'] if detalle['numeroSerie'] is not None else None,
            numeroImei=detalle['numeroImei'] if detalle['numeroImei'] is not None else None
        )
        with session.begin():
            session.execute(query)
        session.commit()  # Confirmar la transacción
        logging.info(f"Detalle almacenado exitosamente: {detalle}")
    except SQLAlchemyError as e:
        session.rollback()  # Revertir la transacción en caso de error
        logging.error(f"Error al guardar el detalle de la factura: {e}")
        raise
    finally:
        session.close()

