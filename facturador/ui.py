import streamlit as st
import streamlit.components.v1 as components
from data_access import (
    fetch_comandas, fetch_metodos_pago, fetch_tipos_documento, fetch_cliente, 
    fetch_random_leyenda, guardar_factura_cabecera, guardar_factura_detalle
)
from business_logic import calculate_totals, collect_product_lines
from invoice_xml_generator import generate_xml_invoice
from num2words import num2words
from database import SessionLocal
import models
from sqlalchemy.exc import IntegrityError
import re
from zeep import Client
from zeep.transports import Transport
import os
from dotenv import load_dotenv
from requests import Session
import time
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

# Lista de códigos permitidos para gift cards
gift_card_codes = [
    102, 109, 115, 120, 124, 128, 129, 130, 138, 146, 153, 159, 164, 168,
    172, 173, 174, 182, 189, 195, 200, 204, 208, 209, 210, 217, 221, 222,
    223, 224, 225, 226, 228, 232, 241, 246, 250, 254, 255, 256, 261, 265,
    269, 270, 271, 275, 279, 280, 281, 285, 286, 287, 291, 292, 293, 30,
    304, 35, 40, 49, 53, 60, 64, 68, 72, 76, 77, 78, 86, 94
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

def es_email_valido(email):
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
            return False, "❗ Verifica el NIT o elige otro Tipo de Documento."
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
        return f"Son {parte_entera_palabras} {parte_decimal:02d}/100 bolivianos"
    else:
        return f"Son {parte_entera_palabras} 00/100 bolivianos"

def generate_html_invoice(subtotal, descuento_adicional, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura, metodo_pago=None, codigo_clasificador_metodo_pago=None, tipo_documento=None, codigo_clasificador_documento=None, numero_documento=None, complemento=None, email=None, telefono=None, ultimos_digitos_tarjeta=None):
    total = subtotal - descuento_adicional
    total_final = total
    
    if codigo_clasificador_metodo_pago in gift_card_codes:
        monto_total_sujeto_iva = total - monto_giftcard
    else:
        monto_total_sujeto_iva = total

    total_en_palabras = numero_a_palabras_con_decimales_como_fraccion(total, lang='es') if total else ""

    leyenda = fetch_random_leyenda()

    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Factura</title>
        <style>
            body {{
                background-color: #000;
                color: white;
                font-family: Monospace, sans-serif;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #444;
            }}
        </style>
    </head>
    <body>
        <h2>Factura</h2>
        <h3>Fecha de Emisión: {fecha_emision}</h3>
        <h3>Número de Factura: {numero_factura}</h3>
    """
    if nombre_cliente:
        html_content += f"<h3>Razón Social: {nombre_cliente}</h3>"
    if email:
        html_content += f"<h3>Email: {email}</h3>"
    if telefono:
        html_content += f"<h3>Teléfono: {telefono}</h3>"

    html_content += """
        <table>
            <tr>
                <th>Codigo</th>
                <th>Cantidad</th>
                <th>Unidad</th>
                <th>Descripcion</th>
                <th>Precio Unitario</th>
                <th>Descuento</th>
                <th>Sub Total</th>
            </tr>
    """

    for linea in lineas_productos:
        html_content += f"""
            <tr>
                <td>{linea["codigo"]}</td>
                <td>{linea["cantidad"]}</td>
                <td>{linea["unidad"]}</td>
                <td>{linea["nombre"]}</td>
                <td>{linea["precio_venta"]}</td>
                <td>{linea.get("montoDescuento", 0)}</td>
                <td>{linea["sub_total"]}</td>
            </tr>
        """

    html_content += f"""
        </table>
        <h3>Subtotal: {subtotal:.2f}</h3>
        <h3>Descuento Adicional: {descuento_adicional:.2f}</h3>
        <h3>Gift Card: {monto_giftcard:.2f}</h3>
        <h3>Total Final: {total_final:.2f}</h3>
        <h3>Monto Total Sujeto a IVA: {monto_total_sujeto_iva:.2f}</h3>
        <h3>{total_en_palabras}</h3>
        <h3>{leyenda}</h3>
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

def save_or_fetch_client_data(codigo_cliente, codigo_tipo_documento_identidad, complemento, email, nombre_razon_social, numero_documento, telefono):
    if not nombre_razon_social:
        st.error("El campo 'Razón Social' es obligatorio.")
        return None

    if email and not es_email_valido(email):
        st.error("Por favor, ingrese un email válido.")
        return None

    if telefono and not es_telefono_valido(telefono):
        st.error("Por favor, ingrese un número de teléfono válido.")
        return None

    cliente_data, error = fetch_cliente(codigo_cliente)
    if error:
        session = SessionLocal()
        try:
            nuevo_cliente = models.Cliente(
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
            st.error("El cliente ya existe en la base de datos.")
            return None
        except Exception as e:
            session.rollback()
            st.error(f"Error al guardar los datos del cliente: {e}")
            return None
        finally:
            session.close()
    return cliente_data

def get_cufd():
    session = SessionLocal()
    try:
        cufd_record = session.query(models.Cufd).filter(models.Cufd.vigente == 1).first()
        if cufd_record:
            return cufd_record.codigo
        else:
            raise ValueError("CUFD no encontrado en la base de datos.")
    except Exception as e:
        raise ValueError(f"Error al obtener el CUFD: {e}")
    finally:
        session.close()

def verificar_y_obtener_cufd():
    session = SessionLocal()
    try:
        cufd_record = session.query(models.Cufd).filter(models.Cufd.vigente == 1).first()
        if cufd_record and cufd_record.fecha_vigencia > datetime.now():
            return cufd_record.codigo
        else:
            nuevo_cufd = solicitar_cufd()
            st.info("Se ha renovado el CUFD.")
            return nuevo_cufd
    except Exception as e:
        st.error(f"Error al verificar o solicitar CUFD: {e}")
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

def main():
    st.title("Facturador Electrónico")
    
    leyenda = fetch_random_leyenda()

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

    numero_documento = st.sidebar.text_input("Número de Documento:", key="numero_documento")
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
            email = st.sidebar.text_input("Email:", value=cliente_data['email'] if cliente_data['email'] else "", disabled=True)
            telefono = st.sidebar.text_input("Teléfono:", value=cliente_data['telefono'] if cliente_data['telefono'] else "", disabled=True)
            codigo_cliente = cliente_data['codigo_cliente']  # Set the codigo_cliente from existing data
        else:
            opciones_tipos_documento = [doc["descripcion"] for doc in tipos_documento]
            seleccion_tipo_documento = st.sidebar.selectbox("Tipo de Documento:", opciones_tipos_documento, index=2)
            tipo_documento_seleccionado = next((doc for doc in tipos_documento if doc["descripcion"] == seleccion_tipo_documento), None)
            if tipo_documento_seleccionado:
                codigo_clasificador_documento = tipo_documento_seleccionado["codigoClasificador"]
                if tipo_documento_seleccionado['codigoClasificador'] == '2':
                    complemento = st.sidebar.text_input("Complemento:", key="complemento")
                nombre_cliente = st.sidebar.text_input("Razón Social:", key="nombre_cliente")
                email = st.sidebar.text_input("Email:", key="email")
                telefono = st.sidebar.text_input("Teléfono:", key="telefono")

                if seleccion_tipo_documento == "NIT - NÚMERO DE IDENTIFICACIÓN TRIBUTARIA":
                    valido, mensaje = verificar_nit(numero_documento)
                    if valido:
                        st.success(f"NIT válido: {mensaje}")
                        nit_valido = True
                    else:
                        st.error(mensaje)
                        nit_valido = False

                guardar_cliente_button = st.sidebar.button("Guardar Cliente", key="guardar_cliente", disabled=(not nit_valido and seleccion_tipo_documento == "NIT - NÚMERO DE IDENTIFICACIÓN TRIBUTARIA"))
                if guardar_cliente_button:
                    if tipo_documento_seleccionado:
                        cliente_data = save_or_fetch_client_data(numero_documento, tipo_documento_seleccionado['codigoClasificador'], complemento, email, nombre_cliente, numero_documento, telefono)
                        if cliente_data:
                            st.success("Datos del cliente guardados o obtenidos correctamente.")
                            codigo_cliente = numero_documento  # Set codigo_cliente to numero_documento for new client
                    else:
                        st.error("Por favor selecciona un tipo de documento válido.")
    
    id_comanda_set = set(comanda["id_comanda"] for comanda in comandas)
    available_comandas = [comanda for comanda in id_comanda_set if comanda not in st.session_state.processed_comandas]

    selected_id_comanda = st.sidebar.multiselect("Selecciona las comandas", available_comandas, key="selected_comandas", placeholder="Selecciona la(s) comandas", help="Selecciona las comandas que deseas facturar.")

    st.sidebar.divider()

    opciones_metodos_pago = [metodo["descripcion"] for metodo in metodos_pago]

    indice_metodo_pago_predeterminado = next((i for i, metodo in enumerate(metodos_pago) if metodo["codigoClasificador"] == 1), 0)

    logging.debug(f"Opciones de métodos de pago: {opciones_metodos_pago}")
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
    
    if selected_id_comanda:
        comandas_seleccionadas = [comanda for comanda in comandas if comanda["id_comanda"] in selected_id_comanda]
        subtotal, descuento_aplicado, monto_giftcard, total, monto_total_sujeto_iva, monto_total_moneda = calculate_totals(
            comandas_seleccionadas, 
            descuento_adicional, 
            monto_giftcard, 
            codigo_clasificador_metodo_pago,
            tipo_cambio=1
        )
        lineas_productos = collect_product_lines(comandas, selected_id_comanda)
    else:
        comandas_seleccionadas = []
        subtotal, descuento_aplicado, monto_giftcard, total, monto_total_sujeto_iva, monto_total_moneda = 0, 0, 0, 0, 0, 0
        lineas_productos = []

    fecha_emision = datetime.now()
    fecha_emision_str = fecha_emision.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    numero_factura = get_next_invoice_number()

    ACTIVIDAD_ECONOMICA = os.getenv('ACTIVIDAD_ECONOMICA')
    CODIGO_PRODUCTO_SIN = os.getenv('CODIGO_PRODUCTO_SIN')

    html_invoice = generate_html_invoice(
        subtotal, 
        descuento_adicional, 
        monto_giftcard, 
        lineas_productos, 
        nombre_cliente, 
        fecha_emision_str, 
        numero_factura, 
        seleccion_metodo_pago, 
        codigo_clasificador_metodo_pago, 
        seleccion_tipo_documento, 
        codigo_clasificador_documento, 
        numero_documento, 
        complemento, 
        email, 
        telefono, 
        ultimos_digitos_tarjeta
    )

    components.html(html_invoice, height=600, scrolling=True)

    if st.button("Generar Factura en XML", key="generar_xml", disabled=not selected_id_comanda):
        if metodo_pago_seleccionado and seleccion_tipo_documento and numero_documento and selected_id_comanda:
            try:
                tipo_documento_seleccionado = next((doc for doc in tipos_documento if doc["descripcion"] == seleccion_tipo_documento), None)
                nit_emisor = int(os.getenv('NIT'))
                razon_social_emisor = os.getenv('RAZON_SOCIAL')
                municipio = os.getenv('MUNICIPIO')
                telefono = os.getenv('TELEFONO')
                cufd = verificar_y_obtener_cufd()
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

                lineas_productos = collect_product_lines(comandas, selected_id_comanda)
                
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

                filename = f"xmls/factura_{cuf}_.xml"
                with open(filename, "w", encoding='utf-8') as signed_xml_file:
                    signed_xml_file.write(signed_xml_str)

                xsd_main_path = 'xmls/schemas/facturaElectronicaCompraVenta.xsd'
                if validar_xml(filename, xsd_main_path):
                    gzip_path = comprimir_xml(filename)
                    hash_archivo = obtener_hash(gzip_path)
                    response = enviar_solicitud(filename, xsd_main_path, fecha_emision_str, cufd)

                    if isinstance(response, dict) and response.get("error"):
                        st.error(f"Error al enviar la factura: {response['error']}")
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
                                        st.success(f"""FACTURA {codigo_descripcion} :heavy_check_mark:\n 
                                        Código de recepción: {codigo_recepcion}\n Código de estado: {codigo_estado}\n
                                        """)

                                        is_valid, error_message = validar_factura_cabecera(factura_cabecera_data)
                                        if is_valid:
                                            guardar_factura_cabecera(factura_cabecera_data)
                                            increment_invoice_number(numero_factura)
                                        else:
                                            st.error(error_message)
                                            return

                                        for detalle in detalles_data:
                                            is_valid, error_message = validar_factura_detalle(detalle)
                                            if is_valid:
                                                guardar_factura_detalle(detalle)
                                            else:
                                                st.error(error_message)
                                                return

                                    else:
                                        mensajes_list = respuesta_servicio.find('mensajesList')
                                        error_message = "La factura no fue procesada correctamente."
                                        if mensajes_list is not None:
                                            for mensaje in mensajes_list:
                                                codigo = mensaje.find('codigo')
                                                descripcion = mensaje.find('descripcion')
                                                if codigo is not None and descripcion is not None:
                                                    error_message += f"\nCódigo: {codigo.text}, Descripción: {descripcion.text}"
                                            
                                            st.error(f"""{error_message}
                                                Código de recepción: {codigo_recepcion}\n
                                                Descripción: {codigo_descripcion}\n
                                                Estado: {codigo_estado}\n
                                            """)
                                        else:
                                            st.error("La respuesta del servicio no contiene todos los campos esperados.")
                                            st.write("Contenido de la respuesta:", response.content)
                                        
                                else:
                                    st.error("No se pudo encontrar RespuestaServicioFacturacion en la respuesta XML.")
                                    st.write("Contenido de la respuesta:", response.content)
                                    
                        except ET.ParseError as e:
                            st.error(f"Error al parsear la respuesta XML: {str(e)}")
                            st.write("Contenido de la respuesta:", response.content)

            except Exception as e:
                st.error(f"Error inesperado al procesar la respuesta: {str(e)}")
                if 'response' in locals():
                    st.write("Contenido de la respuesta:", response.content)
        else:
            st.error("Por favor, selecciona un método de pago, un tipo de documento y proporciona un número de documento válido para generar la factura en XML.")

if __name__ == "__main__":
    main()
