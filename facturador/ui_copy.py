import os
import sys
import time
import re
import logging
import traceback
import base64
import queue
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal

# Agregar la ruta del directorio padre al path de Python
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Streamlit y componentes
import streamlit as st
import streamlit.components.v1 as components

# Base de datos y modelos
from database import SessionLocal
from facturador.models import Cufd, Cliente
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Librerías externas
from dotenv import load_dotenv
from zeep import Client
from zeep.transports import Transport
from requests import Session
from lxml import etree
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
from num2words import num2words

# Módulos de acceso a datos
from data_access import (
    fetch_comandas, fetch_metodos_pago, fetch_tipos_documento, fetch_cliente,
    fetch_random_leyenda, obtener_nombre_unidad_medida, obtener_motivos_anulacion,
    obtener_cuf_por_numero_factura, obtener_factura_completa, 
    guardar_factura_cabecera, guardar_factura_detalle, obtener_facturas_por_estado,
    fetch_all_clientes, contar_total_clientes
)

# Módulos de lógica de negocio
from business_logic import calculate_totals, collect_product_lines, generate_invoice_link, generate_qr
from invoice_xml_generator import generate_xml_invoice
from invoice_templates import generate_html_invoice, generate_compact_html_invoice

# Módulos modularizados
from validators import es_email_valido, es_telefono_valido, validar_factura_cabecera, validar_factura_detalle
from client_manager import save_or_fetch_client_data, verificar_nit_cliente
from invoice_manager import guardar_factura_en_bd, obtener_y_reservar_numero_factura, mostrar_lista_facturas
from print_manager import initialize_print_state, reiniciar_estados, imprimir_en_hilo, mostrar_mensaje_impresion_en_curso
from xml_signer import sign_xml

# Módulos de servicios SIN
from generate_cuf import generate_cuf
from cufd import solicitar_cufd
import cuis
from zeeper import validar_xml, comprimir_xml, obtener_hash, enviar_solicitud
import verifica_stream
from estado_factura import verificar_estado_factura
from anulacion import anular_factura
from reversion import enviar_solicitud_reversion, procesar_respuesta_reversion
from facturador.response_handler import parse_siat_response, display_siat_response

# Configuración de loggers
from logger_config import get_logger, get_printer_logger, get_facturacion_logger, get_xml_logger

# Configurar loggers
logger = get_logger()
printer_logger = get_printer_logger()
facturacion_logger = get_facturacion_logger()
xml_logger = get_xml_logger()
ui_logger = get_logger()  # Logger para la interfaz de usuario

# Funciones utilitarias para la UI
def init_session_state(key, default_value):
    """
    Inicializa una clave en el session_state si no existe.
    
    Args:
        key (str): Clave del session_state
        default_value: Valor por defecto
    """
    if key not in st.session_state:
        st.session_state[key] = default_value

def reset_session_keys(keys):
    """
    Reinicia múltiples claves del session_state.
    
    Args:
        keys (list): Lista de claves a reiniciar
    """
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]

# Lista de códigos permitidos para gift cards
gift_card_codes = [
    102, 109, 115, 120, 124, 128, 129, 130, 138, 146, 153, 159, 164, 168,
    172, 173, 174, 182, 189, 195, 200, 204, 208, 209, 210, 217, 221, 222,
    223, 224, 225, 226, 228, 232, 241, 246, 250, 254, 255, 256, 261, 265,
    269, 270, 271, 275, 279, 280, 281, 285, 286, 287, 291, 292, 293, 30,
    304, 35, 40, 49, 53, 60, 64, 68, 72, 76, 77, 78, 86, 94, 27
]

# Agregar al inicio del script o en la configuración inicial
if not os.path.exists('pdfs'):
    os.makedirs('pdfs')
    
# Agregar al inicio del script
try:
    if not os.access('pdfs', os.W_OK):
        logger.error("No hay permisos de escritura en la carpeta pdfs")
        raise PermissionError("No hay permisos de escritura en la carpeta pdfs")
except Exception as e:
    logger.error(f"Error al verificar permisos: {str(e)}")

# Estas funciones ahora están en validators.py

load_dotenv()

from contingency_manager import check_connectivity

# Verificar conectividad antes de inicializar el cliente SOAP
is_connected, server_accessible = check_connectivity()

if is_connected and server_accessible:
    session = Session()
    session.headers.update({'apikey': os.getenv('API_KEY', '')})

    wsdl_url = os.getenv('WSDL_URL_CODIGOS')
    client = Client(wsdl_url, transport=Transport(session=session))
else:
    client = None  # No inicializar el cliente SOAP en modo offline

# Asegurarse de que las funciones dependientes del cliente SOAP manejen el caso de client=None
# Esta función ahora está en validators.py

# Estas funciones ahora están en validators.py

