import os
import time
import logging
from datetime import datetime
from database import SessionLocal
from facturador.models import FacturaCabecera, FacturaDetalle
from facturador.logger_config import get_logger  # Cambiar esta importación

logger = get_logger('contingency')  # Usar el logger general con nombre específico
facturacion_logger = get_logger('facturacion')

def mark_invoice_as_contingency(numero_factura):
    """
    Marca una factura existente como emitida en contingencia
    
    Args:
        numero_factura (int): Número de la factura a marcar
        
    Returns:
        bool: True si se marcó correctamente, False en caso contrario
    """
    session = SessionLocal()
    try:
        factura = session.query(FacturaCabecera).filter(
            FacturaCabecera.numeroFactura == numero_factura
        ).first()
        
        if not factura:
            logger.warning(f"No se encontró la factura {numero_factura}")
            return False
        
        factura.estadoFirma = "CONTINGENCIA"
        factura.tipoEmision = 2  # Tipo emisión fuera de línea
        factura.codigoRecepcion = None
        
        session.commit()
        logger.info(f"Factura {numero_factura} marcada como emitida en contingencia")
        return True
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error al marcar factura {numero_factura} como contingencia: {str(e)}")
        return False
    
    finally:
        session.close()

def save_offline_invoice(factura_cabecera_data, factura_detalle_data):
    """
    Guarda una factura emitida en modo contingencia
    
    Args:
        factura_cabecera_data (dict): Datos de la cabecera de la factura
        factura_detalle_data (list): Lista de items en el detalle de la factura
        
    Returns:
        tuple: (success, message) donde success es un booleano y message es un mensaje descriptivo
    """
    session = SessionLocal()
    try:
        # Asegurar que los campos críticos para contingencia estén configurados correctamente
        factura_cabecera_data['estadoFirma'] = "CONTINGENCIA"
        factura_cabecera_data['tipoEmision'] = 2  # Tipo emisión fuera de línea
        factura_cabecera_data['codigoRecepcion'] = None
        
        # Crear el objeto de la cabecera de factura
        factura_cabecera = FacturaCabecera(**factura_cabecera_data)
        session.add(factura_cabecera)
        session.flush()
        
        # Agregar los detalles de la factura
        for detalle in factura_detalle_data:
            detalle['numeroFactura'] = factura_cabecera.numeroFactura
            factura_detalle = FacturaDetalle(**detalle)
            session.add(factura_detalle)
        
        session.commit()
        
        # Crear el XML y almacenarlo para envío posterior
        xml_filepath = create_offline_invoice_xml(factura_cabecera.numeroFactura)
        
        if xml_filepath:
            logger.info(f"Factura {factura_cabecera.numeroFactura} guardada en modo contingencia. XML: {xml_filepath}")
            return True, f"Factura {factura_cabecera.numeroFactura} guardada en modo contingencia"
        else:
            logger.warning(f"Factura {factura_cabecera.numeroFactura} guardada pero no se pudo generar el XML")
            return True, f"Factura {factura_cabecera.numeroFactura} guardada pero sin XML"
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error al guardar factura en modo contingencia: {str(e)}")
        return False, f"Error al guardar factura: {str(e)}"
    
    finally:
        session.close()

