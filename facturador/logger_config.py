import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime

def setup_logger(name='root', log_file=None, level=logging.DEBUG, max_size=10*1024*1024, backup_count=3, console_output=True):
    """
    Configura un logger con manejadores de archivo y consola.
    
    Args:
        name (str): Nombre del logger
        log_file (str): Ruta del archivo de log
        level (int): Nivel de logging
        max_size (int): Tamaño máximo del archivo de log en bytes
        backup_count (int): Número de archivos de backup
        console_output (bool): Si es True, añade un handler para la consola
    
    Returns:
        Logger: Objeto logger configurado
    """
    # Crear el directorio de logs si no existe
    if log_file and not os.path.exists(os.path.dirname(os.path.abspath(log_file))):
        os.makedirs(os.path.dirname(os.path.abspath(log_file)))
    
    # Estandarizar el nombre del logger si no es root y no tiene el prefijo
    if name != 'root' and not name.startswith('facturador.'):
        name = f'facturador.{name}'
        
    # Obtener o crear el logger
    if name == 'root':
        logger = logging.getLogger()  # Root logger
    else:
        logger = logging.getLogger(name)
    
    logger.setLevel(level)
    
    # Evitar duplicación de handlers
    if logger.handlers:
        logger.handlers = []
        
    # Formato común para todos los logs
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Handler para consola si está habilitado
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Handler para archivo con rotación si se especifica
    if log_file:
        # Usar RotatingFileHandler en lugar de FileHandler
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_size,  
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Asegurar que los loggers no raíz no propaguen mensajes al root logger
    if name != 'root':
        logger.propagate = False
    
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
            name='facturador.printer',
            log_file=f"{log_dir}/printer_{date_str}.log",
            level=logging.DEBUG
        ),
        'facturacion': setup_logger(
            name='facturador.facturacion',
            log_file=f"{log_dir}/facturacion_{date_str}.log",
            level=logging.INFO
        ),
        'cliente': setup_logger(
            name='facturador.cliente',
            log_file=f"{log_dir}/cliente_{date_str}.log",
            level=logging.INFO
        ),
        'xml': setup_logger(
            name='facturador.xml',
            log_file=f"{log_dir}/xml_{date_str}.log",
            level=logging.DEBUG
        ),
        'response_handler': setup_logger(
            name='facturador.response_handler',
            log_file=f"{log_dir}/response_{date_str}.log",
            level=logging.DEBUG
        ),
        'siat': setup_logger(
            name='facturador.siat',
            log_file=f"{log_dir}/siat_{date_str}.log",
            level=logging.DEBUG
        ),
        'zeeper': setup_logger(
            name='facturador.zeeper',
            log_file=f"{log_dir}/zeeper_{date_str}.log",
            level=logging.DEBUG
        ),
        'eventos': setup_logger(
            name='facturador.eventos',
            log_file=f"{log_dir}/eventos_significativos.log", # Mantener nombre de archivo específico
            level=logging.INFO,
            console_output=False # Ejemplo: si no queremos que este vaya a consola
        ),
        'contingency': setup_logger(
            name='facturador.contingency',
            log_file=f"{log_dir}/contingency.log", # Mantener nombre de archivo específico
            level=logging.INFO,
            console_output=False # Ejemplo: si no queremos que este vaya a consola
        ),
        'invoice_exporter': setup_logger(
            name='facturador.invoice_exporter',
            log_file=f"{log_dir}/invoice_exporter_{date_str}.log",
            level=logging.INFO
        )
    }
    
    return loggers

# Configuración que se ejecuta al importar este módulo
loggers = setup_application_loggers()

# Configurar niveles para loggers de bibliotecas específicas para reducir verbosidad
logging.getLogger('fontTools').setLevel(logging.WARNING)
# Esto hará que solo los mensajes de WARNING y ERROR de la biblioteca fontTools 
# (y sus submódulos como fontTools.subset) se procesen por los handlers configurados.

# Funciones de conveniencia para obtener loggers
def get_logger(name='root'):
    """
    Obtiene un logger por nombre.
    Si el nombre no es 'root' y no comienza con 'facturador.', se le añade el prefijo.
    
    Args:
        name (str): Nombre del logger
    
    Returns:
        Logger: Logger configurado
    """
    if name != 'root' and not name.startswith('facturador.'):
        name = f'facturador.{name}'
    return logging.getLogger(name)

def get_printer_logger():
    """
    Obtiene el logger para operaciones de impresión.
    
    Returns:
        Logger: Logger de impresión
    """
    return get_logger('facturador.printer')

def get_eventos_logger():
    """
    Obtiene el logger para eventos significativos.
    
    Returns:
        Logger: Logger de eventos
    """
    return get_logger('facturador.eventos')

def get_facturacion_logger():
    """
    Obtiene el logger para operaciones de facturación.
    
    Returns:
        Logger: Logger de facturación
    """
    return get_logger('facturador.facturacion')

def get_cliente_logger():
    """
    Obtiene el logger para operaciones con clientes.
    
    Returns:
        Logger: Logger de clientes
    """
    return get_logger('facturador.cliente')

def get_xml_logger():
    """
    Obtiene el logger para operaciones con XML.
    
    Returns:
        Logger: Logger de XML
    """
    return get_logger('facturador.xml')

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
    return get_logger('facturador.siat')

def get_zeeper_logger():
    """
    Obtiene el logger para el módulo zeeper.
    
    Returns:
        Logger: Logger de zeeper
    """
    return get_logger('facturador.zeeper')

def get_contingency_logger():
    """
    Obtiene un logger configurado para el módulo de contingencia.

    Returns:
        logging.Logger: Logger configurado para contingencias.
    """
    return get_logger('facturador.contingency')

def get_invoice_exporter_logger():
    """
    Obtiene el logger para el módulo de exportación de facturas.

    Returns:
        logging.Logger: Logger configurado para exportación de facturas.
    """
    return get_logger('facturador.invoice_exporter')
