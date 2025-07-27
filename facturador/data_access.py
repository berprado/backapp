def get_eventos_parametricos():
    """Obtiene los eventos significativos disponibles (paramétricos)"""
    session = SessionLocal()
    try:
        # Ajusta el nombre del modelo si es diferente
        eventos = session.query(SincronizarParametricaEventosSignificativos).all()
        return [
            {"codigoClasificador": e.codigoClasificador, "descripcion": e.descripcion}
            for e in eventos
        ]
    except Exception as e:
        logger.error(f"Error al obtener eventos paramétricos: {e}")
        return []
    finally:
        session.close()

def insertar_evento_local(codigo_evento, descripcion, fecha_inicio, cufd):
    """
    Inserta un nuevo evento significativo en la BD local.
    Para eventos "abiertos", usa fecha_inicio = fecha_fin siguiendo la convención estándar.
    """
    session = SessionLocal()
    try:
        nuevo_evento = EventoSignificativoRegistrado(
            codigo_evento=codigo_evento,
            descripcion=descripcion,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_inicio,  # Para eventos abiertos - convención estándar
            cufd=cufd,
            fecha_registro=datetime.now()  # ✅ Agregar fecha_registro explícitamente
        )
        session.add(nuevo_evento)
        session.commit()
        logger.info(f"Evento significativo insertado: {codigo_evento} - {descripcion}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error al insertar evento significativo: {e}")
    finally:
        session.close()

def obtener_evento_abierto():
    """Devuelve el último evento sin cerrar (fecha_inicio = fecha_fin y sin codigo_recepcion)"""
    session = SessionLocal()
    try:
        evento = (
            session.query(EventoSignificativoRegistrado)
            .filter(EventoSignificativoRegistrado.fecha_inicio == EventoSignificativoRegistrado.fecha_fin)
            .filter(EventoSignificativoRegistrado.codigo_recepcion == None)
            .order_by(EventoSignificativoRegistrado.fecha_inicio.desc())
            .first()
        )
        if evento:
            return {c.name: getattr(evento, c.name) for c in EventoSignificativoRegistrado.__table__.columns}
        return None
    except Exception as e:
        logger.error(f"Error al obtener evento abierto: {e}")
        return None
    finally:
        session.close()

def actualizar_evento_final(evento_id, fecha_fin, codigo_recepcion):
    """Actualiza el evento con su fecha de cierre y código de recepción"""
    session = SessionLocal()
    try:
        evento = session.query(EventoSignificativoRegistrado).filter_by(id=evento_id).first()
        if evento:
            evento.fecha_fin = fecha_fin
            evento.codigo_recepcion = codigo_recepcion
            evento.fecha_registro = datetime.now()
            session.commit()
            logger.info(f"Evento actualizado (id={evento_id}): fecha_fin={fecha_fin}, codigo_recepcion={codigo_recepcion}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error al actualizar evento final: {e}")
    finally:
        session.close()
import os
import sys
import random
import requests
import streamlit as st
from database import SessionLocal, engine, URL_DATABASE
from config import ENDPOINT_URL
from dotenv import load_dotenv
from models import (
    SincronizarListaLeyendasFactura, SincronizarParametricaTipoMetodoPago, SincronizarParametricaTipoDocumentoIdentidad, Cliente, FacturaCabecera, FacturaDetalle, ProductoSiat, PuntoVenta, Cuis, SincronizarParametricaMotivoAnulacion, SincronizarListaMensajesServicios, Cufd, SincronizarParametricaEventosSignificativos, EventoSignificativoRegistrado
)
from sqlalchemy import create_engine, Table, Column, Integer, String, DECIMAL, MetaData, TIMESTAMP, Text, BIGINT, ForeignKeyConstraint
from sqlalchemy.dialects.mysql import VARCHAR
from typing import List, Dict, Union
from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from datetime import datetime
from zeep import Client
from logger_config import get_logger
from api_clients import get_soap_client
import traceback
from typing import Optional
from models import EventoSignificativoRegistrado 

# Obtener logger para este módulo
logger = get_logger()

# Configurar logging básico - NO REPETIR ESTO
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    filename='invoice_log.log')
# Cargar variables de entorno solo una vez
load_dotenv()
# Definir metadata y engine solo una vez
metadata = MetaData()
engine = create_engine(URL_DATABASE)

@st.cache_resource
def fetch_comandas():
    try:
        logger.info("Obteniendo comandas")
        response = requests.get(f"{ENDPOINT_URL}")
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener comandas: {e}")
        logger.error(traceback.format_exc())
        return [], f"Error al obtener los id_comanda: {e}"

