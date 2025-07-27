---
applyTo: '**'
---
Aquí tienes las instrucciones finales, claras y consolidadas para el **único paso** que debemos realizar ahora.

---

### **Tarea Actual: Refactorizar el Nombre de los Archivos Offline**

**Objetivo:** Modificar la forma en que se nombran los archivos XML de las facturas generadas en modo offline. Esto es un requisito para poder procesarlos en paquetes más adelante.

**Archivo a modificar:** `tabs/facturacion_tab.py`

**Función específica a modificar:** `_handle_offline_submission(...)`

---

#### **Instrucciones Precisas**

1.  **Abre el archivo** ubicado en `tabs/facturacion_tab.py`.

2.  **Navega dentro del archivo** hasta que encuentres la definición de la función `_handle_offline_submission`.

3.  **Dentro de esa función**, localiza la línea de código donde se define la variable `filename`. Actualmente se ve así:

    ```python
    # Esta es la línea que vamos a cambiar
    filename = f"offline_invoices/factura_{numero_factura}.xml"
    ```

4.  **Reemplaza esa única línea** con el siguiente bloque de código. Este bloque es más seguro y crea el nombre de archivo descriptivo que necesitamos:

    ```python
    # --- INICIO DEL CÓDIGO DE REEMPLAZO ---

    evento_id = evento_activo.get('id')
    if not evento_id:
        show_message('error', "Error crítico: El evento de contingencia no tiene un ID. No se puede guardar la factura.", message_placeholder)
        logger.error(f"El evento activo {evento_activo} no tiene una clave 'id'.")
        return

    # Creamos un nombre de archivo descriptivo y fácil de procesar
    filename = f"offline_invoices/factura_offline_ev{evento_id}_n{numero_factura}.xml"

    # --- FIN DEL CÓDIGO DE REEMPLAZO ---
    ```

**Eso es todo.** No necesitas hacer ningún otro cambio en ningún otro archivo por ahora.