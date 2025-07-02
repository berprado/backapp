"""
Servicio de comunicación centralizado y mejorado.

Este módulo NO reemplaza las funciones existentes de verificar_comunicacion,
sino que ofrece un servicio adicional con funcionalidades mejoradas para
casos de uso futuros.

COMPATIBILIDAD: 100% - No afecta ninguna función existente.
"""

from typing import Tuple, Optional, Dict, List
from enum import Enum
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

# Importar las funciones existentes SIN modificarlas
from soap_services import verificar_comunicacion as verificar_operaciones
from business_logic import verificar_comunicacion as verificar_servicio_especifico

class TipoContingencia(Enum):
    """Tipos de contingencia según normativa SIN"""
    NORMAL = "0"
    SIN_RESPUESTA = "1"
    ERROR_SERVICIO = "2"
    PLANIFICADO = "3"
    PLANIFICADO_OTRO = "4"
    FALLA_SOFTWARE = "5"
    FALLA_HARDWARE = "6"
    CORTE_ENERGIA = "7"

@dataclass
class ResultadoComunicacion:
    """Resultado estructurado de verificación de comunicación"""
    conectado: bool
    mensaje: str
    tipo_contingencia: Optional[str] = None
    servicio: Optional[str] = None
    timestamp: Optional[datetime] = None

class CommunicationServiceEnhanced:
    """
    Servicio mejorado de comunicación que complementa (NO reemplaza) 
    las funciones existentes de verificar_comunicacion.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_resultados: Dict[str, ResultadoComunicacion] = {}
        
    def verificar_con_fallback(self) -> ResultadoComunicacion:
        """
        Verificación con fallback automático entre servicios.
        Usa las funciones existentes SIN modificarlas.
        """
        try:
            # PRIMERO: Usar la función principal existente
            mensaje, conectado, tipo_deducido = verificar_operaciones()
            
            if conectado:
                return ResultadoComunicacion(
                    conectado=True,
                    mensaje=mensaje,
                    servicio="operaciones",
                    timestamp=datetime.now()
                )
            else:
                # FALLBACK: Intentar otros servicios usando business_logic
                return self._verificar_servicios_alternativos(tipo_deducido)
                
        except Exception as e:
            self.logger.error(f"Error en verificación principal: {e}")
            return ResultadoComunicacion(
                conectado=False,
                mensaje=f"Error crítico: {e}",
                tipo_contingencia=TipoContingencia.FALLA_SOFTWARE.value,
                timestamp=datetime.now()
            )
    
    def _verificar_servicios_alternativos(self, tipo_sugerido: Optional[str]) -> ResultadoComunicacion:
        """
        Verifica servicios alternativos usando las funciones existentes
        """
        servicios_alternativos = [
            "Facturación Códigos",
            "Facturación Sincronización"
        ]
        
        for servicio in servicios_alternativos:
            try:
                # Usar la función existente de business_logic SIN modificarla
                exito, mensaje = verificar_servicio_especifico(servicio)
                if exito:
                    return ResultadoComunicacion(
                        conectado=True,
                        mensaje=f"Conectado vía {servicio}: {mensaje}",
                        servicio=servicio.lower().replace(" ", "_"),
                        timestamp=datetime.now()
                    )
            except Exception:
                continue
        
        # Si todos fallan
        return ResultadoComunicacion(
            conectado=False,
            mensaje="Todos los servicios sin respuesta",
            tipo_contingencia=tipo_sugerido or TipoContingencia.SIN_RESPUESTA.value,
            timestamp=datetime.now()
        )
    
    def verificar_servicio_especifico(self, servicio: str) -> ResultadoComunicacion:
        """
        Wrapper mejorado para verificar_comunicacion de business_logic
        """
        try:
            exito, mensaje = verificar_servicio_especifico(servicio)
            return ResultadoComunicacion(
                conectado=exito,
                mensaje=mensaje,
                servicio=servicio,
                timestamp=datetime.now()
            )
        except Exception as e:
            return ResultadoComunicacion(
                conectado=False,
                mensaje=f"Error: {e}",
                servicio=servicio,
                timestamp=datetime.now()
            )
    
    def obtener_estado_detallado(self) -> Dict[str, ResultadoComunicacion]:
        """
        Obtiene estado detallado de todos los servicios
        """
        servicios = [
            "Facturación Códigos",
            "Facturación Operaciones", 
            "Facturación Sincronización",
            "Documentos de Ajuste",
            "Facturación Compra-Venta"
        ]
        
        resultados = {}
        for servicio in servicios:
            resultados[servicio] = self.verificar_servicio_especifico(servicio)
            
        return resultados

# Instancia global opcional - NO interfiere con código existente
enhanced_communication = CommunicationServiceEnhanced()

# Funciones de conveniencia que mantienen compatibilidad
def verificar_comunicacion_mejorada() -> ResultadoComunicacion:
    """
    Función de conveniencia que usa el servicio mejorado
    pero NO interfiere con verificar_comunicacion existente
    """
    return enhanced_communication.verificar_con_fallback()

def obtener_diagnostico_completo() -> Dict[str, ResultadoComunicacion]:
    """
    Obtiene diagnóstico completo de todos los servicios
    """
    return enhanced_communication.obtener_estado_detallado()
