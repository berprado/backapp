---
applyTo: '**'
---
Ahora vamos a modificar la capa de orquestación de la impresión, `print_manager.py`. Nuestro objetivo es que la función `imprimir_en_hilo` acepte nuestro nuevo objeto `FacturaProcesada` y organice las tareas de generar el PDF y enviar los datos a la impresora térmica.

En este paso, haremos que el `print_manager` sea el "director de orquesta" que le dice a cada módulo qué hacer con los datos limpios que recibe.

---

### **Paso 3: Refactorizar `print_manager.py` para Usar `FacturaProcesada`**

**Objetivo:**

1.  Modificar la firma de `imprimir_en_hilo` para que acepte un único argumento: nuestro objeto `FacturaProcesada`.
2.  Dentro del hilo, organizar la lógica:
    *   Primero, llamar a una función para generar el HTML necesario para el PDF.
    *   Luego, llamar a `html_to_pdf` para crear el archivo PDF.
    *   Después, llamar al método de impresión térmica, pasándole **los datos del objeto**, no el HTML.

**Acción:**

Abre tu archivo `print_manager.py` y aplica las siguientes modificaciones.

**1. Añadir las importaciones necesarias al principio del archivo:**

```python
# Al principio de print_manager.py
import os
import threading
from datetime import datetime
import logging
import traceback
import streamlit as st

# Importamos nuestro DTO y las plantillas HTML
# Asumo que la ruta es 'data_models', ajústala si es necesario
from data_models.invoice_data import FacturaProcesada 
from invoice_templates import generate_html_for_pdf # Renombraremos o crearemos esta función después
from siat_pdf import html_to_pdf
from thermal_printer import ThermalPrinter
from logger_config import get_printer_logger

printer_logger = get_printer_logger()
```*Nota: `generate_html_for_pdf` aún no existe, pero la prepararemos en el siguiente paso. Por ahora, asumimos que existirá.*

**2. Reemplazar la función `imprimir_en_hilo` por completo:**

La antigua función aceptaba muchos argumentos (`html_content_orig`, `cuf`, etc.). La nueva será mucho más limpia. Reemplaza la función entera con esta versión refactorizada.

