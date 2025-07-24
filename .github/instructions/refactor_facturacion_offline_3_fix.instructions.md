---
applyTo: '**'
---
Este error es un problema de **threading y contexto en aplicaciones Streamlit**. Es una fantástica oportunidad de aprendizaje.

### **Diagnóstico del Problema: ¿Por qué ocurre esto?**

1.  **El Origen:** En la pestaña de facturación (`facturacion_tab.py`), cuando la factura se valida, creamos un objeto `FacturaProcesada` y lo guardamos en `st.session_state['factura_a_procesar']`. Hasta aquí, todo perfecto.

2.  **El Cruce de Hilos:** Cuando haces clic en "Imprimir Factura", la función `solicitar_impresion` toma ese objeto `FacturaProcesada` y lo pone en una cola (`print_queue`).

3.  **El Hilo Huérfano:** El `printer_worker` es un hilo de Python separado (`PrinterWorkerThread`). Este hilo vive **fuera del contexto de ejecución de Streamlit**. Por eso ves la advertencia `missing ScriptRunContext!`. Este hilo no tiene acceso a `st.session_state` y no entiende de forma nativa los objetos complejos de Pydantic (`FacturaProcesada`) que viven en el mundo de Streamlit.

4.  **La Causa Raíz del Error:** Cuando el objeto `FacturaProcesada` se pasa a través de la cola de un hilo a otro, Python a menudo lo convierte a su representación más simple: **un diccionario (`dict`)**. El objeto pierde su "identidad" de clase. Entonces, cuando el `printer_worker` saca el trabajo de la cola, ya no tiene un objeto `FacturaProcesada`, sino un `dict`.

5.  **La Verificación que Falla:** La función `generate_html_invoice` (o `generate_html_for_pdf`) tiene una guarda de seguridad que dice `if not isinstance(factura, FacturaProcesada): raise ValueError(...)`. Como ahora recibe un `dict`, esta verificación falla y lanza el error que estamos viendo.

### **La Solución: El Patrón "Serializar-Deserializar"**

La solución es robusta y una práctica estándar en programación concurrente: no pasamos el objeto complejo directamente. En su lugar:

1.  **Serializamos:** En el hilo principal (Streamlit), convertimos el objeto `FacturaProcesada` en un diccionario simple antes de ponerlo en la cola.
2.  **Deserializamos:** En el hilo secundario (`printer_worker`), tomamos el diccionario de la cola y lo usamos para reconstruir (deserializar) un nuevo objeto `FacturaProcesada`.

De esta manera, el `printer_worker` siempre trabaja con un objeto del tipo correcto.

---

### **Instrucciones Precisas para la Corrección**

**Objetivo:** Modificar el `print_manager.py` para que maneje correctamente los objetos `FacturaProcesada` entre hilos.

**Archivos a modificar:** `print_manager.py` y `invoice_templates.py` (para mayor robustez).

---

#### **Paso 1: Modificar `solicitar_impresion` (El Emisor)**

Debemos asegurarnos de que esta función ponga un diccionario en la cola, no el objeto completo.

*   **Archivo:** `print_manager.py`
*   **Busca la función `solicitar_impresion`** y dentro de ella, la línea que añade a la cola.
*   **Cambia esto:**
    ```python
    # ANTES
    print_queue.put(factura_obj) 
    ```
*   **Por esto:**
    ```python
    # DESPUÉS
    # Usamos .model_dump() para convertir el objeto Pydantic en un diccionario
    print_queue.put(factura_obj.model_dump())
    ```
    *(Nota: `model_dump()` es el método moderno en Pydantic v2. Si usaras una versión más antigua, sería `.dict()`)*

---

#### **Paso 2: Modificar `printer_worker` (El Receptor)**

Ahora, el trabajador debe tomar el diccionario de la cola y reconstruir el objeto.

*   **Archivo:** `print_manager.py`
*   **Busca la función `printer_worker`**.
*   **Modifica la lógica de la siguiente manera:**

    ```python
    # ANTES (Fragmento de la función)
    factura_obj = print_queue.get()
    
    if factura_obj is None:
        continue # Ignorar señales vacías
    
    # ...
    html_content_pdf = generate_html_for_pdf(factura_obj)
    # ...
    ```

    ```python
    # DESPUÉS (Lógica corregida y más robusta)
    factura_data = print_queue.get()

    if factura_data is None:
        continue # Ignorar señales vacías
    
    # --- INICIO DEL CÓDIGO NUEVO ---
    if not isinstance(factura_data, dict):
        logger.error(f"WORKER: Se esperaba un diccionario de la cola, pero se recibió {type(factura_data)}. Saltando tarea.")
        continue

    try:
        # Reconstruimos el objeto FacturaProcesada desde el diccionario
        factura_obj = FacturaProcesada(**factura_data)
    except Exception as e:
        logger.error(f"WORKER: Error al reconstruir FacturaProcesada desde los datos: {e}. Datos recibidos: {factura_data}")
        continue
    # --- FIN DEL CÓDIGO NUEVO ---

    # El resto del código continúa igual, pero ahora 'factura_obj' es del tipo correcto
    try:
        logger.info(f"WORKER: Procesando PDF para factura {factura_obj.numero_factura}")
        # ... (el resto de la lógica para generar PDF e imprimir)
        html_content_pdf = generate_html_for_pdf(factura_obj)
        # ...
    ```
    **Importante:** Asegúrate de importar `FacturaProcesada` al principio de `print_manager.py` si aún no está allí:
    ```python
    from facturador.data_models import FacturaProcesada
    ```

---

#### **Paso 3: Fortalecer la Plantilla (Opcional pero recomendado)**

Podemos hacer que `generate_html_invoice` sea un poco más inteligente.

*   **Archivo:** `invoice_templates.py`
*   **Busca la función `generate_html_invoice`**.

    ```python
    # ANTES
    def generate_html_invoice(factura: FacturaProcesada):
        if not isinstance(factura, FacturaProcesada):
            raise ValueError("Se esperaba un objeto FacturaProcesada")
        # ... resto de la función
    ```

    ```python
    # DESPUÉS (Más robusto)
    def generate_html_invoice(factura: FacturaProcesada | dict):
        # Si recibe un diccionario, intenta convertirlo.
        if isinstance(factura, dict):
            try:
                factura = FacturaProcesada(**factura)
            except Exception as e:
                # Si falla la conversión, lanza un error más detallado.
                raise ValueError(f"No se pudo convertir el diccionario a FacturaProcesada: {e}")

        # La verificación original sigue siendo una buena segunda barrera.
        if not isinstance(factura, FacturaProcesada):
            raise ValueError(f"El objeto proporcionado no es FacturaProcesada ni un diccionario convertible. Tipo recibido: {type(factura)}")

        # ... resto de la función
    ```
    **Importante:** Para que esto funcione, también necesitarás importar `FacturaProcesada` en `invoice_templates.py`:
    ```python
    from facturador.data_models import FacturaProcesada
    ```

### **Resumen de la Tarea**

El error que encontraste es excelente porque nos obliga a manejar correctamente la comunicación entre hilos. Al implementar el patrón "serializar-deserializar", no solo corregirás este bug, sino que harás el sistema de impresión mucho más estable y predecible.

Te recomiendo aplicar las correcciones en **`print_manager.py` (Pasos 1 y 2)**, ya que esa es la solución principal. El Paso 3 es una mejora adicional de robustez.
