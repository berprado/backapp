"""
Módulo para gestionar clientes de servicios externos (SOAP, REST, etc.)
Centraliza la configuración y creación de clientes para servicios del SIN.
"""

import os
import threading
from datetime import datetime
from typing import Optional
from requests import Session
from zeep import Client, Transport
from contingency_manager import check_connectivity
from logger_config import get_logger
from dotenv import load_dotenv

# Configurar logger
logger = get_logger()

# Cargar variables de entorno
# Cliente SOAP singleton
_soap_client = None
_initialized = False
_lock = threading.Lock()

def _generate_connectivity_status(is_connected: bool, server_accessible: bool, client_available: bool) -> dict:
    """
    Genera el estado de conectividad y mensajes descriptivos.

    Args:
        is_connected (bool): Si hay conexión a Internet.
        server_accessible (bool): Si el servidor del SIN es accesible.
        client_available (bool): Si el cliente SOAP está disponible.

    Returns:
        dict: Información del estado de conectividad.
    """
    if client_available:
        status = "🟢 Conectado a servicios del SIN"
        status_message = "Todas las funciones están disponibles"
    elif is_connected and not server_accessible:
        status = "🟡 Conexión parcial"
        status_message = "Internet disponible pero servicios del SIN no accesibles"
    else:
        status = "🔴 Sin conexión"
        status_message = "Trabajando en modo offline - funciones limitadas"

    return {
        "status": status,
        "status_message": status_message
    }

def get_soap_client() -> Optional[Client]:
    """
    Devuelve una instancia singleton del cliente SOAP para servicios del SIN.
    La inicializa solo la primera vez que se llama.

    Returns:
        Client: Cliente SOAP configurado o None si no hay conectividad.
    """
    global _soap_client, _initialized

    if _initialized:
        return _soap_client

    with _lock:
        if _initialized:
            return _soap_client

        logger.info("Inicializando cliente SOAP...")

        is_connected, server_accessible = check_connectivity()

        if is_connected and server_accessible:
            try:
                session = Session()
                api_key = os.getenv('API_KEY')
                if not api_key:
                    logger.warning("API_KEY no está configurada en las variables de entorno")
                session.headers.update({'apikey': api_key or ''})

                wsdl_url = os.getenv('WSDL_URL_CODIGOS')
                if not wsdl_url:
                    logger.error("WSDL_URL_CODIGOS no está configurada en las variables de entorno")
                    _soap_client = None
                else:
                    transport = Transport(session=session)
                    _soap_client = Client(wsdl_url, transport=transport)
                    logger.info("Cliente SOAP inicializado correctamente")

            except Exception as e:
                logger.error(f"Error al inicializar cliente SOAP: {e}", exc_info=True)
                _soap_client = None
        else:
            logger.warning("Sin conectividad con el servidor del SIN - modo offline")

        _initialized = True

    return _soap_client

def reset_soap_client():
    """
    Reinicia el cliente SOAP singleton.
    Útil para reconectar después de una contingencia.
    """
    global _soap_client, _initialized
    with _lock:
        logger.info("Reiniciando cliente SOAP...")
        _soap_client = None
        _initialized = False
    return get_soap_client()

def is_soap_client_available() -> bool:
    """
    Verifica si el cliente SOAP está disponible.

    Returns:
        bool: True si el cliente SOAP está inicializado, False en caso contrario.
    """
    global _soap_client
    return _soap_client is not None

def get_connectivity_info() -> dict:
    """
    Devuelve información detallada sobre el estado de conectividad.

    Returns:
        dict: Información del estado de conectividad con campos:
            - connected: bool - Si hay conexión
            - client_available: bool - Si el cliente SOAP está disponible
            - status_message: str - Mensaje descriptivo del estado
            - last_check: str - Timestamp del último chequeo
    """
    is_connected, server_accessible = check_connectivity()
    client_available = is_soap_client_available()

    connectivity_status = _generate_connectivity_status(is_connected, server_accessible, client_available)

    return {
        "connected": is_connected,
        "server_accessible": server_accessible,
        "client_available": client_available,
        "status": connectivity_status["status"],
        "status_message": connectivity_status["status_message"],
        "last_check": datetime.now().strftime("%H:%M:%S")
    }

# Funciones adicionales para otros tipos de clientes si se necesitan en el futuro
def get_rest_client():
    """
    Placeholder para futuros clientes REST si se necesitan.
    """
    logger.warning("get_rest_client no está implementado")
