import os
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

    # --- PROCESO MEJORADO: Usar BatchSender para envío y validación de paquetes ---
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
        logger.info(f"[📦] Encontrados {len(archivos)} archivos offline para procesar.")
        
        # Preparar datos de facturas para el packager
        invoices_data = []
        
        for archivo in archivos:
            # Formato esperado: factura_offline_ev{evento_id}_n{numero}.xml
            try:
                numero_str = archivo.split('_n')[1].replace('.xml', '')
                numero_factura = int(numero_str)
                xml_file_path = os.path.join(carpeta_offline, archivo)
                
                if os.path.exists(xml_file_path):
                    invoices_data.append({
                        'numeroFactura': numero_factura,
                        'xml_path': xml_file_path,
                        'cuf': None  # Se puede obtener desde BD si es necesario
                    })
                else:
                    logger.warning(f"[⚠️] Archivo XML no encontrado: {xml_file_path}")
                    
            except (IndexError, ValueError) as e:
                logger.warning(f"[⚠️] No se pudo extraer número de factura de {archivo}: {e}")

        if invoices_data:
            logger.info(f"[📦] Encontradas {len(invoices_data)} facturas offline válidas para procesar.")
            
            # Crear carpeta de paquetes si no existe
            os.makedirs("paquetes_contingencia", exist_ok=True)
            
            # Usar el nuevo packager que sigue el flujo normativo correcto
            from contingency_packager import ContingencyPackager
            packager = ContingencyPackager()
            
            # Obtener codigo_recepcion del evento registrado (NO el tipo de evento)
            try:
                from data_access import obtener_evento_por_id
                evento_data = obtener_evento_por_id(evento["id"])
                codigo_recepcion_evento = evento_data.get('codigo_recepcion') if evento_data else None
                
                if not codigo_recepcion_evento:
                    logger.error(f"[❌] No se encontró codigo_recepcion para el evento #{evento['id']}. Evento debe estar finalizado.")
                    return False
                    
                logger.info(f"[📡] Usando codigo_recepcion del evento: {codigo_recepcion_evento}")
                
            except Exception as e:
                logger.error(f"[❌] Error al obtener codigo_recepcion del evento #{evento['id']}: {e}")
                return False

            # Usar el método normativo recomendado
            logger.info(f"[📦] Procesando facturas usando método NORMATIVO individual")

            # --- NUEVO FLUJO: Usar BatchSender para compresión y envío normativo ---
            from batch_sender import BatchSender
            batch_sender = BatchSender()
            # Obtener los números de factura
            batch_numbers = [f['numeroFactura'] for f in invoices_data]
            # Crear el archivo .tar.gz con los XML individuales
            tar_path, xmls_incluidos = batch_sender.create_batch_file(batch_numbers)
            if not tar_path or not xmls_incluidos:
                logger.error(f"[❌] Error al crear el archivo comprimido normativo para evento #{evento['id']}")
                return False
            # Enviar y validar el paquete usando el método normativo
            # Corregido: usar nuevo_cufd directamente si es string
            cufd_code = nuevo_cufd["codigo"] if isinstance(nuevo_cufd, dict) and "codigo" in nuevo_cufd else nuevo_cufd
            ok = batch_sender.process_and_validate_batch(
                xml_path=None,  # No se usa, solo el tar.gz
                gzip_path=tar_path,
                cufd=cufd_code,
                batch_numbers=batch_numbers,
                evento_id=evento["id"]
            )
            if ok:
                logger.info(f"[✅] Paquete del evento #{evento['id']} procesado y validado exitosamente.")
                # Mover archivos procesados a subcarpeta
                carpeta_procesados = os.path.join(carpeta_offline, "procesados")
                os.makedirs(carpeta_procesados, exist_ok=True)
                for archivo in archivos:
                    origen = os.path.join(carpeta_offline, archivo)
                    destino = os.path.join(carpeta_procesados, archivo)
                    os.rename(origen, destino)
                logger.info(f"[📁] {len(archivos)} archivos movidos a {carpeta_procesados}")
            else:
                logger.error(f"[❌] Error al procesar paquete del evento #{evento['id']}.")
                return False
        else:
            logger.warning(f"[⚠️] No se pudieron procesar los archivos encontrados o no son válidos.")
    else:
        logger.info(f"[ℹ️] No se encontraron facturas offline para el evento #{evento['id']}.")

    return True