def create_offline_invoice_xml(numero_factura):
    """
    Crea el archivo XML para una factura emitida en modo contingencia
    
    Args:
        numero_factura (int): Número de la factura
        
    Returns:
        str: Ruta del archivo XML generado o None si hubo un error
    """
    try:
        # Obtener los datos de la factura
        session = SessionLocal()
        factura = session.query(FacturaCabecera).filter(
            FacturaCabecera.numeroFactura == numero_factura
        ).first()
        
        if not factura:
            logger.warning(f"No se encontró la factura {numero_factura}")
            return None
        
        # Obtener los detalles de la factura
        detalles = session.query(FacturaDetalle).filter(
            FacturaDetalle.numeroFactura == numero_factura
        ).all()
        
        # Cerrar la sesión
        session.close()
        
        # Aquí va la lógica para generar el XML
        # Importar el generador de XML existente
        from invoice_xml_generator import generate_xml_invoice
        
        # Convertir los objetos a diccionarios
        factura_dict = {c.name: getattr(factura, c.name) for c in factura.__table__.columns}
        detalles_list = [{c.name: getattr(detalle, c.name) for c in detalle.__table__.columns} for detalle in detalles]
        
        # Generar el XML sin enviarlo al SIAT
        # Esta función debe ser una versión modificada del generador actual que no envía el XML
        xml_str, _, _ = generate_xml_invoice_offline(
            factura_dict, 
            detalles_list
        )
        
        # Guardar el XML en un archivo
        os.makedirs("xmls_offline", exist_ok=True)
        xml_filepath = f"xmls_offline/factura_{numero_factura}_{factura.cuf}.xml"
        
        with open(xml_filepath, "w", encoding="utf-8") as f:
            f.write(xml_str)
        
        return xml_filepath
    
    except Exception as e:
        logger.error(f"Error al crear XML para factura {numero_factura}: {str(e)}")
        return None

def generate_xml_invoice_offline(factura_cabecera_data, factura_detalle_data):
    """
    Versión modificada de generate_xml_invoice para generar XML en modo offline
    Nota: Esta es una función de ejemplo y requiere adaptación al código existente
    """
    # Importar las funciones necesarias
    from invoice_xml_generator import generate_xml_invoice as original_generator
    
    # Esta función debería ser modificada para adaptarse a tu lógica actual
    # En este ejemplo asumimos que la función original puede usarse directamente
    return original_generator(factura_cabecera_data, factura_detalle_data, skip_sending=True)

def get_pending_offline_invoices():
    """
    Obtiene todas las facturas pendientes de envío emitidas en modo contingencia
    
    Returns:
        list: Lista de facturas pendientes de envío
    """
    session = SessionLocal()
    try:
        facturas = session.query(FacturaCabecera).filter(
            FacturaCabecera.estadoFirma == "CONTINGENCIA"
        ).all()
        
        return [factura.to_dict() if hasattr(factura, 'to_dict') else 
                {c.name: getattr(factura, c.name) for c in factura.__table__.columns} 
                for factura in facturas]
    
    except Exception as e:
        logger.error(f"Error al obtener facturas pendientes: {str(e)}")
        return []
    
    finally:
        session.close()

def count_pending_offline_invoices():
    """
    Cuenta las facturas pendientes de envío emitidas en modo contingencia
    
    Returns:
        int: Número de facturas pendientes
    """
    session = SessionLocal()
    try:
        count = session.query(FacturaCabecera).filter(
            FacturaCabecera.estadoFirma == "CONTINGENCIA"
        ).count()
        
        return count
    
    except Exception as e:
        logger.error(f"Error al contar facturas pendientes: {str(e)}")
        return 0
    
    finally:
        session.close()

