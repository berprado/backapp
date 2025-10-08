# -*- coding: utf-8 -*-
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime

def setup_logger(name='root', log_file=None, level=logging.DEBUG, max_size=10*1024*1024, backup_count=3):
    """
    Configura un logger con manejadores de archivo y consola.
    
    Args:
        name (str): Nombre del logger
        log_file (str): Ruta del archivo de log
        level (int): Nivel de logging
        max_size (int): Tamaño máximo del archivo de log en bytes
        backup_count (int): Número de archivos de backup
    
    Returns:
        Logger: Objeto logger configurado
    """
    # Crear el directorio de logs si no existe
    if log_file and not os.path.exists(os.path.dirname(os.path.abspath(log_file))):
        os.makedirs(os.path.dirname(os.path.abspath(log_file)))
    
    # Intentar asegurar que la salida estándar use codificación UTF-8
    # Esto ayuda a que los mensajes con acentos y emojis se muestren correctamente en la consola.
    try:
        # Disponible en Python 3.7+; puede fallar en versiones anteriores o entornos limitados
        sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
    except Exception:
        # Si no es posible reconfigurar, continuar sin interrumpir la funcionalidad
        pass

    # Obtener o crear el logger
    if name == 'root':
        logger = logging.getLogger()  # Root logger
    else:
        logger = logging.getLogger(name)
    
    logger.setLevel(level)

    # Evitar duplicación de handlers
    if logger.handlers:
        logger.handlers = []

    # Desactivar propagación al logger raíz
    logger.propagate = False
    
    # Formato común para todos los logs
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo con rotación si se especifica
    if log_file:
        # Usar RotatingFileHandler en lugar de FileHandler
        # Especificar la codificación UTF-8 para soportar caracteres especiales
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_size,  
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def setup_application_loggers(log_dir='logs'):
    """
    Configura todos los loggers necesarios para la aplicación.
    
    Args:
        log_dir (str): Directorio donde se guardarán los logs
    
    Returns:
        dict: Diccionario con los loggers configurados
    """
    # Asegurarse de que el directorio de logs exista
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Fecha actual para los nombres de archivo
    date_str = datetime.now().strftime('%Y%m%d')
    
    # Configurar loggers para diferentes componentes
    loggers = {
        'root': setup_logger(
            name='root',
            log_file=f"{log_dir}/app_{date_str}.log",
            level=logging.INFO
        ),
        'printer': setup_logger(
            name='printer',
            log_file=f"{log_dir}/printer_{date_str}.log",
            level=logging.DEBUG
        ),
        'facturacion': setup_logger(
            name='facturacion',
            log_file=f"{log_dir}/facturacion_{date_str}.log",
            level=logging.INFO
        ),
        'cliente': setup_logger(
            name='cliente',
            log_file=f"{log_dir}/cliente_{date_str}.log",
            level=logging.INFO
        ),
        'xml': setup_logger(
            name='xml',
            log_file=f"{log_dir}/xml_{date_str}.log",
            level=logging.DEBUG
        ),
        'response_handler': setup_logger(
            name='facturador.response_handler',
            log_file=f"{log_dir}/response_{date_str}.log",
            level=logging.DEBUG
        ),
        'siat': setup_logger(
            name='siat',
            log_file=f"{log_dir}/siat_{date_str}.log",
            level=logging.DEBUG
        ),
        'sincronizacion': setup_logger(
            name='facturador.sincronizacion',
            log_file=f"{log_dir}/sincronizacion_{date_str}.log",
            level=logging.DEBUG
        ),
        'zeeper': setup_logger(
            name='zeeper',
            log_file=f"{log_dir}/zeeper_{date_str}.log",
            level=logging.DEBUG
        ),
        'ui': setup_logger(
            name='ui',
            log_file=f"{log_dir}/ui_{date_str}.log",
            level=logging.INFO
        )
    }

    # Configurar el logger raíz para que no propague mensajes a los handlers por defecto
    logging.getLogger().handlers = []

    return loggers

# Configuración que se ejecuta al importar este módulo
loggers = setup_application_loggers()

# Funciones de conveniencia para obtener loggers
def get_logger(name='root'):
    """
    Obtiene un logger por nombre.
    
    Args:
        name (str): Nombre del logger
    
    Returns:
        Logger: Logger configurado
    """
    return logging.getLogger(name)

def get_printer_logger():
    """
    Obtiene el logger para operaciones de impresión.
    
    Returns:
        Logger: Logger de impresión
    """
    return get_logger('printer')

def get_facturacion_logger():
    """
    Obtiene el logger para operaciones de facturación.
    
    Returns:
        Logger: Logger de facturación
    """
    return get_logger('facturacion')

def get_cliente_logger():
    """
    Obtiene el logger para operaciones con clientes.
    
    Returns:
        Logger: Logger de clientes
    """
    return get_logger('cliente')

def get_xml_logger():
    """
    Obtiene el logger para operaciones con XML.
    
    Returns:
        Logger: Logger de XML
    """
    return get_logger('xml')

def get_response_logger():
    """
    Obtiene el logger para el manejo de respuestas SIAT.
    
    Returns:
        Logger: Logger de respuestas
    """
    return get_logger('facturador.response_handler')

def get_siat_logger():
    """
    Obtiene el logger para comunicaciones con SIAT.
    
    Returns:
        Logger: Logger de SIAT
    """
    return get_logger('siat')

def get_sincronizacion_logger():
    """
    Obtiene el logger dedicado a la sincronización de catálogos.

    Returns:
        Logger: Logger de sincronización.
    """
    return get_logger('facturador.sincronizacion')

def get_zeeper_logger():
    """
    Obtiene el logger para el módulo zeeper.
    
    Returns:
        Logger: Logger de zeeper
    """
    return get_logger('zeeper')

def get_contingency_logger():
    """
    Obtiene un logger configurado para el módulo de contingencia.

    Returns:
        logging.Logger: Logger configurado para contingencias.
    """
    return _get_custom_logger('contingency', 'logs/contingency.log')

def _get_custom_logger(name, log_file):
    """
    Crea un logger personalizado con un handler de archivo.

    Args:
        name (str): Nombre del logger.
        log_file (str): Ruta del archivo de log.

    Returns:
        logging.Logger: Logger configurado.
    """
    logger = logging.getLogger(f'facturador.{name}')
    logger.setLevel(logging.INFO)

    # Verificar si ya tiene handlers para evitar duplicados
    if not logger.handlers:
        # Crear file handler para escribir en archivo
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # Crear el formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
        file_handler.setFormatter(formatter)

        # Añadir el handler al logger
        logger.addHandler(file_handler)

    return logger
