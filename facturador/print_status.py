"""Utilities for strongly-typed print status updates."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class PrintSeverity(str, Enum):
    """Legal severities for UI rendering."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class PrintStatusCode(str, Enum):
    """Canonical identifiers for the print workflow."""

    READY = "ready"
    QUEUED = "queued"
    PROCESSING = "processing"
    DATA_ERROR = "data_error"
    PDF_ERROR = "pdf_error"
    PRINTER_SUCCESS = "printer_success"
    PRINTER_WARNING = "printer_warning"
    PRINTER_ERROR = "printer_error"
    CRITICAL_ERROR = "critical_error"


_DEFAULT_MESSAGES: Dict[PrintStatusCode, str] = {
    PrintStatusCode.READY: "Sistema de impresion listo.",
    PrintStatusCode.QUEUED: "Factura enviada a la cola de impresion.",
    PrintStatusCode.PROCESSING: "Procesando factura...",
    PrintStatusCode.DATA_ERROR: "Los datos de la factura no son validos para impresion.",
    PrintStatusCode.PDF_ERROR: "No se pudo generar el PDF de la factura.",
    PrintStatusCode.PRINTER_SUCCESS: "Factura impresa exitosamente.",
    PrintStatusCode.PRINTER_WARNING: "La impresora reporto un problema durante la impresion.",
    PrintStatusCode.PRINTER_ERROR: "La impresora no pudo completar la impresion.",
    PrintStatusCode.CRITICAL_ERROR: "Servicio de impresion detenido. Reinicie la aplicacion.",
}

_DEFAULT_SEVERITY: Dict[PrintStatusCode, PrintSeverity] = {
    PrintStatusCode.READY: PrintSeverity.INFO,
    PrintStatusCode.QUEUED: PrintSeverity.INFO,
    PrintStatusCode.PROCESSING: PrintSeverity.INFO,
    PrintStatusCode.DATA_ERROR: PrintSeverity.ERROR,
    PrintStatusCode.PDF_ERROR: PrintSeverity.ERROR,
    PrintStatusCode.PRINTER_SUCCESS: PrintSeverity.SUCCESS,
    PrintStatusCode.PRINTER_WARNING: PrintSeverity.WARNING,
    PrintStatusCode.PRINTER_ERROR: PrintSeverity.ERROR,
    PrintStatusCode.CRITICAL_ERROR: PrintSeverity.ERROR,
}


@dataclass
class PrintStatusPayload:
    """Structured payload stored in session_state."""

    code: PrintStatusCode
    message: str
    severity: PrintSeverity
    detail: Optional[str] = None
    timestamp: str = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, str]:
        data = asdict(self)
        # Enum values should be plain strings for Streamlit JSON serialization.
        data["code"] = self.code.value
        data["severity"] = self.severity.value
        return data


def build_status(
    code: PrintStatusCode,
    message: Optional[str] = None,
    severity: Optional[PrintSeverity] = None,
    *,
    detail: Optional[str] = None,
) -> PrintStatusPayload:
    """Factory with sensible defaults for each status code."""

    resolved_message = message or _DEFAULT_MESSAGES[code]
    resolved_severity = severity or _DEFAULT_SEVERITY[code]
    return PrintStatusPayload(
        code=code,
        message=resolved_message,
        severity=resolved_severity,
        detail=detail,
    )


def infer_status_from_message(message: str) -> PrintStatusPayload:
    """Fallback helper for legacy string-only messages."""

    lowered = message.lower()
    if any(token in lowered for token in ("error critico", "critical", "reinicie")):
        code = PrintStatusCode.CRITICAL_ERROR
    elif "advertencia" in lowered or "warning" in lowered:
        code = PrintStatusCode.PRINTER_WARNING
    elif any(token in lowered for token in ("error", "fall")):
        code = PrintStatusCode.PRINTER_ERROR
    elif any(token in lowered for token in ("ok", "impresa", "exitos")):
        code = PrintStatusCode.PRINTER_SUCCESS
    elif "proceso" in lowered:
        code = PrintStatusCode.PROCESSING
    elif "enviado" in lowered:
        code = PrintStatusCode.QUEUED
    else:
        code = PrintStatusCode.READY

    inferred = build_status(code, message)
    return inferred
