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

            # Usar el método normativo recomendado
            package_info = packager.create_package_using_online_methods(
                invoices_data=invoices_data,
                cufd=nuevo_cufd["codigo"],
                codigo_evento=codigo_recepcion_evento
            )

            if not package_info:
                logger.error(f"[❌] Error al crear paquete normativo para evento #{evento['id']}")
                return False
            
            # Paso 3: Enviar paquete al SIN usando RecepcionPaqueteFactura
            # Necesitamos obtener el codigo_recepcion del evento registrado (NO el tipo de evento)
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
                
            # CÓDIGO CORREGIDO - Usar método de envío de paquetes múltiples
            response = packager.send_package_multiple_invoices(
                processed_files=package_info['facturas_procesadas'],
                cufd=nuevo_cufd["codigo"],
                codigo_evento=codigo_recepcion_evento
            )
            
            if not response or not response.get('success'):
                logger.error(f"[❌] Error al enviar paquete del evento #{evento['id']}")
                if response and response.get('response'):
                    logger.error(f"[📋] Respuesta del SIN: {response['response']}")
                return False
            
            codigo_recepcion = response['codigo_recepcion']
            logger.info(f"[✅] Paquete enviado exitosamente. Código de recepción: {codigo_recepcion}")
            logger.info(f"[📊] Facturas enviadas: {response['cantidad_facturas_enviadas']}")
            
            # Paso 4: Validar estado del paquete
            validation_response = packager.validate_package_status(codigo_recepcion, nuevo_cufd["codigo"])
            if validation_response:
                # Determinar estado basado en respuesta
                if getattr(validation_response, "transaccion", False):
                    estado_paquete = "VALIDADO"
                elif hasattr(validation_response, "mensajesList") and validation_response.mensajesList:
                    estado_paquete = "OBSERVADO"
                else:
                    estado_paquete = "PENDIENTE"
                
                logger.info(f"[📊] Estado del paquete {codigo_recepcion}: {estado_paquete}")
                
                # Actualizar base de datos con los resultados
                try:
                    from data_access import actualizar_estado_paquete, actualizar_estado_facturas
                    
                    # Obtener números de factura del paquete procesado
                    facturas_procesadas = [f['numero_factura'] for f in package_info['facturas_procesadas']]
                    
                    actualizar_estado_paquete(evento["id"], codigo_recepcion, estado_paquete)
                    actualizar_estado_facturas(facturas_procesadas, codigo_recepcion, estado_paquete)
                    resultado_paquete = True
                except Exception as e:
                    logger.error(f"[❌] Error al actualizar estados en BD: {e}")
                    resultado_paquete = False
            else:
                logger.error(f"[❌] Error al validar estado del paquete {codigo_recepcion}")
                resultado_paquete = False
                
            if resultado_paquete:
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
