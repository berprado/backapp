"""
Funciones auxiliares para la facturación offline.
Este módulo implementa las funciones necesarias para manejar el flujo
de facturación cuando el sistema está en modo contingencia.
"""
import os
import logging
from datetime import datetime
import streamlit as st
from facturador.database import SessionLocal
from facturador.models import Cufd
from facturador.generate_cuf import generate_cuf
from facturador.invoice_xml_generator import generate_xml_invoice
from facturador.common.validaciones import validar_factura_cabecera, validar_factura_detalle

logger = logging.getLogger(__name__)

def obtener_cufd_vigente():
    """
    Obtiene el CUFD vigente almacenado en la BD.
    En modo offline NO se debe solicitar un CUFD nuevo.
    
    Returns:
        dict: Datos del CUFD vigente o None si no se encuentra
    """
    session = SessionLocal()
    try:
        cufd_record = session.query(Cufd).filter(Cufd.vigente == True).first()
        if not cufd_record:
            logger.warning("No se encontró CUFD vigente para modo offline")
            return None
        
        logger.info(f"CUFD vigente encontrado: {cufd_record.codigo}")
        return {
            'codigo': cufd_record.codigo,
            'codigo_control': cufd_record.codigoControl
        }
    except Exception as e:
        logger.error(f"Error al obtener CUFD vigente: {str(e)}")
        return None
    finally:
        session.close()

def generar_cuf_offline(nit_emisor, fecha_emision, codigo_sucursal, codigo_modalidad, 
                        codigo_tipo_factura, codigo_documento_sector, numero_factura, codigo_punto_venta):
    """
    Genera un CUF específico para modo offline (tipo_emision=2)
    
    Args:
        nit_emisor: NIT del emisor
        fecha_emision: Fecha y hora de emisión
        codigo_sucursal: Código de sucursal
        codigo_modalidad: Código de modalidad
        codigo_tipo_factura: Código de tipo de factura
        codigo_documento_sector: Código de documento sector
        numero_factura: Número de factura
        codigo_punto_venta: Código de punto de venta
        
    Returns:
        str: CUF generado para modo offline
    """
    return generate_cuf(
        nit_emisor, 
        fecha_emision, 
        codigo_sucursal, 
        codigo_modalidad,
        2,  # Usar tipo_emision=2 para offline
        codigo_tipo_factura,
        codigo_documento_sector, 
        numero_factura,
        codigo_punto_venta
    )

def generar_xml_offline(datos_emisor, datos_cliente, datos_factura, datos_totales, lineas_productos, evento_contingencia):
    """
    Genera el XML de una factura en modo offline
    
    Args:
        datos_emisor: Dict con datos del emisor (NIT, razon social, etc)
        datos_cliente: Dict con datos del cliente (NIT/CI, nombre, etc)
        datos_factura: Dict con datos de la factura (numero, fecha, etc)
        datos_totales: Dict con datos de totales (subtotal, descuentos, etc)
        lineas_productos: Lista de productos/servicios
        evento_contingencia: Dict con datos del evento de contingencia
        
    Returns:
        tuple: (xml_str, factura_cabecera_data, detalles_data)
    """
    # Determinar si se debe incluir código de excepción
    codigo_excepcion = 1 if datos_cliente['codigo_tipo_documento_identidad'] == '5' else None
    logger.info(f"Generando XML offline - CódigoExcepción: {codigo_excepcion}")
    
    # Generar XML con tipo_emision=2
    xml_str, factura_cabecera_data, detalles_data = generate_xml_invoice(
        nit_emisor=datos_emisor['nit'], 
        razon_social_emisor=datos_emisor['razon_social'], 
        municipio=datos_emisor['municipio'],
        telefono_emisor=datos_emisor['telefono'], 
        numero_factura=datos_factura['numero'],
        cuf=datos_factura['cuf'], 
        cufd=datos_factura['cufd'], 
        codigo_sucursal=datos_emisor['sucursal'],
        direccion=datos_emisor['direccion'], 
        codigo_punto_venta=datos_emisor['punto_venta'],
        fecha_emision=datos_factura['fecha_emision'],
        nombre_razon_social=datos_cliente['nombre'].upper(),
        codigo_tipo_documento_identidad=datos_cliente['codigo_tipo_documento_identidad'],
        numero_documento=datos_cliente['numero_documento'],
        complemento=datos_cliente['complemento'],
        codigo_cliente=datos_cliente['codigo_cliente'],
        codigo_metodo_pago=datos_cliente['codigo_metodo_pago'],
        ultimos_digitos_tarjeta=datos_cliente['ultimos_digitos_tarjeta'],
        subtotal=datos_totales['subtotal'],
        total=datos_totales['total'],
        codigo_moneda=datos_totales['codigo_moneda'],
        tipo_cambio=datos_totales['tipo_cambio'],
        monto_total_moneda=datos_totales['monto_total_moneda'],
        monto_giftcard=datos_totales['monto_giftcard'],
        descuento_adicional=datos_totales['descuento_adicional'],
        usuario=datos_emisor['usuario'],
        codigo_documento_sector=datos_emisor['codigo_documento_sector'],
        lineas_productos=lineas_productos,
        actividad_economica=datos_emisor['actividad_economica'],
        codigo_producto_sin=datos_emisor['codigo_producto_sin'],
        tipo_emision=2,  # Modo offline
        codigo_excepcion=codigo_excepcion  # 1 para NIT en offline
    )
    
    # Actualizar datos de cabecera con información de contingencia
    factura_cabecera_data.update({
        'estado': 'PENDIENTE',
        'tipoEmision': 2,  # Offline
        'evento_contingencia_id': evento_contingencia['id'],
        'almacenadoSiat': False,
        'mensajeRecepcion': f"Factura emitida en contingencia - Evento #{evento_contingencia['id']}",
        'codigoExcepcion': codigo_excepcion  # Asegurar que se guarda en BD
    })
    
    return xml_str, factura_cabecera_data, detalles_data

