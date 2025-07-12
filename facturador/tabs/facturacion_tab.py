"""
Módulo para la pestaña principal de facturación.
"""
import os
import logging
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from decimal import Decimal

# Imports de la aplicación
from database import SessionLocal
from data_access import fetch_tipos_documento
from business_logic import calculate_totals, collect_product_lines, generate_invoice_link
from invoice_xml_generator import generate_xml_invoice
from invoice_templates import generate_html_invoice, generate_compact_html_invoice
from validators import validar_factura_cabecera, validar_factura_detalle
from xml_signer import sign_xml
from generate_cuf import generate_cuf
from cufd import solicitar_cufd
from zeeper import validar_xml, comprimir_xml, obtener_hash, enviar_solicitud
from response_handler import parse_siat_response, display_siat_response
from data_access import guardar_factura_cabecera, guardar_factura_detalle
from invoice_manager import obtener_y_reservar_numero_factura
from print_manager import initialize_print_state, mostrar_mensaje_impresion_en_curso, imprimir_en_hilo

# Módulos locales
from facturacion_sidebar import load_base_data, render_sidebar_client_data, render_sidebar_invoice_config
from ui_utils import show_message
from logger_config import get_logger, get_facturacion_logger, get_xml_logger, get_printer_logger

logger = get_logger()
facturacion_logger = get_facturacion_logger()
xml_logger = get_xml_logger()
printer_logger = get_printer_logger()

def get_cufd():
    """Obtiene el CUFD válido de la base de datos."""
    from database import SessionLocal
    from facturador.models import Cufd
    
    session = SessionLocal()
    try:
        cufd_record = session.query(Cufd).filter(Cufd.vigente == 1).first()
        if cufd_record:
            return cufd_record.codigo
        else:
            raise ValueError("❌CUFD no encontrado en la base de datos.")
    except Exception as e:
        raise ValueError(f"❌Error al obtener el CUFD: {e}")
    finally:
        session.close()

def verificar_y_obtener_cufd(message_placeholder):
    """Verifica y obtiene un CUFD válido, renovándolo si es necesario."""
    from database import SessionLocal
    from facturador.models import Cufd
    
    session = SessionLocal()
    try:
        cufd_record = session.query(Cufd).filter(Cufd.vigente == 1).first()
        if cufd_record and cufd_record.fecha_vigencia > datetime.now():
            return cufd_record.codigo
        else:
            nuevo_cufd = solicitar_cufd()
            show_message('info', ":heavy_check_mark: Se ha renovado el CUFD.", message_placeholder)
            logger.info("CUFD renovado exitosamente")
            return nuevo_cufd
    except Exception as e:
        show_message('error', f"❌Error al verificar o solicitar CUFD: {e}", message_placeholder)
        logger.error(f"Error al verificar o solicitar CUFD: {e}")
        raise ValueError(f"Error al verificar o solicitar CUFD: {e}")
    finally:
        session.close()

