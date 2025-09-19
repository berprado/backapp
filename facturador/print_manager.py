# print_manager.py
import os
import threading
import queue
import time
from datetime import datetime
from typing import Optional

import streamlit as st

from siat_pdf import html_to_pdf
from thermal_printer import ThermalPrinter
from logger_config import get_printer_logger
from data_models import FacturaProcesada
from invoice_templates import generate_html_invoice as generate_html_for_pdf

printer_logger = get_printer_logger()


class PrinterRuntime:
    """Administra la cola, el hilo y el estado del servicio de impresion."""

    def __init__(self) -> None:
        self.queue: queue.Queue = queue.Queue()
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.last_heartbeat: Optional[float] = None
        self.start_count: int = 0

    def mark_heartbeat(self) -> None:
        now = time.time()
        self.last_heartbeat = now
        _update_print_session(worker_heartbeat=now)

    def ensure_worker(self) -> str:
        """Garantiza que exista un worker vivo."""
        with self.lock:
            if self.thread and self.thread.is_alive():
                _update_print_session(worker_status="running", worker_heartbeat=self.last_heartbeat)
                return "running"

            status = "started" if self.thread is None else "restarted"
            if self.thread and not self.thread.is_alive():
                printer_logger.warning("El hilo trabajador no estaba activo. Reiniciando...")

            self.thread = threading.Thread(
                target=printer_worker,
                args=(self,),
                daemon=True,
                name="PrinterWorkerThread"
            )
            self.thread.start()
            self.start_count += 1
            _update_print_session(worker_status="running", worker_heartbeat=time.time())
            return status

    def mark_stopped(self) -> None:
        _update_print_session(worker_status="stopped")


@st.cache_resource
def get_printer_runtime() -> PrinterRuntime:
    return PrinterRuntime()


