"""
Servicio centralizado para la verificación de comunicación con el SIN.

Este módulo crea un servicio PARALELO que NO reemplaza las funciones existentes,
sino que proporciona funcionalidades adicionales y mejoradas manteniendo 
compatibilidad total con el código existente.

IMPORTANTE: 
- NO modifica las funciones existentes en soap_services.py, business_logic.py, etc.
- NO cambia imports existentes
- SOLO proporciona nuevas funcionalidades opcionales
"""

import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
from enum import Enum
import streamlit as st

# Importar las funciones existentes SIN modificarlas
from soap_services import verificar_comunicacion as soap_verificar_comunicacion
from business_logic import verificar_comunicacion as business_verificar_comunicacion
from logger_config import get_logger

logger = get_logger()

class TipoContingencia(Enum):
    """Tipos de contingencia según normativa SIN - NUEVOS códigos estandarizados"""
    NORMAL = "0"  # Sin contingencia
    SIN_RESPUESTA = "1"  # Sin respuesta del SIN
    ERROR_SERVICIO = "2"  # Error en servicios
    FALLA_SOFTWARE = "5"  # Virus informático o falla de software
    FALLA_HARDWARE = "6"  # Cambio de infraestructura o falla de hardware
    CORTE_ENERGIA = "7"  # Corte de energía eléctrica

class EstadoComunicacion(Enum):
    """Estados posibles de comunicación - NUEVOS estados para mejor control"""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MONITORING = "MONITORING"  # Verificando conexión
    RECOVERING = "RECOVERING"  # Recuperando conexión