def render():
    """Renderiza la pestaña principal de facturación."""
    logger.info("Usuario accedió a la pestaña principal de facturación")
    
    # Placeholder para mensajes
    message_placeholder = st.empty()
    
    # Cargar datos base
    comandas, metodos_pago, tipos_documento, error = load_base_data()
    if error:
        st.error(f"Error al cargar datos base: {error}")
        return
    
    # Renderizar sidebar
    client_data = render_sidebar_client_data(tipos_documento, message_placeholder)
    invoice_config = render_sidebar_invoice_config(comandas, metodos_pago)
    
    # Calcular totales y generar vista previa
    if invoice_config['selected_id_comanda']:
        comandas_seleccionadas = [
            comanda for comanda in comandas 
            if comanda["id_comanda"] in invoice_config['selected_id_comanda']
        ]
        
        subtotal, descuento_aplicado, monto_giftcard, total, monto_total_sujeto_iva, monto_total_moneda = calculate_totals(
            comandas_seleccionadas, 
            invoice_config['descuento_adicional'], 
            invoice_config['monto_giftcard'], 
            invoice_config['codigo_clasificador_metodo_pago'],
            tipo_cambio=1
        )
        
        db = SessionLocal()
        try:
            lineas_productos = collect_product_lines(comandas, invoice_config['selected_id_comanda'], db)
        finally:
            db.close()
    else:
        comandas_seleccionadas = []
        subtotal, descuento_aplicado, monto_giftcard, total, monto_total_sujeto_iva, monto_total_moneda = 0, 0, 0, 0, 0, 0
        lineas_productos = []

    # Configurar fechas
    fecha_emision = datetime.now()
    fecha_emision_str = fecha_emision.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    fecha_emision_display = fecha_emision.strftime("%d/%m/%Y %H:%M:%S")
    
    # Vista previa de la factura
    numero_factura_preview = '(se asignará al emitir)'
    html_invoice = generate_html_invoice(
        subtotal, 
        invoice_config['descuento_adicional'], 
        invoice_config['monto_giftcard'], 
        lineas_productos,
        client_data['nombre_cliente'], 
        fecha_emision_display, 
        numero_factura_preview, 
        invoice_config['seleccion_metodo_pago'],
        invoice_config['codigo_clasificador_metodo_pago'], 
        client_data['seleccion_tipo_documento'],
        client_data['codigo_clasificador_documento'], 
        client_data['numero_documento'], 
        client_data['complemento'],
        client_data['email'], 
        client_data['telefono'], 
        invoice_config['ultimos_digitos_tarjeta']
    )
    
    components.html(html_invoice, height=700, scrolling=True)

    # Botones de acción
    col1, col2, col3 = st.columns(3)

    with col1:
        _render_facturar_button(
            invoice_config, client_data, tipos_documento, comandas_seleccionadas,
            lineas_productos, subtotal, total, fecha_emision, fecha_emision_str,
            fecha_emision_display, message_placeholder
        )

    with col2:
        _render_print_button()

    with col3:
        _render_consultar_button()

