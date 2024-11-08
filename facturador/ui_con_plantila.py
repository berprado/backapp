import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import streamlit.components.v1 as components
from data_access import (
    fetch_comandas, fetch_metodos_pago, fetch_tipos_documento, fetch_cliente, 
    fetch_random_leyenda, guardar_factura_cabecera, guardar_factura_detalle, obtener_nombre_unidad_medida, obtener_motivos_anulacion
)
from business_logic import calculate_totals, collect_product_lines, generate_invoice_link, generate_qr
from invoice_xml_generator import generate_xml_invoice
from num2words import num2words
from database import SessionLocal
from facturador.models import Cufd, Cliente
from sqlalchemy.exc import IntegrityError
import re
from zeep import Client
from zeep.transports import Transport
from dotenv import load_dotenv
from requests import Session
from datetime import datetime
from generate_cuf import generate_cuf
from cufd import solicitar_cufd
from lxml import etree
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import base64
import hashlib
from zeeper import validar_xml, comprimir_xml, obtener_hash, enviar_solicitud
from decimal import Decimal
import logging
import traceback
import xml.etree.ElementTree as ET
from export import imprimir_recibo
import verifica_stream
from estado_factura import verificar_estado_factura
import cuis
from anulacion import anular_factura
from reversion import enviar_solicitud_reversion, procesar_respuesta_reversion, obtener_cuf_por_numero_factura
from invoice_templates import generate_html_invoice, generate_compact_html_invoice



# Lista de códigos permitidos para gift cards
gift_card_codes = [
    102, 109, 115, 120, 124, 128, 129, 130, 138, 146, 153, 159, 164, 168,
    172, 173, 174, 182, 189, 195, 200, 204, 208, 209, 210, 217, 221, 222,
    223, 224, 225, 226, 228, 232, 241, 246, 250, 254, 255, 256, 261, 265,
    269, 270, 271, 275, 279, 280, 281, 285, 286, 287, 291, 292, 293, 30,
    304, 35, 40, 49, 53, 60, 64, 68, 72, 76, 77, 78, 86, 94, 27
]

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='firma_log.txt',
        filemode='w'
    )


def es_email_valido(email, message_placeholder):
    patron = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(patron, email) is not None

def es_telefono_valido(telefono):
    return telefono.isdigit()

load_dotenv()

session = Session()
session.headers.update({'apikey': os.getenv('API_KEY')})

wsdl_url = os.getenv('WSDL_URL_CODIGOS')
client = Client(wsdl_url, transport=Transport(session=session))

def verificar_nit(nit):
    
    solicitud_verificar_nit = {
        'codigoAmbiente': os.getenv('CODIGO_AMBIENTE'),
        'codigoModalidad': os.getenv('CODIGO_MODALIDAD'),
        'codigoSistema': os.getenv('CODIGO_SISTEMA'),
        'codigoSucursal': os.getenv('CODIGO_SUCURSAL'),
        'cuis': os.getenv('CUIS'),
        'nit': os.getenv('NIT'),
        'nitParaVerificacion': nit
    }

    try:
        response = client.service.verificarNit(SolicitudVerificarNit=solicitud_verificar_nit)
        if response.transaccion:
            return True, response.mensajesList[0].descripcion
        else:
            return False, "Verifica el NIT o elige otro Tipo de Documento."
    except Exception as e:
        return False, f"Ocurrió un error: {str(e)}"

def validar_factura_cabecera(factura_cabecera_data):
    required_fields = [
        'nitEmisor', 'razonSocialEmisor', 'municipio', 'numeroFactura', 'cuf', 'cufd', 
        'codigoSucursal', 'direccion', 'fechaEmision', 'codigoTipoDocumentoIdentidad', 
        'numeroDocumento', 'codigoCliente', 'codigoMetodoPago', 'montoTotal', 'montoTotalSujetoIva', 
        'codigoMoneda', 'tipoCambio', 'montoTotalMoneda', 'leyenda', 'usuario', 'codigoDocumentoSector'
    ]
    
    for field in required_fields:
        if factura_cabecera_data.get(field) is None or factura_cabecera_data.get(field) == '':
            return False, f"El campo {field} es requerido y no puede estar vacío."
    
    return True, ""

