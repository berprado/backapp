import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import random
import requests
import streamlit as st
from database import SessionLocal, engine, URL_DATABASE
from config import ENDPOINT_URL
from dotenv import load_dotenv
from facturador.models import (SincronizarListaLeyendasFactura, SincronizarParametricaTipoMetodoPago, SincronizarParametricaTipoDocumentoIdentidad, Cliente, FacturaCabecera, FacturaDetalle, ProductoSiat, PuntoVenta, Cuis, SincronizarParametricaMotivoAnulacion, SincronizarListaMensajesServicios, Cufd)
from sqlalchemy import create_engine, Table, Column, Integer, String, DECIMAL, MetaData, TIMESTAMP, Text, BIGINT, ForeignKeyConstraint
from sqlalchemy.dialects.mysql import VARCHAR
from typing import List, Dict, Union
from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from zeep import Client



logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    filename='invoice_log.txt')
load_dotenv()
metadata = MetaData()
engine = create_engine(URL_DATABASE)
# Create the engine to connect to the database


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
        metodos = session.query(SincronizarParametricaTipoMetodoPago).all()
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
        documentos = session.query(SincronizarParametricaTipoDocumentoIdentidad).all()
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
        cliente = session.query(Cliente).filter(Cliente.codigo_cliente == numero_documento).first()
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

