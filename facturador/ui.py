import streamlit as st
import streamlit.components.v1 as components
from data_access import fetch_comandas, fetch_metodos_pago, fetch_tipos_documento, fetch_cliente
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
from prueba import generate_txt_file
from generate_cuf import generate_cuf
from cufd import solicitar_cufd
from lxml import etree
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import base64
import hashlib
from zeeper import validar_xml, comprimir_xml, obtener_hash, enviar_solicitud

import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='firma_log.txt', filemode='w')

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

def generate_html_invoice(total, descuento, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision, numero_factura, metodo_pago=None, codigo_clasificador_metodo_pago=None, tipo_documento=None, codigo_clasificador_documento=None, numero_documento=None, complemento=None, email=None, telefono=None, ultimos_digitos_tarjeta=None):
    total_final = total - descuento - monto_giftcard
    total_en_palabras = num2words(total_final, lang='es').capitalize() if total_final else ""

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
    if lineas_productos:
        for linea in lineas_productos:
            codigo = linea.get('codigo', 'Cod')
            unidad = linea.get('unidad', 'Unid')
            html_content += f"""
                <tr>
                    <td>{codigo}</td>
                    <td>{linea['cantidad']}</td>
                    <td>{unidad}</td>
                    <td>{linea['nombre']}</td>
                    <td>{linea['precio_venta']}</td>
                    <td>0</td>
                    <td>{linea['sub_total']}</td>
                </tr>
            """
    else:
        html_content += """
            <tr>
                <td colspan="7">No hay productos seleccionados.</td>
            </tr>
        """

    html_content += f"""
        </table>
        <h2>Total: {total:.2f}</h2>
        <h3>Descuento: {descuento:.2f}</h3>
        <h3>Gift Card: {monto_giftcard:.2f}</h3>
        <h3>Total Final: {total_final:.2f}</h3>
        <h3>Son: {total_en_palabras} boliviano</h3>
    """

    if metodo_pago:
        html_content += f"<h3>Método de Pago: {metodo_pago.capitalize()}</h3>"
    if codigo_clasificador_metodo_pago:
        html_content += f"<h3>Código Clasificador del Método de Pago: {codigo_clasificador_metodo_pago}</h3>"
    if ultimos_digitos_tarjeta:
        html_content += f"<h3>Últimos 4 Dígitos de la Tarjeta: {ultimos_digitos_tarjeta}</h3>"
    if tipo_documento:
        html_content += f"<h3>Tipo de Documento: {tipo_documento}</h3>"
    if codigo_clasificador_documento:
        html_content += f"<h3>Código Clasificador del Documento: {codigo_clasificador_documento}</h3>"
    if numero_documento:
        html_content += f"<h3>Número de Documento: {numero_documento}</h3>"
    if complemento:
        html_content += f"<h3>Complemento: {complemento}</h3>"

    html_content += """
    </body>
    </html>
    """
    return html_content

def get_next_invoice_number():
    try:
        with open("invoice_number.txt", "r") as file:
            numero_factura = int(file.read().strip()) + 1
    except FileNotFoundError:
        numero_factura = 0
    return numero_factura

