import os
import sys
import time
import json
import threading
import requests
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List
import streamlit as st
from database import SessionLocal
from sqlalchemy.exc import SQLAlchemyError
from facturador.logger_config import get_logger  # Cambiar esta importación

from facturador.models import (
    FacturaCabecera, 
    Cufd, 
    SincronizarParametricaEventosSignificativos,
    SincronizarParametricaTipoEmision
)
from facturador.response_handler import parse_siat_response
from facturador.significant_events import register_significant_event
from facturador.utils.log_cleaner import clean_xml_responses

# Obtener logger para este módulo
logger = get_logger('contingency')  # Usar el logger general con nombre específico

# Estado de la contingencia
class ContingencyStatus(Enum):
    NORMAL = "normal"             # Operación normal, todos los servicios disponibles
    MONITORING = "monitoring"     # Detectamos un problema, estamos monitoreando
    CONTINGENCY = "contingency"   # En contingencia, servicios no disponibles
    RECOVERING = "recovering"     # Servicios recuperados, enviando pendientes

# Definir tipos de eventos significativos
class SignificantEventType(Enum):
    INTERNET_OUTAGE = "1"         # Corte del servicio de internet
    WEB_SERVICE_UNAVAILABLE = "2" # Inaccesibilidad al Servicio Web de la Administración Tributaria
    NO_INTERNET_ZONE = "3"        # Ingreso a zonas sin internet por despliegue de punto de venta móvil
    REMOTE_SALE = "4"             # Venta en lugares sin internet
    VIRUS_OR_SOFTWARE_FAULT = "5" # Virus informático o fallas del software
    HARDWARE_FAULT = "6"          # Cambio de infraestructura del sistema o fallas de hardware
    POWER_OUTAGE = "7"            # Corte de suministro de energía eléctrica

