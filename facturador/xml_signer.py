"""
Módulo para la firma de archivos XML de facturas.

Este módulo contiene funciones para calcular el hash de un XML, firmarlo digitalmente
y prepararlo para su envío a los servicios del SIN.
"""

import base64
import hashlib
import traceback
import logging
from lxml import etree
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
from logger_config import get_xml_logger

# Configuración de logger
xml_logger = get_xml_logger()

def load_certificate(cert_path):
    """
    Carga un certificado desde un archivo PEM.
    
    Args:
        cert_path (str): Ruta al archivo de certificado
        
    Returns:
        Certificate: Objeto de certificado cargado
    """
    with open(cert_path, 'rb') as file:
        return x509.load_pem_x509_certificate(file.read())

def load_private_key(private_key_path, password=None):
    """
    Carga una clave privada desde un archivo PEM.
    
    Args:
        private_key_path (str): Ruta al archivo de clave privada
        password (bytes, optional): Contraseña para descifrar la clave
        
    Returns:
        PrivateKey: Objeto de clave privada cargado
    """
    with open(private_key_path, 'rb') as key_file:
        return serialization.load_pem_private_key(
            key_file.read(),
            password=password
        )

def calculate_hash(xml_str):
    """
    Calcula el hash SHA-256 de una cadena XML.
    
    Args:
        xml_str (str): Cadena XML a hashear
        
    Returns:
        str: Hash hexadecimal
    """
    hasher = hashlib.sha256()
    hasher.update(xml_str.encode('utf-8'))
    return hasher.hexdigest()

def sign_xml(xml_str, private_key_path, cert_path, cuf):
    """
    Firma digitalmente un documento XML utilizando el algoritmo RSA-SHA256.
    
    Args:
        xml_str (str): Contenido del XML a firmar
        private_key_path (str): Ruta al archivo de clave privada
        cert_path (str): Ruta al archivo de certificado
        cuf (str): Código Único de Facturación
        
    Returns:
        str: XML firmado o None en caso de error
    """
    xml_logger.info("Iniciando proceso de firma del XML")
    xml_str = xml_str.replace('\r\n', '\n')

    original_hash = calculate_hash(xml_str)
    xml_logger.info(f"Hash del XML original: {original_hash}")

    try:
        xml_root = etree.fromstring(xml_str.encode('utf-8'))
        canonical_xml = etree.tostring(xml_root, method="c14n").decode()
        xml_logger.info("XML canonicalizado exitosamente.")
    except Exception as e:
        xml_logger.error(f"Error al parsear o canonicalizar el XML: {e}")
        xml_logger.error(traceback.format_exc())
        return None

    try:
        digest = hashes.Hash(hashes.SHA256())
        digest.update(canonical_xml.encode())
        hash_value = digest.finalize()
        xml_logger.info(f"Hash del XML: {hash_value.hex()}")
    except Exception as e:
        xml_logger.error(f"Error al calcular el hash SHA256: {e}")
        xml_logger.error(traceback.format_exc())
        return None

    try:
        digest_base64 = base64.b64encode(hash_value).decode()
        xml_logger.info(f"Hash del XML en Base64: {digest_base64}")
    except Exception as e:
        xml_logger.error(f"Error al codificar el hash en Base64: {e}")
        xml_logger.error(traceback.format_exc())
        return None

    try:
        ds_ns = "http://www.w3.org/2000/09/xmldsig#"
        signature = etree.Element("{http://www.w3.org/2000/09/xmldsig#}Signature", nsmap={None: ds_ns})
        signed_info = etree.SubElement(signature, "SignedInfo", nsmap={})

        canonicalization_method = etree.SubElement(signed_info, "CanonicalizationMethod")
        # Corregir la URL del algoritmo de canonicalización (faltaba el "3" después de "w")
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
        xml_logger.info("Etiquetas de signature añadidas al XML.")
    except Exception as e:
        xml_logger.error(f"Error al adicionar las etiquetas de signature al XML: {e}")
        xml_logger.error(traceback.format_exc())
        return None

    # Firmar el XML con la clave privada
    try:
        # Obtener el XML con las etiquetas de signature incluidas
        xml_with_signature_tags = etree.tostring(xml_root, encoding='UTF-8', xml_declaration=True).decode()
        xml_logger.info("XML con etiquetas de firma generado correctamente.")
        
        # Canonicalizar el XML con las etiquetas de signature
        si_element = signature.find(".//SignedInfo")
        if si_element is None:
            xml_logger.error("No se encontró el elemento SignedInfo en el XML")
            return None
        
        si_canonicalized = etree.tostring(si_element, method="c14n").decode()
        xml_logger.info("SignedInfo canonicalizado correctamente.")
        
        # Cargar la clave privada
        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
        xml_logger.info("Clave privada cargada correctamente.")
        
        # Firmar el contenido de SignedInfo con la clave privada
        signature_value = private_key.sign(
            si_canonicalized.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signature_value_base64 = base64.b64encode(signature_value).decode()
        xml_logger.info("Firma digital generada correctamente.")
        
        # Agregar el valor de firma al XML
        signature_value_element = etree.SubElement(signature, "SignatureValue")
        signature_value_element.text = signature_value_base64
        
        # Agregar información sobre la clave
        key_info = etree.SubElement(signature, "KeyInfo")
        
        # Agregar información X509
        x509_data = etree.SubElement(key_info, "X509Data")
        
        # Leer el certificado y agregar su valor
        with open(cert_path, "rb") as cert_file:
            cert_content = cert_file.read()
            cert = x509.load_pem_x509_certificate(cert_content)
            
        x509_cert = etree.SubElement(x509_data, "X509Certificate")
        cert_base64 = base64.b64encode(cert.public_bytes(encoding=serialization.Encoding.DER)).decode()
        x509_cert.text = cert_base64
        xml_logger.info("Información del certificado añadida al XML.")

        # Obtener el XML firmado completo
        signed_xml = etree.tostring(xml_root, encoding='UTF-8', xml_declaration=True).decode()
        xml_logger.info(f"XML firmado generado exitosamente. Tamaño: {len(signed_xml)} bytes.")
        
        return signed_xml
    
    except Exception as e:
        xml_logger.error(f"Error al firmar el XML: {e}")
        xml_logger.error(traceback.format_exc())
        return None
