from weasyprint import HTML
import logging

def html_to_pdf(html_content, output_path):
    """
    Genera un PDF a partir de HTML usando WeasyPrint.
    Registra cualquier error que ocurra durante el proceso.
    """
    try:
        HTML(string=html_content).write_pdf(output_path)
        logging.getLogger("printer").info(f"[html_to_pdf] PDF generado correctamente en: {output_path}")
    except Exception as e:
        logging.getLogger("printer").error(f"[html_to_pdf] Error al generar PDF en {output_path}: {e}")
        raise