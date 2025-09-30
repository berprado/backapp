import os
from datetime import datetime
from typing import Tuple, Optional
from data_access import (
    obtener_evento_activo_actual, 
    cerrar_evento_significativo
)
from communication_manager import communication_manager
from soap_services import enviar_evento_significativo
from logger_config import get_logger
logger = get_logger()

MANUAL_EVENT_CODES = {"3", "4", "5", "6", "7"}
NON_OPERATIONAL_CODES = {"5", "6", "7"}

def finalizar_evento_si_conectado(
    cierre_manual: bool = False,
    cafc_manual: Optional[str] = None,
    confirmacion_manual: bool = True,
) -> Tuple[bool, str]:
    """Finaliza el evento activo si hay conexion y entrega un mensaje detallado."""

    resultado_completo = communication_manager.verificar_comunicacion_completa()
    principal = resultado_completo.get("verificacion_principal", {})
    conectado = principal.get("conectado", False)

    if not conectado:
        detalle = "Aun no hay conexion con el SIN. El evento se mantiene abierto."
        logger.info("[EVENTOS] %s", detalle)
        return False, detalle

    evento = obtener_evento_activo_actual()
    if not evento:
        detalle = "No existe un evento de contingencia abierto. El sistema opera con normalidad."
        logger.info("[EVENTOS] %s", detalle)
        return True, detalle

    codigo_evento = str(evento.get("codigo_evento", ""))
    logger.info(
        "[EVENTOS] Conectividad restablecida. Preparando cierre del evento %s (codigo %s).",
        evento["id"],
        codigo_evento,
    )

    def _limpiar_cafc_estado():
        if codigo_evento in NON_OPERATIONAL_CODES:
            try:
                import streamlit as st  # type: ignore
                if "evento_cafc" in st.session_state:
                    st.session_state["evento_cafc"].pop(evento.get("id"), None)
            except Exception:
                pass

    if codigo_evento in MANUAL_EVENT_CODES and not cierre_manual:
        detalle = "El evento requiere cierre manual desde la pantalla de eventos significativos."
        logger.info("[EVENTOS] %s", detalle)
        return False, detalle

    if codigo_evento in MANUAL_EVENT_CODES and cierre_manual and not confirmacion_manual:
        detalle = "Debe confirmar la transcripcion o validacion de facturas antes de cerrar el evento."
        logger.warning("[EVENTOS] %s", detalle)
        return False, detalle

    cafc_en_uso = None
    if codigo_evento in NON_OPERATIONAL_CODES:
        cafc_en_uso = (cafc_manual or "").strip()
        if not cafc_en_uso:
            try:
                import streamlit as st  # type: ignore
                cafc_en_uso = (st.session_state.get("evento_cafc", {}).get(evento.get("id")) or "").strip()
            except Exception:
                cafc_en_uso = ""

    from cufd import solicitar_cufd

    nuevo_cufd = solicitar_cufd()
    if not nuevo_cufd:
        detalle = "No se pudo obtener un nuevo CUFD. Imposible finalizar el evento segun normativa."
        logger.error("[EVENTOS] %s", detalle)
        return False, detalle

    logger.info("[EVENTOS] Nuevo CUFD obtenido para cierre: %s", nuevo_cufd)

    fecha_fin = datetime.now()
    codigo_recepcion, transaccion = enviar_evento_significativo(
        evento=evento,
        fecha_fin=fecha_fin,
        cufd=nuevo_cufd
    )

    if not transaccion:
        if codigo_recepcion is None:
            detalle = "El SIN no acepto el cierre del evento. Revise la respuesta del servicio."
        else:
            detalle = f"El SIN rechazo el evento. Codigo de recepcion devuelto: {codigo_recepcion}."
        logger.error("[EVENTOS] %s", detalle)
        return False, detalle

    exito_cierre, detalle_cierre = cerrar_evento_significativo(
        evento_id=evento["id"],
        codigo_recepcion=codigo_recepcion or ""
    )

    if not exito_cierre:
        logger.error("[EVENTOS] %s", detalle_cierre)
        return False, detalle_cierre

    logger.info("[EVENTOS] %s", detalle_cierre)

    carpeta_offline = "offline_invoices"
    if not os.path.exists(carpeta_offline):
        detalle = (
            "Evento finalizado y registrado. No existe la carpeta 'offline_invoices',"
            " por lo que no hay facturas offline que procesar."
        )
        logger.info("[EVENTOS] %s", detalle)
        _limpiar_cafc_estado()
        return True, detalle

    archivos = [
        f for f in os.listdir(carpeta_offline)
        if f.startswith(f"factura_offline_ev{evento['id']}_") and f.endswith(".xml")
    ]

    if archivos:
        if codigo_evento in NON_OPERATIONAL_CODES and not cafc_en_uso:
            detalle = "Debe proporcionar el CAFC utilizado en las facturas manuales antes de cerrar el evento."
            logger.warning("[EVENTOS] %s", detalle)
            return False, detalle

        logger.info("[EVENTOS] Se encontraron %d archivos offline para procesar.", len(archivos))

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
                    logger.warning("[EVENTOS] Archivo XML no encontrado: %s", xml_file_path)

            except (IndexError, ValueError) as exc:
                logger.warning("[EVENTOS] No se pudo extraer el numero de factura de %s: %s", archivo, exc)

        if not invoices_data:
            detalle = (
                "Evento finalizado, pero los archivos offline encontrados no cumplen con la nomenclatura esperada."
                " Revise la carpeta 'offline_invoices'."
            )
            logger.warning("[EVENTOS] %s", detalle)
            return True, detalle

        logger.info("[EVENTOS] %d facturas offline validas preparadas para empaquetar.", len(invoices_data))

        os.makedirs("paquetes_contingencia", exist_ok=True)

        try:
            from data_access import obtener_evento_por_id
            evento_data = obtener_evento_por_id(evento["id"])
            codigo_recepcion_evento = evento_data.get("codigo_recepcion") if evento_data else None

            if not codigo_recepcion_evento:
                detalle = (
                    f"No se encontro codigo_recepcion almacenado para el evento #{evento['id']}."
                    " Verifique que el evento se haya cerrado correctamente."
                )
                logger.error("[EVENTOS] %s", detalle)
                return False, detalle

            logger.info("[EVENTOS] Usando codigo_recepcion del evento: %s", codigo_recepcion_evento)

        except Exception as exc:
            detalle = f"Error al obtener codigo_recepcion del evento #{evento['id']}: {exc}"
            logger.error("[EVENTOS] %s", detalle)
            return False, detalle

        from batch_sender import BatchSender
        batch_sender = BatchSender()
        batch_numbers = [item["numeroFactura"] for item in invoices_data]

        tar_path, xmls_incluidos = batch_sender.create_batch_file(batch_numbers)
        if not tar_path or not xmls_incluidos:
            detalle = f"Error al crear el archivo comprimido normativo para evento #{evento['id']}"
            logger.error("[EVENTOS] %s", detalle)
            return False, detalle

        cufd_code = nuevo_cufd["codigo"] if isinstance(nuevo_cufd, dict) and "codigo" in nuevo_cufd else nuevo_cufd
        ok = batch_sender.process_and_validate_batch(
            xml_path=None,
            gzip_path=tar_path,
            cufd=cufd_code,
            batch_numbers=batch_numbers,
            evento_id=evento["id"],
            cafc_override=cafc_en_uso
        )

        if not ok:
            detalle = f"Error al procesar y validar el paquete del evento #{evento['id']}"
            logger.error("[EVENTOS] %s", detalle)
            return False, detalle

        carpeta_procesados = os.path.join(carpeta_offline, "procesados")
        os.makedirs(carpeta_procesados, exist_ok=True)
        for archivo in archivos:
            origen = os.path.join(carpeta_offline, archivo)
            destino = os.path.join(carpeta_procesados, archivo)
            os.rename(origen, destino)

        detalle = (
            f"Evento finalizado. Paquete validado y {len(archivos)} archivos movidos a "
            f"'{carpeta_procesados}'."
        )
        logger.info("[EVENTOS] %s", detalle)
        _limpiar_cafc_estado()
        return True, detalle

    detalle = f"Evento finalizado. No se encontraron facturas offline para el evento #{evento['id']}."
    logger.info("[EVENTOS] %s", detalle)
    _limpiar_cafc_estado()
    return True, detalle
