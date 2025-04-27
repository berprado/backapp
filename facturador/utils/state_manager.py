"""
Módulo centralizado para gestión de estado de la aplicación.
Maneja toda la persistencia de datos entre recargas de páginas y componentes.
"""
import streamlit as st
from typing import Any, Dict, List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def initialize_app_state():
    """
    Inicializa todos los estados de la aplicación de manera centralizada.
    Debe llamarse al inicio de la aplicación o cuando se necesite reiniciar todos los estados.
    """
    # Estados de formulario (sidebar)
    form_defaults = {
        # Cliente
        'numero_documento': '',
        'nombre_cliente': '',
        'complemento': None,
        'email': '',
        'telefono': '',
        'nit_valido': False,
        'cliente_id': None,
        'tipo_documento_seleccionado': None,
        'codigo_clasificador_documento': None,
        
        # Comandas y productos
        'processed_comandas': [],
        'selected_comandas': [],
        
        # Pagos
        'metodo_pago': None,
        'codigo_clasificador_metodo_pago': None,
        'ultimos_digitos_tarjeta': '',
        'descuento_adicional': 0,
        'monto_giftcard': 0,
        
        # Modo operación
        'modo_offline': False,
        'evento_contingencia': None,
        'evento_activo': None,
        'excepcion_nit': False
    }
    
    # Estados de impresión
    print_defaults = {
        'print_status': None,
        'datos_impresion': {},
        'cuf': None,
        'ultima_factura': None,
        'impresion_en_progreso': False,
        'impresion_finalizada': False,
        'factura_validada': False
    }
    
    # Estados de navegación
    ui_defaults = {
        'factura_detalle': None,
        'factura_anular': None,
        'page_TODAS': 1,
        'page_PENDIENTE': 1,
        'page_VALIDADA': 1,
        'page_ANULADA': 1
    }
    
    # Inicializar estados que no existen
    for category in [form_defaults, print_defaults, ui_defaults]:
        for key, default in category.items():
            if key not in st.session_state:
                st.session_state[key] = default
    
    logger.debug("Estados de la aplicación inicializados")

def get_state(key: str, default: Any = None) -> Any:
    """
    Obtiene un valor de estado con manejo de errores.
    
    Args:
        key: Clave del estado a obtener
        default: Valor por defecto si no existe
    
    Returns:
        El valor almacenado o el valor por defecto
    """
    try:
        return st.session_state.get(key, default)
    except Exception as e:
        logger.error(f"Error al obtener estado '{key}': {e}")
        return default

def set_state(key: str, value: Any) -> None:
    """
    Establece un valor en el estado con manejo de errores.
    
    Args:
        key: Clave del estado a establecer
        value: Valor a almacenar
    """
    try:
        st.session_state[key] = value
        logger.debug(f"Estado '{key}' actualizado")
    except Exception as e:
        logger.error(f"Error al establecer estado '{key}': {e}")

def get_decimal_state(key: str, default: float = 0.0) -> Decimal:
    """
    Obtiene un valor de estado como Decimal.
    Útil para manejar valores monetarios con precisión.
    
    Args:
        key: Clave del estado a obtener
        default: Valor por defecto si no existe
        
    Returns:
        El valor convertido a Decimal
    """
    try:
        value = st.session_state.get(key, default)
        return Decimal(str(value))
    except Exception as e:
        logger.error(f"Error al obtener estado decimal '{key}': {e}")
        return Decimal(str(default))

def reset_states(mode: str = 'factura') -> None:
    """
    Reinicia estados según el modo especificado.
    
    Args:
        mode (str): 
            - 'factura': solo datos actuales de factura
            - 'formulario': datos de formulario de cliente
            - 'all': reinicia todo excepto navegación
    """
    factura_keys = [
        'factura_validada', 'print_status', 'datos_impresion', 
        'cuf', 'ultima_factura', 'impresion_en_progreso', 
        'impresion_finalizada'
    ]
    
    formulario_keys = [
        'numero_documento', 'nombre_cliente', 'complemento', 'email', 
        'telefono', 'nit_valido', 'cliente_id', 'selected_comandas',
        'descuento_adicional', 'monto_giftcard', 'ultimos_digitos_tarjeta'
    ]
    
    keys_to_reset = []
    if mode == 'factura':
        keys_to_reset = factura_keys
    elif mode == 'formulario':
        keys_to_reset = formulario_keys
    elif mode == 'all':
        keys_to_reset = factura_keys + formulario_keys
    else:
        logger.warning(f"Modo de reinicio no reconocido: {mode}")
        return
    
    for key in keys_to_reset:
        if key in st.session_state:
            if key in ['descuento_adicional', 'monto_giftcard']:
                st.session_state[key] = 0
            else:
                del st.session_state[key]
    
    logger.info(f"Reiniciados {len(keys_to_reset)} estados en modo '{mode}'")

def is_offline_mode() -> bool:
    """
    Determina si estamos en modo offline/contingencia.
    
    Returns:
        True si estamos en modo offline, False en caso contrario
    """
    return get_state('modo_offline', False)

def get_active_event() -> Optional[Dict]:
    """
    Obtiene el evento activo de contingencia.
    
    Returns:
        Diccionario con información del evento o None si no hay evento activo
    """
    return get_state('evento_activo')

def save_form_data() -> Dict[str, Any]:
    """
    Captura el estado actual del formulario para uso posterior.
    
    Returns:
        Diccionario con los datos del formulario
    """
    form_keys = [
        'numero_documento', 'nombre_cliente', 'complemento', 'email', 
        'telefono', 'tipo_documento_seleccionado', 'codigo_clasificador_documento',
        'selected_comandas', 'metodo_pago', 'codigo_clasificador_metodo_pago',
        'ultimos_digitos_tarjeta', 'descuento_adicional', 'monto_giftcard'
    ]
    
    return {key: get_state(key) for key in form_keys}