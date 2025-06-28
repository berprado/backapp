import logging

def html_to_pdf(html_content, output_path):
    """
    Genera un PDF a partir de HTML usando WeasyPrint.

    Args:
        html_content (str): Contenido HTML de la factura.
        output_path (str): Ruta donde se guardará el PDF generado.

    Returns:
        bool: True si el PDF se generó correctamente, False en caso de error.
    """
    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(output_path)
        logging.getLogger("printer").info(f"[html_to_pdf] PDF generado correctamente en: {output_path}")
        return True
    except Exception as e:
        logging.getLogger("printer").error(f"[html_to_pdf] Error al generar PDF: {str(e)}")
        return False