def increment_invoice_number(numero_factura):
    with open("invoice_number.txt", "w") as file:
        file.write(str(numero_factura))

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
                codigo_cliente=codigo_cliente,
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

    # Calcular el hash del XML original
    original_hash = calculate_hash(xml_str)
    logging.info(f"Hash del XML original: {original_hash}")

    # Paso 1: Canonicalización del XML completo
    try:
        xml_root = etree.fromstring(xml_str.encode('utf-8'))
        canonical_xml = etree.tostring(xml_root, method="c14n").decode()
        logging.info("XML canonicalizado exitosamente.")
    except Exception as e:
        logging.error(f"Error al parsear o canonicalizar el XML: {e}")
        traceback.print_exc()
        return None

    # Paso 2: Cálculo del Hash SHA256
    try:
        digest = hashes.Hash(hashes.SHA256())
        digest.update(canonical_xml.encode())
        hash_value = digest.finalize()
        logging.info(f"Hash del XML: {hash_value.hex()}")
    except Exception as e:
        logging.error(f"Error al calcular el hash SHA256: {e}")
        traceback.print_exc()
        return None

    # Paso 3: Codificación en Base64
    try:
        digest_base64 = base64.b64encode(hash_value).decode()
        logging.info(f"Hash del XML en Base64: {digest_base64}")
    except Exception as e:
        logging.error(f"Error al codificar el hash en Base64: {e}")
        traceback.print_exc()
        return None

    # Paso 4: Adicionar las etiquetas de signature al XML
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

    # Paso 5: Agregar a la etiqueta DigestValue el valor obtenido en el paso 3
    # Ya realizado en el paso 4

    # Paso 6: Canonicalización de SignedInfo
    try:
        signed_info_canonical = etree.tostring(signed_info, method="c14n").decode()
        logging.info("SignedInfo canonicalizado exitosamente.")
    except Exception as e:
        logging.error(f"Error al canonicalizar SignedInfo: {e}")
        traceback.print_exc()
        return None

    # Paso 7: Firmar SignedInfo
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

    # Paso 8: Codificación de la firma en Base64
    try:
        signature_value_base64 = base64.b64encode(signature_value).decode()
        logging.info(f"SignatureValue en Base64: {signature_value_base64}")
    except Exception as e:
        logging.error(f"Error al codificar SignatureValue en Base64: {e}")
        traceback.print_exc()
        return None

    # Paso 9: Adicionar a la etiqueta de SignatureValue la cadena anterior
    try:
        signature_value_element = etree.SubElement(signature, "SignatureValue")
        signature_value_element.text = signature_value_base64
        logging.info("SignatureValue añadido al XML.")
    except Exception as e:
        logging.error(f"Error al adicionar SignatureValue al XML: {e}")
        traceback.print_exc()
        return None

    # Paso 10: Colocar en la etiqueta X509Certificate la llave pública
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

    # Paso 11: Devolver el XML firmado
    try:
        signed_xml_str = etree.tostring(xml_root, xml_declaration=True, encoding='UTF-8').decode()
        logging.info(f"XML firmado:\n{signed_xml_str}")

        # Calcular el hash del XML firmado (sin el nodo de firma)
        signed_xml_root = etree.fromstring(signed_xml_str.encode('utf-8'))
        signature_element = signed_xml_root.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
        if signature_element is not None:
            signed_xml_root.remove(signature_element)
        else:
            logging.error("No se encontró el elemento Signature para remover.")
            return None

        signed_xml_canonical = etree.tostring(signed_xml_root, method="c14n").decode()
        signed_hash = calculate_hash(signed_xml_canonical)
        logging.info(f"Hash del XML firmado (sin nodo de firma): {signed_hash}")

        if original_hash == signed_hash:
            logging.info("El XML no se ha modificado después de la firma.")
        else:
            logging.warning("El XML se ha modificado después de la firma.")

        return signed_xml_str
    except Exception as e:
        logging.error(f"Error al devolver el XML firmado: {e}")
        traceback.print_exc()
        return None

