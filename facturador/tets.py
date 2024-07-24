import random
import requests
from database import SessionLocal, engine, URL_DATABASE
import models
from config import ENDPOINT_URL
import os
from dotenv import load_dotenv
from models import FacturaCabecera, FacturaDetalle, SincronizarListaLeyendasFactura
from sqlalchemy import create_engine, Table, Column, Integer, String, DECIMAL, MetaData, TIMESTAMP, Text, BIGINT, ForeignKeyConstraint, DateTime
from sqlalchemy.dialects.mysql import VARCHAR
from typing import Dict, Union, List
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configuración de logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    filename='invoice_log.txt')

load_dotenv()
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

def guardar_factura_detalle(detalles: List[Dict[str, Union[str, float, int]]]) -> None:
    session = SessionLocal()
    try:
        for detalle in detalles:
            logging.debug(f"Preparando para almacenar el detalle: {detalle}")
            query = models.FacturaDetalle.__table__.insert().values(
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
                numeroSerie=detalle.get('numeroSerie'),
                numeroImei=detalle.get('numeroImei')
            )
            session.execute(query)
        session.commit()
        logging.info("Detalles almacenados exitosamente.")
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error al guardar el detalle de la factura: {e}")
        raise e
    finally:
        session.close()

# Ejemplo de uso
if __name__ == "__main__":
    cabecera_data = {
        'numeroFactura': 529,
        'nitEmisor': 344096024,
        'razonSocialEmisor': 'BOLIVIAN FOODS & DRINKS S.R.L.',
        'municipio': 'LA PAZ',
        'telefono': '65560514',
        'cuf': '178B43EFDB95AF61816BCD8111CDA45046C3C3B0A9247CC9ACC4D8E74',
        'cufd': 'BQW9Dfm9pQUE=N0jIwOUI5RDBENjY=Qj5pdklBWUhZVUFM0OEY3NkRBRkU0R',
        'codigoSucursal': 0,
        'direccion': 'AVENIDA MONTENEGRO NRO. SN EDIF.: ARACELY PISO: PB DEPTO.: BLOQUE E7 ZONA/BARRIO: SAN MIGUEL',
        'codigoPuntoVenta': 0,
        'fechaEmision': '2024-07-24T01:16:57.837',
        'nombreRazonSocial': 'prado',
        'codigoTipoDocumentoIdentidad': '5',
        'numeroDocumento': '344096024',
        'complemento': None,
        'codigoCliente': '344096024',
        'codigoMetodoPago': '1',
        'numeroTarjeta': None,
        'montoTotal': 20.00,
        'montoTotalSujetoIva': 20.00,
        'codigoMoneda': 1,
        'tipoCambio': 1,
        'montoTotalMoneda': 20.00,
        'montoGiftCard': 0,
        'descuentoAdicional': 0,
        'codigoExcepcion': None,
        'cafc': None,
        'leyenda': 'Ley N° 453: Los servicios deben suministrarse en condiciones de inocuidad, calidad y seguridad.',
        'usuario': 'don_bercho',
        'codigoDocumentoSector': 1
    }

    detalles_data = [
        {
            'numeroFactura': 529,
            'actividadEconomica': '561110',
            'codigoProductoSin': '99100',
            'codigoProducto': 49,
            'descripcion': 'C DON LUCHO SILVER',
            'cantidad': 1.0,
            'unidadMedida': 1,
            'precioUnitario': 400.0,
            'montoDescuento': 0.0,
            'subTotal': 400.0,
            'numeroSerie': None,
            'numeroImei': None
        },
        {
            'numeroFactura': 529,
            'actividadEconomica': '561110',
            'codigoProductoSin': '99100',
            'codigoProducto': 152,
            'descripcion': 'HAVANA MEDIA',
            'cantidad': 1.0,
            'unidadMedida': 1,
            'precioUnitario': 200.0,
            'montoDescuento': 0.0,
            'subTotal': 200.0,
            'numeroSerie': None,
            'numeroImei': None
        }
    ]

    try:
        # Guardar cabecera
        guardar_factura_cabecera(cabecera_data)
        
        # Guardar detalles
        guardar_factura_detalle(detalles_data)
        
        logging.info("Datos almacenados correctamente.")
    except SQLAlchemyError as e:
        logging.error(f"Error al almacenar los datos: {e}")
