"""
Módulo para gestionar clientes de servicios externos (SOAP, REST, etc.)
Centraliza la configuración y creación de clientes para servicios del SIN.
"""

import os
from typing import Optional
from requests import Session
from zeep import Client, Transport
from contingency_manager import check_connectivity
from logger_config import get_logger
from dotenv import load_dotenv

# Configurar logger
logger = get_logger()

# Cargar variables de entorno
load_dotenv()

# Cliente SOAP singleton
_soap_client = None
_initialized = False

def get_soap_client() -> Optional[Client]:
    """
    Devuelve una instancia singleton del cliente SOAP para servicios del SIN.
    La inicializa solo la primera vez que se llama.
    
    Returns:
        Client: Cliente SOAP configurado o None si no hay conectividad
    """
    global _soap_client, _initialized
    
    if _initialized:
        return _soap_client

    logger.info("Inicializando cliente SOAP...")
    
    # Verificar conectividad antes de crear el cliente
    is_connected, server_accessible = check_connectivity()
    
    if is_connected and server_accessible:
        try:
            # Configurar sesión con API Key
            session = Session()
            api_key = os.getenv('API_KEY', '')
            session.headers.update({'apikey': api_key})
            
            # Obtener URL del WSDL
            wsdl_url = os.getenv('WSDL_URL_CODIGOS')
            if not wsdl_url:
                logger.error("WSDL_URL_CODIGOS no está configurada en las variables de entorno")
                _soap_client = None
            else:
                # Crear cliente SOAP
                transport = Transport(session=session)
                _soap_client = Client(wsdl_url, transport=transport)
                logger.info("Cliente SOAP inicializado correctamente")
                
        except Exception as e:
            logger.error(f"Error al inicializar cliente SOAP: {e}")
            _soap_client = None
    else:
        logger.warning("Sin conectividad con el servidor del SIN - modo offline")
        _soap_client = None
        
    _initialized = True
    return _soap_client

def reset_soap_client():
    """
    Reinicia el cliente SOAP singleton.
    Útil para reconectar después de una contingencia.
    """
    global _soap_client, _initialized
    logger.info("Reiniciando cliente SOAP...")
    _soap_client = None
    _initialized = False
    return get_soap_client()

def is_soap_client_available() -> bool:
    """
    Verifica si el cliente SOAP está disponible.
    
    Returns:
        bool: True si el cliente está disponible, False en caso contrario
    """
    client = get_soap_client()
    return client is not None

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
    from datetime import datetime
    
    is_connected, server_accessible = check_connectivity()
    client_available = is_soap_client_available()
    
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
        "connected": is_connected,
        "server_accessible": server_accessible,
        "client_available": client_available,
        "status": status,
        "status_message": status_message,
        "last_check": datetime.now().strftime("%H:%M:%S")
    }

# Funciones adicionales para otros tipos de clientes si se necesitan en el futuro
def get_rest_client():
    """
    Placeholder para futuros clientes REST si se necesitan.
    """
    pass