class CommunicationManager:
    """
    Gestor MEJORADO para verificación de comunicación.
    
    NOTA IMPORTANTE: Este servicio NO reemplaza las funciones existentes.
    Es un servicio ADICIONAL que puede usarse opcionalmente para funcionalidades avanzadas.
    """
    
    def __init__(self):
        self.ultimo_check = None
        self.estado_actual = EstadoComunicacion.MONITORING
        self.intentos_fallidos = 0
        self.max_intentos = 3
        self.historial_verificaciones = []
        
    def verificar_comunicacion_principal(self) -> Tuple[str, bool, Optional[str]]:
        """
        Wrapper que usa la función EXISTENTE de soap_services.py sin modificarla.
        
        Returns:
            tuple: (mensaje, conectado, tipo_deducido) - MISMO formato que soap_services
        """
        try:
            logger.info("Usando verificación EXISTENTE de soap_services.py")
            # Llamar a la función ORIGINAL sin modificaciones
            resultado = soap_verificar_comunicacion()
            
            # Registrar en historial para análisis (NUEVA funcionalidad)
            self._registrar_verificacion("soap_services", resultado)
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error en verificación principal: {e}")
            return f"Error crítico: {e}", False, TipoContingencia.FALLA_SOFTWARE.value
    
    def verificar_comunicacion_por_servicio(self, servicio: str) -> Tuple[bool, str]:
        """
        Wrapper que usa la función EXISTENTE de business_logic.py sin modificarla.
        
        Args:
            servicio: Nombre del servicio a verificar
            
        Returns:
            tuple: (conectado, mensaje) - MISMO formato que business_logic
        """
        try:
            logger.info(f"Usando verificación EXISTENTE de business_logic.py para {servicio}")
            # Llamar a la función ORIGINAL sin modificaciones
            resultado = business_verificar_comunicacion(servicio)
            
            # Registrar en historial para análisis (NUEVA funcionalidad)
            self._registrar_verificacion(f"business_logic_{servicio}", resultado)
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error en verificación de servicio {servicio}: {e}")
            return False, f"Error crítico: {e}"
    
    def verificar_comunicacion_completa(self) -> Dict[str, Any]:
        """
        NUEVA funcionalidad: Verificación completa usando TODAS las funciones existentes.
        
        Returns:
            dict: Resultado completo con detalles de todas las verificaciones
        """
        resultado_completo = {
            "timestamp": datetime.now().isoformat(),
            "verificacion_principal": None,
            "verificaciones_servicios": {},
            "estado_general": EstadoComunicacion.MONITORING.value,
            "recomendacion": ""
        }
        
        try:
            # 1. Verificación principal (soap_services.py - EXISTENTE)
            mensaje, conectado, tipo = self.verificar_comunicacion_principal()
            resultado_completo["verificacion_principal"] = {
                "mensaje": mensaje,
                "conectado": conectado,
                "tipo_contingencia": tipo,
                "fuente": "soap_services.py"
            }
            
            # 2. Verificaciones por servicio (business_logic.py - EXISTENTE)
            servicios = [
                "Facturación Códigos",
                "Facturación Operaciones", 
                "Facturación Sincronización"
            ]
            
            for servicio in servicios:
                try:
                    conectado_srv, mensaje_srv = self.verificar_comunicacion_por_servicio(servicio)
                    resultado_completo["verificaciones_servicios"][servicio] = {
                        "conectado": conectado_srv,
                        "mensaje": mensaje_srv,
                        "fuente": "business_logic.py"
                    }
                except Exception as e:
                    resultado_completo["verificaciones_servicios"][servicio] = {
                        "conectado": False,
                        "mensaje": f"Error: {e}",
                        "fuente": "business_logic.py"
                    }
            
            # 3. Análisis general (NUEVA funcionalidad)
            resultado_completo = self._analizar_resultados_completos(resultado_completo)
            
            return resultado_completo
            
        except Exception as e:
            logger.error(f"Error en verificación completa: {e}")
            resultado_completo["estado_general"] = EstadoComunicacion.OFFLINE.value
            resultado_completo["recomendacion"] = f"Error crítico: {e}"
            return resultado_completo
    
    def _registrar_verificacion(self, fuente: str, resultado: Any):
        """NUEVA funcionalidad: Registra verificaciones para análisis histórico"""
        registro = {
            "timestamp": datetime.now().isoformat(),
            "fuente": fuente,
            "resultado": resultado
        }
        
        self.historial_verificaciones.append(registro)
        
        # Mantener solo últimos 50 registros
        if len(self.historial_verificaciones) > 50:
            self.historial_verificaciones = self.historial_verificaciones[-50:]
    
    def _analizar_resultados_completos(self, resultado_completo: Dict) -> Dict:
        """NUEVA funcionalidad: Analiza todos los resultados y da recomendaciones"""
        principal = resultado_completo["verificacion_principal"]
        servicios = resultado_completo["verificaciones_servicios"]
        
        # Determinar estado general
        if principal and principal["conectado"]:
            servicios_ok = sum(1 for s in servicios.values() if s["conectado"])
            total_servicios = len(servicios)
            
            if servicios_ok == total_servicios:
                resultado_completo["estado_general"] = EstadoComunicacion.ONLINE.value
                resultado_completo["recomendacion"] = "Sistema completamente online. Todos los servicios funcionan."
            elif servicios_ok > total_servicios // 2:
                resultado_completo["estado_general"] = EstadoComunicacion.ONLINE.value
                resultado_completo["recomendacion"] = f"Sistema mayormente online. {servicios_ok}/{total_servicios} servicios funcionan."
            else:
                resultado_completo["estado_general"] = EstadoComunicacion.MONITORING.value
                resultado_completo["recomendacion"] = f"Conexión inestable. Solo {servicios_ok}/{total_servicios} servicios funcionan."
        else:
            resultado_completo["estado_general"] = EstadoComunicacion.OFFLINE.value
            tipo_contingencia = principal.get("tipo_contingencia") if principal else None
            if tipo_contingencia:
                nombre_contingencia = TipoContingencia(tipo_contingencia).name
                resultado_completo["recomendacion"] = f"Sistema offline. Activar contingencia tipo: {nombre_contingencia}"
            else:
                resultado_completo["recomendacion"] = "Sistema offline. Activar contingencia general."
        
        return resultado_completo
    
    def obtener_estado_persistente(self) -> Dict:
        """NUEVA funcionalidad: Obtiene/mantiene estado en session_state"""
        if 'communication_manager_state' not in st.session_state:
            st.session_state.communication_manager_state = {
                'ultimo_resultado_completo': None,
                'ultima_verificacion': None,
                'historial_resumido': []
            }
        return st.session_state.communication_manager_state
    
    def mostrar_diagnostico_completo(self):
        """NUEVA funcionalidad: Muestra diagnóstico detallado en Streamlit"""
        st.subheader("🔧 Diagnóstico Completo de Comunicación")
        
        with st.spinner("Ejecutando diagnóstico completo..."):
            resultado = self.verificar_comunicacion_completa()
        
        # Mostrar estado general
        estado = resultado["estado_general"]
        if estado == EstadoComunicacion.ONLINE.value:
            st.success(f"🟢 **{estado}** - {resultado['recomendacion']}")
        elif estado == EstadoComunicacion.MONITORING.value:
            st.warning(f"🟡 **{estado}** - {resultado['recomendacion']}")
        else:
            st.error(f"🔴 **{estado}** - {resultado['recomendacion']}")
        
        # Mostrar detalles
        with st.expander("📊 Detalles de Verificación"):
            # Verificación principal
            st.subheader("🎯 Verificación Principal (soap_services.py)")
            principal = resultado["verificacion_principal"]
            if principal:
                if principal["conectado"]:
                    st.success(f"✅ {principal['mensaje']}")
                else:
                    st.error(f"❌ {principal['mensaje']}")
                    if principal["tipo_contingencia"]:
                        tipo_nombre = TipoContingencia(principal["tipo_contingencia"]).name
                        st.caption(f"Tipo de contingencia sugerido: {tipo_nombre}")
            
            # Verificaciones por servicio
            st.subheader("🔧 Verificaciones por Servicio (business_logic.py)")
            servicios = resultado["verificaciones_servicios"]
            for nombre_servicio, detalle in servicios.items():
                if detalle["conectado"]:
                    st.success(f"✅ **{nombre_servicio}**: {detalle['mensaje']}")
                else:
                    st.error(f"❌ **{nombre_servicio}**: {detalle['mensaje']}")
        
        # Guardar en estado persistente
        estado_persistente = self.obtener_estado_persistente()
        estado_persistente['ultimo_resultado_completo'] = resultado
        estado_persistente['ultima_verificacion'] = datetime.now().isoformat()

# Instancia global del gestor MEJORADO (NO reemplaza funciones existentes)
communication_manager = CommunicationManager()

# ============================================================================
# FUNCIONES DE COMPATIBILIDAD TOTAL - Mantienen todas las funcionalidades existentes
# ============================================================================

def verificar_comunicacion_legacy_compatible():
    """
    Función de conveniencia que mantiene TOTAL compatibilidad con main.py
    y otros módulos que usan soap_services.verificar_comunicacion()
    
    Returns:
        tuple: (mensaje, conectado, tipo_deducido) - MISMO formato que soap_services
    """
    return communication_manager.verificar_comunicacion_principal()

def verificar_comunicacion_por_servicio_compatible(servicio: str):
    """
    Función de conveniencia que mantiene TOTAL compatibilidad con módulos
    que usan business_logic.verificar_comunicacion(servicio)
    
    Args:
        servicio: Nombre del servicio a verificar
        
    Returns:
        tuple: (conectado, mensaje) - MISMO formato que business_logic
    """
    return communication_manager.verificar_comunicacion_por_servicio(servicio)