@st.cache_data
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

@st.cache_data
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

def fetch_all_clientes(limite=50, offset=0, busqueda=None):
    """
    Obtiene una lista paginada de todos los clientes con búsqueda opcional.
    
    Args:
        limite (int): Número máximo de registros a retornar
        offset (int): Número de registros a omitir (para paginación)
        busqueda (str): Término de búsqueda para filtrar por nombre o documento
    
    Returns:
        tuple: (lista_clientes, total_registros, mensaje_error)
    """
    session = SessionLocal()
    try:
        logger.info(f"Obteniendo clientes - Límite: {limite}, Offset: {offset}, Búsqueda: {busqueda}")
        
        # Query base
        query = session.query(Cliente)
        
        # Aplicar filtro de búsqueda si se proporciona
        if busqueda and busqueda.strip():
            busqueda = busqueda.strip()
            query = query.filter(
                (Cliente.nombre_razon_social.ilike(f"%{busqueda}%")) |
                (Cliente.numero_documento.ilike(f"%{busqueda}%")) |
                (Cliente.codigo_cliente.ilike(f"%{busqueda}%"))
            )
        
        # Obtener total de registros para paginación
        total_registros = query.count()
        
        # Aplicar paginación y ordenamiento
        clientes = query.order_by(Cliente.fecha_creacion.desc()).offset(offset).limit(limite).all()
        
        # Convertir a diccionarios
        clientes_dict = [cliente.to_dict() for cliente in clientes]
        
        logger.info(f"Se obtuvieron {len(clientes_dict)} clientes de un total de {total_registros}")
        return clientes_dict, total_registros, None
        
    except Exception as e:
        logger.error(f"Error al obtener lista de clientes: {e}")
        logger.error(traceback.format_exc())
        return [], 0, f"Error al obtener la lista de clientes: {e}"
    finally:
        session.close()

