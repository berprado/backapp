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
from data_models import FacturaProcesada, DetalleFactura
from data_access import fetch_tipos_documento, obtener_cufd_de_evento_activo
from business_logic import calculate_totals, collect_product_lines, generate_invoice_link
from invoice_xml_generator import generate_xml_invoice
from invoice_templates import generate_html_invoice, generate_html_invoice_legacy, generate_compact_html_invoice, numero_a_palabras_con_decimales_como_fraccion
from validators import validar_factura_cabecera, validar_factura_detalle
from xml_signer import sign_xml
from generate_cuf import generate_cuf
from cufd import solicitar_cufd
from zeeper import validar_xml, comprimir_xml, obtener_hash, enviar_solicitud
from response_handler import parse_siat_response, display_siat_response
from data_access import guardar_factura_cabecera, guardar_factura_detalle
from invoice_manager import obtener_y_reservar_numero_factura
from print_manager import initialize_print_state, solicitar_impresion

# Módulos locales
from facturacion_sidebar import (
    load_base_data,
    render_sidebar_client_data,
    render_sidebar_invoice_config,
    reset_sidebar_fields
)
from ui_utils import show_message
from logger_config import get_logger, get_facturacion_logger, get_xml_logger, get_printer_logger

logger = get_logger()
facturacion_logger = get_facturacion_logger()
xml_logger = get_xml_logger()
printer_logger = get_printer_logger()

def get_cufd():
    """Obtiene el CUFD válido de la base de datos."""
    from database import SessionLocal
    from models import Cufd
    
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
    from models import Cufd
    
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

def render(is_online: bool, evento_activo: dict = None):
    """
    Renderiza la pestaña principal de facturación.
    
    Args:
        is_online: Booleano que indica si el sistema está online.
        evento_activo: Diccionario con la información del evento de contingencia activo, si existe.
    """
    logger.info(f"Renderizando pestaña de facturación en modo {'ONLINE' if is_online else 'OFFLINE'}")

    if not is_online:
        if evento_activo:
            st.warning(
                f"""
                ⚠️ **MODO DE CONTINGENCIA ACTIVADO** ⚠️\n
                **Evento:** {evento_activo.get('descripcion', 'N/A')} (ID: {evento_activo.get('id')})\n
                **CUFD del Evento:** `{evento_activo.get('cufd')}`\n
                *Las facturas se generarán y guardarán localmente para su envío posterior.*
                """,
                icon="📡"
            )
        else:
            # Este caso no debería ocurrir si main.py funciona bien, pero es una buena salvaguarda
            st.error("Error crítico: Modo offline pero no se encontró un evento de contingencia activo.")
            return # Detener la renderización de la pestaña si no hay evento
    
    # Placeholder para mensajes
    message_placeholder = st.empty()
    flash = st.session_state.pop('flash_message', None)
    if flash:
        level, text_msg = flash
        show_message(level, text_msg, message_placeholder)
    
    # Cargar datos base
    comandas, metodos_pago, tipos_documento, error = load_base_data()
    if error:
        # Si el mensaje contiene 'Advertencia', es que estamos usando datos simulados
        if error.startswith("Advertencia:"):
            st.warning(f"⚠️ {error}")
        else:
            st.error(f"Error al cargar datos base: {error}")
        
        # Si el error está relacionado solo con las comandas pero tenemos los tipos de documento y métodos de pago, 
        # podemos continuar con los datos que tenemos (sean simulados o vacíos)
        if metodos_pago and tipos_documento:
            if not comandas:
                st.info("ℹ️ Puede continuar la facturación de forma manual seleccionando productos.")
        else:
            # Error crítico, no podemos continuar
            st.error("❌ Error crítico: No se pudieron cargar los datos esenciales para la facturación.")
            st.info("📌 Sugerencia: Intente ejecutar el diagnóstico con `python diagnostico_api.py` para identificar el problema.")
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
    
    # Obtener el NIT del emisor para la vista previa
    nit_emisor = os.getenv('NIT')
    
    # Usar la función legacy para la vista previa
    html_invoice = generate_html_invoice_legacy(
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
        invoice_config['ultimos_digitos_tarjeta'],
        cuf='PREVIEW',  # Para la vista previa usamos un valor de ejemplo
        nit=nit_emisor
    )
    
    components.html(html_invoice, height=700, scrolling=True)

    # Botones de acción
    col1, col2, col3 = st.columns(3)

    with col1:
        _render_facturar_button(
            is_online, invoice_config, client_data, tipos_documento, comandas_seleccionadas,
            lineas_productos, subtotal, total, fecha_emision, fecha_emision_str,
            fecha_emision_display, message_placeholder, evento_activo
        )

    with col2:
        _render_print_button()

    with col3:
        _render_consultar_button()



