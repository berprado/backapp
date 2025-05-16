# contingencia_auto.py

import os
import zipfile
from datetime import datetime
from database import (
    obtener_evento_abierto,
    get_cufd_vigente,
    actualizar_evento_final
)
from soap_services import (
    verificar_comunicacion,
    enviar_evento_significativo
)
from logger_config import get_eventos_logger  # Importación corregida - eliminado el prefijo facturador

# Logger específico para eventos significativos
logger = get_eventos_logger()

def finalizar_evento_si_conectado() -> tuple[str, bool, str | None]: # Actualizado tipo de retorno
    """
    Verifica la conectividad y devuelve el estado completo de la comunicación.
    
    NOTA: La funcionalidad original de cierre de eventos de esta función está desactivada 
    y debe realizarse manualmente. En el flujo de inicio de main.py, su propósito
    principal es realizar una verificación de comunicación inicial.
    
    Returns:
        tuple[str, bool, str | None]: Una tupla conteniendo:
            - mensaje (str): Descripción del estado de la comunicación.
            - conectado (bool): True si hay conexión, False en caso contrario.
            - tipo_deducido (str | None): Código del evento de contingencia sugerido si no hay conexión, o None.
    """
    logger.info("Verificando conectividad inicial")
    mensaje, conectado, tipo_deducido = verificar_comunicacion()
    
    if not conectado:
        logger.warning(f"Conexión inicial no disponible. Estado: {mensaje}, Tipo deducido: {tipo_deducido}")
    else:
        logger.info(f"Conexión inicial disponible. Estado: {mensaje}")

    evento = obtener_evento_abierto()
    if not evento:
        logger.info("No hay eventos abiertos pendientes de cierre")
        # Devolvemos el estado de la comunicación independientemente de si hay evento o no.
        # En main.py, si hay un evento_activo, este resultado de comunicación no se usará
        # para la decisión online/offline directa, pero la función cumple con su contrato de retorno.
    else:
        logger.info(f"Hay un evento abierto (#{evento['id']}) pero se requiere cierre manual según la configuración actual.")
        
    return mensaje, conectado, tipo_deducido