def main():
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
                    else:
                        st.error("Por favor selecciona un tipo de documento válido.")
    
    id_comanda_set = set(comanda["id_comanda"] for comanda in comandas)
    available_comandas = [comanda for comanda in id_comanda_set if comanda not in st.session_state.processed_comandas]

    selected_id_comanda = st.sidebar.multiselect("Selecciona las comandas", available_comandas, key="selected_comandas", placeholder="Selecciona la(s) comandas", help="Selecciona las comandas que deseas facturar.")

    st.sidebar.divider()

    opciones_metodos_pago = [metodo["descripcion"] for metodo in metodos_pago]
    seleccion_metodo_pago = st.sidebar.selectbox("Tipo de Pago:", opciones_metodos_pago, index=66, key="metodo_pago")
    metodo_pago_seleccionado = next((metodo for metodo in metodos_pago if metodo["descripcion"] == seleccion_metodo_pago), None)

    if metodo_pago_seleccionado:
        codigo_clasificador_metodo_pago = metodo_pago_seleccionado["codigoClasificador"]

    if seleccion_metodo_pago == "TARJETA":
        ultimos_digitos_tarjeta = st.sidebar.text_input("Ingresa los últimos 4 dígitos de la tarjeta:", max_chars=4, key="ultimos_digitos_tarjeta")

    on = st.sidebar.checkbox("Aplicar Descuento")

    if on:
        descuento = st.sidebar.number_input("Descuento:", min_value=0, step=5, key="descuento")
        monto_giftcard = st.sidebar.number_input("Gift Card:", min_value=0, step=5, key="monto_giftcard")
    else:
        descuento = 0.00
        monto_giftcard = 0.00

    if selected_id_comanda:
        comandas_seleccionadas = [comanda for comanda in comandas if comanda["id_comanda"] in selected_id_comanda]
        total, descuento_aplicado, _ = calculate_totals(comandas_seleccionadas)
        lineas_productos = collect_product_lines(comandas, selected_id_comanda)
    else:
        comandas_seleccionadas = []
        total, descuento_aplicado = 0, 0
        lineas_productos = []

    total_final = total - descuento - monto_giftcard

    fecha_emision = datetime.now()
    fecha_emision_str = fecha_emision.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    numero_factura = get_next_invoice_number()

    html_invoice = generate_html_invoice(total, descuento, monto_giftcard, lineas_productos, nombre_cliente, fecha_emision_str, numero_factura, seleccion_metodo_pago, codigo_clasificador_metodo_pago, seleccion_tipo_documento, codigo_clasificador_documento, numero_documento, complemento, email, telefono, ultimos_digitos_tarjeta)

    components.html(html_invoice, height=600, scrolling=True)

    if st.button("Generar Factura en XML", key="generar_xml", disabled=not selected_id_comanda):
        if metodo_pago_seleccionado and seleccion_tipo_documento and numero_documento:
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
                cuf = generate_cuf(nit_emisor, fecha_emision, codigo_sucursal, int(os.getenv('CODIGO_MODALIDAD')),
                                   int(os.getenv('CODIGO_TIPO_EMISION')), int(os.getenv('CODIGO_TIPO_FACTURA')),
                                   codigo_documento_sector, numero_factura,
                                   codigo_punto_venta)
                fecha_emision_str = fecha_emision.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

                xml_str = generate_xml_invoice(
                    nit_emisor, razon_social_emisor, municipio, telefono, numero_factura, cuf, cufd,
                    codigo_sucursal, direccion, codigo_punto_venta, fecha_emision_str, nombre_cliente,
                    tipo_documento_seleccionado['codigoClasificador'], numero_documento,
                    complemento, numero_documento, metodo_pago_seleccionado['codigoClasificador'], ultimos_digitos_tarjeta,
                    total, total, 1, 1, total, monto_giftcard, descuento,
                    "Ley N° 453: Tienes derecho a recibir información sobre las características y contenidos de los servicios que utilices.",
                    "don_bercho", codigo_documento_sector, lineas_productos
                )

                private_key_path = "xmls/llaves/private_key_ok.pem"
                cert_path = "xmls/llaves/certificado_ok.pem"
                
                #signed_xml_str = sign_xml(xml_str, private_key_path, cert_path)
                signed_xml_str = sign_xml(xml_str, private_key_path, cert_path, cuf)


                filename = f"xmls/factura_{cuf}_.xml"
                with open(filename, "w", encoding='utf-8') as signed_xml_file:
                    signed_xml_file.write(signed_xml_str)

                # Validar, comprimir, obtener hash y enviar el XML firmado
                xsd_main_path = 'xmls/schemas/facturaElectronicaCompraVenta.xsd'
                if validar_xml(filename, xsd_main_path):
                    gzip_path = comprimir_xml(filename)
                    hash_archivo = obtener_hash(gzip_path)
                    enviar_solicitud(filename, xsd_main_path, fecha_emision_str, cufd)
                else:
                    st.error("El XML no es válido según el esquema XSD.")

                st.session_state.processed_comandas.extend(selected_id_comanda)
                increment_invoice_number(numero_factura)
                st.success("Factura generada, firmada y enviada exitosamente.")
            except Exception as e:
                st.error(f"Error al generar la factura: {e}")
        else:
            st.error("Por favor, selecciona un método de pago, un tipo de documento y proporciona un número de documento válido para generar la factura en XML.")

if __name__ == "__main__":
    main()
