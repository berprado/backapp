from __future__ import annotations

import queue
import threading
import time
from datetime import datetime
from typing import Dict, Optional, Any

import streamlit as st
try:
    from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
except ModuleNotFoundError:
    from streamlit.runtime.scriptrun_context import add_script_run_ctx, get_script_run_ctx  # type: ignore

from data_models import FacturaProcesada
from logger_config import get_printer_logger
from print_services import (
    PdfGenerationError,
    PdfGenerator,
    PrinterJobError,
    ThermalPrintService,
)
from print_status import (
    PrintStatusCode,
    PrintStatusPayload,
    build_status,
    infer_status_from_message,
)

printer_logger = get_printer_logger()


class PrinterRuntime:
    """Administra la cola, el hilo y el estado del servicio de impresion."""

    def __init__(self) -> None:
        self.queue: "queue.Queue[Optional[Dict]]" = queue.Queue()
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
                name="PrinterWorkerThread",
            )
            ctx = get_script_run_ctx()
            if ctx is not None:
                add_script_run_ctx(self.thread, ctx)
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
    if "print_status" not in st.session_state or "print_status_info" not in st.session_state:
        payload = build_status(PrintStatusCode.READY)
        st.session_state.setdefault("print_status", payload.message)
        st.session_state.setdefault("print_status_info", payload.to_dict())
    st.session_state.setdefault("impresion_en_progreso", False)
    st.session_state.setdefault("impresion_finalizada", False)
    st.session_state.setdefault("ultimo_trabajo_impresion", None)
    st.session_state.setdefault("printer_worker_status", "desconocido")
    st.session_state.setdefault("printer_worker_last_heartbeat", None)
    st.session_state.setdefault("print_state_version", 0)
    st.session_state.setdefault("print_state_last_updated", None)
    st.session_state.setdefault("_print_auto_refresh_interval", 1.5)


def _update_print_session(
    status: Optional[str] = None,
    *,
    status_payload: Optional[PrintStatusPayload] = None,
    en_progreso: Optional[bool] = None,
    finalizada: Optional[bool] = None,
    ultimo_trabajo: Optional[Dict] = None,
    worker_status: Optional[str] = None,
    worker_heartbeat: Optional[float] = None,
) -> None:
    _ensure_print_session_keys()

    # ✅ CORRECCIÓN: Rate-limiting para evitar actualizaciones excesivas
    # Máximo 2 actualizaciones por segundo para reducir carga en Streamlit
    last_update = st.session_state.get("print_state_last_updated")
    if last_update and (time.time() - last_update) < 0.5:
        return  # Ignorar actualizaciones demasiado frecuentes

    payload = status_payload
    if payload is None and status is not None:
        payload = infer_status_from_message(status)

    state_changed = False

    if payload is not None:
        st.session_state["print_status"] = payload.message
        st.session_state["print_status_info"] = payload.to_dict()
        state_changed = True

    if en_progreso is not None:
        previous = st.session_state.get("impresion_en_progreso")
        if previous != en_progreso:
            state_changed = True
        st.session_state["impresion_en_progreso"] = en_progreso

    if finalizada is not None:
        previous = st.session_state.get("impresion_finalizada")
        if previous != finalizada:
            state_changed = True
        st.session_state["impresion_finalizada"] = finalizada

    if ultimo_trabajo is not None:
        job_snapshot = dict(ultimo_trabajo)
        if payload is not None:
            job_snapshot.setdefault("timestamp", payload.timestamp)
            job_snapshot["status_code"] = payload.code.value
            job_snapshot["status_severity"] = payload.severity.value
            job_snapshot["status_message"] = payload.message
            if payload.detail:
                job_snapshot["status_detail"] = payload.detail
        st.session_state["ultimo_trabajo_impresion"] = job_snapshot
        state_changed = True

    if worker_status is not None:
        st.session_state["printer_worker_status"] = worker_status

    if worker_heartbeat is not None:
        st.session_state["printer_worker_last_heartbeat"] = worker_heartbeat

    if state_changed:
        status_snapshot = st.session_state.get("print_status_info", {})
        printer_logger.info("UI_STATUS: %s - %s", status_snapshot.get("code", "unknown"), status_snapshot.get("message", st.session_state.get("print_status", "")))
        st.session_state["print_state_version"] = st.session_state.get("print_state_version", 0) + 1
        st.session_state["print_state_last_updated"] = time.time()


def get_print_state_summary() -> Dict[str, Any]:
    """Devuelve un resumen normalizado del estado de impresion actual."""
    initialize_print_state()

    status_info = st.session_state.get("print_status_info") or {}
    ready_message = build_status(PrintStatusCode.READY).message
    print_status = st.session_state.get("print_status", ready_message)

    raw_code = status_info.get("code") or ""
    severity = (status_info.get("severity") or "").lower()

    if not raw_code or not severity:
        inferred = infer_status_from_message(print_status)
        if not raw_code:
            raw_code = inferred.code.value
        if not severity:
            severity = inferred.severity.value

    if severity not in {"success", "warning", "error"}:
        severity = "info"

    message = status_info.get("message") or print_status or ready_message
    impresion_en_progreso = st.session_state.get("impresion_en_progreso", False)
    finalizada = st.session_state.get("impresion_finalizada", False)
    version = st.session_state.get("print_state_version", 0)
    updated_at = st.session_state.get("print_state_last_updated")
    ultimo_trabajo = st.session_state.get("ultimo_trabajo_impresion") or {}
    show_diag = severity in {"warning", "error"}

    return {
        "code": raw_code,
        "severity": severity,
        "message": message,
        "show_diagnostic": show_diag,
        "status_info": status_info,
        "impresion_en_progreso": impresion_en_progreso,
        "impresion_finalizada": finalizada,
        "version": version,
        "updated_at": updated_at,
        "ultimo_trabajo": ultimo_trabajo,
    }


