# -*- coding: utf-8 -*-
"""
Módulo para la pestaña principal de facturación.
"""
import os
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
NON_OPERATIONAL_EVENT_CODES = {"5", "6", "7"}

from invoice_templates import generate_html_invoice, generate_html_invoice_legacy, generate_compact_html_invoice, numero_a_palabras_con_decimales_como_fraccion
from validators import validar_factura_cabecera, validar_factura_detalle
from xml_signer import sign_xml
from generate_cuf import generate_cuf
from cufd import solicitar_cufd
from zeeper import validar_xml, comprimir_xml, obtener_hash, enviar_solicitud
from response_handler import parse_siat_response, display_siat_response
from data_access import guardar_factura_cabecera, guardar_factura_detalle
from invoice_manager import obtener_y_reservar_numero_factura, revertir_incremento_numero_factura
from print_manager import initialize_print_state, solicitar_impresion, get_print_state_summary

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
            raise ValueError("❌ CUFD no encontrado en la base de datos.")
    except Exception as e:
        raise ValueError(f"❌ Error al obtener el CUFD: {e}")
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
        show_message('error', f"❌ Error al verificar o solicitar CUFD: {e}", message_placeholder)
        logger.error(f"Error al verificar o solicitar CUFD: {e}")
        raise ValueError(f"Error al verificar o solicitar CUFD: {e}")
    finally:
        session.close()

