"""
Lógica de negocio principal del sistema de facturación refactorizado.
Orquesta todas las operaciones de facturación según normativas del SIN.
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date
from enum import Enum
import asyncio

from data.rf_models import Factura, Cliente, DetalleFactura, EstadoFactura, TipoEmision
from core.rf_connection_detector import detect_mode, ConnectionMode, get_cached_mode
from utils.rf_logger import log_info, log_error, log_warning, log_factura_action
from config.rf_settings import settings

class OperationResult(Enum):
    """Resultados posibles de operaciones de facturación."""
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    OFFLINE_QUEUED = "OFFLINE_QUEUED"

class RFBusinessLogic:
    """
    Lógica de negocio principal para el sistema de facturación.
    Maneja el flujo completo desde la creación hasta el envío de facturas.
    """
    
    def __init__(self):
        """Inicializa la lógica de negocio."""
        self.current_mode = None
        self.offline_queue = []  # Cola para facturas offline
        
    async def procesar_factura(self, factura: Factura) -> Tuple[OperationResult, Dict[str, Any]]:
        """
        Procesa una factura completa desde validación hasta envío.
        
        Args:
            factura: Factura a procesar
            
        Returns:
            Tupla con resultado y detalles de la operación
        """
        operation_details = {
            "factura_id": f"F{factura.numero_factura:06d}",
            "timestamp": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            log_factura_action("INICIO_PROCESAMIENTO", factura_id=operation_details["factura_id"])
            
            # Paso 1: Validar factura
            step_result = self._validar_factura_completa(factura)
            operation_details["steps"].append(step_result)
            
            if not step_result["success"]:
                log_factura_action("VALIDACION_FALLIDA", 
                                 factura_id=operation_details["factura_id"],
                                 status="ERROR",
                                 details=step_result)
                return OperationResult.ERROR, operation_details
            
            # Paso 2: Detectar modo de conexión
            mode_result = await self._detectar_y_configurar_modo()
            operation_details["steps"].append(mode_result)
            
            # Paso 3: Procesar según el modo detectado
            if mode_result["mode"] == ConnectionMode.ONLINE:
                process_result = await self._procesar_factura_online(factura)
            else:
                process_result = self._procesar_factura_offline(factura)
            
            operation_details["steps"].append(process_result)
            
            # Determinar resultado final
            if process_result["success"]:
                final_result = OperationResult.SUCCESS if mode_result["mode"] == ConnectionMode.ONLINE else OperationResult.OFFLINE_QUEUED
                log_factura_action("PROCESAMIENTO_COMPLETADO", 
                                 factura_id=operation_details["factura_id"],
                                 status="SUCCESS")
            else:
                final_result = OperationResult.ERROR
                log_factura_action("PROCESAMIENTO_FALLIDO", 
                                 factura_id=operation_details["factura_id"],
                                 status="ERROR",
                                 details=process_result)
            
            return final_result, operation_details
            
        except Exception as e:
            log_error("Error crítico en procesamiento de factura", exception=e, 
                     extra_data={"factura_id": operation_details["factura_id"]})
            
            operation_details["steps"].append({
                "step": "error_critico",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return OperationResult.ERROR, operation_details
    
    def _validar_factura_completa(self, factura: Factura) -> Dict[str, Any]:
        """
        Validación completa de la factura según normativas del SIN.
        
        Args:
            factura: Factura a validar
            
        Returns:
            Resultado de la validación
        """
        validation_result = {
            "step": "validacion_factura",
            "success": True,
            "errors": [],
            "warnings": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Validación básica del modelo
            factura.validate()
            
            # Validaciones específicas del SIN
            self._validar_fechas_sin(factura, validation_result)
            self._validar_cliente_sin(factura.cliente, validation_result)
            self._validar_montos_sin(factura, validation_result)
            self._validar_configuracion_sistema(validation_result)
            
            # Determinar si la validación fue exitosa
            validation_result["success"] = len(validation_result["errors"]) == 0
            
            if validation_result["success"]:
                log_info("Validación de factura exitosa", extra_data={
                    "numero": factura.numero_factura,
                    "warnings": len(validation_result["warnings"])
                })
            else:
                log_warning("Errores en validación de factura", extra_data={
                    "numero": factura.numero_factura,
                    "errors": validation_result["errors"]
                })
            
        except Exception as e:
            validation_result["success"] = False
            validation_result["errors"].append(f"Error en validación: {str(e)}")
            log_error("Error durante validación de factura", exception=e)
        
        return validation_result
    
    def _validar_fechas_sin(self, factura: Factura, result: Dict[str, Any]):
        """Validaciones específicas de fechas según el SIN."""
        # Fecha no puede ser futura
        if factura.fecha_emision > date.today():
            result["errors"].append("La fecha de emisión no puede ser futura")
        
        # Fecha no puede ser muy antigua (más de 30 días en producción)
        if settings.siat['codigo_ambiente'] == 1:  # Producción
            dias_antiguedad = (date.today() - factura.fecha_emision).days
            if dias_antiguedad > 30:
                result["warnings"].append("Factura con más de 30 días de antigüedad")
    
    def _validar_cliente_sin(self, cliente: Cliente, result: Dict[str, Any]):
        """Validaciones específicas del cliente según el SIN."""
        # Validar NITs especiales
        nits_especiales = ["99001", "99002", "99003"]
        if cliente.nit in nits_especiales:
            if cliente.codigo_excepcion.value != 1:
                result["errors"].append(f"NIT {cliente.nit} requiere código de excepción 1")
        
        # Validar longitud de razón social
        if len(cliente.razon_social) > 500:
            result["errors"].append("Razón social excede 500 caracteres")
    
    def _validar_montos_sin(self, factura: Factura, result: Dict[str, Any]):
        """Validaciones de montos según normativas del SIN."""
        # Verificar que el monto total sea positivo
        if factura.monto_total_redondeado <= 0:
            result["errors"].append("El monto total debe ser mayor a cero")
        
        # Verificar límites máximos (si aplican)
        monto_maximo_sin_nit = 1000  # Ejemplo: 1000 Bs
        if factura.cliente.nit in ["99001", "99002"] and factura.monto_total_redondeado > monto_maximo_sin_nit:
            result["warnings"].append(f"Monto elevado ({factura.monto_total_redondeado} Bs) para venta sin NIT")
    
    def _validar_configuracion_sistema(self, result: Dict[str, Any]):
        """Valida que la configuración del sistema sea correcta."""
        config_validation = settings.validate_configuration()
        
        if not config_validation['valid']:
            result["errors"].extend([f"Config: {error}" for error in config_validation['errors']])
        
        if config_validation['warnings']:
            result["warnings"].extend([f"Config: {warning}" for warning in config_validation['warnings']])
    
    async def _detectar_y_configurar_modo(self) -> Dict[str, Any]:
        """
        Detecta el modo de conexión y configura el sistema accordingly.
        
        Returns:
            Resultado de la detección de modo
        """
        mode_result = {
            "step": "deteccion_modo",
            "success": True,
            "mode": ConnectionMode.OFFLINE,
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Intentar obtener modo cacheado primero
            cached_mode = get_cached_mode()
            if cached_mode:
                mode, details = cached_mode
                mode_result["mode"] = mode
                mode_result["details"] = details
                mode_result["cached"] = True
                log_info(f"Usando modo cacheado: {mode.value}")
            else:
                # Detectar modo de conexión
                mode, details = await detect_mode(force_check=True)
                mode_result["mode"] = mode
                mode_result["details"] = details
                mode_result["cached"] = False
                log_info(f"Modo detectado: {mode.value}", extra_data=details)
            
            self.current_mode = mode_result["mode"]
            
        except Exception as e:
            log_error("Error en detección de modo", exception=e)
            mode_result["success"] = False
            mode_result["error"] = str(e)
            mode_result["mode"] = ConnectionMode.OFFLINE  # Fallback a offline
            self.current_mode = ConnectionMode.OFFLINE
        
        return mode_result
    
    async def _procesar_factura_online(self, factura: Factura) -> Dict[str, Any]:
        """
        Procesa una factura en modo online.
        
        Args:
            factura: Factura a procesar
            
        Returns:
            Resultado del procesamiento online
        """
        process_result = {
            "step": "procesamiento_online",
            "success": False,
            "cuf_generated": False,
            "xml_generated": False,
            "sent_to_sin": False,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            log_info("Iniciando procesamiento online", extra_data={"numero": factura.numero_factura})
            
            # Paso 1: Generar CUF
            cuf_result = self._generar_cuf(factura)
            if cuf_result["success"]:
                factura.cuf = cuf_result["cuf"]
                process_result["cuf_generated"] = True
                process_result["cuf"] = cuf_result["cuf"]
            else:
                process_result["error"] = "Error generando CUF"
                return process_result
            
            # Paso 2: Generar XML
            xml_result = self._generar_xml_factura(factura)
            if xml_result["success"]:
                process_result["xml_generated"] = True
                process_result["xml_path"] = xml_result["path"]
                factura.xml_path = xml_result["path"]
            else:
                process_result["error"] = "Error generando XML"
                return process_result
            
            # Paso 3: Enviar al SIN (simulado por ahora)
            sin_result = await self._enviar_factura_sin(factura)
            if sin_result["success"]:
                process_result["sent_to_sin"] = True
                process_result["codigo_recepcion"] = sin_result["codigo_recepcion"]
                factura.codigo_recepcion = sin_result["codigo_recepcion"]
                factura.fecha_recepcion = datetime.now()
                factura.set_estado(EstadoFactura.VALIDADA, "Factura enviada y validada por el SIN")
            else:
                process_result["error"] = f"Error enviando al SIN: {sin_result['error']}"
                factura.set_estado(EstadoFactura.OBSERVADA, f"Error en envío: {sin_result['error']}")
                return process_result
            
            process_result["success"] = True
            log_factura_action("PROCESAMIENTO_ONLINE_EXITOSO", 
                             factura_id=f"F{factura.numero_factura:06d}",
                             details={"cuf": factura.cuf, "codigo_recepcion": factura.codigo_recepcion})
            
        except Exception as e:
            log_error("Error en procesamiento online", exception=e)
            process_result["error"] = str(e)
        
        return process_result
    
    def _procesar_factura_offline(self, factura: Factura) -> Dict[str, Any]:
        """
        Procesa una factura en modo offline.
        
        Args:
            factura: Factura a procesar
            
        Returns:
            Resultado del procesamiento offline
        """
        process_result = {
            "step": "procesamiento_offline",
            "success": False,
            "queued": False,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            log_info("Iniciando procesamiento offline", extra_data={"numero": factura.numero_factura})
            
            # Cambiar tipo de emisión a offline
            factura.tipo_emision = TipoEmision.OFFLINE
            
            # Generar CUF con CUFD offline (último válido)
            cuf_result = self._generar_cuf_offline(factura)
            if cuf_result["success"]:
                factura.cuf = cuf_result["cuf"]
            else:
                process_result["error"] = "Error generando CUF offline"
                return process_result
            
            # Generar XML offline
            xml_result = self._generar_xml_factura(factura)
            if xml_result["success"]:
                factura.xml_path = xml_result["path"]
            else:
                process_result["error"] = "Error generando XML offline"
                return process_result
            
            # Agregar a cola offline
            self.offline_queue.append({
                "factura": factura,
                "timestamp": datetime.now(),
                "attempts": 0
            })
            
            factura.set_estado(EstadoFactura.BORRADOR, "Factura procesada offline, pendiente de envío")
            
            process_result["success"] = True
            process_result["queued"] = True
            process_result["queue_size"] = len(self.offline_queue)
            
            log_factura_action("PROCESAMIENTO_OFFLINE_EXITOSO", 
                             factura_id=f"F{factura.numero_factura:06d}",
                             details={"queue_size": len(self.offline_queue)})
            
        except Exception as e:
            log_error("Error en procesamiento offline", exception=e)
            process_result["error"] = str(e)
        
        return process_result
    
    def _generar_cuf(self, factura: Factura) -> Dict[str, Any]:
        """Genera el CUF (Código Único de Facturación) para modo online."""
        # TODO: Implementar generación real de CUF según algoritmo del SIN
        cuf_mock = f"{settings.siat['nit']}{factura.fecha_emision.strftime('%Y%m%d')}{factura.numero_factura:06d}ONLINE"
        
        return {
            "success": True,
            "cuf": cuf_mock,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generar_cuf_offline(self, factura: Factura) -> Dict[str, Any]:
        """Genera el CUF para modo offline usando último CUFD válido."""
        # TODO: Implementar generación real de CUF offline
        cuf_mock = f"{settings.siat['nit']}{factura.fecha_emision.strftime('%Y%m%d')}{factura.numero_factura:06d}OFFLINE"
        
        return {
            "success": True,
            "cuf": cuf_mock,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generar_xml_factura(self, factura: Factura) -> Dict[str, Any]:
        """Genera el XML de la factura según esquemas del SIN."""
        # TODO: Implementar generación real de XML
        xml_filename = f"factura_{factura.cuf}.xml"
        xml_path = f"storage/offline_xmls/{xml_filename}"
        
        # Simular generación exitosa
        return {
            "success": True,
            "path": xml_path,
            "filename": xml_filename,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _enviar_factura_sin(self, factura: Factura) -> Dict[str, Any]:
        """Envía la factura al SIN en modo online."""
        # TODO: Implementar envío real al SIN
        
        # Simular envío exitoso
        codigo_recepcion_mock = f"REC{datetime.now().strftime('%Y%m%d%H%M%S')}{factura.numero_factura:04d}"
        
        return {
            "success": True,
            "codigo_recepcion": codigo_recepcion_mock,
            "estado": "VALIDADA",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_estadisticas_procesamiento(self) -> Dict[str, Any]:
        """Obtiene estadísticas del procesamiento de facturas."""
        return {
            "modo_actual": self.current_mode.value if self.current_mode else "No detectado",
            "facturas_offline_pendientes": len(self.offline_queue),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_cola_offline(self) -> List[Dict[str, Any]]:
        """Obtiene la cola de facturas offline pendientes."""
        return [
            {
                "numero_factura": item["factura"].numero_factura,
                "cliente": item["factura"].cliente.razon_social,
                "monto": str(item["factura"].monto_total_redondeado),
                "timestamp": item["timestamp"].isoformat(),
                "attempts": item["attempts"]
            }
            for item in self.offline_queue
        ]

# Instancia global de la lógica de negocio
rf_business = RFBusinessLogic()

# Funciones de conveniencia
async def procesar_factura(factura: Factura) -> Tuple[OperationResult, Dict[str, Any]]:
    """Función de conveniencia para procesar una factura."""
    return await rf_business.procesar_factura(factura)

def get_estadisticas() -> Dict[str, Any]:
    """Función de conveniencia para obtener estadísticas."""
    return rf_business.get_estadisticas_procesamiento()

def get_cola_offline() -> List[Dict[str, Any]]:
    """Función de conveniencia para obtener la cola offline."""
    return rf_business.get_cola_offline()