def guardar_factura_offline_bd(factura_cabecera_data, detalles_data):
    """
    Guarda la factura offline en la base de datos con estado PENDIENTE
    
    Args:
        factura_cabecera_data: Dict con datos de la cabecera
        detalles_data: Lista de dicts con datos de los detalles
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    from facturador.data_access import guardar_factura_cabecera, guardar_factura_detalle
    
    try:
        # Validar datos
        factura_cabecera_data = validar_factura_cabecera(factura_cabecera_data)
        
        # Guardar cabecera
        factura_id = guardar_factura_cabecera(factura_cabecera_data)
        
        # Guardar detalles
        for detalle in detalles_data:
            detalle = validar_factura_detalle(detalle)
            detalle['factura_id'] = factura_id
            guardar_factura_detalle(detalle)
        
        logger.info(f"Factura #{factura_cabecera_data['numeroFactura']} guardada como PENDIENTE")
        return True
    except Exception as e:
        logger.error(f"Error al guardar factura offline en BD: {str(e)}")
        return False

def validar_modo_offline():
    """
    Verifica si el sistema está correctamente configurado para modo offline
    
    Returns:
        tuple: (valido, mensaje, evento_contingencia)
    """
    # Verificar si hay un evento de contingencia activo
    from facturador.database import obtener_evento_abierto
    evento = obtener_evento_abierto()
    if not evento:
        return False, "No hay un evento de contingencia activo", None
    
    # Verificar si hay un CUFD vigente
    cufd = obtener_cufd_vigente()
    if not cufd:
        return False, "No hay un CUFD vigente para emisión offline", evento
    
    return True, "Sistema listo para emisión offline", evento

def mostrar_banner_offline(evento_contingencia):
    """
    Muestra un banner visual indicando que estamos en modo offline
    
    Args:
        evento_contingencia: Dict con datos del evento
    """
    if not evento_contingencia:
        return
    
    # Formatear fecha de inicio para mostrarla legible
    fecha_inicio = evento_contingencia['fecha_inicio']
    fecha_inicio_str = fecha_inicio.strftime("%d/%m/%Y %H:%M:%S") if fecha_inicio else "N/A"
    
    st.markdown(
        f"""
        <div style="background-color: #ffdd57; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <h2 style="margin: 0; color: #856404;">⚠️ MODO CONTINGENCIA (OFFLINE) ⚠️</h2>
            <p style="margin: 5px 0 0 0; color: #856404;">
                <strong>Evento:</strong> {evento_contingencia['codigo_evento']} - {evento_contingencia['descripcion']}<br>
                <strong>Inicio:</strong> {fecha_inicio_str}<br>
                Las facturas emitidas quedarán en estado PENDIENTE hasta que se restablezca la conexión con el SIAT.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
