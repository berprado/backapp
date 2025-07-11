"""
Sistema de logging centralizado para el sistema de facturación refactorizado.
Proporciona logging unificado con diferentes niveles y destinos.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json

class RFLogger:
    """
    Logger centralizado para el sistema de facturación.
    Maneja logs tanto en archivos como en consola con formato consistente.
    """
    
    def __init__(self, name: str = "rf_facturador", log_dir: Optional[Path] = None):
        """
        Inicializa el logger centralizado.
        
        Args:
            name: Nombre del logger
            log_dir: Directorio donde guardar los logs (opcional)
        """
        self.name = name
        self.log_dir = log_dir or Path(__file__).parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Configurar el logger principal
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicar handlers si ya están configurados
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura los handlers para archivo y consola."""
        
        # Formatter común
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para archivo general
        general_file = self.log_dir / "rf_general.log"
        file_handler = logging.FileHandler(general_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Handler para archivo de errores
        error_file = self.log_dir / "rf_errors.log"
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        
        # Agregar handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log de debug con datos adicionales opcionales."""
        msg = self._format_message(message, extra_data)
        self.logger.debug(msg)
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log de información con datos adicionales opcionales."""
        msg = self._format_message(message, extra_data)
        self.logger.info(msg)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log de advertencia con datos adicionales opcionales."""
        msg = self._format_message(message, extra_data)
        self.logger.warning(msg)
    
    def error(self, message: str, exception: Optional[Exception] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Log de error con excepción y datos adicionales opcionales."""
        msg = self._format_message(message, extra_data)
        if exception:
            msg += f" | Exception: {str(exception)}"
        self.logger.error(msg, exc_info=exception is not None)
    
    def critical(self, message: str, exception: Optional[Exception] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Log crítico con excepción y datos adicionales opcionales."""
        msg = self._format_message(message, extra_data)
        if exception:
            msg += f" | Exception: {str(exception)}"
        self.logger.critical(msg, exc_info=exception is not None)
    
    def log_factura_action(self, action: str, factura_id: Optional[str] = None, 
                          status: str = "SUCCESS", details: Optional[Dict[str, Any]] = None):
        """
        Log específico para acciones de facturación.
        
        Args:
            action: Acción realizada (crear, enviar, anular, etc.)
            factura_id: ID de la factura (opcional)
            status: Estado de la acción (SUCCESS, ERROR, WARNING)
            details: Detalles adicionales
        """
        log_data = {
            "action": action,
            "factura_id": factura_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        message = f"FACTURA_ACTION: {action}"
        if factura_id:
            message += f" | ID: {factura_id}"
        message += f" | STATUS: {status}"
        
        # Determinar nivel según el status
        if status == "ERROR":
            self.error(message, extra_data=log_data)
        elif status == "WARNING":
            self.warning(message, extra_data=log_data)
        else:
            self.info(message, extra_data=log_data)
    
    def log_siat_communication(self, service: str, operation: str, 
                              response_code: Optional[str] = None,
                              success: bool = True, details: Optional[Dict[str, Any]] = None):
        """
        Log específico para comunicaciones con SIAT.
        
        Args:
            service: Servicio SIAT utilizado
            operation: Operación realizada
            response_code: Código de respuesta del SIN
            success: Si la operación fue exitosa
            details: Detalles adicionales
        """
        log_data = {
            "service": service,
            "operation": operation,
            "response_code": response_code,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        message = f"SIAT_COMM: {service}.{operation}"
        if response_code:
            message += f" | CODE: {response_code}"
        message += f" | SUCCESS: {success}"
        
        if success:
            self.info(message, extra_data=log_data)
        else:
            self.error(message, extra_data=log_data)
    
    def _format_message(self, message: str, extra_data: Optional[Dict[str, Any]] = None) -> str:
        """Formatea el mensaje con datos adicionales si están presentes."""
        if extra_data:
            try:
                extra_str = json.dumps(extra_data, ensure_ascii=False, separators=(',', ':'))
                return f"{message} | DATA: {extra_str}"
            except (TypeError, ValueError):
                return f"{message} | DATA: {str(extra_data)}"
        return message


# Instancia global del logger para uso en todo el sistema
rf_logger = RFLogger()

# Funciones de conveniencia para acceso directo
def log_debug(message: str, extra_data: Optional[Dict[str, Any]] = None):
    """Función de conveniencia para debug logging."""
    rf_logger.debug(message, extra_data)

def log_info(message: str, extra_data: Optional[Dict[str, Any]] = None):
    """Función de conveniencia para info logging."""
    rf_logger.info(message, extra_data)

def log_warning(message: str, extra_data: Optional[Dict[str, Any]] = None):
    """Función de conveniencia para warning logging."""
    rf_logger.warning(message, extra_data)

def log_error(message: str, exception: Optional[Exception] = None, extra_data: Optional[Dict[str, Any]] = None):
    """Función de conveniencia para error logging."""
    rf_logger.error(message, exception, extra_data)

def log_critical(message: str, exception: Optional[Exception] = None, extra_data: Optional[Dict[str, Any]] = None):
    """Función de conveniencia para critical logging."""
    rf_logger.critical(message, exception, extra_data)

def log_factura_action(action: str, factura_id: Optional[str] = None, 
                      status: str = "SUCCESS", details: Optional[Dict[str, Any]] = None):
    """Función de conveniencia para logging de acciones de facturación."""
    rf_logger.log_factura_action(action, factura_id, status, details)

def log_siat_communication(service: str, operation: str, 
                          response_code: Optional[str] = None,
                          success: bool = True, details: Optional[Dict[str, Any]] = None):
    """Función de conveniencia para logging de comunicaciones SIAT."""
    rf_logger.log_siat_communication(service, operation, response_code, success, details)