def get_printer_queue() -> "queue.Queue[Optional[Dict]]":
    runtime = get_printer_runtime()
    runtime.ensure_worker()
    return runtime.queue


def printer_worker(runtime: PrinterRuntime) -> None:
    q = runtime.queue
    printer_logger.info("WORKER: hilo de impresion iniciado.")
    runtime.mark_heartbeat()

    pdf_generator = PdfGenerator()
    print_service = ThermalPrintService()

    while True:
        factura_data = q.get()
        should_break = factura_data is None
        pdf_path: Optional[str] = None

        try:
            runtime.mark_heartbeat()

            if should_break:
                printer_logger.info("WORKER: se recibio senal de apagado.")
                break

            if not isinstance(factura_data, dict):
                printer_logger.error(
                    "WORKER: se esperaba un diccionario, se recibio %s. Se descarta la tarea.",
                    type(factura_data),
                )
                payload = build_status(
                    PrintStatusCode.DATA_ERROR,
                    message="Los datos de impresion no tienen el formato esperado.",
                    detail=str(type(factura_data)),
                )
                _update_print_session(
                    status_payload=payload,
                    en_progreso=False,
                    finalizada=False,
                    ultimo_trabajo={"timestamp": datetime.utcnow().isoformat()},
                )
                continue

            job_meta: Dict[str, Optional[str]] = {
                "numero_factura": factura_data.get("numero_factura"),
                "timestamp": datetime.utcnow().isoformat(),
            }

            try:
                factura_obj = FacturaProcesada(**factura_data)
            except Exception as exc:
                printer_logger.error(
                    "WORKER: no se pudo reconstruir FacturaProcesada: %s. Datos: %s",
                    exc,
                    factura_data,
                    exc_info=True,
                )
                payload = build_status(
                    PrintStatusCode.DATA_ERROR,
                    message="Los datos de la factura no son validos para impresion.",
                    detail=str(exc),
                )
                _update_print_session(
                    status_payload=payload,
                    en_progreso=False,
                    finalizada=False,
                    ultimo_trabajo=job_meta,
                )
                continue

            processing_payload = build_status(
                PrintStatusCode.PROCESSING,
                message=f"[EN PROCESO] Procesando factura No. {factura_obj.numero_factura}...",
            )
            _update_print_session(
                status_payload=processing_payload,
                en_progreso=True,
                finalizada=False,
                ultimo_trabajo=job_meta,
            )
            printer_logger.info("WORKER: nueva tarea para factura No. %s", factura_obj.numero_factura)

            try:
                pdf_path = str(pdf_generator.generate(factura_obj))
            except PdfGenerationError as exc:
                printer_logger.error(
                    "WORKER: error al generar PDF para la factura %s: %s",
                    factura_obj.numero_factura,
                    exc,
                    exc_info=True,
                )
                payload = build_status(
                    PrintStatusCode.PDF_ERROR,
                    message=f"No se genero el PDF de la factura {factura_obj.numero_factura}.",
                    detail=str(exc),
                )
                _update_print_session(
                    status_payload=payload,
                    en_progreso=False,
                    finalizada=False,
                    ultimo_trabajo=job_meta,
                )
                continue

            runtime.mark_heartbeat()
            start_print = time.monotonic()
            try:
                print_service.print_factura(factura_obj)
                duration = time.monotonic() - start_print
                printer_logger.info("WORKER: impresion termica completada para la factura %s en %.3fs", factura_obj.numero_factura, duration)
            except PrinterJobError as exc:
                duration = time.monotonic() - start_print
                printer_logger.error(
                    "WORKER: error de impresora en factura %s tras %.3fs: %s",
                    factura_obj.numero_factura,
                    duration,
                    exc,
                    exc_info=True,
                )
                code = (
                    PrintStatusCode.PRINTER_WARNING
                    if exc.code in {"job_failed", "job_exception"}
                    else PrintStatusCode.PRINTER_ERROR
                )
                payload = build_status(
                    code,
                    message=f"El PDF de la factura {factura_obj.numero_factura} se genero, pero la impresora fallo.",
                    detail=str(exc),
                )
                _update_print_session(
                    status_payload=payload,
                    en_progreso=False,
                    finalizada=False,
                    ultimo_trabajo={**job_meta, "pdf_generado": pdf_path, "duracion_impresion": duration},
                )
                continue

            payload = build_status(
                PrintStatusCode.PRINTER_SUCCESS,
                message=f"Factura No. {factura_obj.numero_factura} impresa exitosamente.",
                detail=f"Duracion de impresion: {duration:.3f}s",
            )
            _update_print_session(
                status_payload=payload,
                en_progreso=False,
                finalizada=True,
                ultimo_trabajo={**job_meta, "pdf_generado": pdf_path, "duracion_impresion": duration},
            )

        except Exception as exc:  # pragma: no cover - protecci?n general
            printer_logger.critical(
                "WORKER: error critico en el hilo trabajador: %s",
                exc,
                exc_info=True,
            )
            payload = build_status(
                PrintStatusCode.CRITICAL_ERROR,
                message="[ERROR CRITICO] Servicio de impresion detenido. Reinicie la aplicacion.",
                detail=str(exc),
            )
            _update_print_session(
                status_payload=payload,
                en_progreso=False,
                finalizada=False,
            )
            time.sleep(5)
        finally:
            q.task_done()
            runtime.mark_heartbeat()

        if should_break:
            break

    print_service.shutdown()
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
    payload = build_status(
        PrintStatusCode.QUEUED,
        message=f"Factura No. {factura_obj.numero_factura} enviada a la cola de impresion.",
    )
    _update_print_session(
        status_payload=payload,
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