def _ensure_print_session_keys() -> None:
    defaults = {
        "print_status": "Sistema de impresion listo.",
        "impresion_en_progreso": False,
        "impresion_finalizada": False,
        "ultimo_trabajo_impresion": None,
        "printer_worker_status": "desconocido",
        "printer_worker_last_heartbeat": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _update_print_session(
    status: Optional[str] = None,
    en_progreso: Optional[bool] = None,
    finalizada: Optional[bool] = None,
    ultimo_trabajo: Optional[dict] = None,
    worker_status: Optional[str] = None,
    worker_heartbeat: Optional[float] = None,
) -> None:
    _ensure_print_session_keys()
    if status is not None:
        st.session_state["print_status"] = status
    if en_progreso is not None:
        st.session_state["impresion_en_progreso"] = en_progreso
    if finalizada is not None:
        st.session_state["impresion_finalizada"] = finalizada
    if ultimo_trabajo is not None:
        st.session_state["ultimo_trabajo_impresion"] = ultimo_trabajo
    if worker_status is not None:
        st.session_state["printer_worker_status"] = worker_status
    if worker_heartbeat is not None:
        st.session_state["printer_worker_last_heartbeat"] = worker_heartbeat


def get_printer_queue() -> queue.Queue:
    runtime = get_printer_runtime()
    runtime.ensure_worker()
    return runtime.queue


def printer_worker(runtime: PrinterRuntime) -> None:
    q = runtime.queue
    printer_logger.info("WORKER: hilo de impresion iniciado.")
    runtime.mark_heartbeat()

    printer = ThermalPrinter()

    while True:
        try:
            factura_data = q.get()
            runtime.mark_heartbeat()

            if factura_data is None:
                break

            if not isinstance(factura_data, dict):
                printer_logger.error(
                    "WORKER: se esperaba un diccionario, se recibio %s. Se descarta la tarea.",
                    type(factura_data)
                )
                q.task_done()
                continue

            try:
                factura_obj = FacturaProcesada(**factura_data)
            except Exception as exc:
                printer_logger.error(
                    "WORKER: no se pudo reconstruir FacturaProcesada: %s. Datos: %s",
                    exc,
                    factura_data,
                )
                q.task_done()
                continue

            job_meta = {
                "numero_factura": factura_obj.numero_factura,
                "timestamp": datetime.utcnow().isoformat(),
            }
            _update_print_session(
                status=f"[EN PROCESO] Procesando factura No. {factura_obj.numero_factura}...",
                en_progreso=True,
                finalizada=False,
                ultimo_trabajo=job_meta,
            )
            printer_logger.info("WORKER: nueva tarea para factura No. %s", factura_obj.numero_factura)

            try:
                html_content_pdf = generate_html_for_pdf(factura_obj)
                pdfs_dir = os.path.join(os.getcwd(), "pdfs")
                os.makedirs(pdfs_dir, exist_ok=True)
                output_pdf_path = os.path.join(pdfs_dir, f"factura_{factura_obj.numero_factura}.pdf")
                pdf_result = html_to_pdf(html_content_pdf, output_pdf_path)
                if not pdf_result:
                    raise RuntimeError("html_to_pdf retorno False")
                printer_logger.info("WORKER: PDF generado en %s", output_pdf_path)
            except Exception as exc:
                printer_logger.error(
                    "WORKER: error al generar PDF para la factura %s: %s",
                    factura_obj.numero_factura,
                    exc,
                    exc_info=True,
                )
                _update_print_session(
                    status=f"[ERROR] No se genero el PDF de la factura {factura_obj.numero_factura}.",
                    en_progreso=False,
                    finalizada=False,
                )
                q.task_done()
                continue

            try:
                runtime.mark_heartbeat()
                printer.connect()
                success = printer.print_invoice(factura_obj)
                if not success:
                    raise RuntimeError("print_invoice retorno False")
                printer_logger.info(
                    "WORKER: impresion termica completada para la factura %s",
                    factura_obj.numero_factura,
                )
                _update_print_session(
                    status=f"[OK] Factura No. {factura_obj.numero_factura} impresa exitosamente.",
                    en_progreso=False,
                    finalizada=True,
                )
            except Exception as exc:
                printer_logger.error(
                    "WORKER: error de impresora en factura %s: %s",
                    factura_obj.numero_factura,
                    exc,
                    exc_info=True,
                )
                _update_print_session(
                    status=f"[ADVERTENCIA] El PDF de la factura {factura_obj.numero_factura} se genero, pero la impresora fallo.",
                    en_progreso=False,
                    finalizada=False,
                )
                printer.disconnect()

            q.task_done()
            runtime.mark_heartbeat()

        except Exception as exc:
            printer_logger.critical(
                "WORKER: error critico en el hilo trabajador: %s",
                exc,
                exc_info=True,
            )
            _update_print_session(
                status="[ERROR CRITICO] Servicio de impresion detenido. Reinicie la aplicacion.",
                en_progreso=False,
                finalizada=False,
            )
            time.sleep(5)
            runtime.mark_heartbeat()

    printer.disconnect()
    runtime.mark_stopped()
    printer_logger.info("WORKER: hilo de impresion finalizado.")


def start_printer_worker() -> Optional[threading.Thread]:
    runtime = get_printer_runtime()
    status = runtime.ensure_worker()
    if status == "started":
        printer_logger.info("El hilo trabajador de impresion se ha iniciado.")
    elif status == "restarted":
        printer_logger.warning("El hilo trabajador de impresion fue reiniciado.")
    else:
        printer_logger.debug("El hilo trabajador de impresion continua en ejecucion.")
    return runtime.thread


def solicitar_impresion(factura_obj: FacturaProcesada) -> None:
    initialize_print_state()
    printer_logger.info(
        "SOLICITUD: Anadiendo factura No. %s a la cola de impresion.",
        factura_obj.numero_factura,
    )
    runtime = get_printer_runtime()
    runtime.ensure_worker()
    runtime.queue.put(factura_obj.model_dump())
    job_meta = {
        "numero_factura": factura_obj.numero_factura,
        "timestamp": datetime.utcnow().isoformat(),
    }
    _update_print_session(
        status="[ENVIADO] Factura enviada a la cola de impresion.",
        en_progreso=True,
        finalizada=False,
        ultimo_trabajo=job_meta,
    )


def initialize_print_state() -> None:
    """Asegura que las claves basicas del estado de impresion existen."""
    _ensure_print_session_keys()


def mostrar_mensaje_impresion_en_curso() -> None:
    """Compatibilidad con versiones antiguas."""
    pass