@st.cache_data
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
        query = FacturaCabecera.__table__.insert().values(
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



def obtener_nombre_unidad_medida(codigo_producto: str, db: Session) -> str:
    try:
        producto = db.query(ProductoSiat).filter(ProductoSiat.codigo == codigo_producto).first()
        if producto and producto.unidad_medida:
            return producto.unidad_medida
        return "Unid."  # Valor por defecto si la unidad no se encuentra
    except SQLAlchemyError as e:
        logging.error(f"Error al obtener el nombre de la unidad de medida: {e}")
        return "Error"

def obtener_codigo_unidad_medida_sin(codigo_producto: str, db: Session) -> str:
    try:
        producto = db.query(ProductoSiat).filter(ProductoSiat.codigo == codigo_producto).first()
        if producto and producto.codigo_unidad_medida_sin:
            return producto.codigo_unidad_medida_sin
        return "Unid."  # Valor predeterminado si no se encuentra el código
    except SQLAlchemyError as e:
        logging.error(f"Error al obtener el código de la unidad de medida SIN: {e}")
        return "ERROR"

wsdl_url_codigos = os.getenv("WSDL_URL_CODIGOS")
api_key = os.getenv("API_KEY")
codigo_ambiente = int(os.getenv("CODIGO_AMBIENTE"))
codigo_modalidad = int(os.getenv("CODIGO_MODALIDAD"))
codigo_punto_venta = int(os.getenv("CODIGO_PUNTO_VENTA"))
codigo_sistema = os.getenv("CODIGO_SISTEMA")
codigo_sucursal = int(os.getenv("CODIGO_SUCURSAL"))
nit = int(os.getenv("NIT"))

def solicitar_cuis(db: Session):
    """Solicita un nuevo CUIS y lo guarda en la base de datos si es necesario."""
    # Crear el cliente SOAP para códigos
    client = Client(wsdl_url_codigos)

    # Configurar la sesión con la API Key
    session = requests.Session()
    session.headers.update({"apikey": api_key})
    client.transport.session = session

    # Definir la estructura SolicitudCuis
    SolicitudCuis = client.get_type('ns0:solicitudCuis')

    # Crear el objeto SolicitudCuis con los datos necesarios
    solicitud = SolicitudCuis(
        codigoAmbiente=codigo_ambiente,
        codigoModalidad=codigo_modalidad,
        codigoPuntoVenta=codigo_punto_venta,
        codigoSistema=codigo_sistema,
        codigoSucursal=codigo_sucursal,
        nit=nit
    )

    try:
        # Llamar al método cuis para obtener un nuevo CUIS
        response = client.service.cuis(solicitud)
        print("Respuesta completa del servicio SOAP:", response)

        # Verificar si la transacción fue exitosa
        if not response.transaccion:
            mensaje_error = response.mensajesList[0]['descripcion']
            if response.mensajesList[0]['codigo'] == 980:
                # Extraer el CUIS y la fecha de vigencia incluso cuando la transacción no es exitosa
                return {
                    "success": False,
                    "message": mensaje_error,
                    "codigo": response.codigo,  # Extraer el código CUIS
                    "fecha_vigencia": response.fechaVigencia  # Extraer la fecha de vigencia
                }
            else:
                print(f"Error en la transacción SOAP: {response.mensajesList}")
                return {"success": False, "message": mensaje_error}

        # Extraer datos de la respuesta
        nuevo_cuis = response.codigo
        fecha_vigencia = response.fechaVigencia

        # Obtener el punto de venta asociado
        punto_venta = db.query(PuntoVenta).filter(PuntoVenta.codigo_punto_venta == codigo_punto_venta).first()

        if punto_venta:
            # Actualizar vigencia de CUIS existentes a 0
            db.query(Cuis).filter(Cuis.vigente == 1, Cuis.codigo_punto_venta == punto_venta.codigo_punto_venta).update({"vigente": 0})

            # Insertar el nuevo CUIS
            cuis_entry = Cuis(
                codigo=nuevo_cuis,
                fecha_vigencia=fecha_vigencia,
                vigente=1,
                codigo_punto_venta=punto_venta.codigo_punto_venta
            )
            db.add(cuis_entry)
            db.commit()  # Confirmar la transacción
            print("CUIS solicitado y almacenado correctamente.")
            return {"success": True, "message": "CUIS solicitado y almacenado correctamente."}
        else:
            print("Error: No se encontró el punto de venta en la tabla 'punto_venta'")
            return {"success": False, "message": "No se encontró el punto de venta en la tabla 'punto_venta'"}

    except Exception as e:
        db.rollback()  # Revertir la transacción en caso de error
        print(f"Error durante la solicitud del CUIS: {e}")
        return {"success": False, "message": f"Error durante la solicitud del CUIS: {e}"}

def insertar_cuis_manual(db: Session, codigo: str, fecha_vigencia: datetime, codigo_punto_venta: int):
    """Inserta un CUIS manualmente en la base de datos."""
    try:
        # Actualizar vigencia de CUIS existentes a 0
        db.query(Cuis).filter(Cuis.vigente == 1, Cuis.codigo_punto_venta == codigo_punto_venta).update({"vigente": 0})

        # Insertar el nuevo CUIS
        cuis_entry = Cuis(
            codigo=codigo,
            fecha_vigencia=fecha_vigencia,
            vigente=1,
            codigo_punto_venta=codigo_punto_venta
        )
        db.add(cuis_entry)
        db.commit()  # Confirmar la transacción
        print("CUIS introducido manualmente y almacenado correctamente.")
        return {"success": True, "message": "CUIS introducido manualmente y almacenado correctamente."}
    except Exception as e:
        db.rollback()  # Revertir la transacción en caso de error
        print(f"Error durante la inserción manual del CUIS: {e}")
        return {"success": False, "message": f"Error durante la inserción manual del CUIS: {e}"}
@st.cache_data
def obtener_motivos_anulacion():
    session = SessionLocal()
    try:
        motivos = session.query(SincronizarParametricaMotivoAnulacion).all()
        if motivos:
            return [motivo.descripcion for motivo in motivos]  # Retorna las descripciones
        return []
    except Exception as e:
        logging.error(f"Error al obtener los motivos de anulación: {e}")
        return []
    finally:
        session.close()
@st.cache_data
def obtener_mensaje_por_codigo(codigo_clasificador):
    session = SessionLocal()
    try:
        # Usar la clase importada para hacer la consulta
        mensaje = session.query(SincronizarListaMensajesServicios).filter_by(codigoClasificador=codigo_clasificador).first()
        
        # Retornar la descripción si se encuentra
        if mensaje:
            return mensaje.descripcion
        else:
            return None  # Si no se encuentra el código
    except Exception as e:
        logging.error(f"Error al obtener el mensaje: {e}")
        return None
    finally:
        session.close()

def obtener_cufd_vigente():
    session = SessionLocal()
    try:
        cufd_vigente = session.query(Cufd).filter_by(vigente=1).first()
        if cufd_vigente:
            return cufd_vigente.codigo
        else:
            return None
    except Exception as e:
        logging.error(f"Error al obtener CUFD vigente: {e}")
        return None
    finally:
        session.close()
