import os

#config.py

# Configuraciones generales del proyecto
ENDPOINT_URL = "http://127.0.0.1:8000/"
PDF_FOLDER_PATH = os.path.join(os.getcwd(), "pdfs")
XML_FOLDER_PATH = os.path.join(os.getcwd(), "xmls")
FILES_FOLDER_PATH = os.path.join(os.getcwd(), "files")
SIGNATURE_FILE_PATH = os.path.join(os.getcwd(), "files", "signature.pem")
XSDDOC_FILE_PATH = os.path.join(os.getcwd(), "files", "factura.xsd")