import os
import time
import logging
import requests
from datetime import datetime, timedelta
from zeep import Client, Transport
from requests import Session
from database import SessionLocal
from facturador.models import Cufd, SincronizarParametricaEventosSignificativos, FacturaCabecera
from dotenv import load_dotenv
from facturador.significant_events import register_significant_event, get_significant_events
from logger_config import get_contingency_logger

logger = get_contingency_logger()
load_dotenv()

class ContingencyManager:
    """
    Clase para gestionar las operaciones en modo contingencia
    """
    def __init__(self):
        self.session = SessionLocal()
        self._is_contingency_mode = False
        self.last_check_time = datetime.now()
        self.check_interval = timedelta(minutes=5)  # Verificar cada 5 minutos
        self.retry_attempts = 3  # Intentos antes de entrar en contingencia
        self.retry_delay = 5  # Segundos entre intentos
        self.last_valid_cufd = None
        self.contingency_start_time = None
        self.event_type = None
        self.event_description = None
        
        # Cargar el último CUFD válido al inicializar
        self._load_last_valid_cufd()
    
    def _load_last_valid_cufd(self):
        """Cargar el último CUFD válido desde la base de datos"""
        try:
            cufd_record = self.session.query(Cufd).filter(Cufd.vigente == 1).first()
            if cufd_record:
                self.last_valid_cufd = cufd_record.codigo
                logger.info(f"CUFD válido cargado: {self.last_valid_cufd}")
            else:
                logger.warning("No se encontró un CUFD válido")
        except Exception as e:
            logger.error(f"Error al cargar el CUFD: {str(e)}")
    
    @property
    def is_contingency_mode(self):
        """Propiedad que indica si estamos en modo contingencia"""
        return self._is_contingency_mode
    
    def verify_siat_connection(self):
        """
        Verifica la conexión con el servicio del SIAT
        Retorna: (bool) True si la conexión está disponible, False en caso contrario
        """
        now = datetime.now()
        
        # Verificar solo si ha pasado el intervalo de verificación
        if self._is_contingency_mode or (now - self.last_check_time) >= self.check_interval:
            self.last_check_time = now
            
            wsdl_url = os.getenv('WSDL_URL_SINCRONIZACION')
            soap_session = Session()
            soap_session.headers.update({'apikey': os.getenv('API_KEY')})
            
            for attempt in range(self.retry_attempts):
                try:
                    client = Client(wsdl_url, transport=Transport(session=soap_session))
                    
                    solicitud = {
                        'codigoAmbiente': os.getenv('CODIGO_AMBIENTE'),
                        'codigoSistema': os.getenv('CODIGO_SISTEMA'),
                        'nit': os.getenv('NIT'),
                        'cuis': os.getenv('CUIS'),
                        'codigoSucursal': os.getenv('CODIGO_SUCURSAL'),
                        'codigoPuntoVenta': os.getenv('CODIGO_PUNTO_VENTA')
                    }
                    
                    response = client.service.verificarComunicacion()
                    
                    if hasattr(response, 'transaccion') and response.transaccion:
                        if self._is_contingency_mode:
                            logger.info("Conexión con SIAT restablecida")
                            return True
                        return True
                    
                    logger.warning(f"Intento {attempt+1}/{self.retry_attempts}: Servicio no disponible")
                    time.sleep(self.retry_delay)
                    
                except (requests.RequestException, TimeoutError) as e:
                    logger.warning(f"Intento {attempt+1}/{self.retry_attempts}: Error de conexión - {str(e)}")
                    time.sleep(self.retry_delay)
                except Exception as e:
                    logger.error(f"Error inesperado al verificar conexión: {str(e)}")
                    time.sleep(self.retry_delay)
            
            if not self._is_contingency_mode:
                logger.error("No se pudo establecer conexión con SIAT después de múltiples intentos")
            return False
        
        return not self._is_contingency_mode
    
    def enter_contingency_mode(self, event_type=1, description="Corte del servicio de Internet"):
        """
        Activa el modo contingencia
        event_type: (int) Código del evento significativo
        description: (str) Descripción adicional del evento
        """
        if not self._is_contingency_mode:
            self._is_contingency_mode = True
            self.contingency_start_time = datetime.now()
            self.event_type = event_type
            self.event_description = description
            
            # Cargar el último CUFD válido si no lo tenemos
            if not self.last_valid_cufd:
                self._load_last_valid_cufd()
            
            logger.info(f"MODO CONTINGENCIA ACTIVADO - Evento: {event_type} - {description}")
            return True
        return False
    
    def exit_contingency_mode(self):
        """
        Sale del modo contingencia y registra el evento significativo
        Retorna: (bool) True si se pudo salir del modo contingencia, False en caso contrario
        """
        if not self._is_contingency_mode:
            logger.warning("No se puede salir del modo contingencia porque no está activo")
            return False
        
        # Verificar que la conexión esté disponible antes de salir
        if not self.verify_siat_connection():
            logger.warning("No se puede salir del modo contingencia porque la conexión sigue sin estar disponible")
            return False
        
        # Registrar el evento significativo
        end_time = datetime.now()
        
        try:
            # Formatear fechas para el servicio web
            fecha_inicio = self.contingency_start_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            fecha_fin = end_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            
            # Registrar el evento significativo
            success, msg = register_significant_event(
                self.event_type, 
                self.event_description,
                fecha_inicio,
                fecha_fin,
                self.last_valid_cufd
            )
            
            if success:
                logger.info(f"Evento significativo registrado con éxito: {msg}")
                self._is_contingency_mode = False
                logger.info("MODO CONTINGENCIA DESACTIVADO")
                return True
            else:
                logger.error(f"Error al registrar evento significativo: {msg}")
                return False
        
        except Exception as e:
            logger.error(f"Error al salir del modo contingencia: {str(e)}")
            return False
    
    def get_pending_invoices(self):
        """
        Obtiene las facturas pendientes de envío (emitidas en contingencia)
        """
        try:
            facturas_pendientes = self.session.query(FacturaCabecera).filter(
                FacturaCabecera.estadoFirma == "CONTINGENCIA"
            ).all()
            
            logger.info(f"Se encontraron {len(facturas_pendientes)} facturas pendientes de envío")
            return facturas_pendientes
        except Exception as e:
            logger.error(f"Error al obtener facturas pendientes: {str(e)}")
            return []
    
    def get_contingency_status(self):
        """
        Obtiene el estado actual de la contingencia
        Retorna: (dict) Información del estado de contingencia
        """
        status = {
            "is_active": self._is_contingency_mode,
            "start_time": self.contingency_start_time,
            "duration": None,
            "event_type": self.event_type,
            "event_description": self.event_description,
            "last_valid_cufd": self.last_valid_cufd,
            "pending_invoices_count": 0
        }
        
        if self._is_contingency_mode and self.contingency_start_time:
            duration = datetime.now() - self.contingency_start_time
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            seconds = duration.seconds % 60
            
            status["duration"] = f"{hours}h {minutes}m {seconds}s"
            
            # Contar facturas pendientes
            try:
                pending_count = self.session.query(FacturaCabecera).filter(
                    FacturaCabecera.estadoFirma == "CONTINGENCIA"
                ).count()
                
                status["pending_invoices_count"] = pending_count
            except:
                pass
        
        return status
    
    def close(self):
        """Cierra la sesión de la base de datos"""
        if self.session:
            self.session.close()