def _render_facturar_button(invoice_config, client_data, tipos_documento, comandas_seleccionadas,
                           lineas_productos, subtotal, total, fecha_emision, fecha_emision_str,
                           fecha_emision_display, message_placeholder):
    """Renderiza el botón de facturar y maneja la lógica de facturación."""
    if st.button("Facturar", key="generar_xml", help="Generar la factura", 
                disabled=not invoice_config['selected_id_comanda']):
        
        if (invoice_config['metodo_pago_seleccionado'] and 
            client_data['seleccion_tipo_documento'] and 
            client_data['numero_documento'] and 
            invoice_config['selected_id_comanda']):
            
            try:
                logger.info("Iniciando proceso de facturación")
                
                # Configuración inicial
                tipo_documento_seleccionado = next(
                    (doc for doc in tipos_documento 
                     if doc["descripcion"] == client_data['seleccion_tipo_documento']), 
                    None
                )
                
                # Variables de entorno
                nit_emisor = int(os.getenv('NIT'))
                razon_social_emisor = os.getenv('RAZON_SOCIAL')
                municipio = os.getenv('MUNICIPIO')
                telefono_emisor = os.getenv('TELEFONO')
                codigo_sucursal = int(os.getenv('CODIGO_SUCURSAL'))
                codigo_punto_venta = int(os.getenv('CODIGO_PUNTO_VENTA'))
                codigo_documento_sector = int(os.getenv('CODIGO_DOCUMENTO_SECTOR'))
                direccion = os.getenv('DIRECCION')
                
                # Obtener CUFD
                cufd = verificar_y_obtener_cufd(message_placeholder)
                
                # Reservar número de factura
                numero_factura = obtener_y_reservar_numero_factura()
                logger.info(f"Número de factura reservado: {numero_factura}")
                
                # Generar CUF
                cuf = generate_cuf(
                    nit_emisor, 
                    fecha_emision, 
                    codigo_sucursal, 
                    int(os.getenv('CODIGO_MODALIDAD')),
                    int(os.getenv('CODIGO_TIPO_EMISION')), 
                    int(os.getenv('CODIGO_TIPO_FACTURA')),
                    codigo_documento_sector, 
                    numero_factura,
                    codigo_punto_venta
                )
                logger.info(f"CUF generado: {cuf}")
                
                # Generar XML
                xml_str, factura_cabecera_data, detalles_data = generate_xml_invoice(
                    nit_emisor, razon_social_emisor, municipio, telefono_emisor, numero_factura,
                    cuf, cufd, codigo_sucursal, direccion, codigo_punto_venta,
                    fecha_emision_str, client_data['nombre_cliente'], 
                    tipo_documento_seleccionado['codigoClasificador'],
                    client_data['numero_documento'], client_data['complemento'], 
                    client_data['numero_documento'],
                    invoice_config['metodo_pago_seleccionado']['codigoClasificador'], 
                    invoice_config['ultimos_digitos_tarjeta'],
                    subtotal, total, 1, 1, total / 1, 
                    invoice_config['monto_giftcard'], invoice_config['descuento_adicional'],
                    "don_bercho", codigo_documento_sector, lineas_productos,
                    os.getenv('ACTIVIDAD_ECONOMICA'), os.getenv('CODIGO_PRODUCTO_SIN')
                )
                
                # Firmar XML
                private_key_path = "xmls/llaves/private_key_ok.pem"
                cert_path = "xmls/llaves/certificado_ok.pem"
                signed_xml_str = sign_xml(xml_str, private_key_path, cert_path, cuf)
                
                # Guardar XML firmado
                filename = f"xmls/factura_{numero_factura}_{cuf}_.xml"
                with open(filename, "w", encoding='utf-8') as signed_xml_file:
                    signed_xml_file.write(signed_xml_str)
                
                # Validar XML
                xsd_main_path = 'xmls/schemas/facturaElectronicaCompraVenta.xsd'
                if not validar_xml(filename, xsd_main_path):
                    show_message('error', "❌ El XML generado no es válido contra el XSD.", message_placeholder)
                    logger.error("XML no válido contra XSD")
                    return
                
                # Comprimir y enviar
                gzip_path = comprimir_xml(filename)
                hash_archivo = obtener_hash(gzip_path)
                response = enviar_solicitud(filename, xsd_main_path, fecha_emision_str, cufd)
                
                # Procesar respuesta
                if isinstance(response, dict) and response.get("error"):
                    show_message('error', f"❌Error al enviar la factura: {response['error']}", message_placeholder)
                    logger.error(f"Error al enviar factura: {response['error']}")
                else:
                    try:
                        success, response_data = parse_siat_response(response.content)
                        if success:
                            transaccion_exitosa = display_siat_response(response_data, message_placeholder)
                            if transaccion_exitosa:
                                # Guardar datos en session state
                                st.session_state['cuf'] = cuf
                                st.session_state['ultima_factura'] = numero_factura
                                st.session_state['factura_validada'] = True
                                st.session_state['datos_impresion'] = {
                                    'subtotal': subtotal,
                                    'descuento_adicional': invoice_config['descuento_adicional'],
                                    'monto_giftcard': invoice_config['monto_giftcard'],
                                    'lineas_productos': lineas_productos,
                                    'nombre_cliente': client_data['nombre_cliente'],
                                    'fecha_emision_str': fecha_emision_display,
                                    'seleccion_metodo_pago': invoice_config['seleccion_metodo_pago'],
                                    'codigo_clasificador_metodo_pago': invoice_config['codigo_clasificador_metodo_pago'],
                                    'seleccion_tipo_documento': client_data['seleccion_tipo_documento'],
                                    'codigo_clasificador_documento': client_data['codigo_clasificador_documento'],
                                    'numero_documento': client_data['numero_documento'],
                                    'complemento': client_data['complemento'],
                                    'email': client_data['email'],
                                    'telefono': client_data['telefono'],
                                    'ultimos_digitos_tarjeta': invoice_config['ultimos_digitos_tarjeta']
                                }
                                
                                # Guardar en base de datos
                                factura_cabecera_data['tipoEmision'] = "1"
                                is_valid, error_message = validar_factura_cabecera(factura_cabecera_data)
                                if is_valid:
                                    guardar_factura_cabecera(factura_cabecera_data)
                                    for detalle in detalles_data:
                                        is_valid, error_message = validar_factura_detalle(detalle)
                                        if is_valid:
                                            guardar_factura_detalle(detalle)
                                        else:
                                            show_message('error', error_message, message_placeholder)
                                            logger.error(f"Error al validar detalle: {error_message}")
                                            return
                                    
                                    logger.info(f"Factura {numero_factura} procesada exitosamente")
                                else:
                                    show_message('error', error_message, message_placeholder)
                                    logger.error(f"Error al validar cabecera: {error_message}")
                        else:
                            facturacion_logger.error(f"Error al procesar respuesta: {response_data.get('error')}")
                            if 'xml_content' in response_data:
                                xml_logger.error(f"Contenido XML problemático: {response_data['xml_content'][:500]}...")
                    except Exception as e:
                        show_message('error', f"❌Error al procesar la respuesta: {str(e)}", message_placeholder)
                        facturacion_logger.exception("Error inesperado al procesar respuesta")
                        
            except Exception as e:
                show_message('error', f"❌Error en el proceso de facturación: {str(e)}", message_placeholder)
                logger.exception("Error en facturación")
        else:
            show_message('error', "❌Por favor, complete todos los campos requeridos.", message_placeholder)
            logger.warning("Intento de facturación con campos incompletos")