def render(is_online: bool, evento_activo: dict = None):
    """
    Renderiza la pestaña principal de facturación con soporte para modo online y contingencia.

    NOTA ARQUITECTÓNICA - OPTIMIZACIÓN DE VERIFICACIONES:
    --------------------------------------------------------
    Esta función NO realiza verificaciones de comunicación propias para evitar
    llamadas redundantes al SIN. Confía en los parámetros 'is_online' y 
    'evento_activo' provistos centralmente por main.py.
    
    FLUJO DE VERIFICACIÓN OPTIMIZADO:
    1. main.py usa communication_manager con caché de 30 segundos
    2. El estado se propaga a todas las pestañas vía parámetros
    3. Evita 93% de verificaciones redundantes (30/min → 2/min)
    4. Respuesta instantánea: 800ms → <50ms desde caché
    
    MANEJO DE MODOS DE OPERACIÓN:
    - **Modo Online:** Facturación normal con validación inmediata del SIN
    - **Modo Contingencia:** Generación offline con envío diferido en paquetes
    - El usuario puede forzar reconexión con el botón "Reconectar" de la barra lateral
    
    GESTIÓN DE CONTINGENCIA:
    - Si is_online=False, se verifica que evento_activo exista
    - Las facturas offline usan el CUFD del evento activo
    - Se marcan con tipoEmision=2 y estado="PENDIENTE_ENVIO"

    Args:
        is_online (bool): Estado de conectividad determinado centralmente
        evento_activo (dict): Información del evento de contingencia activo (si existe).
                              Incluye: id, descripcion, cufd, fecha_inicio
    
    Returns:
        None: Renderiza la interfaz directamente en Streamlit
    """
    log_enabled = st.session_state.get("main_active_tab_name") == "Facturar"

    if log_enabled:
        logger.info(f"Renderizando pestaña de facturación en modo {'ONLINE' if is_online else 'OFFLINE'}")

    if not is_online:
        if evento_activo:
            st.warning(
                f"""
                ⚠️ **MODO DE CONTINGENCIA ACTIVADO** ⚠️
                **Evento:** {evento_activo.get('descripcion', 'N/A')} (ID: {evento_activo.get('id')})
                **CUFD del Evento:** `{evento_activo.get('cufd')}`
                *Las facturas se generarán y guardarán localmente para su envío posterior.*
                """,
                icon="📡"
            )
        else:
            # Este caso no debería ocurrir si main.py funciona bien, pero es una buena salvaguarda
            st.error("Error crítico: Modo offline pero no se encontró un evento de contingencia activo.")
            return  # Detener la renderización de la pestaña si no hay evento
    
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
    client_data = render_sidebar_client_data(tipos_documento, message_placeholder, is_online)
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
    # Intentamos leer el próximo número disponible sin reservarlo (solo lectura)
    numero_factura_preview = 1
    if os.path.exists("invoice_number.txt"):
        try:
            with open("invoice_number.txt", "r") as f:
                content = f.read().strip()
                if content:
                    numero_factura_preview = int(content)
        except Exception:
            # Si hay error leyendo, asumimos 1 o mostramos un placeholder
            pass
    
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

        # Limpiar cualquier éxito pendiente de ejecuciones previas
        st.session_state.pop('last_submission_success', None)

        if (invoice_config['metodo_pago_seleccionado'] and
            client_data['seleccion_tipo_documento'] and
            client_data['numero_documento'] and
            invoice_config['selected_id_comanda']):

            if is_online:
                _handle_online_submission(
                    invoice_config, client_data, tipos_documento, comandas_seleccionadas,
                    lineas_productos, subtotal, total, fecha_emision, fecha_emision_str,
                    fecha_emision_display, message_placeholder,
                    evento_activo=evento_activo
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
                st.session_state['flash_message'] = (
                    'success',
                    payload.get('message', 'Factura procesada exitosamente.')
                )
                success = True
        else:
            # Mostrar mensaje de error cuando faltan campos requeridos
            show_message('error', "❌ Por favor, complete todos los campos requeridos.", message_placeholder)
            logger.warning("Intento de facturación con campos incompletos")

    if success:
        st.rerun()


def _render_print_button():
    """Renderiza la impresión automática después de validar."""
    initialize_print_state()

    summary = get_print_state_summary()
    display = summary.get('display') or {}
    status_info = summary.get('status_info') or {}
    code = (summary.get('code') or '').lower()
    severity = (display.get('severity') or summary.get('severity') or 'info').lower()
    primary_message = display.get('primary') or summary.get('message', 'Sistema de impresión listo.')
    ultimo_trabajo = summary.get('ultimo_trabajo') or {}
    impresion_en_progreso = summary.get('impresion_en_progreso', False)

    st.session_state.setdefault('auto_print_last_id', None)

    details = display.get('details') or []
    if not isinstance(details, list):
        details = list(details)

    severity_map = {
        'error': st.error,
        'warning': st.warning,
        'success': st.success,
    }
    severity_map.get(severity, st.info)(primary_message)

    for line in details:
        st.caption(line)

    factura_validada = st.session_state.get('factura_validada')
    factura_obj = st.session_state.get('factura_a_procesar')

    numero_factura = ultimo_trabajo.get('numero_factura') or status_info.get('numero_factura')
    active_codes = {'processing', 'queued'}
    terminal_codes = {
        'printer_success',
        'printer_warning',
        'printer_error',
        'pdf_error',
        'data_error',
        'critical_error',
    }

    if factura_validada:
        if factura_obj:
            identifier = getattr(factura_obj, 'cuf', None) or f"numero:{getattr(factura_obj, 'numero_factura', 'N/D')}"
            last_identifier = st.session_state.get('auto_print_last_id')
            if identifier and identifier != last_identifier and code not in active_codes and not impresion_en_progreso:
                st.session_state['auto_print_last_id'] = identifier
                _trigger_print_job(factura_obj, source='auto', rerun=False)
                st.rerun()
            else:
                if impresion_en_progreso or code in active_codes:
                    st.caption('La factura validada se está enviando a la impresora en segundo plano.')
                elif code in terminal_codes:
                    st.session_state['impresion_en_progreso'] = False
                    if code == 'printer_success':
                        st.session_state['impresion_finalizada'] = True
                else:
                    st.caption('La factura validada se enviará automáticamente en cuanto el sistema quede libre.')
        else:
            st.error('No se encontraron los datos de la factura para imprimir automáticamente.')
    else:
        st.caption('La impresión automática se activará cuando la factura sea validada por el SIN.')



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
                            "📌 Consultar factura (No disponible offline)",
                            disabled=True,
                            help="Esta factura fue generada en modo offline. El enlace funcionará después del envío al SIN.",
                            key="consultar_offline_disabled"
                        )
                else:
                    # Botón normal para facturas online
                    st.link_button(
                        "📌 Consultar factura",
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
                           fecha_emision_display, message_placeholder, evento_activo=None):
    """Maneja la lógica para generar y enviar una factura en modo online."""
    try:
        logger.info("Iniciando proceso de facturación ONLINE")

        tipo_documento_seleccionado = next(
            (doc for doc in tipos_documento
             if doc["descripcion"] == client_data['seleccion_tipo_documento']),
            None
        )

        nit_emisor = int(os.getenv('NIT'))
        razon_social_emisor = os.getenv('RAZON_SOCIAL')
        municipio = os.getenv('MUNICIPIO')
        telefono_emisor = os.getenv('TELEFONO')
        codigo_sucursal = int(os.getenv('CODIGO_SUCURSAL'))
        codigo_punto_venta = int(os.getenv('CODIGO_PUNTO_VENTA'))
        codigo_documento_sector = int(os.getenv('CODIGO_DOCUMENTO_SECTOR'))
        direccion = os.getenv('DIRECCION')

        # Validaciones previas para evitar quemar números innecesariamente
        if total <= 0:
             show_message('error', "El monto total debe ser mayor a 0.", message_placeholder)
             return False

        cufd = verificar_y_obtener_cufd(message_placeholder)
        numero_factura = obtener_y_reservar_numero_factura()
        logger.info(f"Número de factura reservado: {numero_factura}")

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

        # CORRECCIÓN ONLINE: Por defecto 0. Solo 1 si el usuario marcó excepción explícitamente.
        if client_data.get('usar_excepcion', False):
            codigo_excepcion = 1
        else:
            codigo_excepcion = 0

        cafc_para_factura = None

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
            monto_total_moneda=total,
            monto_giftcard=invoice_config['monto_giftcard'],
            descuento_adicional=invoice_config['descuento_adicional'],
            usuario="don_bercho",
            codigo_documento_sector=codigo_documento_sector,
            lineas_productos=lineas_productos,
            actividad_economica=os.getenv('ACTIVIDAD_ECONOMICA'),
            codigo_producto_sin=os.getenv('CODIGO_PRODUCTO_SIN'),
            codigoExcepcion=codigo_excepcion,
            cafc=cafc_para_factura
        )

        signed_xml_str = sign_xml(xml_str, "xmls/llaves/private_key_ok.pem", "xmls/llaves/certificado_ok.pem", cuf)
        filename = f"xmls/factura_{numero_factura}_{cuf}_.xml"
        with open(filename, "w", encoding='utf-8') as signed_xml_file:
            signed_xml_file.write(signed_xml_str)

        xsd_main_path = 'xmls/schemas/facturaElectronicaCompraVenta.xsd'
        if not validar_xml(filename, xsd_main_path):
            raise ValueError("El XML generado no es válido contra el XSD.")

        gzip_path = comprimir_xml(filename)
        obtener_hash(gzip_path)
        response = enviar_solicitud(filename, xsd_main_path, fecha_emision_str, cufd)

        if isinstance(response, dict) and response.get("error"):
            show_message('error', f"❌ Error al enviar la factura: {response['error']}", message_placeholder)
            logger.error(f"Error al enviar factura: {response['error']}")
            return False

        try:
            success, response_data = parse_siat_response(response.content)
            facturacion_logger.info(f"[SIAT] Respuesta recibida: {response_data}")
            if 'xml_content' in response_data:
                xml_logger.info(f"[SIAT] XML enviado/recibido: {response_data['xml_content'][:500]}...")

            if success:
                transaccion_exitosa = display_siat_response(response_data, message_placeholder)
                if transaccion_exitosa:
                    try:
                        facturacion_logger.info("Ensamblando objeto FacturaProcesada.")
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

                        factura_para_procesar = FacturaProcesada(
                            cuf=cuf,
                            numero_factura=numero_factura,
                            fecha_emision=fecha_emision_display,
                            nit_emisor=os.getenv('NIT'),
                            razon_social_emisor=os.getenv('RAZON_SOCIAL'),
                            nombre_sucursal=os.getenv('NOMBRE_SUCURSAL'),
                            punto_venta=int(os.getenv('CODIGO_PUNTO_VENTA', 0)),
                            direccion_emisor=os.getenv('DIRECCION'),
                            municipio_emisor=os.getenv('MUNICIPIO'),
                            telefono_emisor=os.getenv('TELEFONO'),
                            nombre_cliente=client_data['nombre_cliente'],
                            numero_documento=client_data['numero_documento'],
                            complemento=client_data.get('complemento'),
                            cod_cliente=client_data['numero_documento'],
                            lineas_productos=detalles_factura_obj,
                            subtotal_factura=float(subtotal),
                            descuento_adicional=float(invoice_config['descuento_adicional']),
                            monto_giftcard=float(invoice_config['monto_giftcard']),
                            monto_total=float(total),
                            monto_total_pagar=float(total - invoice_config['monto_giftcard']),
                            monto_base_iva=float(Decimal(str(total)) * Decimal("0.87")),
                            total_en_palabras=numero_a_palabras_con_decimales_como_fraccion(total),
                            metodo_pago=invoice_config['seleccion_metodo_pago'],
                            ultimos_digitos_tarjeta=invoice_config.get('ultimos_digitos_tarjeta'),
                            tipo_factura=os.getenv('DESCRIPCION_TIPO_FACTURA', 'FACTURA'),
                            subtitulo_factura=os.getenv('SUBTITULO', '(CON DERECHO A CREDITO FISCAL)'),
                            leyenda=factura_cabecera_data.get('leyenda', 'Ley Nro 453: ...'),
                            url_qr=generate_invoice_link(nit_emisor, cuf, numero_factura)
                        )

                        st.session_state['factura_a_procesar'] = factura_para_procesar
                        st.session_state['factura_validada'] = True
                        st.session_state['factura_emitida_offline'] = False
                    except Exception as e:
                        facturacion_logger.error(f"Error al ensamblar FacturaProcesada: {e}", exc_info=True)
                        show_message('error', f"Error interno al preparar datos para impresión: {e}", message_placeholder)
                        return False

                    factura_cabecera_data['tipoEmision'] = "1"
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
                                return False
                        st.session_state['last_submission_success'] = {
                            'comandas': list(invoice_config['selected_id_comanda']),
                            'message': f"Factura N° {numero_factura} procesada exitosamente."
                        }
                        logger.info(f"Factura {numero_factura} procesada exitosamente")
                        return True
                    else:
                        show_message('error', error_message, message_placeholder)
                        logger.error(f"Error al validar cabecera: {error_message}")
                        return False
                
                # NUEVO: Manejo de facturas RECHAZADAS por el SIN (Código 902)
                elif str(response_data.get('codigoEstado')) == '902':
                    facturacion_logger.warning(f"Factura {numero_factura} RECHAZADA por el SIN. Guardando registro.")
                    
                    # Extraer mensajes de error detallados
                    mensajes_error = []
                    mensajes_list = response_data.get('mensajesList', [])
                    
                    # Normalizar a lista si es un solo objeto
                    if isinstance(mensajes_list, dict):
                        mensajes_list = [mensajes_list]
                    elif not isinstance(mensajes_list, list):
                        mensajes_list = []
                        
                    for msg in mensajes_list:
                        desc = msg.get('descripcion', '')
                        if desc:
                            mensajes_error.append(desc)
                    
                    mensaje_completo = " | ".join(mensajes_error) if mensajes_error else "Rechazada por el SIN sin detalle."
                    
                    # Actualizar datos para guardar como rechazada
                    factura_cabecera_data['tipoEmision'] = "1"
                    factura_cabecera_data['estado'] = "RECHAZADA"
                    factura_cabecera_data['resultadoValidacion'] = "RECHAZADA"
                    factura_cabecera_data['mensajeError'] = mensaje_completo
                    
                    # Guardar en BD para trazabilidad (el número se consume)
                    guardar_factura_cabecera(factura_cabecera_data)
                    for detalle in detalles_data:
                        guardar_factura_detalle(detalle)
                        
                    show_message('error', f"❌ Factura RECHAZADA por el SIN: {mensaje_completo}. El número de factura ha sido consumido.", message_placeholder)
                    return False
            else:
                facturacion_logger.error(f"[SIAT] Error al procesar respuesta: {response_data.get('error')}")
        except Exception as e:
            show_message('error', f"❌ Error al procesar la respuesta: {str(e)}", message_placeholder)
            facturacion_logger.exception("Error inesperado al procesar respuesta")
            return False

    except Exception as e:
        logger.exception("Error en facturación")
        
        msg_adicional = ""
        if 'numero_factura' in locals():
            # Intentar revertir el número de factura
            if revertir_incremento_numero_factura(numero_factura):
                msg_adicional = " El número de factura ha sido recuperado."
            else:
                msg_adicional = " El número de factura no se pudo recuperar."
            
            # Intentar borrar el archivo si se creó
            if 'filename' in locals() and os.path.exists(filename):
                try:
                    os.remove(filename)
                    logger.info(f"Archivo XML eliminado: {filename}")
                except Exception as del_e:
                    logger.error(f"No se pudo eliminar archivo XML: {del_e}")

        show_message('error', f"❌ Error en el proceso de facturación: {str(e)}.{msg_adicional}", message_placeholder)
        return False

    return False