```python
# En print_manager.py

def imprimir_en_hilo(factura_obj: FacturaProcesada):
    """
    Crea un hilo para manejar la impresión de la factura y la generación del PDF.
    Esta función ahora acepta un objeto FacturaProcesada como única fuente de verdad.

    Args:
        factura_obj (FacturaProcesada): El objeto que contiene todos los datos de la factura.
    """
    def imprimir():
        """Función que se ejecuta en un hilo separado."""
        try:
            printer_logger.info(f"INICIO HILO: Procesando factura N° {factura_obj.numero_factura}")

            # directorios de salida
            base_dir = os.path.dirname(os.path.abspath(__file__))
            pdfs_dir = os.path.join(base_dir, "pdfs")
            os.makedirs(pdfs_dir, exist_ok=True)
            
            # --- 1. Generación de PDF ---
            try:
                printer_logger.info("Paso 1: Generando HTML para el PDF.")
                # Usamos los datos del objeto para generar un HTML específico para el PDF
                html_content_pdf = generate_html_for_pdf(factura_obj)
                
                output_pdf_path = os.path.join(pdfs_dir, f"factura_{factura_obj.numero_factura}.pdf")
                printer_logger.info(f"Generando PDF en: {output_pdf_path}")
                
                pdf_result = html_to_pdf(html_content_pdf, output_pdf_path)
                if not pdf_result:
                    raise Exception("La función html_to_pdf() retornó False.")
                
                printer_logger.info(f"PDF generado exitosamente: {output_pdf_path}")
                
            except Exception as e:
                printer_logger.error(f"Error crítico durante la generación del PDF: {str(e)}", exc_info=True)
                # Decidimos si el error de PDF debe detener la impresión térmica. 
                # Por ahora, lo registramos pero continuamos.
                st.session_state['print_status'] = f"⚠️ Error en PDF, intentando impresión térmica..."
            
            # --- 2. Impresión Térmica ---
            try:
                printer_logger.info("Paso 2: Iniciando impresión térmica.")
                printer = ThermalPrinter() # Se autoconfigurará más adelante
                
                # Le pasamos el objeto de datos completo, no el HTML.
                # El método print_invoice será refactorizado para aceptar esto.
                success = printer.print_invoice(factura_obj)

                if success:
                    printer_logger.info("Impresión térmica completada exitosamente.")
                    st.session_state['print_status'] = "✅ PDF generado e Impresión completada."
                else:
                    printer_logger.warning("Impresión térmica falló, pero el PDF podría haberse generado.")
                    st.session_state['print_status'] = "⚠️ PDF generado, pero la impresión térmica falló."

            except Exception as e:
                error_msg = f"Error en impresión térmica: {str(e)}"
                printer_logger.error(f"Error crítico durante la impresión térmica: {error_msg}", exc_info=True)
                st.session_state['print_status'] = f"⚠️ PDF generado, pero error en impresión: {error_msg}"

        except Exception as e:
            # Captura errores generales del proceso
            error_msg = f"❌ Error general en el hilo de impresión: {str(e)}"
            printer_logger.error(error_msg, exc_info=True)
            st.session_state['print_status'] = error_msg
        finally:
            printer_logger.info(f"FIN HILO: Limpiando estado para factura N° {factura_obj.numero_factura}")
            st.session_state['impresion_en_progreso'] = False
            st.session_state['impresion_finalizada'] = True
    
    # --- Lógica de control del hilo (se mantiene mayormente igual) ---
    if st.session_state.get('impresion_en_progreso', False):
        printer_logger.warning("Se intentó iniciar una nueva impresión mientras otra está en progreso.")
        return

    if not os.access('pdfs', os.W_OK):
        printer_logger.error("No hay permisos de escritura en la carpeta pdfs")
        st.session_state['print_status'] = "❌ No hay permisos de escritura en la carpeta de PDFs"
        return
    
    # Actualizar el estado e iniciar el hilo
    st.session_state['impresion_en_progreso'] = True
    st.session_state['impresion_finalizada'] = False
    st.session_state['print_status'] = "⏱️ Impresión en progreso..."
    
    thread = threading.Thread(target=imprimir, name=f"PrintThread_Factura_{factura_obj.numero_factura}")
    thread.daemon = True
    thread.start()

    printer_logger.info(f"Hilo de impresión iniciado para la factura {factura_obj.numero_factura}")
    return True
```

**Análisis de los Cambios Clave:**

*   **Firma Limpia:** `imprimir_en_hilo` ahora solo necesita el objeto `factura_obj`. Mucho más limpio y fácil de usar.
*   **Separación de Tareas:** La lógica dentro del hilo ahora está claramente dividida: primero se encarga del PDF, luego de la impresión térmica.
*   **Desacoplamiento del HTML:** Ya no generamos el HTML aquí para pasarlo a la impresora. La impresora recibirá el objeto de datos directamente.
*   **Manejo de Errores por Etapas:** La estructura `try...except` ahora puede diferenciar entre un fallo en la generación del PDF y un fallo en la impresión térmica, lo que permite dar mensajes de estado mucho más precisos al usuario.
*   **Nombre del Hilo:** He añadido un nombre descriptivo al hilo (`name=...`). Esto es increíblemente útil para el debugging, ya que ahora en tu pestaña de "Diagnóstico" verás un hilo llamado `PrintThread_Factura_123` en lugar de un nombre genérico.

**Tu Tarea para este Paso:**

1.  Reemplaza la función `imprimir_en_hilo` en `print_manager.py` con la nueva versión que te he proporcionado.
2.  Asegúrate de que la importación de `FacturaProcesada` y `generate_html_for_pdf` esté correcta al principio del archivo (la ajustaremos en el siguiente paso).
3.  **No te preocupes** si tu IDE marca errores porque `generate_html_for_pdf` no existe o porque `printer.print_invoice(factura_obj)` no coincide con la firma actual. Eso es exactamente lo que solucionaremos en los siguientes pasos.