def validar_factura_detalle(factura_detalle_data):
    required_fields = [
        'numeroFactura', 'actividadEconomica', 'codigoProductoSin', 'codigoProducto', 
        'descripcion', 'cantidad', 'unidadMedida', 'precioUnitario', 'subTotal'
    ]
    
    for field in required_fields:
        if factura_detalle_data.get(field) is None or factura_detalle_data.get(field) == '':
            return False, f"El campo {field} es requerido y no puede estar vacío."
    
    return True, ""

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

#factura en formato estandar
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
        <td class="tg-n17z" colspan="4"><span style="font-weight:bold">Fecha/Hora:</span> {fecha_emision}<br><span style="font-weight:bold">Nombre/Razón Social:</span> {nombre_cliente}</td>
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
        logging.warning("Archivo 'invoice_number.txt' no encontrado. Se creará uno nuevo con el número de factura inicial 0.")
        numero_factura = 0
    except ValueError as e:
        logging.error(f"Error de formato en 'invoice_number.txt': {e}")
        raise ValueError("El archivo 'invoice_number.txt' contiene un valor no válido.")
    except Exception as e:
        logging.error(f"Error inesperado al leer 'invoice_number.txt': {e}")
        raise e
    return numero_factura + 1

def increment_invoice_number(numero_factura):
    try:
        with open("invoice_number.txt", "w") as file:
            file.write(str(numero_factura))
    except Exception as e:
        logging.error(f"Error al escribir en 'invoice_number.txt': {e}")
        raise e

def save_or_fetch_client_data(codigo_cliente, codigo_tipo_documento_identidad, complemento, email, nombre_razon_social, numero_documento, telefono, message_placeholder):
    if not nombre_razon_social:
        message_placeholder.error("❌El campo 'Razón Social' es obligatorio.")
        return None

    if email and not es_email_valido(email, message_placeholder):
        message_placeholder.error("❌Por favor, ingrese un email válido.")
        return None

    if telefono and not es_telefono_valido(telefono):
        message_placeholder.error("❌Por favor, ingrese un número de teléfono válido.")
        return None

    cliente_data, error = fetch_cliente(codigo_cliente)
    if error:
        session = SessionLocal()
        try:
            nuevo_cliente = Cliente(
                codigo_cliente=numero_documento,  # Set codigo_cliente to numero_documento
                codigo_tipo_documento_identidad=codigo_tipo_documento_identidad,
                complemento=complemento,
                email=email if email else None,
                nombre_razon_social=nombre_razon_social,
                numero_documento=numero_documento,
                telefono=telefono if telefono else None
            )
            session.add(nuevo_cliente)
            session.commit()
            cliente_data = nuevo_cliente.to_dict()
        except IntegrityError:
            session.rollback()
            message_placeholder.error("❌El cliente ya existe en la base de datos.")
            return None
        except Exception as e:
            session.rollback()
            message_placeholder.error(f"❌Error al guardar los datos del cliente: {e}")
            return None
        finally:
            session.close()
    return cliente_data

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

def load_certificate(cert_path):
    with open(cert_path, 'rb') as file:
        return x509.load_pem_x509_certificate(file.read())

def calculate_hash(xml_str):
    hasher = hashlib.sha256()
    hasher.update(xml_str.encode('utf-8'))
    return hasher.hexdigest()