def _mark_comandas_as_processed(comanda_ids):
    """Marca las comandas facturadas para que no vuelvan a mostrarse en la UI."""
    if not comanda_ids:
        return

    processed = st.session_state.get('processed_comandas')
    processed_list = list(processed) if processed is not None else []
    processed_set = set(processed_list)

    updated = False
    for comanda_id in comanda_ids:
        if comanda_id not in processed_set:
            processed_list.append(comanda_id)
            processed_set.add(comanda_id)
            updated = True

    if updated:
        st.session_state['processed_comandas'] = processed_list
        st.session_state['selected_comandas_pending_cleanup'] = []


def _render_facturar_button(is_online, invoice_config, client_data, tipos_documento, comandas_seleccionadas,
                           lineas_productos, subtotal, total, fecha_emision, fecha_emision_str,
                           fecha_emision_display, message_placeholder, evento_activo=None):
    """Renderiza el botón de facturar y maneja la lógica de facturación."""
    button_label = "Facturar y Enviar al SIN" if is_online else "Generar y Guardar Factura Offline"
    button_help = "Se conectará con el SIN para validar la factura." if is_online else "Guardará la factura localmente. NO se enviará al SIN."

    success = False

    if st.button(button_label, key="generar_xml", help=button_help,
                 disabled=not invoice_config['selected_id_comanda']):

        # Limpiar banderas previas de éxito
        st.session_state.pop('last_submission_success', None)

        if (invoice_config['metodo_pago_seleccionado'] and
            client_data['seleccion_tipo_documento'] and
            client_data['numero_documento'] and
            invoice_config['selected_id_comanda']):

            # Ejecutar el flujo correspondiente según el modo de operación
            if is_online:
                _handle_online_submission(
                    invoice_config, client_data, tipos_documento, comandas_seleccionadas,
                    lineas_productos, subtotal, total, fecha_emision, fecha_emision_str,
                    fecha_emision_display, message_placeholder
                )
            else:
                if evento_activo:
                    _handle_offline_submission(
                        invoice_config, client_data, evento_activo, tipos_documento,
                        lineas_productos, subtotal, total, fecha_emision,
                        fecha_emision_str, message_placeholder
                    )
                else:
                    show_message('error', "No se puede facturar en modo offline sin un evento de contingencia activo.", message_placeholder)

            payload = st.session_state.pop('last_submission_success', None)
            if payload:
                _mark_comandas_as_processed(payload.get('comandas', []))
                reset_sidebar_fields()
                st.session_state['flash_message'] = ('success', payload.get('message', 'Factura procesada exitosamente.'))
                success = True
        else:
            show_message('error', "❌Por favor, complete todos los campos requeridos.", message_placeholder)
            logger.warning("Intento de facturación con campos incompletos")

    if success:
        st.rerun()

def _render_print_button():
    """Renderiza el botón de impresión usando el sistema de cola de tareas."""
    initialize_print_state()
    
    # Mostrar el estado actual del servicio de impresión
    print_status = st.session_state.get('print_status', 'Sistema de impresión listo.')
    if "✅" in print_status:
        st.success(f"🖨️ {print_status}")
    elif any(icon in print_status for icon in ["⚠️", "❌", "🚨"]):
        st.error(f"🖨️ {print_status}")
    else:
        st.info(f"🖨️ {print_status}")

    if st.session_state.get('factura_validada'):
        factura_obj = st.session_state.get('factura_a_procesar')
        
        if st.button("🖨️ Imprimir Factura", key="imprimir_factura_final", disabled=not factura_obj):
            if factura_obj:
                try:
                    logger.info(f"Solicitando impresión para factura {factura_obj.numero_factura}.")
                    solicitar_impresion(factura_obj)
                    st.rerun() # Actualiza la UI para mostrar el estado "enviado a la cola"
                except Exception as e:
                    st.error(f"❌ Error al solicitar la impresión: {str(e)}")
                    logger.exception("Error en la llamada a solicitar_impresion")
            else:
                st.error("No se encontraron los datos de la factura para imprimir.")
    else:
        st.info("El botón de impresión solo estará disponible cuando la factura haya sido validada exitosamente por el SIN.")

