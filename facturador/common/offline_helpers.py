"""
Módulo con funciones auxiliares para el soporte de facturación offline.
Contiene funciones compartidas entre ui_copy.py y ui_offline.py para
garantizar consistencia en el manejo de contingencias.
"""

import os
import logging
from datetime import datetime
from facturador.database import SessionLocal
from facturador.generate_cuf import generate_cuf
from facturador.cufd import get_cufd
import streamlit as st

def verificar_requisitos_offline(message_placeholder):
    """
    Verifica que los requisitos para facturación offline estén disponibles.
    
    Args:
        message_placeholder: Placeholder para mostrar mensajes
        
    Returns:
        tuple: (exito, cufd_record) - Indica si están disponibles los requisitos y el CUFD a usar
    """
    # Verificar que exista un CUFD para usar en contingencia
    cufd_record = get_cufd()
    if not cufd_record:
        message_placeholder.error("❌ No hay un CUFD disponible para emitir facturas en modo offline.")
        return False, None
    
    return True, cufd_record

def preparar_xml_offline(factura_cabecera_data, evento_contingencia):
    """
    Prepara los datos adicionales para el XML de factura en modo offline.
    
    Args:
        factura_cabecera_data: Diccionario con los datos de la cabecera
        evento_contingencia: Datos del evento de contingencia actual
    
    Returns:
        dict: Datos de cabecera modificados para offline
    """
    # Actualizar los datos para modo offline
    factura_cabecera_data.update({
        'estado': 'PENDIENTE',
        'resultadoValidacion': None,
        'tipoEmision': 2,  # Modo offline
        'mensajeRecepcion': f'Factura en contingencia - Evento #{evento_contingencia["id"]}',
        'almacenadoSiat': False,
        'evento_contingencia_id': evento_contingencia.get('id')
    })
    
    return factura_cabecera_data

def generar_cuf_offline(fecha_emision):
    """
    Genera un CUF específico para modo offline (tipo_emision=2)
    
    Args:
        fecha_emision: Fecha y hora de emisión de la factura
    
    Returns:
        str: CUF generado para modo offline
    """
    nit_emisor = int(os.getenv('NIT'))
    codigo_sucursal = int(os.getenv('CODIGO_SUCURSAL'))
    codigo_punto_venta = int(os.getenv('CODIGO_PUNTO_VENTA'))
    codigo_documento_sector = int(os.getenv('CODIGO_DOCUMENTO_SECTOR'))
    numero_factura = get_next_invoice_number()
    
    # Generar CUF con tipo_emision=2 (Offline)
    cuf = generate_cuf(
        nit_emisor, 
        fecha_emision, 
        codigo_sucursal, 
        int(os.getenv('CODIGO_MODALIDAD')),
        2,  # Usar tipo_emision=2 para offline
        int(os.getenv('CODIGO_TIPO_FACTURA')),
        codigo_documento_sector, 
        numero_factura,
        codigo_punto_venta
    )
    
    return cuf, numero_factura

def guardar_factura_en_bd(factura_cabecera_data, detalles_data):
    """
    Guarda la factura y sus detalles en la base de datos.
    
    Args:
        factura_cabecera_data: Datos de la cabecera de la factura
        detalles_data: Lista de detalles de la factura
        
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    from facturador.data_access import guardar_factura_cabecera, guardar_factura_detalle
    from facturador.common.validaciones import validar_factura_cabecera, validar_factura_detalle
    
    try:
        # Validar datos
        factura_cabecera_data = validar_factura_cabecera(factura_cabecera_data)
        detalles_data = [validar_factura_detalle(detalle) for detalle in detalles_data]
        
        # Guardar cabecera y obtener ID
        id_factura = guardar_factura_cabecera(factura_cabecera_data)
        
        # Guardar detalles con el ID de la cabecera
        for detalle in detalles_data:
            detalle['idFacturaCabecera'] = id_factura
            guardar_factura_detalle(detalle)
            
        return True
    except Exception as e:
        logging.exception(f"Error al guardar factura en BD: {str(e)}")
        return False

def validar_campos_requeridos(codigo_metodo_pago, codigo_documento, numero_documento, comandas_seleccionadas):
    """
    Valida que todos los campos requeridos para la facturación estén completos.
    
    Args:
        codigo_metodo_pago: Código del método de pago seleccionado
        codigo_documento: Código del tipo de documento seleccionado
        numero_documento: Número de documento ingresado
        comandas_seleccionadas: Lista de comandas seleccionadas
    
    Returns:
        tuple: (bool, str) - Indica si la validación fue exitosa y un mensaje de error si no lo fue
    """
    if not codigo_metodo_pago:
        return False, "Debe seleccionar un método de pago"
    
    if not codigo_documento:
        return False, "Debe seleccionar un tipo de documento"
        
    if not numero_documento:
        return False, "Debe ingresar un número de documento"
        
    if not comandas_seleccionadas or len(comandas_seleccionadas) == 0:
        return False, "Debe seleccionar al menos una comanda"
    
    return True, ""

def mostrar_opciones_impresion(message_placeholder):
    """
    Muestra las opciones de impresión para la factura.
    
    Args:
        message_placeholder: Placeholder para mostrar mensajes
    """
    # Opciones de impresión
    if st.session_state.get('factura_validada'):
        # Imprimir factura
        impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)
        
        if st.button("Imprimir Factura", disabled=impresion_en_progreso):
            try:
                # Marcar que la impresión está en progreso
                st.session_state['impresion_en_progreso'] = True
                st.session_state['print_status'] = "⏳ Procesando..."
                
                # Validar que las claves necesarias estén presentes
                required_keys = ['datos_impresion', 'cuf', 'ultima_factura']
                missing_keys = [key for key in required_keys if key not in st.session_state]
                if missing_keys:
                    st.session_state['print_status'] = f"❌ Faltan datos necesarios: {', '.join(missing_keys)}"
                    st.session_state['impresion_en_progreso'] = False
                    return
                
                # Generar HTML para impresión
                from facturador.invoice_templates import generate_compact_html_invoice
                html_content = generate_compact_html_invoice(**st.session_state['datos_impresion'])
                
                # Añadir banner de contingencia si estamos en modo offline
                html_content = html_content.replace("<body>",
                    """
                    <body>
                    <div class="contingency-banner">
                        *** FACTURA EMITIDA EN CONTINGENCIA ***
                    </div>
                    """
                )
                
                # Imprimir en hilo separado
                from facturador.common.ui_helpers import imprimir_en_hilo, monitorear_hilo_impresion
                nit = os.getenv('NIT')
                cuf = st.session_state['cuf']
                numero_factura = st.session_state['ultima_factura']
                hilo = imprimir_en_hilo(html_content, cuf, nit, numero_factura)
                monitorear_hilo_impresion(hilo)
                
            except Exception as e:
                st.error(f"❌ Error al preparar la impresión: {str(e)}")
                st.session_state['impresion_en_progreso'] = False
                logging.exception("Error en impresión")
        
        # Mostrar estado de la impresión si existe
        if st.session_state.get('print_status'):
            if "✅" in st.session_state['print_status']:
                st.success(st.session_state['print_status'])
            elif "❌" in st.session_state['print_status']:
                st.error(st.session_state['print_status'])
            else:
                st.info(st.session_state['print_status'])
