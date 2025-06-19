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

def canonicalize_xml(xml_str):
    """
    Devuelve la forma canónica (C14N) de un XML.
    
    Args:
        xml_str (str): Cadena XML a canonicalizar
        
    Returns:
        str: XML en forma canónica
    """
    xml_root = etree.fromstring(xml_str.encode('utf-8'))
    return etree.tostring(xml_root, method="c14n").decode()

def calculate_digest_base64(canonical_xml):
    """
    Calcula el hash SHA-256 en base64 de un XML canonicalizado.
    
    Args:
        canonical_xml (str): XML en forma canónica
        
    Returns:
        str: Hash en Base64
    """
    digest = hashes.Hash(hashes.SHA256())
    digest.update(canonical_xml.encode())
    hash_value = digest.finalize()
    return base64.b64encode(hash_value).decode()

def build_signature_element(digest_base64):
    """
    Construye el elemento Signature (sin SignatureValue ni KeyInfo).
    
    Args:
        digest_base64 (str): Hash en Base64 del XML
        
    Returns:
        Element: Elemento Signature construido
    """
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
    return signature

def sign_xml(xml_str, private_key_path, cert_path, cuf):
    """
    Firma digitalmente un documento XML utilizando el algoritmo RSA-SHA256.
    Optimizada para evitar redundancias y mejorar la mantenibilidad.
    
    Args:
        xml_str (str): Contenido del XML a firmar
        private_key_path (str): Ruta al archivo de clave privada
        cert_path (str): Ruta al archivo de certificado
        cuf (str): Código Único de Facturación
        
    Returns:
        str: XML firmado o None en caso de error
    """
    xml_logger.info("Iniciando proceso de firma del XML (optimizado)")
    xml_str = xml_str.replace('\r\n', '\n')

    try:
        # 1. Canonicalizar el XML original
        canonical_xml = canonicalize_xml(xml_str)
        xml_logger.info("XML canonicalizado exitosamente.")

        # 2. Calcular el digest en base64
        digest_base64 = calculate_digest_base64(canonical_xml)
        xml_logger.info(f"Digest (Base64): {digest_base64}")

        # 3. Construir el elemento Signature (sin SignatureValue ni KeyInfo)
        signature = build_signature_element(digest_base64)

        # 4. Insertar Signature en el XML (en memoria)
        xml_root = etree.fromstring(xml_str.encode('utf-8'))
        xml_root.append(signature)

        # 5. Canonicalizar SignedInfo
        si_element = signature.find(".//SignedInfo")
        si_canonicalized = etree.tostring(si_element, method="c14n").decode()
        xml_logger.info("SignedInfo canonicalizado correctamente.")

        # 6. Cargar clave privada y certificado solo una vez
        private_key = load_private_key(private_key_path)
        cert = load_certificate(cert_path)
        xml_logger.info("Clave privada y certificado cargados correctamente.")

        # 7. Firmar SignedInfo
        signature_value = private_key.sign(
            si_canonicalized.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signature_value_base64 = base64.b64encode(signature_value).decode()
        xml_logger.info("Firma digital generada correctamente.")

        # 8. Agregar SignatureValue
        signature_value_element = etree.SubElement(signature, "SignatureValue")
        signature_value_element.text = signature_value_base64

        # 9. Agregar KeyInfo y X509Certificate
        key_info = etree.SubElement(signature, "KeyInfo")
        x509_data = etree.SubElement(key_info, "X509Data")
        x509_cert = etree.SubElement(x509_data, "X509Certificate")
        cert_base64 = base64.b64encode(cert.public_bytes(encoding=serialization.Encoding.DER)).decode()
        x509_cert.text = cert_base64
        xml_logger.info("Información del certificado añadida al XML.")

        # 10. Obtener el XML firmado completo
        signed_xml = etree.tostring(xml_root, encoding='UTF-8', xml_declaration=True).decode()
        xml_logger.info(f"XML firmado generado exitosamente. Tamaño: {len(signed_xml)} bytes.")
        return signed_xml

    except Exception as e:
        xml_logger.error(f"Error en el proceso de firma optimizado: {e}")
        xml_logger.error(traceback.format_exc())
        return None

# Documentación:
# - Se modularizó el proceso de firma en funciones pequeñas y reutilizables.
# - Se centralizó la carga de la clave privada y el certificado.
# - Se eliminó el cálculo de hash redundante.
# - Se mejoró el manejo de errores y el logging.
# - El flujo sigue cumpliendo la normativa del SIN y es compatible con la funcionalidad existente.