def numero_a_palabras_con_decimales_como_fraccion(numero, lang='es'):
    if not numero:
        return ""
    
    parte_entera = int(numero)
    parte_decimal = int(round((numero - parte_entera) * 100))
    parte_entera_palabras = num2words(parte_entera, lang=lang).capitalize()
    
    if parte_decimal > 0:
        return f" {parte_entera_palabras} {parte_decimal:02d}/100 bolivianos."
    else:
        return f" {parte_entera_palabras} 00/100 bolivianos."


def get_next_invoice_number():
    """
    [OBSOLETA] Usar obtener_y_reservar_numero_factura() de invoice_manager.
    """
    import logging
    logging.warning("No usar get_next_invoice_number. Usar obtener_y_reservar_numero_factura().")
    return None

# Esta función ahora está in client_manager.py

def get_cufd():
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
    session = SessionLocal()
    try:
        cufd_record = session.query(Cufd).filter(Cufd.vigente == 1).first()
        if cufd_record and cufd_record.fecha_vigencia > datetime.now():
            return cufd_record.codigo
        else:
            nuevo_cufd = solicitar_cufd()
            message_placeholder.info(":heavy_check_mark: Se ha renovado el CUFD.")
            return nuevo_cufd
    except Exception as e:
        message_placeholder.error(f"❌Error al verificar o solicitar CUFD: {e}")
        raise ValueError(f"Error al verificar o solicitar CUFD: {e}")
    finally:
        session.close()

# Se elimina la función local load_private_key porque ya está implementada y centralizada en xml_signer.py
# Si necesitas usarla, impórtala directamente: from xml_signer import load_private_key


with open('verifica_stream.py', 'r') as file:
    file_content = file.read()
# Eliminando la lectura de cuis.py ya que estamos importando el módulo directamente
# with open('cuis.py', 'r') as file:
#     file_content += file.read()
@st.cache_data
def render_sidebar():
    # Toda la lógica relacionada con st.sidebar aquí
    numero_documento = st.sidebar.text_input("Número de Documento:", key="numero_documento", help="Ingresa el número de documento del cliente.")
    nit_valido = False
    nombre_cliente = ""
    complemento = None
    email = ""
    telefono = ""
    seleccion_tipo_documento = None
    codigo_clasificador_documento = None
    codigo_clasificador_metodo_pago = None
    ultimos_digitos_tarjeta = None
    codigo_cliente = None
    

    return numero_documento, nit_valido, nombre_cliente, complemento, email, telefono, seleccion_tipo_documento, codigo_clasificador_documento, codigo_clasificador_metodo_pago, ultimos_digitos_tarjeta, codigo_cliente

# Monitoreo del hilo de impresión. Actualiza ``st.session_state`` en el hilo principal.
def monitorear_hilo_impresion(hilo, result_queue=None):
    """Lee resultados de ``result_queue`` y actualiza ``st.session_state`` mientras
    el hilo de impresión está en ejecución."""
    try:
        ui_logger.info(f"Iniciando monitoreo del hilo de impresión: {hilo.name}")
        status_placeholder = st.empty()
        numero_factura = hilo.name.split('_')[-1]
        complete_signal = f"debug/print_complete_{numero_factura}.signal"
        error_signal = f"debug/print_error_{numero_factura}.signal"
        timeout = 30
        start_time = time.time()
        status_placeholder.info("⏳ Procesando...")

        while (hilo.is_alive() or st.session_state.get('impresion_en_progreso', False)):
            if result_queue is not None:
                try:
                    msg_type, msg = result_queue.get_nowait()
                    if msg_type == "success" or msg_type == "error":
                        st.session_state['print_status'] = msg
                    if msg_type == "done":
                        st.session_state['impresion_en_progreso'] = False
                        st.session_state['impresion_finalizada'] = True
                except queue.Empty:
                    pass
            if os.path.exists(complete_signal):
                st.session_state['print_status'] = "✅ Impresión completada exitosamente"
                st.session_state['impresion_en_progreso'] = False
                ui_logger.info(f"Impresión completada para la factura {numero_factura}")
                os.remove(complete_signal)
                break

            if os.path.exists(error_signal):
                with open(error_signal, 'r') as f:
                    error_info = f.read().strip()
                st.session_state['print_status'] = f"❌ {error_info}"
                st.session_state['impresion_en_progreso'] = False
                ui_logger.error(f"Error en la impresión de la factura {numero_factura}: {error_info}")
                os.remove(error_signal)
                break

            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                st.session_state['print_status'] = "⚠️ Tiempo de espera excedido, pero el proceso continúa en segundo plano."
                st.session_state['impresion_en_progreso'] = False
                ui_logger.warning(f"Tiempo de espera excedido para la impresión de la factura {numero_factura}")
                break

            print_status = st.session_state.get('print_status', "⏳ Procesando...")
            status_placeholder.info(print_status)
            time.sleep(0.5)

        final_status = st.session_state.get('print_status', "❓ Estado desconocido.")
        if "✅" in final_status:
            status_placeholder.success(final_status)
        elif "❌" in final_status:
            status_placeholder.error(final_status)
        else:
            status_placeholder.warning(final_status)

        ui_logger.info(f"Estado final del monitoreo de impresión: {final_status}")

    except Exception as e:
        st.error(f"❌ Error durante el monitoreo del proceso: {str(e)}")
        ui_logger.exception("Error en monitorear_hilo_impresion")
        st.session_state['impresion_en_progreso'] = False

