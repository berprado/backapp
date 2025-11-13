"""
Manejador centralizado de timeouts según protocolo oficial SIAT.

Este módulo implementa el protocolo oficial documentado por el SIN para
el manejo de timeouts en operaciones críticas (anulación, reversión, etc.):

1. Intentar la operación (hasta N reintentos)
2. Si persiste el timeout:
   - Verificar el estado REAL en SIAT
   - Si el estado coincide con el esperado: Sincronizar BD local
   - Si no coincide: Reportar fallo real

Referencia: Documentación SIAT - "Anulación de Facturas" (sección Timeouts)
Versión: 1.0.0
Fecha: 16/10/2025
"""

import time
from typing import Optional, Literal, Callable, Any, Dict
from logger_config import get_logger

logger = get_logger()

# Tipos de estado de factura según SIAT
EstadoFactura = Literal["VALIDA", "ANULADA", "OBSERVADA", "RECHAZADA"]


class TimeoutHandler:
    """
    Maneja timeouts en operaciones críticas siguiendo el protocolo oficial SIAT.
    
    Uso típico:
    >>> handler = TimeoutHandler(max_reintentos=3, tiempo_espera=5)
    >>> exito = handler.ejecutar_con_protocolo(
    ...     operacion_nombre="Reversión",
    ...     funcion_operacion=lambda: enviar_reversion_siat(cuf),
    ...     funcion_verificacion=lambda cuf, force: verificar_estado_factura(cuf, force),
    ...     estado_esperado="VALIDA",
    ...     identificador=cuf
    ... )
    """
    
    def __init__(self, max_reintentos: int = 3, tiempo_espera: int = 5):
        """
        Inicializa el manejador de timeouts.
        
        Args:
            max_reintentos: Número máximo de intentos antes de verificar en SIAT
            tiempo_espera: Segundos a esperar entre reintentos
        """
        self.max_reintentos = max_reintentos
        self.tiempo_espera = tiempo_espera
        logger.info(
            f"[TIMEOUT_HANDLER] Inicializado con max_reintentos={max_reintentos}, "
            f"tiempo_espera={tiempo_espera}s"
        )
    
    def ejecutar_con_protocolo(
        self,
        operacion_nombre: str,
        funcion_operacion: Callable[[], Any],
        funcion_verificacion: Callable[[str, bool], str],
        estado_esperado: EstadoFactura,
        identificador: str,
        funcion_sync: Optional[Callable[[str, str], bool]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta una operación crítica con manejo de timeout según protocolo SIAT.
        
        Args:
            operacion_nombre: Nombre descriptivo ("Anulación", "Reversión", etc.)
            funcion_operacion: Función que ejecuta la operación en SIAT (sin args)
            funcion_verificacion: Función(identificador, force_check) que verifica estado
            estado_esperado: Estado esperado si la operación tuvo éxito
            identificador: CUF, número de factura u otro identificador
            funcion_sync: Función opcional para sincronizar BD local
        
        Returns:
            Dict con:
            - 'exito': bool
            - 'response': respuesta de SIAT (si existe)
            - 'sincronizado': bool (si se aplicó sincronización)
            - 'mensaje': str descriptivo
        """
        logger.info(
            f"[TIMEOUT_HANDLER] Iniciando {operacion_nombre} "
            f"para {identificador[:30]}..."
        )
        
        resultado = {
            'exito': False,
            'response': None,
            'sincronizado': False,
            'mensaje': ''
        }
        
        for intento in range(1, self.max_reintentos + 1):
            try:
                logger.debug(
                    f"[TIMEOUT_HANDLER] {operacion_nombre} - "
                    f"Intento {intento}/{self.max_reintentos}"
                )
                
                # Ejecutar la operación
                response = funcion_operacion()
                
                # Caso 1: Respuesta exitosa recibida
                if response and self._es_respuesta_exitosa(response):
                    logger.info(
                        f"[TIMEOUT_HANDLER] ✅ {operacion_nombre} exitosa "
                        f"en intento {intento}"
                    )
                    resultado['exito'] = True
                    resultado['response'] = response
                    resultado['mensaje'] = f"{operacion_nombre} completada exitosamente"
                    return resultado
                
                # Caso 2: Respuesta con rechazo explícito
                if response and self._es_respuesta_rechazada(response):
                    mensajes = self._extraer_mensajes(response)
                    logger.error(
                        f"[TIMEOUT_HANDLER] ❌ {operacion_nombre} rechazada: {mensajes}"
                    )
                    resultado['exito'] = False
                    resultado['response'] = response
                    resultado['mensaje'] = f"{operacion_nombre} rechazada: {mensajes}"
                    return resultado
                
                # Caso 3: Respuesta ambigua (ni éxito ni rechazo claro)
                logger.warning(
                    f"[TIMEOUT_HANDLER] ⚠️ Respuesta ambigua en intento {intento}"
                )
                    
            except TimeoutError as e:
                logger.warning(
                    f"[TIMEOUT_HANDLER] ⏱️ TimeoutError en intento {intento}: {e}"
                )
                
            except ConnectionError as e:
                logger.warning(
                    f"[TIMEOUT_HANDLER] 🔌 ConnectionError en intento {intento}: {e}"
                )
                
            except Exception as e:
                error_tipo = type(e).__name__
                logger.warning(
                    f"[TIMEOUT_HANDLER] ⚠️ {error_tipo} en intento {intento}: {e}"
                )
            
            # Si no es el último intento, esperar y reintentar
            if intento < self.max_reintentos:
                logger.info(
                    f"[TIMEOUT_HANDLER] Esperando {self.tiempo_espera}s "
                    f"antes de reintentar..."
                )
                time.sleep(self.tiempo_espera)
                continue
            
            # Último intento falló: APLICAR PROTOCOLO OFICIAL
            logger.warning(
                f"[TIMEOUT_HANDLER] ⚠️ Todos los intentos de {operacion_nombre} "
                f"fallaron. Aplicando protocolo oficial..."
            )
            return self._verificar_y_sincronizar(
                operacion_nombre=operacion_nombre,
                funcion_verificacion=funcion_verificacion,
                estado_esperado=estado_esperado,
                identificador=identificador,
                funcion_sync=funcion_sync,
                resultado=resultado
            )
        
        # No debería llegar aquí, pero por seguridad
        resultado['mensaje'] = f"{operacion_nombre} falló después de {self.max_reintentos} intentos"
        return resultado
    
    def _verificar_y_sincronizar(
        self,
        operacion_nombre: str,
        funcion_verificacion: Callable[[str, bool], str],
        estado_esperado: EstadoFactura,
        identificador: str,
        funcion_sync: Optional[Callable[[str, str], bool]],
        resultado: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Implementa el paso crítico del protocolo oficial:
        Verifica el estado en SIAT y sincroniza BD local si es necesario.
        
        Este método implementa exactamente lo descrito en la documentación oficial:
        "Transcurrido un tiempo y antes de intentar nuevamente debemos verificar
        el estado de la factura. Si esta figura como [estado_esperado] simplemente
        completar la operación de forma local."
        """
        logger.warning(
            f"[TIMEOUT_HANDLER] 🔍 Verificando estado real en SIAT "
            f"(Protocolo Oficial)..."
        )
        
        try:
            # Forzar consulta real al SIAT (sin caché)
            estado_real = funcion_verificacion(identificador, True)
            
            logger.info(
                f"[TIMEOUT_HANDLER] Estado en SIAT: '{estado_real}' | "
                f"Esperado: '{estado_esperado}'"
            )
            
            # Normalizar estados para comparación
            estado_real_norm = self._normalizar_estado(estado_real)
            estado_esperado_norm = self._normalizar_estado(estado_esperado)
            
            if estado_real_norm == estado_esperado_norm:
                # ✅ LA OPERACIÓN SÍ SE COMPLETÓ EN SIAT
                logger.info(
                    f"[TIMEOUT_HANDLER] ✅ {operacion_nombre} completada en SIAT "
                    f"(confirmado por verificación). Sincronizando BD local..."
                )
                
                # Sincronizar BD local si se proporcionó la función
                if funcion_sync:
                    try:
                        sync_ok = funcion_sync(identificador, estado_esperado)
                        if sync_ok:
                            logger.info(
                                f"[TIMEOUT_HANDLER] ✅ BD local sincronizada correctamente"
                            )
                            resultado['sincronizado'] = True
                        else:
                            logger.error(
                                f"[TIMEOUT_HANDLER] ⚠️ Error al sincronizar BD local"
                            )
                    except Exception as e:
                        logger.error(
                            f"[TIMEOUT_HANDLER] ❌ Excepción al sincronizar BD: {e}"
                        )
                
                resultado['exito'] = True
                resultado['mensaje'] = (
                    f"{operacion_nombre} completada en SIAT (verificado). "
                    f"BD local {'sincronizada' if resultado['sincronizado'] else 'requiere sincronización manual'}"
                )
                return resultado
                
            else:
                # ❌ LA OPERACIÓN NO SE COMPLETÓ
                logger.error(
                    f"[TIMEOUT_HANDLER] ❌ {operacion_nombre} NO completada en SIAT. "
                    f"Estado actual: '{estado_real}' (esperado: '{estado_esperado}')"
                )
                resultado['exito'] = False
                resultado['mensaje'] = (
                    f"{operacion_nombre} no completada. "
                    f"Estado en SIAT: {estado_real} (esperado: {estado_esperado})"
                )
                return resultado
                
        except Exception as e:
            logger.error(
                f"[TIMEOUT_HANDLER] ❌ Error crítico al verificar estado en SIAT: {e}"
            )
            resultado['exito'] = False
            resultado['mensaje'] = f"Error al verificar estado en SIAT: {e}"
            return resultado
    
    def _es_respuesta_exitosa(self, response: Any) -> bool:
        """Determina si la respuesta indica éxito."""
        # Verificar atributo 'transaccion'
        if hasattr(response, 'transaccion'):
            return response.transaccion is True
        
        # Verificar código de estado exitoso
        if hasattr(response, 'codigoEstado'):
            # 905 = Anulada, 907 = Reversión OK, 908 = Validada
            return response.codigoEstado in [905, 907, 908]
        
        return False
    
    def _es_respuesta_rechazada(self, response: Any) -> bool:
        """Determina si la respuesta indica rechazo explícito."""
        # Si transaccion es explícitamente False
        if hasattr(response, 'transaccion'):
            if response.transaccion is False:
                return True
        
        # Verificar códigos de error
        if hasattr(response, 'codigoEstado'):
            # 904 = Observada, 909 = Rechazada
            return response.codigoEstado in [904, 909]
        
        # Si hay mensajes de error
        if hasattr(response, 'mensajesList') and response.mensajesList:
            return True
        
        return False
    
    def _extraer_mensajes(self, response: Any) -> str:
        """Extrae mensajes de error de la respuesta."""
        mensajes = []
        
        if hasattr(response, 'mensajesList'):
            for msg in response.mensajesList:
                if hasattr(msg, 'codigo') and hasattr(msg, 'descripcion'):
                    mensajes.append(f"[{msg.codigo}] {msg.descripcion}")
                elif hasattr(msg, 'descripcion'):
                    mensajes.append(msg.descripcion)
        
        if hasattr(response, 'codigoDescripcion'):
            mensajes.append(response.codigoDescripcion)
        
        return " | ".join(mensajes) if mensajes else "Sin mensajes específicos"
    
    def _normalizar_estado(self, estado: Any) -> str:
        """
        Normaliza estados para comparación consistente.
        
        Maneja tuplas, strings y otros tipos devueltos por verificación.
        Ej: (True, 'Factura: ANULADA') → 'ANULADA'
            'VALIDADA' → 'VALIDADA'
        
        Args:
            estado: Puede ser tuple, str o cualquier tipo
            
        Returns:
            str: Estado normalizado en mayúsculas
        """
        if not estado:
            return ""
        
        # Si es una tupla (resultado de verificación), extraer el segundo elemento
        if isinstance(estado, tuple):
            # Ej: (True, 'Factura: ANULADA') → 'Factura: ANULADA'
            estado = estado[1] if len(estado) > 1 else estado[0]
        
        # Convertir a string y normalizar
        estado_str = str(estado).strip().upper()
        
        # Extraer el estado del texto (por si viene "Factura: ANULADA")
        if "ANULADA" in estado_str or "ANULADO" in estado_str:
            return "ANULADA"
        elif "VALIDA" in estado_str or "VALIDADA" in estado_str:
            return "VALIDA"
        elif "RECHAZADA" in estado_str or "RECHAZADO" in estado_str:
            return "RECHAZADA"
        elif "OBSERVADA" in estado_str or "OBSERVADO" in estado_str:
            return "OBSERVADA"
        
        # Si no coincide con patrones conocidos, devolver limpio
        return estado_str


# Instancia global singleton
timeout_handler = TimeoutHandler(max_reintentos=3, tiempo_espera=5)


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

def ejecutar_anulacion_con_protocolo(
    cuf: str,
    funcion_anular: Callable[[], Any],
    funcion_verificar: Callable[[str, bool], str],
    funcion_sync: Optional[Callable[[str, str], bool]] = None
) -> Dict[str, Any]:
    """
    Ejecuta una anulación siguiendo el protocolo oficial de timeouts.
    
    Args:
        cuf: CUF de la factura a anular
        funcion_anular: Función que envía la anulación al SIAT
        funcion_verificar: Función que verifica el estado en SIAT
        funcion_sync: Función opcional para sincronizar BD local
    
    Returns:
        Diccionario con resultado de la operación
    """
    return timeout_handler.ejecutar_con_protocolo(
        operacion_nombre="Anulación",
        funcion_operacion=funcion_anular,
        funcion_verificacion=funcion_verificar,
        estado_esperado="ANULADA",
        identificador=cuf,
        funcion_sync=funcion_sync
    )


def ejecutar_reversion_con_protocolo(
    cuf: str,
    funcion_revertir: Callable[[], Any],
    funcion_verificar: Callable[[str, bool], str],
    funcion_sync: Optional[Callable[[str, str], bool]] = None
) -> Dict[str, Any]:
    """
    Ejecuta una reversión siguiendo el protocolo oficial de timeouts.
    
    Args:
        cuf: CUF de la factura a revertir
        funcion_revertir: Función que envía la reversión al SIAT
        funcion_verificar: Función que verifica el estado en SIAT
        funcion_sync: Función opcional para sincronizar BD local
    
    Returns:
        Diccionario con resultado de la operación
    """
    return timeout_handler.ejecutar_con_protocolo(
        operacion_nombre="Reversión",
        funcion_operacion=funcion_revertir,
        funcion_verificacion=funcion_verificar,
        estado_esperado="VALIDA",
        identificador=cuf,
        funcion_sync=funcion_sync
    )
