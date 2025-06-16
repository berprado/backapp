import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
import streamlit as st
import streamlit.components.v1 as components
import re  # Necesario para algunas validaciones que quedan en el archivo
from data_access import (
    fetch_comandas, fetch_metodos_pago, fetch_tipos_documento, fetch_cliente,
    fetch_random_leyenda, obtener_nombre_unidad_medida, obtener_motivos_anulacion,
    obtener_cuf_por_numero_factura, obtener_factura_completa, 
    guardar_factura_cabecera, guardar_factura_detalle, obtener_facturas_por_estado
)
from business_logic import calculate_totals, collect_product_lines, generate_invoice_link, generate_qr
from invoice_xml_generator import generate_xml_invoice
from num2words import num2words
from database import SessionLocal
from facturador.models import Cufd, Cliente
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime
from decimal import Decimal
import logging
import traceback
import xml.etree.ElementTree as ET

# Importaciones de los nuevos módulos modularizados
from validators import es_email_valido, es_telefono_valido, validar_factura_cabecera, validar_factura_detalle
from client_manager import save_or_fetch_client_data, verificar_nit_cliente
from invoice_manager import guardar_factura_en_bd, increment_invoice_number, mostrar_lista_facturas
from print_manager import initialize_print_state, reiniciar_estados, imprimir_en_hilo
from xml_signer import sign_xml, calculate_hash

# Zeep y solicitudes
from zeep import Client
from zeep.transports import Transport
from requests import Session
from dotenv import load_dotenv

# Módulos relacionados con CUF/CUFD
from generate_cuf import generate_cuf
from cufd import solicitar_cufd
import cuis

# XML y criptografía
from lxml import etree
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
import base64
import hashlib

# Utilidades para facturación
from zeeper import validar_xml, comprimir_xml, obtener_hash, enviar_solicitud
import verifica_stream
from estado_factura import verificar_estado_factura
from anulacion import anular_factura
from reversion import enviar_solicitud_reversion, procesar_respuesta_reversion
from facturador.response_handler import parse_siat_response, display_siat_response

# Impresión y exportación
#from facturador.export import imprimir_recibo
from invoice_templates import generate_compact_html_invoice
from thermal_printer import ThermalPrinter
from siat_pdf import html_to_pdf
import threading

# Configuración de logger
# Agregar la ruta del directorio padre al path de Python si no está ya
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if (parent_dir not in sys.path):
    sys.path.append(parent_dir)

from logger_config import get_logger, get_printer_logger, get_facturacion_logger, get_xml_logger

# Obtener loggers específicos para diferentes componentes
logger = get_logger()
printer_logger = get_printer_logger()
facturacion_logger = get_facturacion_logger()
xml_logger = get_xml_logger()

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