# Gestión de pestañas con logs
def main():
    ui_logger.info("Iniciando la interfaz principal")
    message_placeholder = st.empty()
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "🧾Facturar", "🔍Ver Facturas", "✅Validar NIT", "😏Clientes", 
        "🔍Verificar Factura", "🔍Gestionar CUIS", "❌Anular/Revertir", "❌Revertir Anulacion", "🔧Diagnóstico"
    ])

    # Pestaña 2: Ver Facturas Generadas
    with tab2:
        st.header("Facturas Generadas")
        ui_logger.info("Usuario accedió a la pestaña 'Ver Facturas'")
        facturas_tabs = st.tabs(["Todas", "Pendientes", "Validadas", "Anuladas"])
        
        with facturas_tabs[0]:
            ui_logger.info("Mostrando todas las facturas")
            mostrar_lista_facturas("TODAS")
        
        with facturas_tabs[1]:
            ui_logger.info("Mostrando facturas pendientes")
            mostrar_lista_facturas("PENDIENTE")
            
        with facturas_tabs[2]:
            ui_logger.info("Mostrando facturas validadas")
            mostrar_lista_facturas("VALIDADA")
            
        with facturas_tabs[3]:
            ui_logger.info("Mostrando facturas anuladas")
            mostrar_lista_facturas("ANULADA")
    
    # Pestaña 3: Validar NIT
    with tab3:
        st.header("Validar NIT")
        verifica_stream.main()
        
    # Pestaña 4: Lista de Clientes
    with tab4:
        st.header("📋 Lista de Clientes")
        
        # Inicializar variables de estado para paginación
        init_session_state('clientes_page', 0)
        init_session_state('clientes_search', "")
        
        # Configuración de paginación
        REGISTROS_POR_PAGINA = 20
        
        # Barra de búsqueda
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            busqueda = st.text_input(
                "🔍 Buscar cliente", 
                value=st.session_state.clientes_search,
                placeholder="Buscar por nombre, documento o código..."
            )
        with col2:
            if st.button("🔄 Buscar"):
                st.session_state.clientes_search = busqueda
                st.session_state.clientes_page = 0  # Reset a primera página
                st.rerun()
        with col3:
            if st.button("🧹 Limpiar"):
                st.session_state.clientes_search = ""
                st.session_state.clientes_page = 0
                st.rerun()
        
        # Obtener datos de clientes
        offset = st.session_state.clientes_page * REGISTROS_POR_PAGINA
        clientes, total_registros, error = fetch_all_clientes(
            limite=REGISTROS_POR_PAGINA,
            offset=offset,
            busqueda=st.session_state.clientes_search if st.session_state.clientes_search else None
        )
        
        if error:
            st.error(f"Error al obtener clientes: {error}")
        elif not clientes:
            if st.session_state.clientes_search:
                st.warning("No se encontraron clientes que coincidan con la búsqueda.")
            else:
                st.info("No hay clientes registrados en el sistema.")
        else:
            # Mostrar estadísticas
            total_paginas = (total_registros - 1) // REGISTROS_POR_PAGINA + 1 if total_registros > 0 else 0
            pagina_actual = st.session_state.clientes_page + 1
            
            st.info(f"📊 **Total de clientes**: {total_registros} | **Página**: {pagina_actual}/{total_paginas}")
            
            # Crear DataFrame para mostrar en tabla
            if clientes:
                # Preparar datos para la tabla
                datos_tabla = []
                for cliente in clientes:
                    datos_tabla.append({
                        "ID": cliente.get("id", ""),
                        "Código": cliente.get("codigo_cliente", ""),
                        "Nombre/Razón Social": cliente.get("nombre_razon_social", ""),
                        "Documento": cliente.get("numero_documento", ""),
                        "Tipo Doc": cliente.get("codigo_tipo_documento_identidad", ""),
                        "Email": cliente.get("email", ""),
                        "Teléfono": cliente.get("telefono", ""),
                        "Complemento": cliente.get("complemento", "")
                    })
                
                # Mostrar tabla
                st.dataframe(
                    datos_tabla,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Controles de paginación
                if total_paginas > 1:
                    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                    
                    with col1:
                        if st.button("⬅️ Primera", disabled=(st.session_state.clientes_page == 0)):
                            st.session_state.clientes_page = 0
                            st.rerun()
                    
                    with col2:
                        if st.button("◀️ Anterior", disabled=(st.session_state.clientes_page == 0)):
                            st.session_state.clientes_page -= 1
                            st.rerun()
                    
                    with col3:
                        st.write(f"Página {pagina_actual} de {total_paginas}")
                    
                    with col4:
                        if st.button("▶️ Siguiente", disabled=(st.session_state.clientes_page >= total_paginas - 1)):
                            st.session_state.clientes_page += 1
                            st.rerun()
                    
                    with col5:
                        if st.button("➡️ Última", disabled=(st.session_state.clientes_page >= total_paginas - 1)):
                            st.session_state.clientes_page = total_paginas - 1
                            st.rerun()
            
            # Mostrar detalles de cliente seleccionado (opcional)
            with st.expander("ℹ️ Ver detalles de cliente específico"):
                documento_detalle = st.text_input("Ingrese número de documento para ver detalles:")
                if st.button("Ver Detalles") and documento_detalle:
                    cliente_detalle, error_detalle = fetch_cliente(documento_detalle)
                    if error_detalle:
                        st.error(error_detalle)
                    else:
                        st.json(cliente_detalle)

    # Pestaña 5: Verificar Factura
    with tab5:
        st.header("Verificar Factura")
        numero_factura = st.text_input("Ingrese el número de la factura:")

        if st.button("Verificar Factura"):
            # Limpiar cualquier mensaje previo
            message_placeholder.empty()

            if not numero_factura:
                message_placeholder.warning("Por favor, ingrese un número de factura.")
            else:
                exito, mensaje = verificar_estado_factura(numero_factura)
                if exito:
                    message_placeholder.success(mensaje)
                else:
                    message_placeholder.error(mensaje)

    # Pestaña 6: Gestionar CUIS
    with tab6:
        st.header("🔑 Gestionar CUIS")
        st.markdown("""
        **CUIS (Código Único de Inicio de Sistemas)** es un código único que autoriza al sistema 
        de facturación para operar con el SIN. Es necesario tenerlo vigente para emitir facturas.
        """)
        
        # Información sobre el CUIS actual
        st.subheader("📊 Estado actual del CUIS")
        
        # Llamar a la funcionalidad principal de CUIS
        cuis.main()

    # Pestaña 7: Anular Factura
    with tab7:
        st.header("Anular Factura")
        
        # Entrada para el número de factura
        numero_factura_anular = st.text_input("Ingrese el número de la factura a anular:")
        
        # Obtener las opciones de motivos desde la base de datos
        opciones_motivos = obtener_motivos_anulacion()
        
        # Verificar si hay motivos de anulación disponibles
        if opciones_motivos:
            descripcion_motivo = st.selectbox("Seleccione el motivo de la anulación", opciones_motivos)
        else:
            st.error("No se encontraron motivos de anulación disponibles.")

        # Botón para iniciar la anulación de la factura
        if st.button("Anular Factura"):
            # Limpiar cualquier mensaje previo
            message_placeholder.empty()

            if not numero_factura_anular or not descripcion_motivo:
                message_placeholder.warning("Por favor, ingrese todos los datos requeridos.")
            else:
                # Llamar a la función anular_factura
                exito, mensaje = anular_factura(numero_factura_anular, descripcion_motivo)
                
                if exito:
                    message_placeholder.success(mensaje)
                else:
                    message_placeholder.error(mensaje)
    # Pestaña 8: Revertir Anulación de Factura
    with tab8:
        st.header("Revertir Anulación de Factura")
        
        # Entrada para el número de factura
        numero_factura_revertir = st.text_input("Ingrese el número de la factura a revertir la anulación:")

        # Botón para iniciar la reversión de la anulación
        if st.button("Revertir Anulación"):
            # Limpiar cualquier mensaje previo
            message_placeholder.empty()

            if not numero_factura_revertir:
                message_placeholder.warning("Por favor, ingrese el número de la factura.")
            else:
                cuf, factura = obtener_cuf_por_numero_factura(numero_factura_revertir)
                if not cuf:
                    message_placeholder.error("No se encontró la factura especificada.")
                else:
                    exito, respuesta = enviar_solicitud_reversion(cuf)
                    if exito:
                        exito_reversion, mensaje_reversion = procesar_respuesta_reversion(respuesta, factura)
                        if exito_reversion:
                            message_placeholder.success(mensaje_reversion)
                        else:
                            message_placeholder.error(mensaje_reversion)
                    else:
                        message_placeholder.error(respuesta)
    
    if 'processed_comandas' not in st.session_state:
        st.session_state.processed_comandas = []

    comandas, mensaje_error = fetch_comandas()
    if mensaje_error:
        st.error(mensaje_error)

    metodos_pago, error_metodos = fetch_metodos_pago()
    if error_metodos:
        st.error(error_metodos)

    tipos_documento, error_documentos = fetch_tipos_documento()
    if error_documentos:
        st.error(error_documentos)

    numero_documento = st.sidebar.text_input("Número de Documento:", key="numero_documento", help="Ingresa el número de documento del cliente.")
    nit_valido = False

    nombre_cliente = ""
    complemento = None
    email = ""
    telefono = ""
    seleccion_tipo_documento = None
    codigo_clasificador_documento = None
    codigo_clasificador_metodo_pago = None
    ultimos_digitos_tarjeta = None
    codigo_cliente = None   

    if numero_documento:
        cliente_data, error = fetch_cliente(numero_documento)
        if cliente_data:
            tipo_documento_cliente = next((doc for doc in tipos_documento if doc["codigoClasificador"] == cliente_data["codigo_tipo_documento_identidad"]), None)
            if tipo_documento_cliente:
                seleccion_tipo_documento = tipo_documento_cliente["descripcion"]
                codigo_clasificador_documento = tipo_documento_cliente["codigoClasificador"]
                st.sidebar.text_input("Tipo de Documento:", value=tipo_documento_cliente["descripcion"], disabled=True)
            if cliente_data["codigo_tipo_documento_identidad"] == '2':
                complemento = st.sidebar.text_input("Complemento:", value=cliente_data['complemento'], disabled=True)
            nombre_cliente = st.sidebar.text_input("Razón Social:", value=cliente_data['nombre_razon_social'].upper(), disabled=True)

            # Mostrar el campo email solo si no es None o está vacío
            if cliente_data['email']:
                email = st.sidebar.text_input("Email:", value=cliente_data['email'], disabled=True)

            # Mostrar el campo teléfono solo si no es None o está vacío
            if cliente_data['telefono']:
                telefono = st.sidebar.text_input("Teléfono:", value=cliente_data['telefono'], disabled=True)
            
            codigo_cliente = cliente_data['codigo_cliente']

        else:
            opciones_tipos_documento = [doc["descripcion"] for doc in tipos_documento]
            seleccion_tipo_documento = st.sidebar.selectbox("Tipo de Documento:", opciones_tipos_documento, index=2)
            tipo_documento_seleccionado = next((doc for doc in tipos_documento if doc["descripcion"] == seleccion_tipo_documento), None)
            if tipo_documento_seleccionado:
                codigo_clasificador_documento = tipo_documento_seleccionado["codigoClasificador"]
                if tipo_documento_seleccionado['codigoClasificador'] == '2':
                    complemento = st.sidebar.text_input("Complemento:", key="complemento")
                nombre_cliente = st.sidebar.text_input("Razón Social:", placeholder="Sin Nombre", key="nombre_cliente")
                email = st.sidebar.text_input("Email:", key="email")
                telefono = st.sidebar.text_input("Teléfono:", key="telefono")

                if seleccion_tipo_documento == "NIT - NÚMERO DE IDENTIFICACIÓN TRIBUTARIA":
                    valido, mensaje = verificar_nit_cliente(numero_documento, message_placeholder)
                    if valido:
                        message_placeholder.success(f"✔️ NIT válido: {mensaje}")
                        nit_valido = True
                    else:
                        message_placeholder.error(mensaje, icon="❌")
                        nit_valido = False

                guardar_cliente_button = st.sidebar.button("Guardar Cliente", key="guardar_cliente", disabled=(not nit_valido and seleccion_tipo_documento == "NIT - NÚMERO DE IDENTIFICACIÓN TRIBUTARIA"))
                if guardar_cliente_button:
                    if tipo_documento_seleccionado:
                        cliente_data = save_or_fetch_client_data(numero_documento, tipo_documento_seleccionado['codigoClasificador'], complemento, email, nombre_cliente, numero_documento, telefono, message_placeholder)
                        if cliente_data:
                            message_placeholder.success("✔️ Datos del cliente guardados correctamente.")
                            codigo_cliente = numero_documento  # Set codigo_cliente to numero_documento for new client
                    else:
                             message_placeholder.error("Por favor selecciona un tipo de documento válido")
    
    id_comanda_set = set(comanda["id_comanda"] for comanda in comandas)
    available_comandas = [comanda for comanda in id_comanda_set if comanda not in st.session_state.processed_comandas]

    selected_id_comanda = st.sidebar.multiselect("Selecciona las comandas", available_comandas, key="selected_comandas", placeholder="Comandas Generadas", help="Selecciona las comandas que componen la factura.")


    opciones_metodos_pago = [metodo["descripcion"] for metodo in metodos_pago]

    indice_metodo_pago_predeterminado = next((i for i, metodo in enumerate(metodos_pago) if metodo["codigoClasificador"] == 1), 0)

    #logging.debug(f"Opciones de métodos de pago: {opciones_metodos_pago}")
    logging.debug(f"Índice del método de pago predeterminado: {indice_metodo_pago_predeterminado}")

    seleccion_metodo_pago = st.sidebar.selectbox("Tipo de Pago:", opciones_metodos_pago, index=66, key="metodo_pago")

    logging.debug(f"Método de pago seleccionado: {seleccion_metodo_pago}")

    metodo_pago_seleccionado = next((metodo for metodo in metodos_pago if metodo["descripcion"] == seleccion_metodo_pago), None)

    codigo_clasificador_metodo_pago = None
    if metodo_pago_seleccionado:
        codigo_clasificador_metodo_pago = int(metodo_pago_seleccionado["codigoClasificador"])
        logging.info(f"Código clasificador del método de pago seleccionado: {codigo_clasificador_metodo_pago} ({type(codigo_clasificador_metodo_pago)})")

    if seleccion_metodo_pago == "TARJETA":
        ultimos_digitos_tarjeta = st.sidebar.text_input("Ingresa los últimos 4 dígitos de la tarjeta:", max_chars=4, key="ultimos_digitos_tarjeta")

    on = st.sidebar.checkbox("Aplicar Descuento")

    descuento_adicional = Decimal(0.00)
    monto_giftcard = Decimal(0.00)

    logging.debug(f"Aplicar Descuento: {on}")

    if on:
        descuento_adicional = st.sidebar.number_input("Descuento Adicional:", min_value=0, step=5, key="descuento_adicional")
        if descuento_adicional is None:
            descuento_adicional = Decimal(0.00)
        else:
            descuento_adicional = Decimal(descuento_adicional)
        logging.debug(f"Descuento adicional ingresado: {descuento_adicional}")

    if codigo_clasificador_metodo_pago is not None:
        logging.info(f"Verificando si el código clasificador {codigo_clasificador_metodo_pago} ({type(codigo_clasificador_metodo_pago)}) está en la lista de códigos de gift card: {gift_card_codes}")
        if codigo_clasificador_metodo_pago in gift_card_codes:
            monto_giftcard = st.sidebar.number_input("Gift Card:", min_value=0, step=5, key="monto_giftcard")
            if monto_giftcard is None:
                monto_giftcard = Decimal(0.00)
            else:
                monto_giftcard = Decimal(monto_giftcard)
            logging.info(f"Monto de Gift Card ingresado: {monto_giftcard}")
        else:
            monto_giftcard = Decimal(0.00)
    else:
        monto_giftcard = Decimal(0.00)
    
    logging.debug(f"Descuento Adicional Final: {descuento_adicional}")
    logging.debug(f"Monto Gift Card Final: {monto_giftcard}")
    numero_factura = None  # Se asignará solo si la transacción es exitosa
    if selected_id_comanda:
        comandas_seleccionadas = [comanda for comanda in comandas if comanda["id_comanda"] in selected_id_comanda]
        subtotal, descuento_aplicado, monto_giftcard, total, monto_total_sujeto_iva, monto_total_moneda = calculate_totals(
            comandas_seleccionadas, 
            descuento_adicional, 
            monto_giftcard, 
            codigo_clasificador_metodo_pago,
            tipo_cambio=1
        )
        db = SessionLocal()
        try:
            lineas_productos = collect_product_lines(comandas, selected_id_comanda, db)
        finally:
            db.close()
    else:
        comandas_seleccionadas = []
        subtotal, descuento_aplicado, monto_giftcard, total, monto_total_sujeto_iva, monto_total_moneda = 0, 0, 0, 0, 0, 0
        lineas_productos = []

    fecha_emision = datetime.now()
    # Este formato se usa para el XML y comunicación con SIAT (ISO 8601 con milisegundos)
    fecha_emision_str = fecha_emision.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    
    # Para mostrar en la interfaz y factura impresa se usa el formato:
    fecha_emision_display = fecha_emision.strftime("%d/%m/%Y %H:%M:%S")
    # Eliminar el segundo get_next_invoice_number aquí para evitar doble incremento
    # numero_factura = get_next_invoice_number()

    ACTIVIDAD_ECONOMICA = os.getenv('ACTIVIDAD_ECONOMICA')
    CODIGO_PRODUCTO_SIN = os.getenv('CODIGO_PRODUCTO_SIN')

    

    # Solo mostrar vista previa en la UI, sin reservar número ni generar XML
    numero_factura = '(se asignará al emitir)'
    with tab1:
        html_invoice = generate_html_invoice(
            subtotal, descuento_adicional, monto_giftcard, lineas_productos,
            nombre_cliente, fecha_emision_display, numero_factura, seleccion_metodo_pago,
            codigo_clasificador_metodo_pago, seleccion_tipo_documento,
            codigo_clasificador_documento, numero_documento, complemento,
            email, telefono, ultimos_digitos_tarjeta
        )
        components.html(html_invoice, height=700, scrolling=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Facturar", key="generar_xml", help="Generar la factura", disabled=not selected_id_comanda):
                if metodo_pago_seleccionado and seleccion_tipo_documento and numero_documento and selected_id_comanda:
                    try:
                        # Configuración inicial
                        tipo_documento_seleccionado = next((doc for doc in tipos_documento if doc["descripcion"] == seleccion_tipo_documento), None)
                        nit_emisor = int(os.getenv('NIT'))
                        razon_social_emisor = os.getenv('RAZON_SOCIAL')
                        municipio = os.getenv('MUNICIPIO')
                        telefono = os.getenv('TELEFONO')
                        cufd = verificar_y_obtener_cufd(message_placeholder)
                        codigo_sucursal = int(os.getenv('CODIGO_SUCURSAL'))
                        codigo_punto_venta = int(os.getenv('CODIGO_PUNTO_VENTA'))
                        codigo_documento_sector = int(os.getenv('CODIGO_DOCUMENTO_SECTOR')) 
                        direccion = os.getenv('DIRECCION')

                        # Reservar el número real de factura SOLO aquí
                        numero_factura = obtener_y_reservar_numero_factura()
                        # Generar CUF y XML definitivos
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
                        xml_str, factura_cabecera_data, detalles_data = generate_xml_invoice(
                            nit_emisor, razon_social_emisor, municipio, telefono, numero_factura,
                            cuf, cufd, codigo_sucursal, direccion, codigo_punto_venta,
                            fecha_emision_str, nombre_cliente, tipo_documento_seleccionado['codigoClasificador'],
                            numero_documento, complemento, numero_documento,
                            metodo_pago_seleccionado['codigoClasificador'], ultimos_digitos_tarjeta,
                            subtotal, total, 1, 1, total / 1, monto_giftcard, descuento_adicional,
                            "don_bercho", codigo_documento_sector, lineas_productos,
                            os.getenv('ACTIVIDAD_ECONOMICA'), os.getenv('CODIGO_PRODUCTO_SIN')
                        )
                        # Firmar el XML
                        private_key_path = "xmls/llaves/private_key_ok.pem"
                        cert_path = "xmls/llaves/certificado_ok.pem"
                        signed_xml_str = sign_xml(xml_str, private_key_path, cert_path, cuf)
                        # Guardar XML firmado
                        filename = f"xmls/factura_{numero_factura}_{cuf}_.xml"
                        with open(filename, "w", encoding='utf-8') as signed_xml_file:
                            signed_xml_file.write(signed_xml_str)
                        # Validar XML contra el XSD
                        xsd_main_path = 'xmls/schemas/facturaElectronicaCompraVenta.xsd'
                        if not validar_xml(filename, xsd_main_path):
                            message_placeholder.error("❌ El XML generado no es válido contra el XSD.")
                            return
                        # Comprimir y enviar
                        gzip_path = comprimir_xml(filename)
                        hash_archivo = obtener_hash(gzip_path)
                        response = enviar_solicitud(filename, xsd_main_path, fecha_emision_str, cufd)
                        # Procesar respuesta y guardar en base de datos si es exitosa
                        if isinstance(response, dict) and response.get("error"):
                            message_placeholder.error(f"❌Error al enviar la factura: {response['error']}")
                        else:
                            try:
                                success, response_data = parse_siat_response(response.content)
                                if success:
                                    transaccion_exitosa = display_siat_response(response_data, message_placeholder)
                                    if transaccion_exitosa:
                                        st.session_state['cuf'] = cuf
                                        st.session_state['ultima_factura'] = numero_factura
                                        st.session_state['factura_validada'] = True
                                        st.session_state['datos_impresion'] = {
                                            'subtotal': subtotal,
                                            'descuento_adicional': descuento_adicional,
                                            'monto_giftcard': monto_giftcard,
                                            'lineas_productos': lineas_productos,
                                            'nombre_cliente': nombre_cliente,
                                            'fecha_emision_str': fecha_emision_display, 
                                            'seleccion_metodo_pago': seleccion_metodo_pago,
                                            'codigo_clasificador_metodo_pago': codigo_clasificador_metodo_pago,
                                            'seleccion_tipo_documento': seleccion_tipo_documento,
                                            'codigo_clasificador_documento': codigo_clasificador_documento,
                                            'numero_documento': numero_documento,
                                            'complemento': complemento,
                                            'email': email,
                                            'telefono': telefono,
                                            'ultimos_digitos_tarjeta': ultimos_digitos_tarjeta
                                        }
                                        factura_cabecera_data['tipoEmision'] = "1"
                                        is_valid, error_message = validar_factura_cabecera(factura_cabecera_data)
                                        if is_valid:
                                            guardar_factura_cabecera(factura_cabecera_data)
                                            for detalle in detalles_data:
                                                is_valid, error_message = validar_factura_detalle(detalle)
                                                if is_valid:
                                                    guardar_factura_detalle(detalle)
                                                else:
                                                    message_placeholder.error(error_message)
                                                    return
                                else:
                                    facturacion_logger.error(f"Error al procesar respuesta: {response_data.get('error')}")
                                    if 'xml_content' in response_data:
                                        xml_logger.error(f"Contenido XML problemático: {response_data['xml_content'][:500]}...")
                            except Exception as e:
                                message_placeholder.error(f"❌Error al procesar la respuesta: {str(e)}")
                                facturacion_logger.exception("Error inesperado al procesar respuesta")
                    except Exception as e:
                        message_placeholder.error(f"❌Error en el proceso de facturación: {str(e)}")
                        logging.exception("Error en facturación")
                else:   
                    message_placeholder.error("❌Por favor, complete todos los campos requeridos.")

        with col2:
            # Asegurarse de que el estado esté inicializado
            initialize_print_state()

            # Mostrar advertencia si la impresión está en curso
            mostrar_mensaje_impresion_en_curso()

            # Botón para forzar liberación de impresión si está colgada
            if st.session_state.get('impresion_en_progreso', False):
                if st.button("Forzar liberación de impresión", key="forzar_liberacion_impresion"):
                    st.session_state['impresion_en_progreso'] = False
                    st.session_state['print_status'] = "⚠️ Impresión liberada manualmente. Puedes volver a intentar imprimir."

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
                            hilo_impresion, result_queue = imprimir_en_hilo(
                                html_content,
                                st.session_state['cuf'],
                                os.getenv('NIT'),
                                st.session_state['ultima_factura']
                            )

                            monitorear_hilo_impresion(hilo_impresion, result_queue)
                    except Exception as e:
                        st.session_state['print_status'] = f"❌ Error: {str(e)}"
                        st.session_state['impresion_en_progreso'] = False
                        printer_logger.exception("Error en el proceso de impresión")
            else:
                st.info("El botón de impresión solo estará disponible cuando la factura haya sido validada exitosamente por el SIN.")
        
        with col3:
            if st.session_state.get('factura_validada'):
                nit_emisor = int(os.getenv('NIT'))
                enlace = generate_invoice_link(nit_emisor, st.session_state['cuf'], st.session_state['ultima_factura'])
                st.link_button("Consultar factura", enlace)

    # Pestaña 9: Diagnóstico Avanzado (NUEVA funcionalidad)
    with tab9:
        st.header("🔧 Diagnóstico Avanzado de Comunicación")
        st.markdown("""
        Esta pestaña utiliza un **servicio mejorado** que combina todas las verificaciones existentes
        del sistema para proporcionar un diagnóstico completo del estado de comunicación con el SIN.
        
        **Nota**: Este diagnóstico **NO reemplaza** las funcionalidades existentes, sino que las **mejora**.
        """)
        
        # Importar el nuevo servicio de manera segura
        try:
            from communication_manager import communication_manager
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if st.button("🔍 Ejecutar Diagnóstico Completo", type="primary"):
                    communication_manager.mostrar_diagnostico_completo()
            
            with col2:
                st.info("**Fuentes de Verificación:**\n"
                       "• soap_services.py\n"
                       "• business_logic.py\n"
                       "• Análisis combinado")
            
            # Mostrar último resultado si existe
            estado_persistente = communication_manager.obtener_estado_persistente()
            ultimo_resultado = estado_persistente.get('ultimo_resultado_completo')
            
            if ultimo_resultado:
                st.subheader("📊 Último Diagnóstico")
                with st.expander("Ver detalles del último diagnóstico"):
                    st.json(ultimo_resultado)
                    
                    # Mostrar tiempo transcurrido
                    try:
                        timestamp = datetime.fromisoformat(ultimo_resultado['timestamp'])
                        tiempo_transcurrido = datetime.now() - timestamp
                        st.caption(f"Ejecutado hace: {tiempo_transcurrido}")
                    except:
                        st.caption("Tiempo de ejecución: No disponible")
            
            # Información sobre compatibilidad
            with st.expander("ℹ️ Información sobre Compatibilidad"):
                st.markdown("""
                ### 🛡️ Garantías de Compatibilidad
                
                Este diagnóstico avanzado:
                
                ✅ **NO modifica** las funciones existentes en `soap_services.py`  
                ✅ **NO modifica** las funciones existentes en `business_logic.py`  
                ✅ **NO cambia** imports existentes en otros módulos  
                ✅ **NO interfiere** con el funcionamiento normal del sistema  
                ✅ **SOLO agrega** funcionalidades adicionales opcionales  
                
                ### 🔧 Cómo Funciona
                
                1. **Usa las funciones ORIGINALES** como base
                2. **Combina** los resultados de múltiples fuentes
                3. **Analiza** patrones y proporciona recomendaciones
                4. **Registra** histórico para análisis de tendencias
                
                ### 📈 Beneficios Adicionales
                
                - **Diagnóstico más completo** que las verificaciones individuales
                - **Recomendaciones inteligentes** basadas en múltiples fuentes
                - **Histórico de verificaciones** para análisis de patrones
                - **Interfaz mejorada** con detalles visuales
                """)
                
        except ImportError as e:
            st.error("❌ Error al cargar el servicio de diagnóstico avanzado")
            st.code(f"Error: {e}")
            st.info("💡 El sistema continúa funcionando normalmente con las verificaciones existentes.")

# Esta función ahora está en invoice_manager.py
    
    if __name__ == "__main__":
        initialize_print_state()
        main()