def update_invoice_status_after_sending(numero_factura, codigo_recepcion, estado="VALIDADA"):
    """
    Actualiza el estado de una factura después de ser enviada a SIAT
    
    Args:
        numero_factura (int): Número de la factura
        codigo_recepcion (str): Código de recepción retornado por SIAT
        estado (str): Nuevo estado de la factura
        
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    session = SessionLocal()
    try:
        factura = session.query(FacturaCabecera).filter(
            FacturaCabecera.numeroFactura == numero_factura
        ).first()
        
        if not factura:
            logger.warning(f"No se encontró la factura {numero_factura}")
            return False
        
        factura.codigoRecepcion = codigo_recepcion
        factura.estadoFirma = estado
        
        session.commit()
        logger.info(f"Factura {numero_factura} actualizada con código de recepción {codigo_recepcion}")
        return True
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error al actualizar factura {numero_factura}: {str(e)}")
        return False
    
    finally:
        session.close()

import os
import sys
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from database import SessionLocal
from facturador.models import FacturaCabecera, FacturaDetalle, Cufd
from facturador.logger_config import get_logger  # Cambiar esta importación

# Obtener logger para este módulo
logger = get_logger('contingency')  # Usar el logger general con nombre específico

def prepare_invoice_for_offline(factura_cabecera_data, detalles_factura):
    """
    Prepara una factura para ser emitida en modo offline durante contingencia
    
    Args:
        factura_cabecera_data (dict): Datos de la cabecera de la factura
        detalles_factura (list): Lista de detalles de la factura
        
    Returns:
        tuple: (bool, str) - (éxito, mensaje)
    """
    try:
        # Marcar la factura como emitida en contingencia
        factura_cabecera_data["tipoEmision"] = "2"  # 2 = Fuera de línea
        factura_cabecera_data["estadoFirma"] = "CONTINGENCIA"
        
        # Obtener info de contingencia si existe
        from facturador.contingency_manager import get_contingency_manager
        contingency_manager = get_contingency_manager()
        status = contingency_manager.get_status()
        
        # Añadir info de contingencia si está disponible
        if status["contingency_active"] and status["contingency_start_time"]:
            factura_cabecera_data["codigoEvento"] = status["event_type"]
            factura_cabecera_data["descripcionEvento"] = status["event_description"]
            factura_cabecera_data["fechaInicioEvento"] = status["contingency_start_time"]
            
        # Guardar la factura en la base de datos
        session = SessionLocal()
        try:
            # Intentar guardar la cabecera de la factura
            new_factura = FacturaCabecera(**factura_cabecera_data)
            session.add(new_factura)
            session.flush()
            
            # Si la cabecera se guardó correctamente, guardar los detalles
            for detalle in detalles_factura:
                new_detalle = FacturaDetalle(**detalle)
                session.add(new_detalle)
            
            session.commit()
            logger.info(f"Factura #{factura_cabecera_data['numeroFactura']} guardada para emisión offline")
            return True, "Factura guardada correctamente para emisión offline"
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error SQL al guardar la factura offline: {e}")
            return False, f"Error al guardar la factura: {str(e)}"
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error general al preparar factura offline: {e}")
        return False, f"Error al preparar factura offline: {str(e)}"

def save_invoice_xml(numero_factura, cuf, xml_content):
    """
    Guarda el XML de una factura emitida offline
    
    Args:
        numero_factura (int): Número de factura
        cuf (str): CUF de la factura
        xml_content (str): Contenido XML de la factura
        
    Returns:
        tuple: (bool, str) - (éxito, mensaje)
    """
    try:
        # Crear directorio si no existe
        os.makedirs("xmls_offline", exist_ok=True)
        
        # Guardar el XML
        filename = f"xmls_offline/factura_{numero_factura}_{cuf}.xml"
        with open(filename, "w", encoding='utf-8') as f:
            f.write(xml_content)
        
        logger.info(f"XML de factura offline guardado: {filename}")
        return True, f"XML guardado en {filename}"
    except Exception as e:
        logger.error(f"Error al guardar XML de factura offline: {e}")
        return False, f"Error al guardar XML: {str(e)}"

def get_pending_invoices():
    """
    Obtiene todas las facturas pendientes de envío
    
    Returns:
        list: Lista de facturas pendientes
    """
    session = SessionLocal()
    try:
        facturas = session.query(FacturaCabecera).filter(
            FacturaCabecera.estadoFirma == "CONTINGENCIA"
        ).all()
        return [f.to_dict() for f in facturas]
    except Exception as e:
        logger.error(f"Error al obtener facturas pendientes: {e}")
        return []
    finally:
        session.close()

def update_invoice_status_after_sending(numero_factura, codigo_recepcion, estado):
    """
    Actualiza el estado de una factura después de enviarla al SIN
    
    Args:
        numero_factura (int): Número de factura
        codigo_recepcion (str): Código de recepción del SIN
        estado (str): Nuevo estado de la factura
        
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    session = SessionLocal()
    try:
        factura = session.query(FacturaCabecera).filter(
            FacturaCabecera.numeroFactura == numero_factura
        ).first()
        
        if factura:
            factura.codigoRecepcion = codigo_recepcion
            factura.estadoFirma = "FIRMADO"
            factura.resultadoValidacion = estado
            factura.fechaValidacion = datetime.now()
            factura.fechaSincronizacion = datetime.now()
            session.commit()
            
            logger.info(f"Factura #{numero_factura} actualizada con estado {estado}")
            return True
        else:
            logger.warning(f"No se encontró la factura #{numero_factura}")
            return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error al actualizar estado de factura #{numero_factura}: {e}")
        return False
    finally:
        session.close()

