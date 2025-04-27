"""
Módulo de compatibilidad para facilitar la transición del sistema actual
al nuevo sistema de gestión de estado modular.

Este archivo proporciona funciones de redireccionamiento que permiten
una migración gradual desde el código acoplado actual hacia el nuevo
sistema centralizado de gestión de estados.
"""
import logging
from utils.state_manager import (
    initialize_app_state, get_state, set_state, get_decimal_state,
    reset_states, is_offline_mode, get_active_event
)
from utils.cache_manager import invalidate_cache

logger = logging.getLogger(__name__)

# Funciones de compatibilidad con nombres idénticos a las originales
def initialize_print_state():
    """
    Función de compatibilidad que reemplaza a la original en ui_copy.py
    para inicializar los estados de impresión y otros estados de la aplicación.
    """
    logger.info("Llamada a la función de compatibilidad initialize_print_state")
    initialize_app_state()
    return True

def reiniciar_estados():
    """
    Función de compatibilidad que reemplaza a la original en ui_copy.py
    para reiniciar los estados de facturación.
    """
    logger.info("Llamada a la función de compatibilidad reiniciar_estados")
    reset_states('all')
    return True

# Funciones utilitarias para acceder a los estados de forma directa
def get_print_status():
    """Obtiene el estado actual de impresión."""
    return get_state('print_status')

def set_print_status(status):
    """Establece el estado actual de impresión."""
    set_state('print_status', status)
    return True

def get_factura_data():
    """Obtiene los datos de la última factura."""
    return {
        'cuf': get_state('cuf'),
        'numero_factura': get_state('ultima_factura'),
        'datos_impresion': get_state('datos_impresion', {})
    }

def set_factura_data(cuf, numero_factura, datos_impresion=None):
    """Establece los datos de la última factura."""
    set_state('cuf', cuf)
    set_state('ultima_factura', numero_factura)
    if datos_impresion is not None:
        set_state('datos_impresion', datos_impresion)
    return True

def get_impresion_status():
    """Obtiene el estado del proceso de impresión."""
    return {
        'en_progreso': get_state('impresion_en_progreso', False),
        'finalizada': get_state('impresion_finalizada', False),
        'validada': get_state('factura_validada', False)
    }

def set_impresion_status(en_progreso=None, finalizada=None, validada=None):
    """Establece el estado del proceso de impresión."""
    if en_progreso is not None:
        set_state('impresion_en_progreso', en_progreso)
    if finalizada is not None:
        set_state('impresion_finalizada', finalizada)
    if validada is not None:
        set_state('factura_validada', validada)
    return True

# Funciones específicas para el manejo de modo offline/contingencia
def is_contingency_mode():
    """Verifica si el sistema está en modo contingencia/offline."""
    return is_offline_mode()

def get_contingency_event():
    """Obtiene información del evento de contingencia activo, si existe."""
    return get_active_event()

def set_contingency_mode(active=True, event_data=None):
    """
    Establece el modo de contingencia/offline y opcionalmente
    establece datos del evento asociado.
    """
    set_state('modo_offline', active)
    if event_data is not None:
        set_state('evento_contingencia', event_data)
        set_state('evento_activo', event_data)
    return True