def _render_consultar_button():
    """Renderiza el botón de consultar factura."""
    if st.session_state.get('factura_validada'):
        # Obtener la información desde el objeto factura_a_procesar
        factura_obj = st.session_state.get('factura_a_procesar')
        if factura_obj:
            try:
                nit_emisor = int(factura_obj.nit_emisor)
                
                # Verificar que los valores necesarios no sean None
                if factura_obj.cuf is None or factura_obj.numero_factura is None:
                    st.error("Datos incompletos: CUF o número de factura no disponibles.")
                    logger.error(f"Datos de factura incompletos - CUF: {factura_obj.cuf}, Número factura: {factura_obj.numero_factura}")
                    return
                
                # Verificar si la factura fue emitida en modo offline
                es_factura_offline = st.session_state.get('factura_emitida_offline', False)
                
                enlace = generate_invoice_link(
                    nit_emisor, 
                    factura_obj.cuf,
                    factura_obj.numero_factura
                )
                
                # Contenedor para el botón y la información
                if es_factura_offline:
                    with st.container():
                        st.warning("⚠️ **Factura emitida en modo offline**\n\nEl enlace estará disponible después del envío al SIN una vez restablecida la conexión.")
                        
                        # Botón desactivado con estilo visual claro
                        st.button(
                            "🔗 Consultar factura (No disponible offline)",
                            disabled=True,
                            help="Esta factura fue generada en modo offline. El enlace funcionará después del envío al SIN.",
                            key="consultar_offline_disabled"
                        )
                else:
                    # Botón normal para facturas online
                    st.link_button(
                        "🔗 Consultar factura", 
                        enlace,
                        help="Consultar la factura en el portal oficial del SIAT"
                    )
                    logger.info(f"Enlace de consulta de factura generado: {enlace}")
                    
            except Exception as e:
                st.error(f"Error al generar el enlace de consulta: {str(e)}")
                logger.exception("Error al generar el enlace de consulta")
        else:
            st.error("No se encontraron los datos de la factura para la consulta.")
            logger.error("Se intentó generar enlace de consulta pero no se encontró 'factura_a_procesar' en session_state.")
    else:
        st.info("El botón de consulta estará disponible cuando la factura haya sido procesada.")

