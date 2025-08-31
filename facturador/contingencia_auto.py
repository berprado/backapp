import os
import zipfile
from datetime import datetime
from data_access import (
    obtener_evento_activo_actual, 
    obtener_cufd_vigente, 
    cerrar_evento_significativo
)
from communication_manager import communication_manager
from soap_services import enviar_evento_significativo
from logger_config import get_logger
logger = get_logger()

def finalizar_evento_si_conectado():
    """
    Verifica si hay un evento activo y finaliza el evento si el sistema ha recuperado la conexión.
    Además, si hay archivos XML offline vinculados, los comprime en un ZIP y lo nombra con el id y código de recepción.
    """

    # Llamamos a nuestro gestor centralizado. La respuesta será casi instantánea si está en caché.
    resultado_completo = communication_manager.verificar_comunicacion_completa()
    principal = resultado_completo.get("verificacion_principal", {})
    conectado = principal.get("conectado", False)

    if not conectado:
        logger.info("[🛑] Aún no hay conexión con el SIN según el CommunicationManager. No se puede finalizar evento.")
        return False

    evento = obtener_evento_activo_actual()
    if not evento:
        logger.info("[✅] No hay evento abierto. El sistema está en modo normal.")
        return True

    logger.info(f"[📡] Conexión restablecida. Finalizando evento #{evento['id']}...")

    # PASO 1: SEGÚN NORMATIVA - OBTENER **NUEVO** CUFD ANTES DE REGISTRAR EVENTO
    logger.info("[🔄] Obteniendo NUEVO CUFD según normativa (NO reutilizar el anterior)...")
    
    # Importar la función para obtener nuevo CUFD
    from cufd import solicitar_cufd
    
    nuevo_cufd = solicitar_cufd()
    if not nuevo_cufd:
        logger.error("[❌] CRÍTICO: No se pudo obtener NUEVO CUFD. No se puede finalizar evento según normativa.")
        return False
    
    logger.info(f"[✅] NUEVO CUFD obtenido según normativa: {nuevo_cufd}")

    # PASO 2: SEGÚN NORMATIVA - REGISTRAR evento con el SIN usando el NUEVO CUFD
    fecha_fin = datetime.now()
    codigo_recepcion, transaccion = enviar_evento_significativo(
        evento=evento,
        fecha_fin=fecha_fin,
        cufd=nuevo_cufd  # Usar el NUEVO CUFD según normativa
    )

    if not transaccion:
        logger.error("[❌] El SIN no aceptó el cierre del evento.")
        return False

    # Paso 3: Usar la nueva función normativa para cerrar el evento
    resultado_cierre = cerrar_evento_significativo(
        evento_id=evento["id"], 
        codigo_recepcion=codigo_recepcion
    )
    
    if resultado_cierre:
        logger.info(f"[✅] Evento #{evento['id']} finalizado exitosamente con código {codigo_recepcion}.")
    else:
        logger.error(f"[❌] Error al cerrar el evento #{evento['id']} en base de datos.")
        return False

    # --- CORRECCIÓN: Usar la carpeta y patrón correctos ---
    # Paso 4: Verificar si hay archivos relacionados en la carpeta correcta
    carpeta_offline = "offline_invoices"
    if not os.path.exists(carpeta_offline):
        logger.info(f"[ℹ️] No existe la carpeta {carpeta_offline}. No hay facturas offline para procesar.")
        return True

    # Buscar archivos con el patrón correcto: factura_offline_ev{evento_id}_n{numero}.xml
    archivos = [
        f for f in os.listdir(carpeta_offline)
        if f.startswith(f"factura_offline_ev{evento['id']}_") and f.endswith(".xml")
    ]

    if archivos:
        # Crear carpeta de paquetes procesados si no existe
        os.makedirs("paquetes_contingencia", exist_ok=True)
        nombre_zip = f"paquetes_contingencia/evento_{evento['id']}_recepcion_{codigo_recepcion}.zip"

        with zipfile.ZipFile(nombre_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for archivo in archivos:
                ruta_completa = os.path.join(carpeta_offline, archivo)
                zipf.write(ruta_completa, arcname=archivo)
                logger.debug(f"Añadido al ZIP: {archivo}")

        logger.info(f"[📦] {len(archivos)} facturas comprimidas en: {nombre_zip}")
        
        # Opcional: Mover archivos procesados a una subcarpeta
        carpeta_procesados = os.path.join(carpeta_offline, "procesados")
        os.makedirs(carpeta_procesados, exist_ok=True)
        
        for archivo in archivos:
            origen = os.path.join(carpeta_offline, archivo)
            destino = os.path.join(carpeta_procesados, archivo)
            os.rename(origen, destino)
            
        logger.info(f"[📁] Archivos movidos a {carpeta_procesados}")
    else:
        logger.info(f"[ℹ️] No se encontraron facturas offline para el evento #{evento['id']}.")

    return True