def _render_print_button():
    """Renderiza el botón de impresión y maneja la lógica de impresión."""
    # Asegurarse de que el estado esté inicializado
    initialize_print_state()

    # Mostrar advertencia si la impresión está en curso
    mostrar_mensaje_impresion_en_curso()

    # Botón para forzar liberación de impresión si está colgada
    if st.session_state.get('impresion_en_progreso', False):
        if st.button("Forzar liberación de impresión", key="forzar_liberacion_impresion"):
            st.session_state['impresion_en_progreso'] = False
            st.session_state['print_status'] = "⚠️ Impresión liberada manualmente. Puedes volver a intentar imprimir."
            logger.info("Impresión liberada manualmente por el usuario")

    if st.session_state.get('factura_validada'):
        # Determinar si el botón de imprimir debe estar desactivado
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
                    printer_logger.error(f"Faltan claves requeridas en session_state: {missing_keys}")
                else:
                    # Generar contenido HTML para la factura
                    datos = st.session_state['datos_impresion']
                    html_content = generate_compact_html_invoice(
                        subtotal=datos['subtotal'],
                        descuento_adicional=datos['descuento_adicional'],
                        monto_giftcard=datos['monto_giftcard'],
                        lineas_productos=datos['lineas_productos'],
                        nombre_cliente=datos['nombre_cliente'],
                        fecha_emision=datos['fecha_emision_str'],
                        numero_factura=st.session_state['ultima_factura'],
                        metodo_de_pago=datos.get('seleccion_metodo_pago'),
                        codigo_clasificador_metodo_pago=datos.get('codigo_clasificador_metodo_pago'),
                        tipo_documento=datos.get('seleccion_tipo_documento'),
                        codigo_clasificador_documento=datos.get('codigo_clasificador_documento'),
                        numero_documento=datos.get('numero_documento'),
                        complemento=datos.get('complemento'),
                        email=datos.get('email'),
                        telefono=datos.get('telefono'),
                        ultimos_digitos_tarjeta=datos.get('ultimos_digitos_tarjeta'),
                        cuf=st.session_state['cuf']
                    )
                    
                    # Iniciar el hilo de impresión
                    logger.info(f"Iniciando impresión de factura {st.session_state['ultima_factura']}")
                    hilo_impresion = imprimir_en_hilo(
                        html_content,
                        st.session_state['cuf'],
                        os.getenv('NIT'),
                        st.session_state['ultima_factura']
                    )
                    
            except Exception as e:
                st.session_state['print_status'] = f"❌ Error: {str(e)}"
                st.session_state['impresion_en_progreso'] = False
                printer_logger.exception("Error en el proceso de impresión")
    else:
        st.info("El botón de impresión solo estará disponible cuando la factura haya sido validada exitosamente por el SIN.")

def _render_consultar_button():
    """Renderiza el botón de consultar factura."""
    if st.session_state.get('factura_validada'):
        nit_emisor = int(os.getenv('NIT'))
        enlace = generate_invoice_link(
            nit_emisor, 
            st.session_state['cuf'], 
            st.session_state['ultima_factura']
        )
        st.link_button("Consultar factura", enlace)
        logger.info("Enlace de consulta de factura generado")