@st.cache_data
def generate_html_invoice(subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura, metodo_de_pago=None, codigo_clasificador_metodo_pago=None, tipo_documento=None, codigo_clasificador_documento=None, numero_documento=None, complemento=None, email=None, telefono=None, ultimos_digitos_tarjeta=None):
    total = subtotal - descuento_adicional
    total_final = total - monto_giftcard
    
    if codigo_clasificador_metodo_pago in gift_card_codes:
        monto_total_sujeto_iva = total - monto_giftcard
    else:
        monto_total_sujeto_iva = total

    total_en_palabras = numero_a_palabras_con_decimales_como_fraccion(total, lang='es') if total else ""

    leyenda = fetch_random_leyenda()
    
    nit = os.getenv('NIT') # NIT del emisor
    razon_social = os.getenv('RAZON_SOCIAL') # Razón social del emisor
    nombre_sucursal = os.getenv('NOMBRE_SUCURSAL')  # Nombre de la sucursal
    codigo_punto_venta = os.getenv('CODIGO_PUNTO_VENTA')  # Código del punto de venta
    direccion = os.getenv('DIRECCION')  # Dirección de la empresa
    municipio = os.getenv('MUNICIPIO')  # Municipio de la empresa
    telefono_empresa = os.getenv('TELEFONO')  # Teléfono de la empresa
    tipo_factura = os.getenv('DESCRIPCION_TIPO_FACTURA')  # Tipo de factura (original, copia, etc.)
    subtitulo = os.getenv('SUBTITULO')    # Generar el código QR si el CUF está disponible


    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Factura</title>
        <style type="text/css">
        .tg  {{border-collapse:collapse;border-spacing:0;margin:0px auto;}}
        .tg td{{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
        overflow:hidden;padding:10px 5px;word-break:normal;}}
        .tg th{{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
        font-weight:normal;overflow:hidden;padding:10px 5px;word-break:normal;}}
        .tg .tg-4pi9{{background-color:#ffffff;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:left;vertical-align:middle;word-break:break-all;}}
        .tg .tg-tdlr{{background-color:#ffffff;border-color:#ffffff;font-size:12px;text-align:left;vertical-align:top;}}
        .tg .tg-c01i{{background-color:#9b9b9b;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;font-weight:bold;text-align:right;vertical-align:middle;}}
        .tg .tg-n17z{{background-color:#ffffff;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:center;vertical-align:middle;}}
        .tg .tg-i6l2{{background-color:#ffffff;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:right;vertical-align:middle;}}
        .tg .tg-gayi{{background-color:#9b9b9b;border-color:#efefef;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;font-weight:bold;text-align:center;vertical-align:middle;}}
        .tg .tg-1kjo{{background-color:#c0c0c0c0;border-color:#efefef;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:center;vertical-align:middle;}}
        .tg .tg-tm6e{{background-color:#c0c0c0;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:left;vertical-align:middle;}}
        .tg .tg-q5sf{{background-color:#ffffff;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:9px;text-align:center;vertical-align:middle;}}
        .tg .tg-e8cb{{background-color:#9b9b9b;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:right;vertical-align:middle;}}
        .tg .tg-6l70{{background-color:#9b9b9b;border-color:#ffffff;font-family:"Lucida Console", Monaco, monospace !important;
        font-size:12px;text-align:center;vertical-align:middle;}}
        </style>
    </head>
    <body>
    <table class="tg"><tbody>
    <tr>
        <td class="tg-n17z" colspan="4"><span style="font-weight:bold">{razon_social}</span><br><span style="font-weight:bold">{nombre_sucursal}</span><br><span style="font-weight:bold">Punto de Venta:</span> {codigo_punto_venta}</td>
        <td class="tg-n17z"></td>
        <td class="tg-i6l2"><span style="font-weight:bold">NIT:</span><br><span style="font-weight:bold">Factura N°:</span></td>
        <td class="tg-4pi9">{nit}<br>{numero_factura}</td>
    </tr>
    <tr>
        <td class="tg-n17z" colspan="4">{direccion}<br><span style="font-weight:bold">{municipio}</span><br><span style="font-weight:bold">Teléfono:</span> {telefono_empresa}</td>
        <td class="tg-n17z"></td>
        <td class="tg-i6l2"><span style="font-weight:bold">Código de</span><br><span style="font-weight:bold">Autorización</span></td>
        <td class="tg-4pi9">{{cuf}}</td>
    </tr>
    <tr>
        <td class="tg-n17z" colspan="7"><span style="font-weight:bold">{tipo_factura}</span><br>{subtitulo}</td>
    </tr>
    <tr>
        <td class="tg-n17z" colspan="4"><span style="font-weight:bold">Fecha/Hora:</span> {fecha_emision}<br><span style="font-weight:bold">Nombre/Razón Social:</span> {nombre_cliente.upper()}</td>
        <td class="tg-n17z"></td>
        <td class="tg-i6l2"><span style="font-weight:bold">NIT/CI/CEX:</span><br><span style="font-weight:bold">Cod. Cliente:</span></td>
        <td class="tg-4pi9">{numero_documento}<br>{numero_documento}</td>
    </tr>
    <tr>
        <td class="tg-tdlr" colspan="7"></td>
    </tr>
    <tr>
        <td class="tg-gayi" width="10%">CODIGO</td>
        <td class="tg-gayi" width="5%">CANTIDAD</td>
        <td class="tg-gayi" width="10%">UNIDAD</td>
        <td class="tg-gayi" width="35%">DESCRIPCIÓN</td>
        <td class="tg-gayi" width="10%">PRECIO UNIT.</td>
        <td class="tg-gayi" width="15%">DESCUENTO</td>
        <td class="tg-gayi" width="15%">SUBTOTAL</td>
    </tr>
    """

    for linea in lineas_productos:
        html_content += f"""
        <tr>
            <td class="tg-1kjo">{linea["codigo"]}</td>
            <td class="tg-1kjo">{linea["cantidad"]}</td>
            <td class="tg-1kjo">{linea["unidad"]}</td>
            <td class="tg-1kjo">{linea["nombre"]}</td>
            <td class="tg-1kjo">{linea["precio_venta"]}</td>
            <td class="tg-1kjo">{linea.get("montoDescuento", 0)}</td>
            <td class="tg-1kjo">{linea["sub_total"]}</td>
        </tr>
        """

    html_content += f"""
    <tr>
        <td class="tg-n17z" colspan="5"></td>
        <td class="tg-c01i">Sub Total:</td>
        <td class="tg-tm6e"><span style="font-weight:bold">{subtotal:.2f}</span></td>
    </tr>
    <tr>
        <td class="tg-q5sf" colspan="5"></td>
        <td class="tg-c01i">Descuento:</td>
        <td class="tg-tm6e"><span style="font-weight:bold">{descuento_adicional:.2f}</span></td>
    </tr>
    <tr>
        <td class="tg-n17z" colspan="5"><span style="font-weight:bold">Son: {total_en_palabras}</span></td>
        <td class="tg-e8cb"><span style="font-weight:bold">Total:</span></td>
        <td class="tg-tm6e"><span style="font-weight:bold">{total:.2f}</span></td>
    </tr>
    <tr>
        <td class="tg-q5sf" colspan="5"></td>
        <td class="tg-e8cb"><span style="font-weight:bold">Gift Card:</span></td>
        <td class="tg-tm6e"><span style="font-weight:bold">{monto_giftcard:.2f}</span></td>
    </tr>
    <tr>
        <td class="tg-q5sf" colspan="5"></td>
        <td class="tg-e8cb"><span style="font-weight:bold">Monto a Pagar:</span></td>
        <td class="tg-tm6e"><span style="font-weight:bold">{total_final:.2f}</span></td>
    </tr>
    <tr>
        <td class="tg-q5sf" colspan="5"></td>
        <td class="tg-6l70"><span style="font-weight:bold">Imp. Base Cred. Fiscal:</span></td>
        <td class="tg-tm6e"><span style="font-weight:bold">{monto_total_sujeto_iva:.2f}</span></td>
    </tr>
    <tr>
        <td class="tg-n17z" colspan="5"><span class="tg-q5sf">ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS, EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE ACUERDO A LEY</span><br><br><span style="font-weight:bold">{leyenda}</span><br><br><span class="tg-q5sf">“Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido en una modalidad de facturación en línea”</span></td>
        <td class="tg-n17z" colspan="2">{{codigo_qr}}</td>
    </tr>
    </tbody></table>
    </body>
    </html>
    """
    return html_content

def get_next_invoice_number():
    try:
        with open("invoice_number.txt", "r") as file:
            numero_factura = int(file.read().strip())
    except FileNotFoundError:
        logger.warning("Archivo 'invoice_number.txt' no encontrado. Se creará uno nuevo con el número de factura inicial 0.")
        numero_factura = 0
    except ValueError as e:
        logger.error(f"Error de formato en 'invoice_number.txt': {e}")
        raise ValueError("El archivo 'invoice_number.txt' contiene un valor no válido.")
    except Exception as e:
        logger.error(f"Error inesperado al leer 'invoice_number.txt': {e}")
        raise e
    return numero_factura + 1

# Esta función ahora está en invoice_manager.py

# Esta función ahora está en client_manager.py

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

def load_private_key(private_key_path, password=None):
    with open(private_key_path, "rb") as key_file:
        return serialization.load_pem_private_key(key_file.read(), password=password.encode() if password else None)

# Esta función ahora está en xml_signer.py


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

# Estas funciones ahora están en print_manager.pydef monitorear_hilo_impresion(hilo):
    try:
        # Crear un placeholder para actualizar el mensaje de estado
        status_placeholder = st.empty()
        
        # Obtener el número de factura del nombre del hilo
        numero_factura = hilo.name.split('_')[-1]
        complete_signal = f"debug/print_complete_{numero_factura}.signal"
        error_signal = f"debug/print_error_{numero_factura}.signal"
        
        timeout = 30  # Tiempo máximo de espera en segundos
        start_time = time.time()
        
        # Mostrar mensaje inicial
        status_placeholder.info("⏳ Procesando...")
        
        # Mientras el hilo está activo y no hay señal de finalización
        while (hilo.is_alive() or st.session_state.get('impresion_en_progreso', False)):
            # Verificar si hay archivos de señal que indiquen finalización
            if os.path.exists(complete_signal):
                st.session_state['print_status'] = "✅ Impresión completada exitosamente"
                st.session_state['impresion_en_progreso'] = False
                try:
                    os.remove(complete_signal)  # Limpiar la señal
                except:
                    pass
                break
                
            if os.path.exists(error_signal):
                try:
                    with open(error_signal, 'r') as f:
                        error_info = f.read().strip()
                except:
                    error_info = "Error desconocido durante la impresión"
                
                st.session_state['print_status'] = f"❌ {error_info}"
                st.session_state['impresion_en_progreso'] = False
                try:
                    os.remove(error_signal)  # Limpiar la señal
                except:
                    pass
                break
            
            # Verificar timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                st.session_state['print_status'] = "⚠️ Tiempo de espera excedido, pero el proceso continúa en segundo plano."
                st.session_state['impresion_en_progreso'] = False
                printer_logger.warning(f"Tiempo de espera excedido al monitorear hilo de impresión {hilo.name}")
                break
                
            # Obtener el estado actual y actualizar el placeholder (sin duplicar mensajes)
            print_status = st.session_state.get('print_status', "⏳ Procesando...")
            status_placeholder.info(print_status)
            
            # Breve pausa para no sobrecargar la UI
            time.sleep(0.5)
        
        # Verificar estado final una vez que el hilo ha terminado
        final_status = st.session_state.get('print_status', "❓ Estado desconocido.")
        
        # Actualizar el placeholder una última vez con el estado final
        if "✅" in final_status:
            status_placeholder.success(final_status)
        elif "❌" in final_status:
            status_placeholder.error(final_status)
        else:
            status_placeholder.warning(final_status)
            
    except Exception as e:
        st.error(f"❌ Error durante el monitoreo del proceso: {str(e)}")
        printer_logger.exception("Error en monitorear_hilo_impresion")
        st.session_state['impresion_en_progreso'] = False

# Esta función ahora está en invoice_manager.py

def main():
    message_placeholder = st.empty()
    # Definición de las pestañas
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🧾Facturar", "🔍Ver Facturas", "✅Validar NIT", "😏Clientes", 
        "🔍Verificar Factura", "🔍Gestionar CUIS", "❌Anular/Revertir", "❌Revertir Anulacion"
    ])

    # Pestaña 2: Ver Facturas Generadas
    with tab2:
        st.header("Facturas Generadas")
        
        # Crear pestañas para diferentes estados de facturas
        facturas_tabs = st.tabs(["Todas", "Pendientes", "Validadas", "Anuladas"])
        
        with facturas_tabs[0]:
            mostrar_lista_facturas("TODAS")
        
        with facturas_tabs[1]:
            mostrar_lista_facturas("PENDIENTE")
            
        with facturas_tabs[2]:
            mostrar_lista_facturas("VALIDADA")
            
        with facturas_tabs[3]:
            mostrar_lista_facturas("ANULADA")
    
    # Pestaña 3: Validar NIT
    with tab3:
        st.header("Validar NIT")
        verifica_stream.main()
        
    # Pestaña 4: Lista de Clientes
    with tab4:
        st.header("Lista de Clientes")
        st.write("Aquí se mostrarán los clientes.")

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
        st.header("Gestionar CUIS")
        #st.write("Aquí puedes gestionar los códigos CUIS.")
        # Aquí podrías agregar la funcionalidad para gestionar CUIS
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
    numero_factura = get_next_invoice_number()
    logging.debug(f"Factura #: {numero_factura - 1}")
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
    numero_factura = get_next_invoice_number()

    ACTIVIDAD_ECONOMICA = os.getenv('ACTIVIDAD_ECONOMICA')
    CODIGO_PRODUCTO_SIN = os.getenv('CODIGO_PRODUCTO_SIN')

    

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

                        # Generar XML
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

                        # Firmar y validar XML
                        private_key_path = "xmls/llaves/private_key_ok.pem"
                        cert_path = "xmls/llaves/certificado_ok.pem"
                        signed_xml_str = sign_xml(xml_str, private_key_path, cert_path, cuf)

                        # Guardar XML firmado
                        filename = f"xmls/factura_{numero_factura}_{cuf}_.xml"
                        with open(filename, "w", encoding='utf-8') as signed_xml_file:
                            signed_xml_file.write(signed_xml_str)

                        # Validar y enviar
                        xsd_main_path = 'xmls/schemas/facturaElectronicaCompraVenta.xsd'
                        if validar_xml(filename, xsd_main_path):
                            gzip_path = comprimir_xml(filename)
                            hash_archivo = obtener_hash(gzip_path)
                            response = enviar_solicitud(filename, xsd_main_path, fecha_emision_str, cufd)

                            # Envío y procesamiento de la respuesta
                            if isinstance(response, dict) and response.get("error"):
                                message_placeholder.error(f"❌Error al enviar la factura: {response['error']}")
                            else:
                                try:
                                    # Usar el nuevo manejador de respuestas
                                    success, response_data = parse_siat_response(response.content)
                                    
                                    if success:
                                        # Mostrar la respuesta apropiadamente
                                        transaccion_exitosa = display_siat_response(response_data, message_placeholder)
                                        
                                        if transaccion_exitosa:
                                            # Almacenar datos en session_state
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
                                            }                                            # Guardar factura en base de datos
                                            # Asignar explícitamente tipoEmision=1 para factura online (normal)
                                            factura_cabecera_data['tipoEmision'] = "1"  # Tipo emisión online/normal
                                            
                                            is_valid, error_message = validar_factura_cabecera(factura_cabecera_data)
                                            if is_valid:
                                                guardar_factura_cabecera(factura_cabecera_data)
                                                increment_invoice_number(numero_factura)
                                            else:
                                                message_placeholder.error(error_message)
                                                return

                                            for detalle in detalles_data:
                                                is_valid, error_message = validar_factura_detalle(detalle)
                                                if is_valid:
                                                    guardar_factura_detalle(detalle)
                                                else:
                                                    message_placeholder.error(error_message)
                                                    return
                                    else:
                                        # El parser ya reportó el error
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
                            hilo_impresion = imprimir_en_hilo(
                                html_content,
                                st.session_state['cuf'],
                                os.getenv('NIT'),
                                st.session_state['ultima_factura']
                            )
                            
                            # Monitorear el estado del hilo
                            # La función de monitoreo ahora está incorporada en imprimir_en_hilo
                    except Exception as e:
                        st.session_state['print_status'] = f"❌ Error: {str(e)}"
                        st.session_state['impresion_en_progreso'] = False
                        printer_logger.exception("Error en el proceso de impresión")
                
                # Mostrar un botón para generar nueva factura si la impresión está completa o ha fallado
                if st.session_state.get('print_status') and not st.session_state.get('impresion_en_progreso', False):
                    if st.button("Generar Nueva Factura"):
                        reiniciar_estados()
                        # Usar st.rerun() en lugar de st.experimental_rerun()
                        st.rerun()
        
        with col3:
            if st.session_state.get('factura_validada'):
                nit_emisor = int(os.getenv('NIT'))
                enlace = generate_invoice_link(nit_emisor, st.session_state['cuf'], st.session_state['ultima_factura'])
                st.link_button("Consultar factura", enlace)

# Esta función ahora está en invoice_manager.py
    
    if __name__ == "__main__":
        initialize_print_state()
        main()