"""
Módulo para la gestión de clientes en el sistema de facturación.

Este módulo contiene funciones para guardar, recuperar y validar datos de clientes.
"""

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from database import SessionLocal
from facturador.models import Cliente
from validators import es_email_valido, es_telefono_valido, verificar_nit
from api_clients import get_soap_client
from logger_config import get_logger

# Configuración de logger
logger = get_logger()

def save_or_fetch_client_data(codigo_cliente, codigo_tipo_documento_identidad, complemento, email, nombre_razon_social, numero_documento, telefono, message_placeholder):
    """
    Guarda o recupera datos de cliente de la base de datos.
    
    Args:
        codigo_cliente (str): Código del cliente
        codigo_tipo_documento_identidad (str): Código del tipo de documento de identidad
        complemento (str): Complemento del documento de identidad
        email (str): Email del cliente
        nombre_razon_social (str): Nombre o razón social del cliente
        numero_documento (str): Número de documento de identidad
        telefono (str): Teléfono del cliente
        message_placeholder: Objeto para mostrar mensajes de error
        
    Returns:
        dict: Datos del cliente o None si hay error
    """
    if not nombre_razon_social:
        message_placeholder.error("❌El campo 'Razón Social' es obligatorio.")
        return None

    if email and not es_email_valido(email, message_placeholder):
        message_placeholder.error("❌Por favor, ingrese un email válido.")
        return None

    if telefono and not es_telefono_valido(telefono):
        message_placeholder.error("❌Por favor, ingrese un número de teléfono válido.")
        return None

    # Intentar obtener el cliente existente
    cliente_data, error = fetch_cliente(codigo_cliente)
    
    # Si no existe, crear un nuevo cliente
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

def fetch_cliente(codigo_cliente):
    """
    Obtiene los datos de un cliente por su código.
    
    Esta función es un wrapper para la función de data_access,
    solo se incluye aquí para mantener todas las funciones de cliente
    en el mismo módulo.
    
    Args:
        codigo_cliente (str): Código del cliente
        
    Returns:
        tuple: (datos_cliente, error) donde datos_cliente es un diccionario
               con los datos del cliente y error es None si no hay error,
               o un mensaje de error si lo hay.
    """
    from data_access import fetch_cliente as da_fetch_cliente
    return da_fetch_cliente(codigo_cliente)

def verificar_nit_cliente(nit, message_placeholder):
    """
    Verifica la validez de un NIT utilizando el servicio web SIAT
    y muestra el resultado en la interfaz.
    
    Args:
        nit (str): NIT a verificar
        message_placeholder: Objeto para mostrar mensajes
        
    Returns:
        tuple: (bool, str) donde bool indica si es válido y str el mensaje
    """
    client = get_soap_client()
    
    success, message = verificar_nit(nit, client)
    
    if success:
        return True, message
    else:
        return False, message