def _handle_online_submission(invoice_config, client_data, tipos_documento, comandas_seleccionadas,
                           lineas_productos, subtotal, total, fecha_emision, fecha_emision_str,
                           fecha_emision_display, message_placeholder):
    """Maneja la lógica para generar y enviar una factura en modo online."""
    try:
        logger.info("Iniciando proceso de facturación ONLINE")
        
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
            nit=nit_emisor, 
            fecha_emision=fecha_emision, 
            codigoSucursal=codigo_sucursal, 
            codigoModalidad=int(os.getenv('CODIGO_MODALIDAD')),
            tipoEmision=int(os.getenv('CODIGO_TIPO_EMISION')), 
            tipoFactura=int(os.getenv('CODIGO_TIPO_FACTURA')),
            tipoDocumentoSector=codigo_documento_sector, 
            numeroFactura=numero_factura,
            puntoVenta=codigo_punto_venta
        )
        logger.info(f"CUF generado: {cuf}")
        
        # Manejo de excepciones NIT
        codigo_excepcion = 1 if tipo_documento_seleccionado and tipo_documento_seleccionado['codigoClasificador'] == '5' else None
        
        # Generar XML
        xml_str, factura_cabecera_data, detalles_data = generate_xml_invoice(
            nit_emisor=nit_emisor,
            razon_social_emisor=razon_social_emisor,
            municipio=municipio,
            telefono=telefono_emisor,
            numero_factura=numero_factura,
            cuf=cuf, 
            cufd=cufd, 
            codigo_sucursal=codigo_sucursal, 
            direccion=direccion, 
            codigo_punto_venta=codigo_punto_venta,
            fecha_emision=fecha_emision_str, 
            nombre_razon_social=client_data['nombre_cliente'], 
            codigo_tipo_documento_identidad=tipo_documento_seleccionado['codigoClasificador'],
            numero_documento=client_data['numero_documento'], 
            complemento=client_data['complemento'], 
            codigo_cliente=client_data['numero_documento'],
            codigo_metodo_pago=invoice_config['metodo_pago_seleccionado']['codigoClasificador'], 
            ultimos_digitos_tarjeta=invoice_config['ultimos_digitos_tarjeta'],
            subtotal=subtotal, 
            total=total, 
            codigo_moneda=1, 
            tipo_cambio=1, 
            monto_total_moneda=total / 1, 
            monto_giftcard=invoice_config['monto_giftcard'], 
            descuento_adicional=invoice_config['descuento_adicional'],
            usuario="don_bercho", 
            codigo_documento_sector=codigo_documento_sector, 
            lineas_productos=lineas_productos,
            actividad_economica=os.getenv('ACTIVIDAD_ECONOMICA'), 
            codigo_producto_sin=os.getenv('CODIGO_PRODUCTO_SIN'),
            codigoExcepcion=codigo_excepcion
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
                # Registrar la respuesta SIEMPRE, tanto en éxito como en error
                facturacion_logger.info(f"[SIAT] Respuesta recibida: {response_data}")
                if 'xml_content' in response_data:
                    xml_logger.info(f"[SIAT] XML enviado/recibido: {response_data['xml_content'][:500]}...")

                if success:
                    transaccion_exitosa = display_siat_response(response_data, message_placeholder)
                    if transaccion_exitosa:
                        try:
                            facturacion_logger.info("Ensamblando objeto FacturaProcesada.")

                            # 1. Preparar el detalle de la factura
                            detalles_factura_obj = [
                                DetalleFactura(
                                    codigo=p["codigo"],
                                    nombre=p["nombre"],
                                    unidad=p["unidad"],
                                    cantidad=float(p["cantidad"]),
                                    precio=float(p["precio"]),
                                    montoDescuento=float(p.get("montoDescuento", 0.0)),
                                    sub_total=float(p["sub_total"])
                                ) for p in lineas_productos
                            ]

                            # 2. Ensamblar el objeto principal con todos los datos
                            factura_para_procesar = FacturaProcesada(
                                # Datos de la transacción
                                cuf=cuf,
                                numero_factura=numero_factura,
                                fecha_emision=fecha_emision_display,
                                # Datos del emisor
                                nit_emisor=os.getenv('NIT'),
                                razon_social_emisor=os.getenv('RAZON_SOCIAL'),
                                nombre_sucursal=os.getenv('NOMBRE_SUCURSAL'),
                                punto_venta=int(os.getenv('CODIGO_PUNTO_VENTA', 0)),
                                direccion_emisor=os.getenv('DIRECCION'),
                                municipio_emisor=os.getenv('MUNICIPIO'),
                                telefono_emisor=os.getenv('TELEFONO'),
                                # Datos del cliente
                                nombre_cliente=client_data['nombre_cliente'],
                                numero_documento=client_data['numero_documento'],
                                complemento=client_data.get('complemento'),
                                cod_cliente=client_data['numero_documento'],
                                # Datos de la venta
                                lineas_productos=detalles_factura_obj,
                                # Datos de totales y pago
                                subtotal_factura=float(subtotal),
                                descuento_adicional=float(invoice_config['descuento_adicional']),
                                monto_giftcard=float(invoice_config['monto_giftcard']),
                                monto_total=float(total),
                                monto_total_pagar=float(total - invoice_config['monto_giftcard']),
                                monto_base_iva=float(Decimal(str(total)) * Decimal("0.87")), # Cálculo de ejemplo
                                total_en_palabras=numero_a_palabras_con_decimales_como_fraccion(total), # Asumiendo que esta función existe
                                metodo_pago=invoice_config['seleccion_metodo_pago'],
                                ultimos_digitos_tarjeta=invoice_config.get('ultimos_digitos_tarjeta'),
                                # Datos fiscales y leyendas
                                tipo_factura=os.getenv('DESCRIPCION_TIPO_FACTURA', 'FACTURA'),
                                subtitulo_factura=os.getenv('SUBTITULO', '(CON DERECHO A CREDITO FISCAL)'),
                                leyenda=factura_cabecera_data.get('leyenda', 'Ley Nro 453: ...'), # Obtener de los datos ya generados
                                # URL para QR - usando función centralizada
                                url_qr=generate_invoice_link(nit_emisor, cuf, numero_factura)
                            )

                            # 3. Guardar el objeto único en session_state
                            st.session_state['factura_a_procesar'] = factura_para_procesar
                            st.session_state['factura_validada'] = True # Mantenemos esta para la lógica del botón
                            st.session_state['factura_emitida_offline'] = False  # Factura emitida online

                            facturacion_logger.info(f"Objeto FacturaProcesada para factura {numero_factura} creado y guardado en session_state.")

                        except Exception as e:
                            facturacion_logger.error(f"Error al ensamblar FacturaProcesada: {e}", exc_info=True)
                            show_message('error', f"Error interno al preparar datos para impresión: {e}", message_placeholder)
                            return # Detener si hay un error aquí
                        
                        # Guardar en base de datos
                        factura_cabecera_data['tipoEmision'] = "1"
                        # Refactorización: almacenar codigoRecepcion y estado (codigoDescripcion) de la respuesta SIAT
                        factura_cabecera_data['codigoRecepcion'] = response_data.get('codigoRecepcion')
                        factura_cabecera_data['estado'] = response_data.get('codigoDescripcion', 'PENDIENTE')

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
                            st.session_state['last_submission_success'] = {
                                'comandas': list(invoice_config['selected_id_comanda']),
                                'message': f"Factura N° {numero_factura} procesada exitosamente."
                            }
                        logger.info(f"Factura {numero_factura} procesada exitosamente")
                    else:
                        facturacion_logger.error(f"Error al procesar respuesta: {response_data.get('error')}")
                else:
                    facturacion_logger.error(f"[SIAT] Error al procesar respuesta: {response_data.get('error')}")
            except Exception as e:
                show_message('error', f"❌Error al procesar la respuesta: {str(e)}", message_placeholder)
                facturacion_logger.exception("Error inesperado al procesar respuesta")
                
    except Exception as e:
        show_message('error', f"❌Error en el proceso de facturación: {str(e)}", message_placeholder)
        logger.exception("Error en facturación")

def _handle_offline_submission(invoice_config, client_data, evento_activo, tipos_documento,
                             lineas_productos, subtotal, total, fecha_emision,
                             fecha_emision_str, message_placeholder):
    """Maneja la lógica para generar y guardar una factura en modo offline."""
    try:
        logger.info("Iniciando proceso de facturación OFFLINE")

        # 1. OBTENER CUFD DEL EVENTO (corrección normativa)
        cufd_evento = evento_activo.get('cufd')
        if not cufd_evento:
            show_message('error', "No se encontró un CUFD válido para el evento de contingencia.", message_placeholder)
            return

        # 2. OBTENER NÚMERO DE FACTURA Y GENERAR CUF OFFLINE
        numero_factura = obtener_y_reservar_numero_factura()
        nit_emisor = int(os.getenv('NIT'))
        cuf = generate_cuf(
            nit=nit_emisor,
            fecha_emision=fecha_emision,
            codigoSucursal=int(os.getenv('CODIGO_SUCURSAL')),
            codigoModalidad=int(os.getenv('CODIGO_MODALIDAD')),
            tipoEmision=2,  # <-- TIPO DE EMISIÓN OFFLINE
            tipoFactura=int(os.getenv('CODIGO_TIPO_FACTURA')),
            tipoDocumentoSector=int(os.getenv('CODIGO_DOCUMENTO_SECTOR')),
            numeroFactura=numero_factura,
            puntoVenta=int(os.getenv('CODIGO_PUNTO_VENTA'))
        )

        # 3. MANEJAR EXCEPCIÓN DE NIT (verificación normativa)
        tipo_documento_seleccionado = next((doc for doc in tipos_documento if doc["descripcion"] == client_data['seleccion_tipo_documento']), None)
        codigo_excepcion = 1 if tipo_documento_seleccionado and tipo_documento_seleccionado['codigoClasificador'] == '5' else None

        # 4. GENERAR XML (verificar parámetros de contingencia)
        xml_str, factura_cabecera_data, detalles_data = generate_xml_invoice(
            nit_emisor=nit_emisor,
            razon_social_emisor=os.getenv('RAZON_SOCIAL'),
            municipio=os.getenv('MUNICIPIO'),
            telefono=os.getenv('TELEFONO'),
            numero_factura=numero_factura,
            cuf=cuf,
            cufd=cufd_evento,
            codigo_sucursal=int(os.getenv('CODIGO_SUCURSAL')),
            direccion=os.getenv('DIRECCION'),
            codigo_punto_venta=int(os.getenv('CODIGO_PUNTO_VENTA')),
            fecha_emision=fecha_emision_str,
            nombre_razon_social=client_data['nombre_cliente'],
            codigo_tipo_documento_identidad=tipo_documento_seleccionado['codigoClasificador'],
            numero_documento=client_data['numero_documento'],
            complemento=client_data['complemento'],
            codigo_cliente=client_data['numero_documento'],
            codigo_metodo_pago=invoice_config['metodo_pago_seleccionado']['codigoClasificador'],
            ultimos_digitos_tarjeta=invoice_config['ultimos_digitos_tarjeta'],
            subtotal=subtotal,
            total=total,
            codigo_moneda=1,
            tipo_cambio=1,
            monto_total_moneda=total / 1,
            monto_giftcard=invoice_config['monto_giftcard'],
            descuento_adicional=invoice_config['descuento_adicional'],
            usuario="don_bercho",
            codigo_documento_sector=int(os.getenv('CODIGO_DOCUMENTO_SECTOR')),
            lineas_productos=lineas_productos,
            actividad_economica=os.getenv('ACTIVIDAD_ECONOMICA'),
            codigo_producto_sin=os.getenv('CODIGO_PRODUCTO_SIN'),
            codigoExcepcion=codigo_excepcion
        )

        # 5. FIRMAR Y VALIDAR LOCALMENTE
        signed_xml_str = sign_xml(xml_str, "xmls/llaves/private_key_ok.pem", "xmls/llaves/certificado_ok.pem", cuf)

        # --- INICIO DEL CÓDIGO DE REEMPLAZO ---

        evento_id = evento_activo.get('id')
        if not evento_id:
            show_message('error', "Error crítico: El evento de contingencia no tiene un ID. No se puede guardar la factura.", message_placeholder)
            logger.error(f"El evento activo {evento_activo} no tiene una clave 'id'.")
            return

        # Creamos un nombre de archivo descriptivo y fácil de procesar
        filename = f"offline_invoices/factura_offline_ev{evento_id}_n{numero_factura}.xml"

        # --- FIN DEL CÓDIGO DE REEMPLAZO ---

        os.makedirs("offline_invoices", exist_ok=True)
        with open(filename, "w", encoding='utf-8') as f:
            f.write(signed_xml_str)

        if not validar_xml(filename, 'xmls/schemas/facturaElectronicaCompraVenta.xsd'):
            show_message('error', "El XML generado localmente no es válido. Revise los logs.", message_placeholder)
            return

        # 6. CREAR OBJETO FacturaProcesada
        try:
            facturacion_logger.info("Ensamblando objeto FacturaProcesada para modo OFFLINE.")
            fecha_emision_display = fecha_emision.strftime("%d/%m/%Y %H:%M:%S")

            # 6.1 Preparar el detalle de la factura
            detalles_factura_obj = [
                DetalleFactura(
                    codigo=p["codigo"],
                    nombre=p["nombre"],
                    unidad=p["unidad"],
                    cantidad=float(p["cantidad"]),
                    precio=float(p["precio"]),
                    montoDescuento=float(p.get("montoDescuento", 0.0)),
                    sub_total=float(p["sub_total"])
                ) for p in lineas_productos
            ]

            # 6.2 Ensamblar el objeto principal con todos los datos
            factura_para_procesar = FacturaProcesada(
                # Datos de la transacción
                cuf=cuf,
                numero_factura=numero_factura,
                fecha_emision=fecha_emision_display,
                # Datos del emisor
                nit_emisor=os.getenv('NIT'),
                razon_social_emisor=os.getenv('RAZON_SOCIAL'),
                nombre_sucursal=os.getenv('NOMBRE_SUCURSAL'),
                punto_venta=int(os.getenv('CODIGO_PUNTO_VENTA', 0)),
                direccion_emisor=os.getenv('DIRECCION'),
                municipio_emisor=os.getenv('MUNICIPIO'),
                telefono_emisor=os.getenv('TELEFONO'),
                # Datos del cliente
                nombre_cliente=client_data['nombre_cliente'],
                numero_documento=client_data['numero_documento'],
                complemento=client_data.get('complemento'),
                cod_cliente=client_data['numero_documento'],
                # Datos de la venta
                lineas_productos=detalles_factura_obj,
                # Datos de totales y pago
                subtotal_factura=float(subtotal),
                descuento_adicional=float(invoice_config['descuento_adicional']),
                monto_giftcard=float(invoice_config['monto_giftcard']),
                monto_total=float(total),
                monto_total_pagar=float(total - invoice_config['monto_giftcard']),
                monto_base_iva=float(Decimal(str(total)) * Decimal("0.87")), # Cálculo de ejemplo
                total_en_palabras=numero_a_palabras_con_decimales_como_fraccion(total),
                metodo_pago=invoice_config['seleccion_metodo_pago'],
                ultimos_digitos_tarjeta=invoice_config.get('ultimos_digitos_tarjeta'),
                # Datos fiscales y leyendas
                tipo_factura=os.getenv('DESCRIPCION_TIPO_FACTURA', 'FACTURA OFFLINE'),
                subtitulo_factura=os.getenv('SUBTITULO', '(CON DERECHO A CREDITO FISCAL)'),
                leyenda=factura_cabecera_data.get('leyenda', 'Ley Nro 453: ...'),
                # URL para QR - usando función centralizada
                url_qr=generate_invoice_link(nit_emisor, cuf, numero_factura)
            )

            # 6.3 Guardar el objeto único en session_state
            st.session_state['factura_a_procesar'] = factura_para_procesar
            st.session_state['factura_validada'] = True # Para que se muestre el botón de consulta/impresión
            st.session_state['factura_emitida_offline'] = True  # Factura emitida en modo offline

            facturacion_logger.info(f"Objeto FacturaProcesada para factura offline {numero_factura} creado y guardado en session_state.")

        except Exception as e:
            facturacion_logger.error(f"Error al ensamblar FacturaProcesada en modo offline: {e}", exc_info=True)
            show_message('error', f"Error interno al preparar datos para impresión/consulta: {e}", message_placeholder)
            return # Detener si hay un error aquí

        # 7. GUARDAR EN BASE DE DATOS (confirmar estado y tipo de emisión)
        factura_cabecera_data['tipoEmision'] = "2" # <-- TIPO DE EMISIÓN OFFLINE
        factura_cabecera_data['estado'] = "PENDIENTE_ENVIO"
        factura_cabecera_data['codigoEvento'] = evento_activo.get('id')

        guardar_factura_cabecera(factura_cabecera_data)
        for detalle in detalles_data:
            guardar_factura_detalle(detalle)

        st.session_state['last_submission_success'] = {
            'comandas': list(invoice_config['selected_id_comanda']),
            'message': f"Factura N° {numero_factura} generada y guardada localmente. Pendiente de envío."
        }
        show_message('success', f"✅ Factura N° {numero_factura} generada y guardada localmente. Pendiente de envío.", message_placeholder)

        # Conservamos el session_state para que los botones de imprimir/consultar estén disponibles
        # Ya no hacemos st.rerun() ni limpiamos 'factura_validada'

    except Exception as e:
        show_message('error', f"❌ Error en el proceso de facturación offline: {str(e)}", message_placeholder)
        logger.exception("Error en facturación offline")
