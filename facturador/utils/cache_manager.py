"""
Módulo para gestionar el caché de datos y su invalidación.
Centraliza el control de todos los mecanismos de caché de la aplicación.
"""
import logging
import os
import json
from datetime import datetime, timedelta
import streamlit as st

logger = logging.getLogger(__name__)

def invalidate_cache(cache_type: str = None) -> list:
    """
    Invalida selectivamente cachés para asegurar datos frescos
    
    Args:
        cache_type (str): Tipo de caché a invalidar: 
            - 'facturas': Solo cachés de facturas
            - 'comandas': Solo cachés de comandas
            - 'parametricos': Cachés de datos paramétricos
            - None o 'all': Todos los cachés (por defecto)
            
    Returns:
        list: Lista de tipos de caché invalidados
    """
    # Importar aquí para evitar importación circular
    from facturador.data_access import (
        obtener_facturas_por_estado,
        fetch_comandas,
        fetch_metodos_pago,
        fetch_tipos_documento,
        obtener_motivos_anulacion
    )
    
    invalidated = []
    
    if cache_type in (None, 'all', 'facturas'):
        try:
            obtener_facturas_por_estado.clear()
            invalidated.append('facturas')
            logger.info("Caché de facturas invalidado")
        except Exception as e:
            logger.error(f"Error al invalidar caché de facturas: {e}")
    
    if cache_type in (None, 'all', 'comandas'):
        try:
            fetch_comandas.clear()
            invalidated.append('comandas')
            
            # También limpiar caché de archivo si existe
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
            cache_file = os.path.join(cache_dir, 'comandas_cache.json')
            if os.path.exists(cache_file):
                os.remove(cache_file)
                invalidated.append('comandas_file')
                logger.info(f"Archivo de caché de comandas eliminado: {cache_file}")
        except Exception as e:
            logger.error(f"Error al invalidar caché de comandas: {e}")
    
    if cache_type in (None, 'all', 'parametricos'):
        try:
            fetch_metodos_pago.clear()
            fetch_tipos_documento.clear()
            obtener_motivos_anulacion.clear()
            invalidated.append('parametricos')
            logger.info("Caché de datos paramétricos invalidado")
        except Exception as e:
            logger.error(f"Error al invalidar caché de datos paramétricos: {e}")
    
    if invalidated:
        logger.info(f"Cachés invalidados: {', '.join(invalidated)}")
    else:
        logger.warning(f"No se invalidó ningún caché para el tipo: {cache_type}")
    
    return invalidated

def check_cache_expiration(cache_file: str, max_age_hours: int = 24) -> bool:
    """
    Verifica si un archivo de caché ha expirado según su antigüedad.
    
    Args:
        cache_file: Ruta al archivo de caché
        max_age_hours: Edad máxima en horas antes de considerarlo expirado
        
    Returns:
        bool: True si el caché ha expirado o no existe, False si sigue siendo válido
    """
    try:
        if not os.path.exists(cache_file):
            return True
            
        # Verificar la fecha de modificación del archivo
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - file_mod_time > timedelta(hours=max_age_hours):
            logger.info(f"Caché expirado: {cache_file} (antigüedad: {(datetime.now() - file_mod_time).total_seconds() / 3600:.1f} horas)")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error al verificar expiración de caché {cache_file}: {e}")
        return True  # Si hay error, asumir que expiró para forzar recarga

def clear_expired_states() -> None:
    """
    Limpia estados de sesión expirados o innecesarios.
    Útil para despliegues de larga duración para evitar crecimiento excesivo de la memoria.
    """
    try:
        # Lista de estados temporales que pueden limpiarse si tienen más de 1 hora
        temp_keys = [k for k in st.session_state.keys() 
                    if k.startswith('temp_') or k.endswith('_temp')]
        
        for key in temp_keys:
            del st.session_state[key]
            
        logger.info(f"Se limpiaron {len(temp_keys)} estados temporales")
    except Exception as e:
        logger.error(f"Error al limpiar estados expirados: {e}")