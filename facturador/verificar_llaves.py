from cryptography.hazmat.primitives import serialization
from cryptography import x509

def validar_cert_y_llave(cert_path, key_path):
    """
    Valida si el certificado y la llave privada corresponden al mismo par.
    Args:
        cert_path (str): Ruta al archivo .pem del certificado
        key_path (str): Ruta al archivo .pem de la llave privada
    Returns:
        bool: True si corresponden, False si no
    """
    with open(cert_path, "rb") as cert_file:
        cert = x509.load_pem_x509_certificate(cert_file.read())
        cert_public_key = cert.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    with open(key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
        private_public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    return cert_public_key == private_public_key

# Uso:
cert_path = r"C:\Users\Bernardo\Desktop\backapp\facturador\xmls\llaves\2025\certificado_ok.pem"
key_path = r"C:\Users\Bernardo\Desktop\backapp\facturador\xmls\llaves\2025\private_key_ok.pem"

if validar_cert_y_llave(cert_path, key_path):
    print("✅ El certificado y la llave privada SÍ corresponden.")
else:
    print("❌ El certificado y la llave privada NO corresponden.")