import streamlit as st
from database import SessionLocal
from facturador.models import SincronizarParametricaEventosSignificativos, EventoSignificativoRegistrado, Cufd
from facturador.logger_config import get_logger

logger = get_logger('contingency')

def register_significant_event_ui():
    """
    Interfaz para registrar un evento significativo antes de operar en modo offline.
    """
    st.subheader("Registrar Evento Significativo")
    session = SessionLocal()

    try:
        # Obtener eventos significativos sincronizados
        eventos = session.query(SincronizarParametricaEventosSignificativos).all()
        if not eventos:
            st.error("No se encontraron eventos significativos sincronizados. Por favor, sincronice los datos.")
            return False

        # Crear opciones para el selectbox
        opciones_eventos = {f"{evento.codigoClasificador} - {evento.descripcion}": evento.codigoClasificador for evento in eventos}
        evento_seleccionado = st.selectbox("Seleccione el evento significativo:", list(opciones_eventos.keys()))

        # Botón para registrar el evento
        if st.button("Registrar Evento"):
            codigo_evento = opciones_eventos[evento_seleccionado]
            descripcion_evento = next(evento.descripcion for evento in eventos if evento.codigoClasificador == codigo_evento)

            # Obtener el CUFD vigente
            cufd_record = session.query(Cufd).filter(Cufd.vigente == 1).first()
            if not cufd_record or not cufd_record.codigo:
                st.error("No se encontró un CUFD vigente. Por favor, solicite un CUFD antes de continuar.")
                return False

            # Registrar el evento en la base de datos
            nuevo_evento = EventoSignificativoRegistrado(
                codigo_evento=codigo_evento,
                descripcion=descripcion_evento,
                fecha_inicio=datetime.now(),
                fecha_fin=None,  # Se actualizará cuando termine la contingencia
                cufd=cufd_record.codigo,
                fecha_registro=datetime.now()
            )
            session.add(nuevo_evento)
            session.commit()
            st.success(f"Evento significativo '{descripcion_evento}' registrado correctamente con ID {nuevo_evento.id}.")
            return True

    except Exception as e:
        logger.error(f"Error al registrar evento significativo: {e}")
        st.error("Ocurrió un error al registrar el evento significativo.")
        return False

    finally:
        session.close()

def offline_main():
    """
    Interfaz para la emisión de facturas en modo offline.
    """
    st.title("Facturación en Modo Offline")
    st.info("Está operando en modo contingencia. Las facturas se generarán y almacenarán localmente.")

    # Registrar evento significativo antes de permitir la facturación
    if not register_significant_event_ui():
        return

    # Formulario para generar facturas
    with st.form("offline_invoice_form"):
        cliente = st.text_input("Nombre del Cliente", placeholder="Ingrese el nombre del cliente")
        nit_ci = st.text_input("NIT/CI del Cliente", placeholder="Ingrese el NIT o CI del cliente")
        monto_total = st.number_input("Monto Total (Bs)", min_value=0.0, step=0.01)
        descripcion = st.text_area("Descripción", placeholder="Ingrese la descripción de la factura")
        
        submit_button = st.form_submit_button("Generar Factura")

    if submit_button:
        if not cliente or not nit_ci or monto_total <= 0:
            st.error("Por favor, complete todos los campos obligatorios.")
        else:
            # Lógica para guardar la factura en modo offline
            factura_cabecera_data = {
                "nombreRazonSocial": cliente,
                "numeroDocumento": nit_ci,
                "montoTotal": monto_total,
                "descripcion": descripcion,
                "estadoFirma": "CONTINGENCIA",
                "tipoEmision": 2,  # Emisión offline
                "fechaEmision": datetime.now()
            }
            success, message = save_offline_invoice(factura_cabecera_data, [])
            if success:
                st.success(message)
            else:
                st.error(message)