def sign_xml(xml_str, private_key_path, cert_path, cuf):
    logging.info("Iniciando proceso de firma del XML")
    xml_str = xml_str.replace('\r\n', '\n')

    original_hash = calculate_hash(xml_str)
    logging.info(f"Hash del XML original: {original_hash}")

    try:
        xml_root = etree.fromstring(xml_str.encode('utf-8'))
        canonical_xml = etree.tostring(xml_root, method="c14n").decode()
        logging.info("XML canonicalizado exitosamente.")
    except Exception as e:
        logging.error(f"Error al parsear o canonicalizar el XML: {e}")
        traceback.print_exc()
        return None

    try:
        digest = hashes.Hash(hashes.SHA256())
        digest.update(canonical_xml.encode())
        hash_value = digest.finalize()
        logging.info(f"Hash del XML: {hash_value.hex()}")
    except Exception as e:
        logging.error(f"Error al calcular el hash SHA256: {e}")
        traceback.print_exc()
        return None

    try:
        digest_base64 = base64.b64encode(hash_value).decode()
        logging.info(f"Hash del XML en Base64: {digest_base64}")
    except Exception as e:
        logging.error(f"Error al codificar el hash en Base64: {e}")
        traceback.print_exc()
        return None

    try:
        ds_ns = "http://www.w3.org/2000/09/xmldsig#"
        signature = etree.Element("{http://www.w3.org/2000/09/xmldsig#}Signature", nsmap={None: ds_ns})
        signed_info = etree.SubElement(signature, "SignedInfo", nsmap={})

        canonicalization_method = etree.SubElement(signed_info, "CanonicalizationMethod")
        canonicalization_method.set("Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315")

        signature_method = etree.SubElement(signed_info, "SignatureMethod")
        signature_method.set("Algorithm", "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256")

        reference = etree.SubElement(signed_info, "Reference")
        reference.set("URI", "")

        transforms = etree.SubElement(reference, "Transforms")
        transform = etree.SubElement(transforms, "Transform")
        transform.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#enveloped-signature")

        transform_with_comments = etree.SubElement(transforms, "Transform")
        transform_with_comments.set("Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315#WithComments")

        digest_method = etree.SubElement(reference, "DigestMethod")
        digest_method.set("Algorithm", "http://www.w3.org/2001/04/xmlenc#sha256")

        digest_value = etree.SubElement(reference, "DigestValue")
        digest_value.text = digest_base64

        xml_root.append(signature)
        logging.info("Etiquetas de signature añadidas al XML.")
    except Exception as e:
        logging.error(f"Error al adicionar las etiquetas de signature al XML: {e}")
        traceback.print_exc()
        return None

    try:
        signed_info_canonical = etree.tostring(signed_info, method="c14n").decode()
        logging.info("SignedInfo canonicalizado exitosamente.")
    except Exception as e:
        logging.error(f"Error al canonicalizar SignedInfo: {e}")
        traceback.print_exc()
        return None

    try:
        private_key = load_private_key(private_key_path)
        signature_value = private_key.sign(
            signed_info_canonical.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        logging.info("SignedInfo firmado exitosamente.")
    except Exception as e:
        logging.error(f"Error al firmar SignedInfo: {e}")
        traceback.print_exc()
        return None

    try:
        signature_value_base64 = base64.b64encode(signature_value).decode()
        logging.info(f"SignatureValue en Base64: {signature_value_base64}")
    except Exception as e:
        logging.error(f"Error al codificar SignatureValue en Base64: {e}")
        traceback.print_exc()
        return None

    try:
        signature_value_element = etree.SubElement(signature, "SignatureValue")
        signature_value_element.text = signature_value_base64
        logging.info("SignatureValue añadido al XML.")
    except Exception as e:
        logging.error(f"Error al adicionar SignatureValue al XML: {e}")
        traceback.print_exc()
        return None

    try:
        certificate = load_certificate(cert_path)
        key_info = etree.SubElement(signature, "KeyInfo")
        x509_data = etree.SubElement(key_info, "X509Data")
        x509_certificate = etree.SubElement(x509_data, "X509Certificate")
        x509_certificate.text = base64.b64encode(certificate.public_bytes(serialization.Encoding.DER)).decode()
        logging.info("X509Certificate añadido al XML.")
    except Exception as e:
        logging.error(f"Error al adicionar X509Certificate al XML: {e}")
        traceback.print_exc()
        return None

    try:
        signed_xml_str = etree.tostring(xml_root, xml_declaration=True, encoding='UTF-8').decode()

        signed_xml_root = etree.fromstring(signed_xml_str.encode('utf-8'))
        signature_element = signed_xml_root.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
        if signature_element is not None:
            signed_xml_root.remove(signature_element)
        else:
            return None

        signed_xml_canonical = etree.tostring(signed_xml_root, method="c14n").decode()
        signed_hash = calculate_hash(signed_xml_canonical)
        logging.info(f"Hash del XML firmado (sin nodo de firma): {signed_hash}")

        if signed_hash == hash_value.hex():
            logging.info("El XML no se ha modificado después de la firma.")
        else:
            logging.warning("El XML se ha modificado después de la firma.")

        return signed_xml_str
    except Exception as e:
        logging.error(f"Error al devolver el XML firmado: {e}")
        traceback.print_exc()
        return None


with open('verifica_stream.py', 'r') as file:
    file_content = file.read()
with open('cuis.py', 'r') as file:
    file_content += file.read()
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
    
    # Resto de la lógica relacionada con la barra lateral
    # (fetch_cliente, selectboxes, etc.)
    return numero_documento, nit_valido, nombre_cliente, complemento, email, telefono, seleccion_tipo_documento, codigo_clasificador_documento, codigo_clasificador_metodo_pago, ultimos_digitos_tarjeta, codigo_cliente

def main():
    message_placeholder = st.empty()
    # Definición de las pestañas
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🧾Facturar", "🔍Ver Facturas", "✅Validar NIT", "😏Clientes", 
        "🔍Verificar Factura", "🔍Gestionar CUIS", "❌Anular Factura", "❌Revertir Anulacion"
    ])

    # Pestaña 2: Ver Facturas Generadas
    with tab2:
        st.header("Facturas Generadas")
        st.write("Aquí se mostrarán las facturas generadas.")   
    
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
            nombre_cliente = st.sidebar.text_input("Razón Social:", value=cliente_data['nombre_razon_social'], disabled=True)

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
                    valido, mensaje = verificar_nit(numero_documento)
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
    fecha_emision_str = fecha_emision.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    numero_factura = get_next_invoice_number()

    ACTIVIDAD_ECONOMICA = os.getenv('ACTIVIDAD_ECONOMICA')
    CODIGO_PRODUCTO_SIN = os.getenv('CODIGO_PRODUCTO_SIN')
    
    

    # Asegurar que todas las variables necesarias estén definidas
    subtotal = subtotal if 'subtotal' in locals() else Decimal('0.00')
    descuento_adicional = descuento_adicional if 'descuento_adicional' in locals() else Decimal('0.00')
    monto_giftcard = monto_giftcard if 'monto_giftcard' in locals() else Decimal('0.00')
    lineas_productos = lineas_productos if 'lineas_productos' in locals() else []
    nombre_cliente = nombre_cliente if 'nombre_cliente' in locals() else "Nombre del Cliente"
    fecha_emision_str = fecha_emision_str if 'fecha_emision_str' in locals() else datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    numero_factura = numero_factura if 'numero_factura' in locals() else get_next_invoice_number()
    seleccion_metodo_pago = seleccion_metodo_pago if 'seleccion_metodo_pago' in locals() else "Método de Pago"
    codigo_clasificador_metodo_pago = codigo_clasificador_metodo_pago if 'codigo_clasificador_metodo_pago' in locals() else None
    seleccion_tipo_documento = seleccion_tipo_documento if 'seleccion_tipo_documento' in locals() else "Tipo de Documento"
    codigo_clasificador_documento = codigo_clasificador_documento if 'codigo_clasificador_documento' in locals() else None
    numero_documento = numero_documento if 'numero_documento' in locals() else "Documento"
    complemento = complemento if 'complemento' in locals() else ""
    email = email if 'email' in locals() else ""
    telefono = telefono if 'telefono' in locals() else ""
    ultimos_digitos_tarjeta = ultimos_digitos_tarjeta if 'ultimos_digitos_tarjeta' in locals() else ""

    with tab1:
    # Importar la función generate_html_invoice
        from invoice_templates import generate_html_invoice

    # Generar el contenido HTML de la factura utilizando generate_html_invoice
    html_invoice = generate_html_invoice(
        subtotal=subtotal,
        descuento_adicional=descuento_adicional,
        monto_giftcard=monto_giftcard,
        lineas_productos=lineas_productos,
        nombre_cliente=nombre_cliente,
        fecha_emision=fecha_emision_str,
        numero_factura=numero_factura,
        metodo_de_pago=seleccion_metodo_pago,
        codigo_clasificador_metodo_pago=codigo_clasificador_metodo_pago,
        tipo_documento=seleccion_tipo_documento,
        codigo_clasificador_documento=codigo_clasificador_documento,
        numero_documento=numero_documento,
        complemento=complemento,
        email=email,
        telefono=telefono,
        ultimos_digitos_tarjeta=ultimos_digitos_tarjeta
    )

    # Mostrar la vista previa de la factura en Tab 1
    components.html(html_invoice, height=700, scrolling=True)

    # Declaramos las columnas en el ámbito adecuado
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Facturar", key="generar_xml", help="Generar la factura", disabled=not selected_id_comanda):
            if metodo_pago_seleccionado and seleccion_tipo_documento and numero_documento and selected_id_comanda:
                try:
                    # ... Código para generar y enviar la factura ...
                    # Después de una generación exitosa:
                    st.session_state['factura_data'] = {
                        'subtotal': subtotal,
                        'descuento_adicional': descuento_adicional,
                        'monto_giftcard': monto_giftcard,
                        'lineas_productos': lineas_productos,
                        'nombre_cliente': nombre_cliente,
                        'fecha_emision_str': fecha_emision_str,
                        'numero_factura': numero_factura,
                        'seleccion_metodo_pago': seleccion_metodo_pago,
                        'codigo_clasificador_metodo_pago': codigo_clasificador_metodo_pago,
                        'seleccion_tipo_documento': seleccion_tipo_documento,
                        'codigo_clasificador_documento': codigo_clasificador_documento,
                        'numero_documento': numero_documento,
                        'complemento': complemento,
                        'email': email,
                        'telefono': telefono,
                        'ultimos_digitos_tarjeta': ultimos_digitos_tarjeta,
                        'cuf': cuf  # Asegúrate de incluir el CUF
                    }
                    st.session_state.factura_generada = True  # Indicar que la factura ha sido generada

                    message_placeholder.success(f":heavy_check_mark: FACTURA {codigo_descripcion}")

                except Exception as e:
                    message_placeholder.error(f"❌Error inesperado al procesar la respuesta: {str(e)}")
                    if 'response' in locals():
                        st.write("Contenido de la respuesta:", response.content)
            else:
                message_placeholder.error("❌Por favor, selecciona un método de pago, un tipo de documento y un número de documento válido para generar la factura.")

    # Mover el bloque de impresión fuera del if st.button("Facturar") y usar col2
    if st.session_state.get('factura_generada'):
        with col2:
            formato_impresion = st.radio(
                "Formato de impresión:",
                ("Normal", "Compacto (papel térmico)"),
                key="formato_impresion"
            )

            if st.button("Imprimir Factura"):
                factura_data = st.session_state.get('factura_data')
                if factura_data:
                    from invoice_templates import generate_html_invoice, generate_compact_html_invoice

                    if formato_impresion == "Normal":
                        html_content = generate_html_invoice(
                            **factura_data
                        )
                    else:
                        html_content = generate_compact_html_invoice(
                            **factura_data
                        )

                    # Generación del PDF
                    file_path, qr_base64 = imprimir_recibo(
                        html_content,
                        factura_data['cuf'],
                        os.getenv('NIT'),
                        factura_data['numero_factura']
                    )

                    # Lectura del PDF para la descarga
                    with open(file_path, "rb") as pdf_file:
                        PDFbyte = pdf_file.read()
                        st.download_button(
                            label=f"Descargar Factura ({formato_impresion})",
                            data=PDFbyte,
                            file_name=f"factura_{factura_data['numero_factura']}_{factura_data['cuf']}_.pdf",
                            mime='application/pdf'
                        )
                else:
                    st.error("No hay datos de factura disponibles. Por favor, genere una factura primero.")

    # Puedes usar col3 para otras acciones, como mostrar un enlace
    if st.session_state.get('factura_generada'):
        with col3:
            nit_emisor = factura_cabecera_data.get('nitEmisor')
            cuf = factura_cabecera_data.get('cuf')
            numero_factura = factura_cabecera_data.get('numeroFactura')

            if nit_emisor and cuf and numero_factura:
                enlace = generate_invoice_link(nit_emisor, cuf, numero_factura)
                st.markdown(f"[Consultar factura]({enlace})")
        # Importar la función generate_html_invoice
        from invoice_templates import generate_html_invoice

        # Generar el contenido HTML de la factura utilizando generate_html_invoice
        html_invoice = generate_html_invoice(
            subtotal=subtotal,
            descuento_adicional=descuento_adicional,
            monto_giftcard=monto_giftcard,
            lineas_productos=lineas_productos,
            nombre_cliente=nombre_cliente,
            fecha_emision=fecha_emision_str,
            numero_factura=numero_factura,
            metodo_de_pago=seleccion_metodo_pago,
            codigo_clasificador_metodo_pago=codigo_clasificador_metodo_pago,
            tipo_documento=seleccion_tipo_documento,
            codigo_clasificador_documento=codigo_clasificador_documento,
            numero_documento=numero_documento,
            complemento=complemento,
            email=email,
            telefono=telefono,
            ultimos_digitos_tarjeta=ultimos_digitos_tarjeta
        )

        # Mostrar la vista previa de la factura en Tab 1
        components.html(html_invoice, height=700, scrolling=True)

        
        col1, col2, col3 = st.columns(3)
        with col1:
         if st.button("Facturar", key="generar_xml", help="Generar la factura", disabled=not selected_id_comanda):
            if metodo_pago_seleccionado and seleccion_tipo_documento and numero_documento and selected_id_comanda:
                try:
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
                    fecha_emision_str = fecha_emision.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

                    lineas_productos = collect_product_lines(comandas, selected_id_comanda, db) 
                    
                    xml_str, factura_cabecera_data, detalles_data = generate_xml_invoice(
                        nit_emisor, 
                        razon_social_emisor,
                        municipio, 
                        telefono, 
                        numero_factura, 
                        cuf, 
                        cufd,
                        codigo_sucursal, 
                        direccion, 
                        codigo_punto_venta, 
                        fecha_emision_str, 
                        nombre_cliente,
                        tipo_documento_seleccionado['codigoClasificador'], 
                        numero_documento,
                        complemento, 
                        numero_documento, 
                        metodo_pago_seleccionado['codigoClasificador'], 
                        ultimos_digitos_tarjeta,
                        subtotal,
                        total,
                        1,
                        1,
                        total / 1,
                        monto_giftcard, 
                        descuento_adicional,
                        "don_bercho", 
                        codigo_documento_sector, 
                        lineas_productos,
                        ACTIVIDAD_ECONOMICA, 
                        CODIGO_PRODUCTO_SIN
                    )

                    private_key_path = "xmls/llaves/private_key_ok.pem"
                    cert_path = "xmls/llaves/certificado_ok.pem"
                    
                    signed_xml_str = sign_xml(xml_str, private_key_path, cert_path, cuf)

                    filename = f"xmls/factura_{numero_factura}_{cuf}_.xml"
                    with open(filename, "w", encoding='utf-8') as signed_xml_file:
                        signed_xml_file.write(signed_xml_str)

                    xsd_main_path = 'xmls/schemas/facturaElectronicaCompraVenta.xsd'
                    if validar_xml(filename, xsd_main_path):
                        gzip_path = comprimir_xml(filename)
                        hash_archivo = obtener_hash(gzip_path)
                        response = enviar_solicitud(filename, xsd_main_path, fecha_emision_str, cufd)

                        if isinstance(response, dict) and response.get("error"):
                            message_placeholder.error(f"❌Error al enviar la factura: {response['error']}")
                        else:
                            try:
                                root = ET.fromstring(response.content)
                                ns = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/', 'ns2': 'https://siat.impuestos.gob.bo/'}

                                respuesta_servicio = root.find('.//RespuestaServicioFacturacion')
                                
                                if respuesta_servicio is not None:
                                    codigo_descripcion = respuesta_servicio.find('codigoDescripcion')
                                    codigo_estado = respuesta_servicio.find('codigoEstado')
                                    codigo_recepcion = respuesta_servicio.find('codigoRecepcion')
                                    transaccion = respuesta_servicio.find('transaccion')
                                    
                                    if all([codigo_descripcion is not None, codigo_estado is not None, 
                                            codigo_recepcion is not None, transaccion is not None]):
                                        
                                        codigo_descripcion = codigo_descripcion.text
                                        codigo_estado = codigo_estado.text
                                        codigo_recepcion = codigo_recepcion.text
                                        transaccion = transaccion.text.lower() == 'true'
                                        
                                        if transaccion:
                                            message_placeholder.success(f""":heavy_check_mark: FACTURA {codigo_descripcion}""")

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

                                            # Almacenar los datos de la factura en st.session_state
                                                st.session_state['factura_data'] = {
                                                    'subtotal': subtotal,
                                                    'descuento_adicional': descuento_adicional,
                                                    'monto_giftcard': monto_giftcard,
                                                    'lineas_productos': lineas_productos,
                                                    'nombre_cliente': nombre_cliente,
                                                    'fecha_emision_str': fecha_emision_str,
                                                    'numero_factura': numero_factura,
                                                    'seleccion_metodo_pago': seleccion_metodo_pago,
                                                    'codigo_clasificador_metodo_pago': codigo_clasificador_metodo_pago,
                                                    'seleccion_tipo_documento': seleccion_tipo_documento,
                                                    'codigo_clasificador_documento': codigo_clasificador_documento,
                                                    'numero_documento': numero_documento,
                                                    'complemento': complemento,
                                                    'email': email,
                                                    'telefono': telefono,
                                                    'ultimos_digitos_tarjeta': ultimos_digitos_tarjeta,
                                                    'cuf': cuf
                                                }

                                           

                                            # Lectura del PDF para la descarga
                                            with col2:
                                                formato_impresion = st.radio(
                                                    "Formato de impresión:",
                                                    ("Normal", "Compacto (papel térmico)"),
                                                    key="formato_impresion1"
                                                )

                                                if st.button("Imprimir Factura"):
                                                    factura_data = st.session_state.get('factura_data')
                                                    if factura_data:
                                                        # Utilizamos las funciones de invoice_templates.py
                                                        
                                                        if formato_impresion == "Normal":
                                                            html_content = generate_html_invoice(
                                                                **factura_data
                                                            )
                                                        else:  # Formato Compacto
                                                            html_content = generate_compact_html_invoice(
                                                                **factura_data
                                                            )

                                                        # Generación del PDF
                                                        file_path, qr_base64 = imprimir_recibo(
                                                            html_content,
                                                            factura_data['cuf'], 
                                                            os.getenv('NIT'), 
                                                            factura_data['numero_factura']
                                                        )

                                                        # Lectura del PDF para la descarga
                                                        with open(file_path, "rb") as pdf_file:
                                                            PDFbyte = pdf_file.read()
                                                            st.download_button(
                                                                label=f"Descargar Factura ({formato_impresion})",
                                                                data=PDFbyte,
                                                                file_name=f"factura_{factura_data['numero_factura']}_{factura_data['cuf']}_.pdf",
                                                                mime='application/pdf'
                                                            )
                                                    else:
                                                        st.error("No hay datos de factura disponibles. Por favor, genere una factura primero.")

                                                

                                                

                                                        # Lectura del PDF para la descarga
                                                        with open(file_path, "rb") as pdf_file:
                                                            PDFbyte = pdf_file.read()
                                                            st.download_button(
                                                                label=f"Descargar Factura ({formato_impresion})",
                                                                data=PDFbyte,
                                                                file_name=f"factura_{numero_factura}_{cuf}_.pdf",
                                                                mime='application/pdf'
                                                            )


                                            nit_emisor = factura_cabecera_data.get('nitEmisor')
                                            cuf = factura_cabecera_data.get('cuf')
                                            numero_factura = factura_cabecera_data.get('numeroFactura')
                                            
                                            
                                            #enlace a la factura en el portal de impuestos
                                            
                                            with col3:
                                                if nit_emisor and cuf and numero_factura:
                                                    enlace = generate_invoice_link(nit_emisor, cuf, numero_factura)
                                                    st.link_button("Consultar factura", enlace)
                                        else:
                                            mensajes_list = respuesta_servicio.find('mensajesList')
                                            error_message = "❌La factura no fue procesada correctamente."
                                            if mensajes_list is not None:
                                                for mensaje in mensajes_list:
                                                    codigo = mensaje.find('codigo')
                                                    descripcion = mensaje.find('descripcion')
                                                    if codigo is not None and descripcion is not None:
                                                        error_message += f"\nCódigo: {codigo.text}, Descripción: {descripcion.text}"
                                                
                                                message_placeholder.error(f"""{error_message}
                                                    Código de recepción: {codigo_recepcion}\n
                                                    Descripción: {codigo_descripcion}\n
                                                    Estado: {codigo_estado}\n
                                                """)
                                            else:
                                                message_placeholder.error("❌La respuesta del servicio no contiene todos los campos esperados.")
                                                st.write("Contenido de la respuesta:", response.content)
                                            
                                    else:
                                        message_placeholder.error("❌No se pudo encontrar RespuestaServicioFacturacion en la respuesta XML.")
                                        st.write("Contenido de la respuesta:", response.content)
                                        
                            except ET.ParseError as e:
                                message_placeholder.error(f"❌Error al parsear la respuesta XML: {str(e)}")
                                st.write("Contenido de la respuesta:", response.content)

                except Exception as e:
                    message_placeholder.error(f"❌Error inesperado al procesar la respuesta: {str(e)}")
                    if 'response' in locals():
                        st.write("Contenido de la respuesta:", response.content)
            else:
                message_placeholder.error("❌Por favor, selecciona un método de pago, un tipo de documento y un número de documento válido para generar la factura.")


if __name__ == "__main__":
    main()
    



