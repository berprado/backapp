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

def finalizar_evento_si_conectado():
    """
    Verifica si hay un evento activo y finaliza el evento si el sistema ha recuperado la conexión.
    Si existen facturas offline vinculadas al evento, las comprime en un archivo zip.
    
    Returns:
        bool: True si el evento fue finalizado correctamente o no hay eventos pendientes,
              False si no pudo finalizar un evento existente
    """
    logger.info("Verificando si hay eventos pendientes para finalizar")
    mensaje, conectado, _ = verificar_comunicacion()
    
    if not conectado:
        logger.warning(f"Conexión no disponible para finalizar eventos. Estado: {mensaje}")
        return False

    evento = obtener_evento_abierto()
    if not evento:
        logger.info("No hay eventos abiertos pendientes de cierre")
        return True

    logger.info(f"Conexión activa. Iniciando proceso de finalización para evento #{evento['id']}")
    
    # Validación de CUFD vigente
    cufd_actual = get_cufd_vigente()
    if not cufd_actual:
        logger.error("No se pudo obtener CUFD vigente para finalizar evento - proceso abortado")
        return False

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
            return False

        # Actualizar evento en la base de datos local
        actualizar_evento_final(
            evento_id=evento["id"], 
            fecha_fin=fecha_fin, 
            codigo_recepcion=codigo_recepcion
        )
        logger.info(f"Evento #{evento['id']} finalizado en BD local. Código recepción: {codigo_recepcion}")

        # Comprimir facturas offline relacionadas con el evento
        try:
            # Verificar si hay facturas offline para este evento
            if not os.path.exists("offline"):
                logger.debug(f"La carpeta offline no existe. No hay facturas para el evento #{evento['id']}")
                return True
                
            archivos = [
                f for f in os.listdir("offline")
                if f.startswith(f"offline_{evento['id']}_") and f.endswith(".xml")
            ]

            if archivos:
                logger.info(f"Se encontraron {len(archivos)} facturas offline para el evento #{evento['id']}")
                
                # Crear directorio para archivos comprimidos si no existe
                os.makedirs("offline_archivos", exist_ok=True)
                nombre_zip = f"offline_archivos/{evento['id']}_{codigo_recepcion}.zip"

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

        return True

    except Exception as e:
        logger.exception(f"Error inesperado durante la finalización del evento #{evento['id']}: {str(e)}")
        return False