def contar_total_clientes():
    """
    Obtiene el número total de clientes registrados.
    
    Returns:
        tuple: (total_clientes, mensaje_error)
    """
    session = SessionLocal()
    try:
        total = session.query(Cliente).count()
        return total, None
    except Exception as e:
        logger.error(f"Error al contar clientes: {e}")
        return 0, f"Error al contar clientes: {e}"
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
        # Crear un diccionario con los valores básicos que sabemos que existen en la tabla
        values = {
            "nitEmisor": cabecera['nitEmisor'],
            "razonSocialEmisor": cabecera['razonSocialEmisor'],
            "municipio": cabecera['municipio'],
            "telefono": cabecera['telefono'],
            "numeroFactura": cabecera['numeroFactura'],
            "cuf": cabecera['cuf'],
            "cufd": cabecera['cufd'],
            "codigoSucursal": cabecera['codigoSucursal'],
            "direccion": cabecera['direccion'],
            "codigoPuntoVenta": cabecera['codigoPuntoVenta'],
            "fechaEmision": cabecera['fechaEmision'],
            "nombreRazonSocial": cabecera['nombreRazonSocial'],
            "codigoTipoDocumentoIdentidad": cabecera['codigoTipoDocumentoIdentidad'],
            "numeroDocumento": cabecera['numeroDocumento'],
            "complemento": cabecera['complemento'],
            "codigoCliente": cabecera['codigoCliente'],
            "codigoMetodoPago": cabecera['codigoMetodoPago'],
            "numeroTarjeta": cabecera['numeroTarjeta'],
            "montoTotal": cabecera['montoTotal'],
            "montoTotalSujetoIva": cabecera['montoTotalSujetoIva'],
            "codigoMoneda": cabecera.get('codigoMoneda', 1),
            "tipoCambio": cabecera.get('tipoCambio', 1.00),
            "montoTotalMoneda": cabecera['montoTotalMoneda'],
            "montoGiftCard": cabecera.get('montoGiftCard'),
            "descuentoAdicional": cabecera.get('descuentoAdicional', 0.00),
            "codigoExcepcion": cabecera.get('codigoExcepcion'),
            "cafc": cabecera.get('cafc'),
            "leyenda": cabecera['leyenda'],
            "usuario": cabecera['usuario'],
            "codigoDocumentoSector": cabecera.get('codigoDocumentoSector', 1),
            "estadoValidacion": cabecera.get('estadoValidacion', 'VALIDADA'),
            "fechaCreacion": datetime.now(),  # Usar datetime en lugar de string
            "creadoPor": cabecera.get('creadoPor', 'ADMIN'),
            "actualizadoPor": cabecera.get('actualizadoPor', 'ADMIN'),
            "detallesFirmaDigital": cabecera.get('detallesFirmaDigital'),
            "mensajeError": cabecera.get('mensajeError'),
            "fechaValidacion": cabecera.get('fechaValidacion'),
            "resultadoValidacion": cabecera.get('resultadoValidacion'),
            "estadoFirma": cabecera.get('estadoFirma', 'Pendiente'),
            "mensajeErrorFirma": cabecera.get('mensajeErrorFirma'),
            "fechaErrorFirma": cabecera.get('fechaErrorFirma'),
            "intentosFirma": cabecera.get('intentosFirma', 0),
            "estado": cabecera.get('estado', 'Activa'),
            "fechaAnulacion": cabecera.get('fechaAnulacion'),
            "anuladaPor": cabecera.get('anuladaPor'),
            "motivoAnulacion": cabecera.get('motivoAnulacion'),
            "enlaceSiat": cabecera.get('enlaceSiat'),
            "codigoRecepcion": cabecera.get('codigoRecepcion')
        }

        # Intentar añadir campos de contingencia si existen en la tabla
        try:
            # Verificar si las columnas existen en la tabla
            insp = inspect(engine)
            columns = insp.get_columns('factura_cabecera')
            column_names = [col['name'] for col in columns]
            
            # Solo añadir columnas que existen en la tabla
            contingency_fields = [
                'tipoEmision', 'codigoEvento', 'descripcionEvento', 'fechaInicioEvento',
                'fechaFinEvento', 'idPaquete', 'estadoPaquete', 'numeroSecuencia',
                'estadoContingencia', 'fechaSincronizacion'
            ]
            
            for field in contingency_fields:
                if field in column_names and field in cabecera:
                    values[field] = cabecera.get(field)
            
            logging.debug(f"Campos de contingencia detectados y añadidos: {[f for f in contingency_fields if f in column_names]}")
        except Exception as e:
            logging.warning(f"No se pudieron verificar columnas de contingencia: {str(e)}")
            # Continuar sin añadir campos de contingencia

        # Ejecutar la inserción con los campos que sabemos que existen
        query = FacturaCabecera.__table__.insert().values(**values)
        session.execute(query)
        session.commit()
        logging.info(f"Cabecera almacenada exitosamente: {cabecera['numeroFactura']}")
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
        nuevo_detalle = FacturaDetalle(
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
            numeroSerie=detalle['numeroSerie'] if detalle.get('numeroSerie') is not None else None,
            numeroImei=detalle['numeroImei'] if detalle.get('numeroImei') is not None else None
        )
        session.add(nuevo_detalle)
        session.commit()
        logging.info(f"Detalle almacenado exitosamente: {detalle}")
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error al guardar el detalle de la factura: {e}")
        raise
    finally:
        session.close()

def obtener_nombre_unidad_medida(codigo_producto: str, db: Session) -> str:
    try:
        producto = db.query(ProductoSiat).filter(ProductoSiat.codigo == codigo_producto).first()
        if producto and producto.unidad_medida:
            return producto.unidad_medida
        return "Unidadxxx."  # Valor por defecto si la unidad no se encuentra
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
    # Obtener el cliente SOAP centralizado
    client = get_soap_client()
    if client is None:
        return {"success": False, "message": "No se puede conectar con el servicio del SIN"}

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
def obtener_cuf_por_numero_factura(numero_factura):
    session = SessionLocal()
    try:
        factura = session.query(FacturaCabecera).filter_by(numeroFactura=numero_factura).first()
        if factura:
            return factura.cuf, factura
        else:
            return None, None
    except Exception as e:
        logger.error(f"Error al consultar factura #{numero_factura}: {str(e)}")
        logger.error(traceback.format_exc())
        return None, None  # Devolver None, None en lugar de None, str(e)
    finally:
        session.close()