def _handle_offline_submission(invoice_config, client_data, evento_activo, tipos_documento,
                             lineas_productos, subtotal, total, fecha_emision,
                             fecha_emision_str, message_placeholder):
    """Maneja la lógica para generar y guardar una factura en modo offline."""
    try:
        logger.info("Iniciando proceso de facturación OFFLINE")

        cufd_evento = evento_activo.get('cufd')
        if not cufd_evento:
            show_message('error', "No se encontró un CUFD válido para el evento de contingencia.", message_placeholder)
            return False

        # Validaciones previas para evitar quemar números innecesariamente
        if total <= 0:
             show_message('error', "El monto total debe ser mayor a 0.", message_placeholder)
             return False

        numero_factura = obtener_y_reservar_numero_factura()
        nit_emisor = int(os.getenv('NIT'))

        cafc_para_factura = None
        if evento_activo and str(evento_activo.get('codigo_evento')) in NON_OPERATIONAL_EVENT_CODES:
            cafc_para_factura = (st.session_state.get('evento_cafc', {}).get(evento_activo.get('id')) or "").strip()
            if not cafc_para_factura:
                show_message('error', "Debe ingresar el CAFC vigente en la barra lateral antes de transcribir facturas manuales para este evento.", message_placeholder)
                return False

        cuf = generate_cuf(
            nit=nit_emisor,
            fecha_emision=fecha_emision,
            codigoSucursal=int(os.getenv('CODIGO_SUCURSAL')),
            codigoModalidad=int(os.getenv('CODIGO_MODALIDAD')),
            tipoEmision=2,
            tipoFactura=int(os.getenv('CODIGO_TIPO_FACTURA')),
            tipoDocumentoSector=int(os.getenv('CODIGO_DOCUMENTO_SECTOR')),
            numeroFactura=numero_factura,
            puntoVenta=int(os.getenv('CODIGO_PUNTO_VENTA'))
        )

        tipo_documento_seleccionado = next(
            (doc for doc in tipos_documento if doc["descripcion"] == client_data['seleccion_tipo_documento']),
            None
        )
        codigo_excepcion = 1 if tipo_documento_seleccionado and tipo_documento_seleccionado['codigoClasificador'] == '5' else 0

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
            monto_total_moneda=total,
            monto_giftcard=invoice_config['monto_giftcard'],
            descuento_adicional=invoice_config['descuento_adicional'],
            usuario="don_bercho",
            codigo_documento_sector=int(os.getenv('CODIGO_DOCUMENTO_SECTOR')),
            lineas_productos=lineas_productos,
            actividad_economica=os.getenv('ACTIVIDAD_ECONOMICA'),
            codigo_producto_sin=os.getenv('CODIGO_PRODUCTO_SIN'),
            codigoExcepcion=codigo_excepcion,
            cafc=cafc_para_factura
        )

        signed_xml_str = sign_xml(xml_str, "xmls/llaves/private_key_ok.pem", "xmls/llaves/certificado_ok.pem", cuf)
        filename = f"offline_invoices/factura_offline_ev{evento_activo.get('id')}_n{numero_factura}.xml"
        os.makedirs("offline_invoices", exist_ok=True)
        with open(filename, "w", encoding='utf-8') as f:
            f.write(signed_xml_str)

        if not validar_xml(filename, 'xmls/schemas/facturaElectronicaCompraVenta.xsd'):
            raise ValueError("El XML generado localmente no es válido. Revise los logs.")

        try:
            facturacion_logger.info("Ensamblando objeto FacturaProcesada para modo OFFLINE.")
            fecha_emision_display = fecha_emision.strftime("%d/%m/%Y %H:%M:%S")

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

            factura_para_procesar = FacturaProcesada(
                cuf=cuf,
                numero_factura=numero_factura,
                fecha_emision=fecha_emision_display,
                nit_emisor=os.getenv('NIT'),
                razon_social_emisor=os.getenv('RAZON_SOCIAL'),
                nombre_sucursal=os.getenv('NOMBRE_SUCURSAL'),
                punto_venta=int(os.getenv('CODIGO_PUNTO_VENTA', 0)),
                direccion_emisor=os.getenv('DIRECCION'),
                municipio_emisor=os.getenv('MUNICIPIO'),
                telefono_emisor=os.getenv('TELEFONO'),
                nombre_cliente=client_data['nombre_cliente'],
                numero_documento=client_data['numero_documento'],
                complemento=client_data.get('complemento'),
                cod_cliente=client_data['numero_documento'],
                lineas_productos=detalles_factura_obj,
                subtotal_factura=float(subtotal),
                descuento_adicional=float(invoice_config['descuento_adicional']),
                monto_giftcard=float(invoice_config['monto_giftcard']),
                monto_total=float(total),
                monto_total_pagar=float(total - invoice_config['monto_giftcard']),
                monto_base_iva=float(Decimal(str(total)) * Decimal("0.87")),
                total_en_palabras=numero_a_palabras_con_decimales_como_fraccion(total),
                metodo_pago=invoice_config['seleccion_metodo_pago'],
                ultimos_digitos_tarjeta=invoice_config.get('ultimos_digitos_tarjeta'),
                tipo_factura=os.getenv('DESCRIPCION_TIPO_FACTURA', 'FACTURA OFFLINE'),
                subtitulo_factura=os.getenv('SUBTITULO', '(CON DERECHO A CREDITO FISCAL)'),
                leyenda=factura_cabecera_data.get('leyenda', 'Ley Nro 453: ...'),
                url_qr=generate_invoice_link(nit_emisor, cuf, numero_factura)
            )

            st.session_state['factura_a_procesar'] = factura_para_procesar
            st.session_state['factura_validada'] = True
            st.session_state['factura_emitida_offline'] = True

            facturacion_logger.info(f"Objeto FacturaProcesada para factura offline {numero_factura} creado y guardado en session_state.")
        except Exception as e:
            facturacion_logger.error(f"Error al ensamblar FacturaProcesada en modo offline: {e}", exc_info=True)
            show_message('error', f"Error interno al preparar datos para impresión/consulta: {e}", message_placeholder)
            return False

        factura_cabecera_data['tipoEmision'] = "2"
        factura_cabecera_data['estado'] = "PENDIENTE_ENVIO"
        factura_cabecera_data['codigoEvento'] = evento_activo.get('id')
        factura_cabecera_data['cafc'] = cafc_para_factura

        guardar_factura_cabecera(factura_cabecera_data)
        for detalle in detalles_data:
            guardar_factura_detalle(detalle)

        st.session_state['last_submission_success'] = {
            'comandas': list(invoice_config['selected_id_comanda']),
            'message': f"Factura N° {numero_factura} generada y guardada localmente. Pendiente de envío."
        }
        show_message('success', f"✅ Factura N° {numero_factura} generada y guardada localmente. Pendiente de envío.", message_placeholder)
        return True

    except Exception as e:
        logger.exception("Error en facturación offline")
        
        msg_adicional = ""
        if 'numero_factura' in locals():
            # Intentar revertir el número de factura
            if revertir_incremento_numero_factura(numero_factura):
                msg_adicional = " El número de factura ha sido recuperado."
            else:
                msg_adicional = " El número de factura no se pudo recuperar."
            
            # Intentar borrar el archivo si se creó
            if 'filename' in locals() and os.path.exists(filename):
                try:
                    os.remove(filename)
                    logger.info(f"Archivo XML eliminado: {filename}")
                except Exception as del_e:
                    logger.error(f"No se pudo eliminar archivo XML: {del_e}")

        show_message('error', f"❌ Error en el proceso de facturación offline: {str(e)}.{msg_adicional}", message_placeholder)
        return False

    return False

def _trigger_print_job(factura_obj, source: str, rerun: bool = True):
    """Envía la factura a impresión y controla errores."""
    if not factura_obj:
        st.error("No se encontraron los datos de la factura para imprimir.")
        return False

    try:
        logger.info("Solicitando impresión (%s) para factura %s.", source, getattr(factura_obj, 'numero_factura', 'N/D'))
        solicitar_impresion(factura_obj)
        if rerun:
            st.rerun()
        return True
    except Exception as exc:
        st.error(f"Error al solicitar la impresión: {exc}")
        logger.exception("Error al solicitar impresión (%s)", source)
        return False

