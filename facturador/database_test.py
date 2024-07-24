from sqlalchemy import MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import Dict, Union
from database import SessionLocal, engine

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)
file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Metadatos y tabla de factura_detalle
metadata = MetaData()
factura_detalle_table = Table('factura_detalle', metadata, autoload_with=engine)

def guardar_factura_detalle(detalle: Dict[str, Union[str, float, int]]) -> None:
    logger.debug(f"Preparando para almacenar el detalle: {detalle}")
    
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
        logger.info(f"Detalle almacenado exitosamente: {detalle}")
    except SQLAlchemyError as e:
        session.rollback()  # Revertir la transacción en caso de error
        logger.error(f"Error al guardar el detalle de la factura: {e}")
        raise
    finally:
        session.close()

# Ejemplo de uso
detalles_data = [
    {
        'numeroFactura': 527,
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
    # Añadir más detalles según sea necesario
]

for detalle in detalles_data:
    guardar_factura_detalle(detalle)
