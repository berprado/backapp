"""
Utilidades compartidas para la interfaz de usuario de Streamlit.
"""
import streamlit as st
from logger_config import get_logger

ui_logger = get_logger()

def init_session_state(key, default_value):
    """
    Inicializa una clave en el session_state si no existe.
    
    Args:
        key (str): Clave del session_state
        default_value: Valor por defecto
    """
    if key not in st.session_state:
        st.session_state[key] = default_value

def reset_session_keys(keys):
    """
    Reinicia múltiples claves del session_state.
    
    Args:
        keys (list): Lista de claves a reiniciar
    """
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]

def show_message(message_type, message, placeholder=None):
    """
    Muestra un mensaje en la interfaz.
    
    Args:
        message_type (str): Tipo de mensaje ('success', 'error', 'warning', 'info')
        message (str): Mensaje a mostrar
        placeholder: Placeholder de Streamlit donde mostrar el mensaje
    """
    if placeholder:
        if message_type == 'success':
            placeholder.success(message)
        elif message_type == 'error':
            placeholder.error(message)
        elif message_type == 'warning':
            placeholder.warning(message)
        else:
            placeholder.info(message)
    else:
        if message_type == 'success':
            st.success(message)
        elif message_type == 'error':
            st.error(message)
        elif message_type == 'warning':
            st.warning(message)
        else:
            st.info(message)