class ContingencyManager:
    """
    Gestor de contingencias para el sistema de facturación.
    
    Esta clase maneja la detección de problemas de comunicación con el SIAT,
    la activación del modo contingencia, y la sincronización posterior.
    """
    
    def __init__(self):
        """Inicializa el gestor de contingencias"""
        self.status = ContingencyStatus.NORMAL
        self.monitoring_thread = None
        self.stop_monitoring = False
        self.contingency_start_time = None
        self.last_check_time = None
        self.event_type = None
        self.event_description = None
        self.state_file_path = "contingency_state.json"
        self.cufd_contingency = None
        self.check_interval = 60  # Intervalo de verificación en segundos (1 minuto)
        self.failure_threshold = 3  # Número de fallos consecutivos para activar contingencia
        self.consecutive_failures = 0
        self.recovery_threshold = 2  # Número de éxitos consecutivos para considerar recuperación
        self.consecutive_successes = 0
        self.services = self._get_services_from_env()
        
        # Ejecutar limpieza inicial de archivos XML antiguos
        clean_xml_responses()
        
        self.last_cleanup_time = datetime.now()
        self.cleanup_interval = 86400  # 24 horas en segundos
        
        # Intentar restaurar el estado si existe
        self._restore_state()
    
    def _get_services_from_env(self) -> Dict[str, str]:
        """Obtiene los servicios SOAP desde las variables de entorno"""
        from dotenv import load_dotenv
        load_dotenv()
        
        return {
            "Facturación Códigos": os.getenv("WSDL_URL_CODIGOS", ""),
            "Facturación Operaciones": os.getenv("WSDL_URL_OPERACIONES", ""),
            "Facturación Sincronización": os.getenv("WSDL_URL_SYNC", ""),
            "Documentos de Ajuste": os.getenv("WSDL_URL_AJUSTE", ""),
            "Facturación Compra-Venta": os.getenv("WSDL_URL_FACTURACION", "")
        }
    
    def _save_state(self) -> None:
        """Guarda el estado actual del gestor de contingencias"""
        try:
            state = {
                "status": self.status.value,
                "contingency_start_time": self.contingency_start_time.isoformat() if self.contingency_start_time else None,
                "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
                "event_type": self.event_type.value if self.event_type else None,
                "event_description": self.event_description,
                "consecutive_failures": self.consecutive_failures,
                "consecutive_successes": self.consecutive_successes,
                "cufd_contingency": self.cufd_contingency
            }
            
            with open(self.state_file_path, 'w') as f:
                json.dump(state, f)
                logger.info("Estado del gestor de contingencias guardado correctamente")
        except Exception as e:
            logger.error(f"Error al guardar el estado del gestor de contingencias: {e}")
    
    def _restore_state(self) -> None:
        """Restaura el estado del gestor de contingencias desde un archivo"""
        try:
            if os.path.exists(self.state_file_path):
                with open(self.state_file_path, 'r') as f:
                    state = json.load(f)
                
                self.status = ContingencyStatus(state.get("status", "normal"))
                
                if state.get("contingency_start_time"):
                    self.contingency_start_time = datetime.fromisoformat(state["contingency_start_time"])
                
                if state.get("last_check_time"):
                    self.last_check_time = datetime.fromisoformat(state["last_check_time"])
                
                if state.get("event_type"):
                    self.event_type = SignificantEventType(state["event_type"])
                
                self.event_description = state.get("event_description")
                self.consecutive_failures = state.get("consecutive_failures", 0)
                self.consecutive_successes = state.get("consecutive_successes", 0)
                self.cufd_contingency = state.get("cufd_contingency")
                
                logger.info(f"Estado restaurado: {self.status.value}")
                
                # Si estamos en contingencia, reiniciar el monitoreo
                if self.status in [ContingencyStatus.CONTINGENCY, ContingencyStatus.MONITORING]:
                    self.start_monitoring()
        except Exception as e:
            logger.error(f"Error al restaurar el estado del gestor de contingencias: {e}")
    
    def check_connection(self) -> Tuple[bool, List[str]]:
        """
        Verifica la conexión con los servicios del SIAT
        
        Returns:
            Tuple[bool, List[str]]: (éxito, lista_servicios_con_problemas)
        """
        problematic_services = []
        all_services_ok = True
        
        # SOAP request template
        soap_request = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
           <soapenv:Header/>
           <soapenv:Body>
              <siat:verificarComunicacion/>
           </soapenv:Body>
        </soapenv:Envelope>"""
        
        headers = {
            "Content-Type": "text/xml;charset=UTF-8",
            "SOAPAction": "",
            "apikey": os.getenv('API_KEY')
        }
        
        # Actualizar tiempo de última verificación
        self.last_check_time = datetime.now()
        
        # Verificar cada servicio
        for service_name, url in self.services.items():
            if not url:
                continue
                
            try:
                # Enviar solicitud SOAP
                response = requests.post(url, data=soap_request, headers=headers, timeout=10)
                
                # Verificar que la respuesta sea exitosa (código 200)
                response.raise_for_status()
                
                # Decidir si forzar guardar la respuesta basado en el estado de verificación
                # Solo guardar respuestas si:
                # 1. Es la primera verificación (last_check_time acaba de ser establecido)
                # 2. Es una verificación después de fallos consecutivos
                # 3. El resultado cambia con respecto a la verificación anterior
                force_save = (self.consecutive_failures > 0 or self.consecutive_successes == 0)
                
                # Procesar la respuesta usando el módulo response_handler
                success, response_data = parse_siat_response(
                    response.content,
                    operation_type="verification", 
                    force_save=force_save
                )
                
                if success:
                    # Verificar si la transacción fue exitosa (ahora manejamos ambas estructuras)
                    if response_data.get('transaccion', False):
                        logger.debug(f"Servicio {service_name} OK")
                    else:
                        all_services_ok = False
                        problematic_services.append(service_name)
                        logger.warning(f"Servicio {service_name} respondió con transacción=false")
                else:
                    all_services_ok = False
                    problematic_services.append(service_name)
                    error = response_data.get('error', 'Error desconocido')
                    logger.warning(f"Error en servicio {service_name}: {error}")
                
            except (requests.exceptions.Timeout, 
                   requests.exceptions.ConnectionError, 
                   requests.exceptions.RequestException) as e:
                all_services_ok = False
                problematic_services.append(service_name)
                logger.warning(f"Error de conexión con servicio {service_name}: {e}")
        
        return all_services_ok, problematic_services

    def _monitoring_loop(self) -> None:
        """Bucle de monitoreo de la conexión con el SIAT"""
        logger.info("Iniciando bucle de monitoreo de conexión")
        
        while not self.stop_monitoring:
            try:
                # Verificar conexión
                all_ok, problem_services = self.check_connection()
                
                if all_ok:
                    self.consecutive_successes += 1
                    self.consecutive_failures = 0
                    logger.info(f"Conexión OK. Éxitos consecutivos: {self.consecutive_successes}")
                    
                    # Si estamos en modo contingencia y tenemos suficientes éxitos consecutivos, recuperamos
                    if (self.status == ContingencyStatus.CONTINGENCY and 
                        self.consecutive_successes >= self.recovery_threshold):
                        logger.info("Conexión recuperada. Cambiando a modo de recuperación.")
                        self.status = ContingencyStatus.RECOVERING
                        self._save_state()
                        
                        # Registrar evento significativo
                        self.register_significant_event()
                        
                        # Activar el envío de facturas pendientes
                        self.sync_pending_invoices()
                else:
                    self.consecutive_failures += 1
                    self.consecutive_successes = 0
                    logger.warning(f"Problemas de conexión con: {', '.join(problem_services)}. Fallos consecutivos: {self.consecutive_failures}")
                    
                    # Si estamos en modo normal y tenemos suficientes fallos consecutivos, activamos contingencia
                    if (self.status == ContingencyStatus.NORMAL and 
                        self.consecutive_failures >= self.failure_threshold):
                        logger.warning("Activando modo de contingencia por fallos consecutivos")
                        self.activate_contingency(
                            SignificantEventType.WEB_SERVICE_UNAVAILABLE,
                            f"Servicios no disponibles: {', '.join(problem_services)}"
                        )
                        
                # Verificar si es momento de limpiar los logs
                if (datetime.now() - self.last_cleanup_time).total_seconds() >= self.cleanup_interval:
                    deleted_count = clean_xml_responses()
                    logger.info(f"Limpieza de logs XML completada: {deleted_count} archivos eliminados")
                    self.last_cleanup_time = datetime.now()
                    
            except Exception as e:
                logger.error(f"Error en bucle de monitoreo: {e}")
            
            # Esperar el intervalo de verificación
            time.sleep(self.check_interval)

    def start_monitoring(self) -> None:
        """Inicia el monitoreo de la conexión con el SIAT"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.info("El monitoreo ya está activo")
            return
        
        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, 
            daemon=True,
            name="contingency-monitoring"
        )
        self.monitoring_thread.start()
        logger.info("Monitoreo de conexión iniciado")

    def stop_monitoring(self) -> None:
        """Detiene el monitoreo de la conexión con el SIAT"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.stop_monitoring = True
            self.monitoring_thread.join(timeout=5)
            logger.info("Monitoreo de conexión detenido")

    def activate_contingency(self, event_type: SignificantEventType, description: str = None) -> bool:
        """
        Activa el modo contingencia
        
        Args:
            event_type: Tipo de evento significativo
            description: Descripción del evento
            
        Returns:
            bool: True si se activó correctamente, False en caso contrario
        """
        try:
            # Validar entradas
            if not event_type or not description:
                logger.error("Se requieren el tipo de evento y la descripción para activar la contingencia.")
                return False

            # Verificar si ya estamos en contingencia
            if self.status == ContingencyStatus.CONTINGENCY:
                logger.warning("Ya estamos en modo contingencia")
                return False

            logger.info(f"Activando modo contingencia: {event_type.name}")

            # Actualizar estado
            self.status = ContingencyStatus.CONTINGENCY
            self.contingency_start_time = datetime.now()
            self.event_type = event_type
            self.event_description = description

            # Guardar el CUFD actual para usarlo en la contingencia
            session = SessionLocal()
            try:
                cufd_record = session.query(Cufd).filter(Cufd.vigente == 1).first()
                if not cufd_record:
                    logger.error("No se encontró un CUFD válido para activar la contingencia.")
                    return False
                self.cufd_contingency = cufd_record.codigo
            finally:
                session.close()

            # Guardar estado
            self._save_state()

            # Iniciar monitoreo si no está activo
            self.start_monitoring()

            logger.info("Modo contingencia activado correctamente.")
            return True

        except Exception as e:
            logger.error(f"Error al activar modo contingencia: {e}")
            return False

    def deactivate_contingency(self) -> bool:
        """
        Desactiva el modo contingencia manualmente
        
        Returns:
            bool: True si se desactivó correctamente, False en caso contrario
        """
        try:
            # Verificar si estamos en contingencia
            if self.status != ContingencyStatus.CONTINGENCY:
                logger.warning("El sistema no está en modo contingencia.")
                return False

            logger.info("Desactivando modo contingencia manualmente.")

            # Registrar evento significativo
            success, message = self.register_significant_event()
            if not success:
                logger.error(f"Error al registrar evento significativo: {message}")
                return False

            # Actualizar estado
            self.status = ContingencyStatus.RECOVERING
            self._save_state()

            # Activar el envío de facturas pendientes
            self.sync_pending_invoices()

            logger.info("Modo contingencia desactivado correctamente.")
            return True

        except Exception as e:
            logger.error(f"Error al desactivar modo contingencia: {e}")
            return False
    
    def register_significant_event(self) -> Tuple[bool, str]:
        """
        Registra el evento significativo en el SIAT
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        if not self.contingency_start_time or not self.event_type:
            return False, "No hay información de contingencia para registrar"
        
        try:
            # Formatear fechas
            start_time = self.contingency_start_time.strftime("%Y-%m-%dT%H:%M:%S.000")
            end_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000")
            
            # Registro en el SIAT
            success, message = register_significant_event(
                self.event_type.value,
                self.event_description or f"Contingencia por {self.event_type.name}",
                start_time,
                end_time,
                self.cufd_contingency
            )
            
            if success:
                logger.info(f"Evento significativo registrado: {message}")
                self.status = ContingencyStatus.NORMAL
                self.contingency_start_time = None
                self.event_type = None
                self.event_description = None
                self.cufd_contingency = None
                self.consecutive_failures = 0
                self.consecutive_successes = 0
                self._save_state()
                return True, message
            else:
                logger.error(f"Error al registrar evento significativo: {message}")
                return False, message
        except Exception as e:
            logger.error(f"Error al registrar evento significativo: {e}")
            return False, str(e)
    
    def sync_pending_invoices(self) -> None:
        """Inicia el proceso de sincronización de facturas pendientes"""
        try:
            from facturador.batch_sender import BatchSender
            
            logger.info("Iniciando sincronización de facturas pendientes")
            
            # Crear una instancia del enviador de lotes
            batch_sender = BatchSender()
            
            # Enviar todas las facturas pendientes
            results = batch_sender.send_all_pending_invoices()
            
            # Registrar resultados
            if results["success"]:
                logger.info(f"Sincronización completada: {results['message']}")
                # Si todo fue exitoso, volvemos a modo normal
                if self.status == ContingencyStatus.RECOVERING:
                    self.status = ContingencyStatus.NORMAL
                    self._save_state()
            else:
                logger.error(f"Error en sincronización: {results['message']}")
        except Exception as e:
            logger.error(f"Error al sincronizar facturas pendientes: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del gestor de contingencias
        
        Returns:
            Dict[str, Any]: Estado actual
        """
        return {
            "status": self.status.value,
            "contingency_active": self.status == ContingencyStatus.CONTINGENCY,
            "contingency_start_time": self.contingency_start_time.isoformat() if self.contingency_start_time else None,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "event_type": self.event_type.value if self.event_type else None,
            "event_description": self.event_description,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "cufd_contingency": self.cufd_contingency
        }
    
    def get_available_event_types(self) -> List[Dict[str, str]]:
        """
        Obtiene los tipos de eventos significativos disponibles
        
        Returns:
            List[Dict[str, str]]: Lista de eventos con código y descripción
        """
        events = []
        try:
            session = SessionLocal()
            try:
                db_events = session.query(SincronizarParametricaEventosSignificativos).all()
                for event in db_events:
                    events.append({
                        "codigo": event.codigoClasificador,
                        "descripcion": event.descripcion
                    })
            finally:
                session.close()
            
            # Si no hay eventos en la base de datos, usar los valores enumerados
            if not events:
                for event in SignificantEventType:
                    events.append({
                        "codigo": event.value,
                        "descripcion": event.name.replace('_', ' ').title()
                    })
            return events
        except Exception as e:
            logger.error(f"Error al obtener tipos de eventos: {e}")
            return []
    
    @staticmethod
    def get_emission_types() -> List[Dict[str, str]]:
        """
        Obtiene los tipos de emisión disponibles
        
        Returns:
            List[Dict[str, str]]: Lista de tipos de emisión con código y descripción
        """
        emission_types = []
        try:
            session = SessionLocal()
            try:
                db_types = session.query(SincronizarParametricaTipoEmision).all()
                for type_item in db_types:
                    emission_types.append({
                        "codigo": type_item.codigoClasificador,
                        "descripcion": type_item.descripcion
                    })
            finally:
                session.close()
            
            # Si no hay tipos en la base de datos, usar valores predeterminados
            if not emission_types:
                emission_types = [
                    {"codigo": "1", "descripcion": "Emisión en línea"},
                    {"codigo": "2", "descripcion": "Emisión fuera de línea"}
                ]
            return emission_types
        except Exception as e:
            logger.error(f"Error al obtener tipos de emisión: {e}")
            return []

# Instancia global del gestor de contingencias
_instance = None

def get_contingency_manager():
    """
    Obtiene la instancia global del gestor de contingencias
    
    Returns:
        ContingencyManager: Instancia global
    """
    global _instance
    if _instance is None:
        _instance = ContingencyManager()
    return _instance
