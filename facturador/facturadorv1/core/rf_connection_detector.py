"""
Detector automático de conexión para el sistema de facturación.
Determina si el sistema debe operar en modo online u offline.
"""
import asyncio
import aiohttp
import socket
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from utils.rf_logger import log_info, log_warning, log_error

class ConnectionMode(Enum):
    """Modos de conexión disponibles."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    UNKNOWN = "UNKNOWN"

class ConnectionStatus(Enum):
    """Estados de conexión posibles."""
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    DEGRADED = "DEGRADED"  # Conexión lenta o inestable
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"

@dataclass
class ConnectionResult:
    """Resultado de una prueba de conexión."""
    status: ConnectionStatus
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: datetime = None
    service_name: str = "unknown"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class RFConnectionDetector:
    """
    Detector de conexión automático para SIAT.
    Verifica la conectividad con los servicios del SIN y determina el modo óptimo.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el detector de conexión.
        
        Args:
            config: Configuración con URLs y timeouts
        """
        self.config = config or self._get_default_config()
        self._last_check = None
        self._cache_duration = timedelta(minutes=5)  # Cache de 5 minutos
        self._cached_result = None
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto para las pruebas de conexión."""
        return {
            "siat_services": {
                "verificacion_comunicacion": "https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionCodigos/verificarComunicacion",
                "sincronizacion": "https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionSincronizacion/sincronizarActividades"
            },
            "fallback_hosts": [
                "8.8.8.8",  # Google DNS
                "1.1.1.1",  # Cloudflare DNS
            ],
            "timeouts": {
                "connection_timeout": 10,  # segundos
                "read_timeout": 15,
                "total_timeout": 30
            },
            "thresholds": {
                "good_response_time": 2000,  # ms
                "acceptable_response_time": 5000,  # ms
                "max_response_time": 10000  # ms
            }
        }
    
    async def detect_connection_mode(self, force_check: bool = False) -> Tuple[ConnectionMode, Dict[str, Any]]:
        """
        Detecta el modo de conexión óptimo.
        
        Args:
            force_check: Fuerza una nueva verificación ignorando el cache
            
        Returns:
            Tupla con (modo, detalles de la verificación)
        """
        # Verificar cache si no es forzado
        if not force_check and self._is_cache_valid():
            log_info("Usando resultado cacheado para detección de conexión")
            return self._cached_result
        
        log_info("Iniciando detección de modo de conexión")
        
        # Ejecutar todas las pruebas de conexión
        results = await self._run_all_connectivity_tests()
        
        # Analizar resultados y determinar el modo
        mode, details = self._analyze_connectivity_results(results)
        
        # Actualizar cache
        self._cached_result = (mode, details)
        self._last_check = datetime.now()
        
        log_info(f"Modo de conexión detectado: {mode.value}", extra_data=details)
        
        return mode, details
    
    async def _run_all_connectivity_tests(self) -> Dict[str, ConnectionResult]:
        """Ejecuta todas las pruebas de conectividad en paralelo."""
        tasks = []
        
        # Pruebas de servicios SIAT
        for service_name, url in self.config["siat_services"].items():
            task = self._test_http_service(service_name, url)
            tasks.append(task)
        
        # Pruebas de conectividad básica
        for i, host in enumerate(self.config["fallback_hosts"]):
            task = self._test_basic_connectivity(f"dns_{i+1}", host)
            tasks.append(task)
        
        # Ejecutar todas las pruebas concurrentemente
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        connectivity_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = f"test_{i}"
                connectivity_results[service_name] = ConnectionResult(
                    status=ConnectionStatus.ERROR,
                    error_message=str(result),
                    service_name=service_name
                )
            else:
                connectivity_results[result.service_name] = result
        
        return connectivity_results
    
    async def _test_http_service(self, service_name: str, url: str) -> ConnectionResult:
        """
        Prueba la conectividad con un servicio HTTP específico.
        
        Args:
            service_name: Nombre del servicio
            url: URL del servicio
            
        Returns:
            Resultado de la prueba
        """
        start_time = datetime.now()
        
        try:
            timeout = aiohttp.ClientTimeout(
                connect=self.config["timeouts"]["connection_timeout"],
                total=self.config["timeouts"]["total_timeout"]
            )
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds() * 1000
                    
                    if response.status == 200:
                        status = self._classify_response_time(response_time)
                    else:
                        status = ConnectionStatus.ERROR
                    
                    return ConnectionResult(
                        status=status,
                        response_time_ms=response_time,
                        service_name=service_name,
                        timestamp=start_time
                    )
        
        except asyncio.TimeoutError:
            return ConnectionResult(
                status=ConnectionStatus.TIMEOUT,
                error_message="Timeout en la conexión",
                service_name=service_name,
                timestamp=start_time
            )
        except Exception as e:
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                error_message=str(e),
                service_name=service_name,
                timestamp=start_time
            )
    
    async def _test_basic_connectivity(self, service_name: str, host: str, port: int = 53) -> ConnectionResult:
        """
        Prueba conectividad básica mediante socket.
        
        Args:
            service_name: Nombre del test
            host: Host a probar
            port: Puerto (por defecto DNS)
            
        Returns:
            Resultado de la prueba
        """
        start_time = datetime.now()
        
        try:
            # Crear socket con timeout
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config["timeouts"]["connection_timeout"])
            
            # Intentar conexión
            result = sock.connect_ex((host, port))
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            sock.close()
            
            if result == 0:
                status = self._classify_response_time(response_time)
            else:
                status = ConnectionStatus.DISCONNECTED
            
            return ConnectionResult(
                status=status,
                response_time_ms=response_time,
                service_name=service_name,
                timestamp=start_time
            )
        
        except socket.timeout:
            return ConnectionResult(
                status=ConnectionStatus.TIMEOUT,
                error_message="Timeout en conexión básica",
                service_name=service_name,
                timestamp=start_time
            )
        except Exception as e:
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                error_message=str(e),
                service_name=service_name,
                timestamp=start_time
            )
    
    def _classify_response_time(self, response_time_ms: float) -> ConnectionStatus:
        """Clasifica la calidad de conexión según el tiempo de respuesta."""
        thresholds = self.config["thresholds"]
        
        if response_time_ms <= thresholds["good_response_time"]:
            return ConnectionStatus.CONNECTED
        elif response_time_ms <= thresholds["acceptable_response_time"]:
            return ConnectionStatus.DEGRADED
        else:
            return ConnectionStatus.DISCONNECTED
    
    def _analyze_connectivity_results(self, results: Dict[str, ConnectionResult]) -> Tuple[ConnectionMode, Dict[str, Any]]:
        """
        Analiza los resultados de conectividad y determina el modo óptimo.
        
        Args:
            results: Resultados de todas las pruebas
            
        Returns:
            Tupla con el modo recomendado y detalles del análisis
        """
        # Contar resultados por categoría
        siat_results = {k: v for k, v in results.items() if not k.startswith("dns_")}
        basic_results = {k: v for k, v in results.items() if k.startswith("dns_")}
        
        # Analizar servicios SIAT
        siat_connected = sum(1 for r in siat_results.values() if r.status == ConnectionStatus.CONNECTED)
        siat_degraded = sum(1 for r in siat_results.values() if r.status == ConnectionStatus.DEGRADED)
        siat_total = len(siat_results)
        
        # Analizar conectividad básica
        basic_connected = sum(1 for r in basic_results.values() if r.status in [ConnectionStatus.CONNECTED, ConnectionStatus.DEGRADED])
        basic_total = len(basic_results)
        
        # Calcular tiempo promedio de respuesta para servicios conectados
        connected_times = [r.response_time_ms for r in results.values() 
                          if r.response_time_ms and r.status in [ConnectionStatus.CONNECTED, ConnectionStatus.DEGRADED]]
        avg_response_time = sum(connected_times) / len(connected_times) if connected_times else None
        
        # Determinar modo basado en análisis
        mode = self._determine_mode(siat_connected, siat_total, basic_connected, basic_total)
        
        # Compilar detalles
        details = {
            "timestamp": datetime.now().isoformat(),
            "siat_services": {
                "connected": siat_connected,
                "degraded": siat_degraded,
                "total": siat_total,
                "success_rate": (siat_connected + siat_degraded) / siat_total if siat_total > 0 else 0
            },
            "basic_connectivity": {
                "connected": basic_connected,
                "total": basic_total,
                "success_rate": basic_connected / basic_total if basic_total > 0 else 0
            },
            "average_response_time_ms": avg_response_time,
            "detailed_results": {name: {
                "status": result.status.value,
                "response_time_ms": result.response_time_ms,
                "error_message": result.error_message
            } for name, result in results.items()},
            "recommended_mode": mode.value
        }
        
        return mode, details
    
    def _determine_mode(self, siat_connected: int, siat_total: int, 
                       basic_connected: int, basic_total: int) -> ConnectionMode:
        """
        Determina el modo de conexión basado en los resultados.
        
        Args:
            siat_connected: Servicios SIAT conectados
            siat_total: Total de servicios SIAT
            basic_connected: Conectividad básica exitosa
            basic_total: Total de pruebas básicas
            
        Returns:
            Modo de conexión recomendado
        """
        # Calcular tasas de éxito
        siat_success_rate = siat_connected / siat_total if siat_total > 0 else 0
        basic_success_rate = basic_connected / basic_total if basic_total > 0 else 0
        
        # Lógica de decisión
        if siat_success_rate >= 0.7 and basic_success_rate >= 0.5:
            # Al menos 70% de servicios SIAT y 50% de conectividad básica
            return ConnectionMode.ONLINE
        elif basic_success_rate >= 0.5:
            # Hay conectividad básica pero servicios SIAT fallan
            log_warning("Servicios SIAT no disponibles pero hay conectividad básica")
            return ConnectionMode.OFFLINE
        else:
            # Sin conectividad confiable
            log_warning("Conectividad limitada detectada")
            return ConnectionMode.OFFLINE
    
    def _is_cache_valid(self) -> bool:
        """Verifica si el cache de resultados es válido."""
        if not self._last_check or not self._cached_result:
            return False
        
        elapsed = datetime.now() - self._last_check
        return elapsed < self._cache_duration
    
    def get_cached_mode(self) -> Optional[Tuple[ConnectionMode, Dict[str, Any]]]:
        """Obtiene el último modo detectado del cache."""
        if self._is_cache_valid():
            return self._cached_result
        return None
    
    def force_mode(self, mode: ConnectionMode, reason: str = "Forced by user"):
        """
        Fuerza un modo específico sobrescribiendo la detección automática.
        
        Args:
            mode: Modo a forzar
            reason: Razón del cambio forzado
        """
        details = {
            "forced": True,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "mode": mode.value
        }
        
        self._cached_result = (mode, details)
        self._last_check = datetime.now()
        
        log_info(f"Modo de conexión forzado a: {mode.value}", extra_data=details)

# Instancia global del detector
connection_detector = RFConnectionDetector()

# Funciones de conveniencia
async def detect_mode(force_check: bool = False) -> Tuple[ConnectionMode, Dict[str, Any]]:
    """Función de conveniencia para detectar el modo de conexión."""
    return await connection_detector.detect_connection_mode(force_check)

def get_cached_mode() -> Optional[Tuple[ConnectionMode, Dict[str, Any]]]:
    """Función de conveniencia para obtener el modo cacheado."""
    return connection_detector.get_cached_mode()

def force_mode(mode: ConnectionMode, reason: str = "Forced by user"):
    """Función de conveniencia para forzar un modo específico."""
    connection_detector.force_mode(mode, reason)
