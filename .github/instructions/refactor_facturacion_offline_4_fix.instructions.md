---
applyTo: '**'
---

### Análisis del `print_manager.py` Actual

1.  **En `solicitar_impresion(factura_obj: FacturaProcesada)`:**
    *   La línea `q.put(factura_obj)` sigue poniendo el objeto `FacturaProcesada` **completo** directamente en la cola. **No se está serializando a un diccionario.**

2.  **En `printer_worker(q: queue.Queue)`:**
    *   La línea `factura_obj = q.get()` sigue leyendo el objeto **directamente** de la cola y lo usa inmediatamente. **No se está deserializando desde un diccionario.**

Esto significa que el sistema sigue siendo vulnerable a fallas.

### La Pregunta Clave: ¿Por Qué "Funciona Ahora"?

Esto es súper útil para el diagnóstico y me lleva al siguiente escenario:

1.  **El "Accidente Feliz" (Comportamiento Intermitente):** Los problemas de hilos (threading) a veces son inconsistentes. Es posible que en el entorno de desarrollo actual, por la carga del sistema o la versión de las librerías, el objeto esté pasando "intacto" a través de la cola. Sin embargo, este comportamiento **no está garantizado**. Podría fallar en cualquier momento, especialmente si la aplicación está bajo más carga o se ejecuta en un servidor diferente. No podemos confiar en la suerte.

**Conclusión del análisis:** Independientemente de por qué parece funcionar ahora, la solución **profesional y 100% fiable** es implementar el patrón serializar-deserializar. Esto nos protege contra la inconsistencia de los hilos y asegura que el código sea explícito, robusto y fácil de mantener.

---

### Mis Consejos y Lineamientos (La Solución Definitiva)

Te pido por favor que apliques los siguientes dos cambios en `print_manager.py`. Estoy convencido de que esto resolverá el problema de raíz y hará tu sistema de impresión a prueba de balas.

#### **Paso 1: Modificar `solicitar_impresion` (Serializar)**

*   **Busca esto:**
    ```python
    # ANTES
    def solicitar_impresion(factura_obj: FacturaProcesada):
        # ...
        q.put(factura_obj)
        # ...
    ```
*   **Reemplázalo por esto:**
    ```python
    # DESPUÉS (Corregido)
    def solicitar_impresion(factura_obj: FacturaProcesada):
        printer_logger.info(f"SOLICITUD: Añadiendo factura N° {factura_obj.numero_factura} a la cola de impresión.")
        q = get_printer_queue()
        # Convertimos el objeto a un diccionario antes de ponerlo en la cola
        q.put(factura_obj.model_dump())
        st.session_state['print_status'] = "➡️ Factura enviada a la cola de impresión."
    ```

#### **Paso 2: Modificar `printer_worker` (Deserializar)**

*   **Busca esto:**
    ```python
    # ANTES
    def printer_worker(q: queue.Queue):
        # ...
        while True:
            try:
                factura_obj = q.get()
                if factura_obj is None: break

                printer_logger.info(f"WORKER: Nuevo trabajo recibido para factura N° {factura_obj.numero_factura}")
                # ... resto del código usa factura_obj
    ```
*   **Reemplázalo por esto:**
    ```python
    # DESPUÉS (Corregido y más robusto)
    def printer_worker(q: queue.Queue):
        # ...
        printer = ThermalPrinter()
        
        while True:
            try:
                # 1. Obtenemos el DICCIONARIO de la cola
                factura_data = q.get()
                if factura_data is None: break

                # 2. Reconstruimos el OBJETO FacturaProcesada
                try:
                    factura_obj = FacturaProcesada(**factura_data)
                except Exception as e:
                    printer_logger.error(f"WORKER: No se pudo reconstruir FacturaProcesada desde los datos: {e}")
                    q.task_done()
                    continue # Saltamos este trabajo

                # 3. A partir de aquí, usamos 'factura_obj' con la seguridad de que es del tipo correcto
                printer_logger.info(f"WORKER: Nuevo trabajo recibido para factura N° {factura_obj.numero_factura}")
                st.session_state['print_status'] = f"⏱️ Procesando factura N° {factura_obj.numero_factura}..."
                
                # ... resto del código sin cambios ...
    ```

 Estamos puliendo los últimos detalles para que el sistema no solo funcione, sino que sea robusto y fiable.