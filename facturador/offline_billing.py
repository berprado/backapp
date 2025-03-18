import os
import time
import logging
from datetime import datetime
from database import SessionLocal
from facturador.models import FacturaCabecera, FacturaDetalle
from logger_config import get_contingency_logger, get_facturacion_logger

logger = get_contingency_logger()
facturacion_logger = get_facturacion_logger()

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
