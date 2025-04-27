import os
import sys
# Agregar la ruta del directorio padre al path de Python si no está ya
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if (parent_dir not in sys.path):
    sys.path.append(parent_dir)

import random
import requests
import json
from datetime import datetime, timedelta
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
from sqlalchemy import inspect
from datetime import datetime
from zeep import Client
from logger_config import get_logger
import traceback

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
    """
    Obtiene las comandas desde el servidor.
    Si el servidor no está disponible, intenta cargar desde caché.
    
    Returns:
        tuple: (comandas, mensaje_error)
    """
    # Ruta para el archivo de caché
    cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
    cache_file = os.path.join(cache_dir, 'comandas_cache.json')
    
    # Asegurarse de que el directorio de caché exista
    if not os.path.exists(cache_dir):
        try:
            os.makedirs(cache_dir)
        except Exception as e:
            logger.error(f"Error al crear directorio de caché: {e}")
    
    try:
        logger.info("Obteniendo comandas del servidor")
        
        # Timeout reducido para evitar bloqueos largos si el servidor no responde
        response = requests.get(f"{ENDPOINT_URL}", timeout=5)
        response.raise_for_status()
        comandas = response.json()
        
        # Guardar en caché para uso futuro
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'comandas': comandas
                }, f, ensure_ascii=False)
            logger.info(f"Guardadas {len(comandas)} comandas en caché")
        except Exception as e:
            logger.warning(f"No se pudo guardar comandas en caché: {e}")
        
        return comandas, None
        
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        logger.error(f"Error al obtener comandas: {e}")
        logger.error(traceback.format_exc())
        
        # Intentar cargar desde caché si existe
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Verificar si el caché es reciente (menos de 24 horas)
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cache_time < timedelta(hours=24):
                    logger.info(f"Usando {len(cache_data['comandas'])} comandas desde caché")
                    return cache_data['comandas'], "Servidor no disponible: usando datos en caché"
                else:
                    logger.warning(f"Caché de comandas expirado ({(datetime.now() - cache_time).total_seconds() / 3600:.1f} horas)")
        except Exception as cache_error:
            logger.error(f"Error al cargar comandas desde caché: {cache_error}")
        
        # Si llegamos aquí, no pudimos obtener comandas ni del servidor ni de caché
        return [], f"Error al obtener comandas: {str(e)}"

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

# Importar el sistema de gestión de caché (al inicio del archivo, después de las importaciones existentes)
try:
    from utils.cache_manager import invalidate_cache
    USE_CACHE_MANAGER = True
    logger.info("Usando sistema de gestión de caché en data_access.py")
except ImportError as e:
    USE_CACHE_MANAGER = False
    logger.warning(f"No se pudo importar el sistema de gestión de caché en data_access.py: {e}")

def guardar_factura_cabecera(cabecera: Dict[str, Union[str, float, int]]) -> tuple:
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

        # Agregar explícitamente los campos de contingencia que sabemos existen en la tabla
        # Sabemos que estos existen porque vimos la estructura de la tabla
        contingency_fields = {
            'tipoEmision': cabecera.get('tipoEmision'),
            'codigoEvento': cabecera.get('codigoEvento'),
            'descripcionEvento': cabecera.get('descripcionEvento'),
            'fechaInicioEvento': cabecera.get('fechaInicioEvento'),
            'fechaFinEvento': cabecera.get('fechaFinEvento'),
            'idPaquete': cabecera.get('idPaquete'),
            'estadoPaquete': cabecera.get('estadoPaquete'),
            'numeroSecuencia': cabecera.get('numeroSecuencia'),
            'estadoContingencia': cabecera.get('estadoContingencia'),
            'fechaSincronizacion': cabecera.get('fechaSincronizacion')
        }
        
        # Filtrar campos None para evitar errores de tipo
        for key, value in contingency_fields.items():
            if value is not None:
                values[key] = value
                
        logging.debug(f"Campos de contingencia añadidos: {[k for k, v in contingency_fields.items() if v is not None]}")

        # Ejecutar la inserción con los campos que sabemos que existen
        query = FacturaCabecera.__table__.insert().values(**values)
        session.execute(query)
        session.commit()
        logging.info(f"Cabecera almacenada exitosamente: {cabecera['numeroFactura']}")
        
        # Invalidar el caché de facturas después de guardar
        if USE_CACHE_MANAGER:
            try:
                invalidate_cache('facturas')
                logger.info("Caché de facturas invalidado después de guardar factura")
            except Exception as e:
                logger.warning(f"Error al invalidar caché: {e}")
        
        return True, "Factura guardada correctamente"
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error al guardar la cabecera de la factura: {e}")
        return False, str(e)
    except Exception as e:
        session.rollback()
        logging.error(f"Error inesperado al guardar la factura: {e}")
        return False, str(e)
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