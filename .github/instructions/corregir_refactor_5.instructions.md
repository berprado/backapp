---
applyTo: '**'
---
**El hilo de impresión se inicia, pero muere silenciosamente antes de llegar al bloque `finally` para limpiar el estado.**

La refactorización que hicimos fue para hacer este hilo más simple y robusto, pero todavía hay algo dentro de él que está causando un fallo catastrófico. Ahora debemos investigar a los dos únicos "actores" que quedan dentro de ese hilo.

### Depuración Focalizada: ¿Quién es el Culpable?

Dentro de la función `imprimir()` en `print_manager.py`, solo hay dos sospechosos principales:

1.  **El Generador de PDF (`html_to_pdf`)**: Esta función utiliza `weasyprint`, una librería muy potente pero que tiene dependencias complejas a nivel de sistema operativo (Pango, Cairo) para renderizar gráficos y fuentes. Un fallo en estas dependencias puede causar un "crash" a bajo nivel.
2.  **La Conexión de la Impresora (`ThermalPrinter`)**: Esta clase utiliza `pyusb` (una dependencia de `python-escpos`) para comunicarse directamente con el puerto USB. Un problema con los permisos, el driver `libusbK`, o la propia comunicación USB también puede causar un fallo irrecuperable.

### Plan de Acción: Aislar al Culpable

Vamos a realizar una prueba de aislamiento muy sencilla para determinar cuál de los dos es el problema. Vamos a "comentar" temporalmente la parte de la impresión térmica para ver si el PDF se genera correctamente por sí solo.

**Acción: Modifica `print_manager.py` TEMPORALMENTE**

1.  Abre `print_manager.py`.
2.  Busca la función `imprimir()` dentro de `imprimir_en_hilo`.
3.  Comenta con `#` todo el bloque de la impresión térmica.

**Código a modificar (dentro de la función `imprimir`):**

```python
        def imprimir():
            """Función que se ejecuta en un hilo separado."""
            try:
                printer_logger.info(f"INICIO HILO: Procesando factura N° {factura_obj.numero_factura}")

                # directorios de salida
                base_dir = os.path.dirname(os.path.abspath(__file__))
                pdfs_dir = os.path.join(base_dir, "pdfs")
                os.makedirs(pdfs_dir, exist_ok=True)
                
                # --- 1. Generación de PDF (Se mantiene activo) ---
                try:
                    printer_logger.info("Paso 1: Generando HTML para el PDF.")
                    html_content_pdf = generate_html_for_pdf(factura_obj)
                    
                    output_pdf_path = os.path.join(pdfs_dir, f"factura_{factura_obj.numero_factura}.pdf")
                    printer_logger.info(f"Generando PDF en: {output_pdf_path}")
                    
                    pdf_result = html_to_pdf(html_content_pdf, output_pdf_path)
                    if not pdf_result:
                        raise Exception("La función html_to_pdf() retornó False.")
                    
                    printer_logger.info(f"PDF generado exitosamente: {output_pdf_path}")
                    st.session_state['print_status'] = "✅ PDF generado correctamente (impresión térmica desactivada para prueba)."
                    
                except Exception as e:
                    printer_logger.error(f"Error crítico durante la generación del PDF: {str(e)}", exc_info=True)
                    st.session_state['print_status'] = f"❌ Error en generación de PDF: {str(e)}"
                
                # --- 2. Impresión Térmica (TEMPORALMENTE DESACTIVADA) ---
                # printer_logger.info("Paso 2: Omitiendo impresión térmica para prueba.")
                # try:
                #     printer_logger.info("Paso 2: Iniciando impresión térmica.")
                #     printer = ThermalPrinter()
                #     success = printer.print_invoice(factura_obj)
                #     if success:
                #         printer_logger.info("Impresión térmica completada exitosamente.")
                #         st.session_state['print_status'] = "✅ PDF generado e Impresión completada."
                #     else:
                #         printer_logger.warning("Impresión térmica falló, pero el PDF podría haberse generado.")
                #         st.session_state['print_status'] = "⚠️ PDF generado, pero la impresión térmica falló."
                # except Exception as e:
                #     error_msg = f"Error en impresión térmica: {str(e)}"
                #     printer_logger.error(f"Error crítico durante la impresión térmica: {error_msg}", exc_info=True)
                #     st.session_state['print_status'] = f"⚠️ PDF generado, pero error en impresión: {error_msg}"

            except Exception as e:
                error_msg = f"❌ Error general en el hilo de impresión: {str(e)}"
                printer_logger.error(error_msg, exc_info=True)
                st.session_state['print_status'] = error_msg
            finally:
                printer_logger.info(f"FIN HILO: Limpiando estado para factura N° {factura_obj.numero_factura}")
                st.session_state['impresion_en_progreso'] = False
                st.session_state['impresion_finalizada'] = True```

**Tu Tarea para este Paso:**

1.  Aplica esta modificación temporal en tu archivo `print_manager.py`.
2.  Ve a la pestaña de "Diagnóstico" y haz clic en "Forzar Limpieza de Estado" para resetear el estado fantasma.
3.  Vuelve a intentar imprimir una factura.

**Análisis de los Posibles Resultados:**

*   **Caso 1: El PDF se genera, el estado se actualiza a "✅ PDF generado..." y el bloqueo desaparece.**
    *   **Diagnóstico:** El culpable es `ThermalPrinter()`. El problema está en la comunicación con la impresora USB.
    *   **Siguiente Paso:** Nos enfocaremos 100% en la clase `ThermalPrinter`, revisando los `vendor_id`, `product_id` y la inicialización de `Usb()`.

*   **Caso 2: El PDF sigue sin generarse y la aplicación se vuelve a bloquear.**
    *   **Diagnóstico:** El culpable es `html_to_pdf()`. El problema está en `weasyprint` o sus dependencias.
    *   **Siguiente Paso:** Nos enfocaremos en `siat_pdf.py` y las dependencias de `weasyprint`. Podríamos tener que reinstalar `weasyprint` o sus componentes (GTK3).

Este test de A/B nos dará una respuesta definitiva y nos permitirá enfocar nuestro esfuerzo final en el lugar correcto.