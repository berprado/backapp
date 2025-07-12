"""
Módulo para la validación de datos en el sistema de facturación.

Este módulo contiene funciones para validar datos de entrada como email,
teléfonos, NIT, así como los datos de factura cabecera y detalle.
"""

import re
import os
from dotenv import load_dotenv
import logging
from logger_config import get_logger
from api_clients import get_soap_client

# Cargar variables de entorno
load_dotenv()
logger = get_logger()

def es_email_valido(email, message_placeholder=None):
    """
    Verifica que un email tenga un formato válido.
    
    Args:
        email (str): Email a validar
        message_placeholder: Objeto para mostrar mensajes de error (opcional)
    
    Returns:
        bool: True si el email es válido, False en caso contrario
    """
    patron = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(patron, email) is not None

def es_telefono_valido(telefono):
    """
    Verifica que un número de teléfono contenga solo dígitos.
    
    Args:
        telefono (str): Número de teléfono a validar
    
    Returns:
        bool: True si el teléfono contiene solo dígitos, False en caso contrario
    """
    return telefono.isdigit()

def validar_factura_cabecera(factura_cabecera_data):
    """
    Valida que los campos requeridos en la cabecera de factura estén presentes.
    
    Args:
        factura_cabecera_data (dict): Datos de la cabecera de factura
    
    Returns:
        tuple: (bool, str) donde bool indica si la validación fue exitosa
               y str contiene un mensaje de error en caso de fallo
    """
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
    """
    Valida que los campos requeridos en el detalle de factura estén presentes.
    
    Args:
        factura_detalle_data (dict): Datos del detalle de factura
    
    Returns:
        tuple: (bool, str) donde bool indica si la validación fue exitosa
               y str contiene un mensaje de error en caso de fallo
    """
    required_fields = [
        'numeroFactura', 'actividadEconomica', 'codigoProductoSin', 'codigoProducto', 
        'descripcion', 'cantidad', 'unidadMedida', 'precioUnitario', 'subTotal'
    ]
    
    for field in required_fields:
        if factura_detalle_data.get(field) is None or factura_detalle_data.get(field) == '':
            return False, f"El campo {field} es requerido y no puede estar vacío."
    
    return True, ""

def verificar_nit(nit, client=None):
    """
    Verifica la validez de un NIT utilizando el servicio web SIAT.
    Si no hay conexión, devuelve una respuesta predeterminada para modo offline.
    
    Args:
        nit (str): El NIT a verificar
        client: Cliente SOAP (opcional, si no se proporciona se obtiene automáticamente)
        
    Returns:
        tuple: (éxito, mensaje) donde éxito es un booleano y mensaje es una cadena
    """
    # Si no se proporciona cliente, obtenerlo del servicio centralizado
    if client is None:
        client = get_soap_client()
    
    # Verificar si estamos en modo offline (sin cliente SOAP)
    if not client:
        return False, "No se puede verificar el NIT - sin conexión con los servicios del SIN"
    
    # Preparar la solicitud para el servicio web
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
        # Llamar al servicio web
        response = client.service.verificarNit(SolicitudVerificarNit=solicitud_verificar_nit)
        if response.transaccion:
            return True, response.mensajesList[0].descripcion
        else:
            return False, "Verifica el NIT o elige otro Tipo de Documento."
    except Exception as e:
        logger.error(f"Error al verificar NIT: {str(e)}")
        return False, f"Ocurrió un error: {str(e)}"


