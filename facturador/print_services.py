"""Support services and exceptions for the printing workflow."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from logger_config import get_printer_logger
from siat_pdf import html_to_pdf
from invoice_templates import generate_html_invoice as generate_html_for_pdf
from thermal_printer import ThermalPrinter

printer_logger = get_printer_logger()


class PdfGenerationError(Exception):
    """Raised when the PDF could not be generated from the HTML template."""


@dataclass
class PdfGenerator:
    """Encapsulates HTML -> PDF generation for FacturaProcesada."""

    base_dir: Path = Path(os.getcwd()) / "pdfs"

    def generate(self, factura_obj) -> Path:
        """Generates a PDF file for the given invoice and returns the path."""

        html_content = generate_html_for_pdf(factura_obj)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        output_pdf_path = self.base_dir / f"factura_{factura_obj.numero_factura}.pdf"
        try:
            pdf_result = html_to_pdf(html_content, str(output_pdf_path))
        except Exception as exc:  # pragma: no cover - passthrough
            raise PdfGenerationError(str(exc)) from exc

        if not pdf_result:
            raise PdfGenerationError("html_to_pdf retorno False")

        printer_logger.info("WORKER: PDF generado en %s", output_pdf_path)
        return output_pdf_path


class PrinterJobError(Exception):
    """Represents a failure reported by the thermal printer."""

    def __init__(self, message: str, code: str = "printer_error") -> None:
        super().__init__(message)
        self.code = code


@dataclass
class ThermalPrintService:
    """Wrapper around `ThermalPrinter` to expose high-level operations."""

    printer: Optional[ThermalPrinter] = None

    def __post_init__(self) -> None:
        if self.printer is None:
            self.printer = ThermalPrinter()

    def print_factura(self, factura_obj) -> None:
        assert self.printer is not None
        try:
            self.printer.connect()
        except Exception as exc:
            raise PrinterJobError("No se pudo conectar con la impresora USB.", "connection_failed") from exc

        try:
            success = self.printer.print_invoice(factura_obj)
        except Exception as exc:  # printer.print_invoice ya desconecta en caso de error
            raise PrinterJobError("Error inesperado al imprimir.", "job_exception") from exc

        if not success:
            raise PrinterJobError("La impresora reporto un fallo en la impresion.", "job_failed")

    def shutdown(self) -> None:
        if self.printer is not None:
            self.printer.disconnect()