def finalizar_evento_manual(evento_id=None):
    """
    Finaliza un evento significativo específico o el evento activo si no se proporciona ID.
    Esta función requiere que haya conexión con el SIN.
    
    Args:
        evento_id (int, optional): ID del evento a finalizar. Si es None, se busca el evento activo.
    
    Returns:
        dict: Diccionario con el resultado de la operación
            {
                'exito': bool,
                'mensaje': str,
                'codigo_recepcion': str o None,
                'facturas_comprimidas': int,
                'ruta_zip': str o None
            }
    """
    logger.info(f"Iniciando finalización manual de evento {evento_id or 'activo'}")
    mensaje, conectado, _ = verificar_comunicacion()
    
    if not conectado:
        logger.warning(f"Conexión no disponible para finalizar eventos. Estado: {mensaje}")
        return {
            'exito': False,
            'mensaje': f"No hay conexión con el SIN: {mensaje}",
            'codigo_recepcion': None,
            'facturas_comprimidas': 0,
            'ruta_zip': None
        }

    # Obtener el evento a finalizar
    evento = None
    if evento_id is None:
        evento = obtener_evento_abierto()
        if not evento:
            return {
                'exito': False,
                'mensaje': "No hay eventos abiertos pendientes de cierre",
                'codigo_recepcion': None,
                'facturas_comprimidas': 0,
                'ruta_zip': None
            }
    else:
        # Aquí se debería implementar la obtención de un evento específico por ID
        # Por ahora, usamos el evento activo
        evento = obtener_evento_abierto()
        if not evento or evento['id'] != evento_id:
            return {
                'exito': False,
                'mensaje': f"No se encontró el evento con ID {evento_id}",
                'codigo_recepcion': None,
                'facturas_comprimidas': 0,
                'ruta_zip': None
            }

    logger.info(f"Iniciando proceso de finalización para evento #{evento['id']}")
    
    # Validación de CUFD vigente
    cufd_actual = get_cufd_vigente()
    if not cufd_actual:
        logger.error("No se pudo obtener CUFD vigente para finalizar evento - proceso abortado")
        return {
            'exito': False,
            'mensaje': "No se pudo obtener CUFD vigente para finalizar el evento",
            'codigo_recepcion': None,
            'facturas_comprimidas': 0,
            'ruta_zip': None
        }

    try:
        fecha_fin = datetime.now()
        logger.info(f"Enviando solicitud para finalizar evento #{evento['id']} al SIN")
        logger.debug(f"Datos del evento: código={evento['codigo_evento']}, inicio={evento['fecha_inicio']}, fin={fecha_fin}")

        # Enviar evento al SIN
        codigo_recepcion, transaccion = enviar_evento_significativo(
            evento=evento,
            fecha_fin=fecha_fin,
            cufd=cufd_actual
        )

        if not transaccion:
            logger.error(f"El SIN rechazó la transacción para el evento #{evento['id']} - no se finalizó")
            return {
                'exito': False,
                'mensaje': f"El SIN rechazó la transacción para el evento #{evento['id']}",
                'codigo_recepcion': codigo_recepcion,
                'facturas_comprimidas': 0,
                'ruta_zip': None
            }

        # Actualizar evento en la base de datos local
        actualizar_evento_final(
            evento_id=evento["id"], 
            fecha_fin=fecha_fin, 
            codigo_recepcion=codigo_recepcion
        )
        logger.info(f"Evento #{evento['id']} finalizado en BD local. Código recepción: {codigo_recepcion}")

        # Comprimir facturas offline relacionadas con el evento
        facturas_comprimidas = 0
        ruta_zip = None
        try:
            # Verificar si hay facturas offline para este evento
            if not os.path.exists("offline"):
                logger.debug(f"La carpeta offline no existe. No hay facturas para el evento #{evento['id']}")
            else:
                archivos = [
                    f for f in os.listdir("offline")
                    if (f.startswith(f"offline_{evento['id']}_") or 
                        f.startswith(f"factura_offline_{evento['id']}_")) and 
                    f.endswith(".xml")
                ]

                if archivos:
                    facturas_comprimidas = len(archivos)
                    logger.info(f"Se encontraron {facturas_comprimidas} facturas offline para el evento #{evento['id']}")
                    
                    # Crear directorio para archivos comprimidos si no existe
                    os.makedirs("offline_archivos", exist_ok=True)
                    nombre_zip = f"offline_archivos/{evento['id']}_{codigo_recepcion}.zip"
                    ruta_zip = nombre_zip

                    # Comprimir los archivos XML
                    with zipfile.ZipFile(nombre_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                        for archivo in archivos:
                            ruta = os.path.join("offline", archivo)
                            zipf.write(ruta, arcname=archivo)
                            logger.debug(f"Archivo agregado al zip: {archivo}")

                    logger.info(f"Facturas offline comprimidas exitosamente en: {nombre_zip}")
                else:
                    logger.info(f"No hay facturas offline relacionadas con el evento #{evento['id']}")
        except Exception as e:
            logger.error(f"Error al comprimir facturas offline: {str(e)}")
            # No se detiene el proceso principal si falla la compresión

        return {
            'exito': True,
            'mensaje': f"Evento #{evento['id']} finalizado exitosamente",
            'codigo_recepcion': codigo_recepcion,
            'facturas_comprimidas': facturas_comprimidas,
            'ruta_zip': ruta_zip
        }

    except Exception as e:
        logger.exception(f"Error inesperado durante la finalización del evento #{evento['id']}: {str(e)}")
        return {
            'exito': False,
            'mensaje': f"Error inesperado: {str(e)}",
            'codigo_recepcion': None,
            'facturas_comprimidas': 0,
            'ruta_zip': None
        }
