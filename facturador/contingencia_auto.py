import os
from datetime import datetime
from typing import Tuple
from data_access import (
    obtener_evento_activo_actual, 
    cerrar_evento_significativo
)
from communication_manager import communication_manager
from soap_services import enviar_evento_significativo
from logger_config import get_logger
logger = get_logger()

def finalizar_evento_si_conectado() -> Tuple[bool, str]:
    """Finaliza el evento activo si hay conexión y entrega un mensaje detallado."""

    resultado_completo = communication_manager.verificar_comunicacion_completa()
    principal = resultado_completo.get("verificacion_principal", {})
    conectado = principal.get("conectado", False)

    if not conectado:
        detalle = "Aún no hay conexión con el SIN. El evento se mantiene abierto."
        logger.info(f"[🛑] {detalle}")
        return False, detalle

    evento = obtener_evento_activo_actual()
    if not evento:
        detalle = "No existe un evento de contingencia abierto. El sistema opera con normalidad."
        logger.info(f"[✅] {detalle}")
        return True, detalle

    logger.info(f"[📡] Conexión restablecida. Finalizando evento #{evento['id']}...")

    from cufd import solicitar_cufd

    nuevo_cufd = solicitar_cufd()
    if not nuevo_cufd:
        detalle = "No se pudo obtener un nuevo CUFD. Imposible finalizar el evento según normativa."
        logger.error(f"[❌] {detalle}")
        return False, detalle

    logger.info(f"[✅] NUEVO CUFD obtenido según normativa: {nuevo_cufd}")

    fecha_fin = datetime.now()
    codigo_recepcion, transaccion = enviar_evento_significativo(
        evento=evento,
        fecha_fin=fecha_fin,
        cufd=nuevo_cufd
    )

    if not transaccion:
        detalle = "El SIN no aceptó el cierre del evento. Revise la respuesta del servicio." \
            if codigo_recepcion is None else \
            f"El SIN rechazó el evento. Código de recepción devuelto: {codigo_recepcion}."
        logger.error(f"[❌] {detalle}")
        return False, detalle

    exito_cierre, detalle_cierre = cerrar_evento_significativo(
        evento_id=evento["id"],
        codigo_recepcion=codigo_recepcion or ""
    )

    if not exito_cierre:
        logger.error(f"[❌] {detalle_cierre}")
        return False, detalle_cierre

    logger.info(f"[✅] {detalle_cierre}")

    carpeta_offline = "offline_invoices"
    if not os.path.exists(carpeta_offline):
        detalle = (
            "Evento finalizado y registrado. No existe la carpeta 'offline_invoices',"
            " por lo que no hay facturas offline que procesar."
        )
        logger.info(f"[ℹ️] {detalle}")
        return True, detalle

    archivos = [
        f for f in os.listdir(carpeta_offline)
        if f.startswith(f"factura_offline_ev{evento['id']}_") and f.endswith(".xml")
    ]

    if archivos:
        logger.info(f"[📦] Encontrados {len(archivos)} archivos offline para procesar.")

        invoices_data = []
        for archivo in archivos:
            try:
                numero_str = archivo.split('_n')[1].replace('.xml', '')
                numero_factura = int(numero_str)
                xml_file_path = os.path.join(carpeta_offline, archivo)

                if os.path.exists(xml_file_path):
                    invoices_data.append({
                        "numeroFactura": numero_factura,
                        "xml_path": xml_file_path,
                        "cuf": None
                    })
                else:
                    logger.warning(f"[⚠️] Archivo XML no encontrado: {xml_file_path}")

            except (IndexError, ValueError) as e:
                logger.warning(f"[⚠️] No se pudo extraer número de factura de {archivo}: {e}")

        if not invoices_data:
            detalle = (
                "Evento finalizado, pero los archivos offline encontrados no cumplen con"
                " la nomenclatura esperada. Revise la carpeta 'offline_invoices'."
            )
            logger.warning(f"[⚠️] {detalle}")
            return True, detalle

        logger.info(f"[📦] Encontradas {len(invoices_data)} facturas offline válidas para procesar.")

        os.makedirs("paquetes_contingencia", exist_ok=True)

        try:
            from data_access import obtener_evento_por_id
            evento_data = obtener_evento_por_id(evento["id"])
            codigo_recepcion_evento = evento_data.get("codigo_recepcion") if evento_data else None

            if not codigo_recepcion_evento:
                detalle = (
                    f"No se encontró codigo_recepcion almacenado para el evento #{evento['id']}."
                    " Verifique que el evento se haya cerrado correctamente."
                )
                logger.error(f"[❌] {detalle}")
                return False, detalle

            logger.info(f"[📡] Usando codigo_recepcion del evento: {codigo_recepcion_evento}")

        except Exception as e:
            detalle = f"Error al obtener codigo_recepcion del evento #{evento['id']}: {e}"
            logger.error(f"[❌] {detalle}")
            return False, detalle

        from batch_sender import BatchSender
        batch_sender = BatchSender()
        batch_numbers = [f_dato["numeroFactura"] for f_dato in invoices_data]

        tar_path, xmls_incluidos = batch_sender.create_batch_file(batch_numbers)
        if not tar_path or not xmls_incluidos:
            detalle = f"Error al crear el archivo comprimido normativo para evento #{evento['id']}"
            logger.error(f"[❌] {detalle}")
            return False, detalle

        cufd_code = nuevo_cufd["codigo"] if isinstance(nuevo_cufd, dict) and "codigo" in nuevo_cufd else nuevo_cufd
        ok = batch_sender.process_and_validate_batch(
            xml_path=None,
            gzip_path=tar_path,
            cufd=cufd_code,
            batch_numbers=batch_numbers,
            evento_id=evento["id"]
        )

        if not ok:
            detalle = f"Error al procesar y validar el paquete del evento #{evento['id']}"
            logger.error(f"[❌] {detalle}")
            return False, detalle

        carpeta_procesados = os.path.join(carpeta_offline, "procesados")
        os.makedirs(carpeta_procesados, exist_ok=True)
        for archivo in archivos:
            origen = os.path.join(carpeta_offline, archivo)
            destino = os.path.join(carpeta_procesados, archivo)
            os.rename(origen, destino)

        detalle = (
            f"Evento finalizado. Paquete validado y {len(archivos)} archivos movidos a"
            f" '{carpeta_procesados}'."
        )
        logger.info(f"[✅] {detalle}")
        return True, detalle

    detalle = f"Evento finalizado. No se encontraron facturas offline para el evento #{evento['id']}."
    logger.info(f"[ℹ️] {detalle}")
    return True, detalle