# Nueva función para obtener facturas pendientes de validación
@st.cache_data(ttl=60)  # Caché por 60 segundos para no sobrecargar la BD
def obtener_facturas_por_estado(estado=None, page=1, per_page=10):
    """
    Obtiene facturas filtradas por estado de validación.
    
    Args:
        estado: Estado de validación a filtrar ('PENDIENTE', 'VALIDADA', 'ANULADA' o None para todas)
        page: Número de página para paginación
        per_page: Cantidad de registros por página
        
    Returns:
        tuple: (facturas, total_registros, mensaje_error)
    """
    session = SessionLocal()
    try:
        query = session.query(FacturaCabecera)
        
        # Aplicar filtros según el estado solicitado
        if estado == "PENDIENTE":
            query = query.filter(FacturaCabecera.resultadoValidacion.is_(None))
        elif estado == "VALIDADA":
            query = query.filter(FacturaCabecera.resultadoValidacion == "VALIDADA")
        elif estado == "ANULADA":
            # Una factura puede tener estado "Anulada" o resultadoValidacion "ANULADA"
            query = query.filter((FacturaCabecera.estado == "Anulada") | 
                                 (FacturaCabecera.resultadoValidacion == "ANULADA"))
        
        # Obtener el conteo total de registros para la paginación
        total = query.count()
        
        # Aplicar ordenamiento y paginación
        facturas = query.order_by(FacturaCabecera.fechaEmision.desc())\
                        .offset((page - 1) * per_page)\
                        .limit(per_page)\
                        .all()
        
        # Convertir a diccionarios para usar en la interfaz
        facturas_dict = [
            {
                "numeroFactura": f.numeroFactura,
                "cuf": f.cuf,
                "fechaEmision": f.fechaEmision,
                "nombreRazonSocial": f.nombreRazonSocial,
                "numeroDocumento": f.numeroDocumento,
                "montoTotal": float(f.montoTotal),
                "estadoValidacion": f.estadoValidacion,
                "resultadoValidacion": f.resultadoValidacion,
                "estado": f.estado
            } for f in facturas
        ]
        
        return facturas_dict, total, None
    except Exception as e:
        logger.error(f"Error al obtener facturas: {str(e)}")
        logger.error(traceback.format_exc())
        return [], 0, f"Error al obtener facturas: {str(e)}"
    finally:
        session.close()

# Nueva función para obtener una factura completa con sus detalles
def obtener_factura_completa(numero_factura):
    """
    Obtiene una factura y sus detalles por número de factura.
    
    Args:
        numero_factura: Número de factura a buscar
        
    Returns:
        tuple: (cabecera, detalles, error)
    """
    session = SessionLocal()
    try:
        # Obtener la cabecera de la factura
        cabecera = session.query(FacturaCabecera).filter_by(numeroFactura=numero_factura).first()
        if not cabecera:
            return None, None, "Factura no encontrada"
        
        # Obtener los detalles de la factura
        detalles = session.query(FacturaDetalle).filter_by(numeroFactura=numero_factura).all()
        
        # Convertir a diccionarios
        cabecera_dict = cabecera.to_dict()
        detalles_dict = [detalle.to_dict() for detalle in detalles]
        
        return cabecera_dict, detalles_dict, None
    except Exception as e:
        logger.error(f"Error al obtener factura completa #{numero_factura}: {str(e)}")
        logger.error(traceback.format_exc())
        return None, None, f"Error: {str(e)}"
    finally:
        session.close()
        
def obtener_cufd_de_evento_activo() -> Optional[str]:
    """
    Busca el último evento significativo abierto en la base de datos y devuelve 
    el CUFD que se registró con él.

    Esta función es crucial para la facturación en modo de contingencia, ya que
    las facturas offline deben usar el CUFD del evento al que pertenecen.

    Un evento se considera "abierto" si todavía no tiene un código de recepción del SIN.
    
    Returns:
        Optional[str]: El código CUFD del evento activo como una cadena, 
                       o None si no se encuentra ningún evento activo o si ocurre un error.
    """
    logger.info("Buscando CUFD de un evento de contingencia activo...")
    session = SessionLocal()
    try:
        # La lógica para encontrar un evento abierto es que su 'codigo_recepcion' aún es NULL.
        # Se ordena por fecha de inicio descendente para obtener el más reciente en caso de
        # que haya más de uno por error.
        evento_activo = session.query(EventoSignificativoRegistrado)\
            .filter(EventoSignificativoRegistrado.codigo_recepcion.is_(None))\
            .order_by(EventoSignificativoRegistrado.fecha_inicio.desc())\
            .first()
            
        if evento_activo:
            logger.info(f"Evento activo encontrado (ID: {evento_activo.id}). CUFD asociado: {evento_activo.cufd}")
            return evento_activo.cufd
        else:
            logger.warning("No se encontró ningún evento de contingencia activo en la base de datos.")
            return None
            
    except Exception as e:
        logger.error(f"Error al obtener el CUFD del evento de contingencia activo: {e}", exc_info=True)
        return None
    finally:
        session.close()