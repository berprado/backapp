---
applyTo: '**'
---
Hemos logrado algo monumental: **la arquitectura ahora es robusta y el problema ya no es un "crash" silencioso, sino un problema de gestión de recursos mucho más sutil y solucionable.**

### Diagnóstico Final y Preciso del Problema de Intermitencia

1.  **El Inicio (`start_printer_worker`):** Al lanzar `streamlit run main.py`, se crea correctamente un único hilo `PrinterWorkerThread`. Tu diagnóstico lo ve y te avisa. **Esto no es un error, es la confirmación de que nuestro "cartero" está contratado y esperando trabajo**.
2.  **La Primera Impresión (Éxito):** Cuando solicitas la primera impresión, el `worker` (que ya estaba corriendo) recibe el trabajo de la cola. Realiza la generación del PDF (vemos los logs detallados de `weasyprint` y sus fuentes) y luego se conecta a la impresora (`Impresora conectada exitosamente`), imprime (`Impresión desde objeto de datos completada`) y cierra la conexión. Todo funciona a la perfección.
3.  **El Segundo Intento (Fallo):** Cuando solicitas la segunda impresión, el `worker` recibe el nuevo trabajo, pero **falla al intentar conectarse a la impresora**.

**La Causa Raíz:**

El problema está en cómo la librería `python-escpos` y el driver `libusbK` manejan el "reclamar" y "liberar" el dispositivo USB.

Cuando el `worker` termina la primera impresión, el `contextmanager` (`printer_connection`) cierra la conexión. Sin embargo, a nivel del sistema operativo y del driver, el dispositivo puede no ser liberado instantáneamente o de manera limpia.

Cuando el `worker` intenta conectarse de nuevo para la segunda factura, el driver USB aún cree que el dispositivo está "en uso" (posiblemente por el proceso anterior, que ahora es un "fantasma" a nivel de driver, aunque el hilo de Python siga vivo). La librería `pyusb` no maneja bien esta condición y, en lugar de esperar o dar un error claro, entra en un estado de bloqueo o fallo, lo que detiene esa ejecución del bucle del `worker`.

El hecho de que a veces funcione después de un tiempo o un reinicio confirma esta teoría: eventualmente, el sistema operativo "limpia" el bloqueo del recurso USB, y el siguiente intento de conexión tiene éxito.

### La Solución: Mantener la Conexión Abierta (Patrón Singleton de Hardware)

La solución es dejar de tratar la conexión a la impresora como algo que se abre y se cierra para cada factura. En su lugar, trataremos a la impresora como un **recurso único y persistente (Singleton)** que nuestro `worker` "poseerá" durante toda su vida.

El `worker` se conectará a la impresora **una sola vez** cuando reciba su primer trabajo y mantendrá esa conexión abierta para todos los trabajos subsiguientes.

---

### Plan de Acción Final y Definitivo

Vamos a hacer un ajuste clave en `print_manager.py` y `thermal_printer.py`.

#### **Paso 1: Modificar `thermal_printer.py` para Soportar una Conexión Persistente**

**Acción:**
Abre `thermal_printer.py`.

1.  Añadiremos un atributo `self._printer` para mantener la conexión.
2.  Crearemos métodos `connect()` y `disconnect()`.
3.  Modificaremos `print_invoice` para que use la conexión existente.

**Código Refactorizado para `thermal_printer.py`:**

```python
# thermal_printer.py
# ... (importaciones se mantienen) ...

class ThermalPrinter:
    def __init__(self, vendor_id=0x04B8, product_id=0x0E15):
        # ... (atributos existentes se mantienen) ...
        self._printer = None # NUEVO: Atributo para mantener la conexión

    def connect(self):
        """Se conecta a la impresora si no está ya conectada."""
        if self._printer is None:
            try:
                self.logger.info("Intentando conectar con la impresora USB...")
                self._printer = Usb(self.vendor_id, self.product_id)
                self.logger.info("Impresora conectada exitosamente.")
            except Exception as e:
                self.logger.error(f"Error al conectar con la impresora: {str(e)}")
                self._printer = None # Asegurarse de que sigue siendo None si falla
                raise # Lanzar la excepción para que el worker la maneje
        else:
            self.logger.info("Ya se encuentra conectado a la impresora.")

    def disconnect(self):
        """Cierra la conexión con la impresora."""
        if self._printer is not None:
            try:
                self.logger.info("Cerrando conexión con la impresora.")
                self._printer.close()
            except Exception as e:
                self.logger.error(f"Error al cerrar la conexión: {str(e)}")
            finally:
                self._printer = None

    # ELIMINAMOS EL CONTEXT MANAGER printer_connection

    # ... (_print_line, _print_separator, _print_qr se mantienen igual) ...

    def print_invoice(self, factura: FacturaProcesada) -> bool:
        """Imprime la factura usando una conexión existente."""
        try:
            if self._printer is None:
                raise Exception("La impresora no está conectada. Se debe llamar a connect() primero.")
            
            printer_logger.info(f"Imprimiendo factura {factura.numero_factura} en conexión existente.")
            
            # EL CUERPO DE LA IMPRESIÓN SE QUEDA EXACTAMENTE IGUAL,
            # PERO SIN EL 'with self.printer_connection() as printer:'
            # Simplemente usamos self._printer en lugar de 'printer'
            
            # Encabezado
            self._print_line(self._printer, factura.tipo_factura, align='center', bold=True)
            # ... (Toda la lógica de impresión de líneas, productos, qr, etc.) ...
            # ... (usando self._printer en lugar de printer) ...
            self._print_qr(self._printer, factura.url_qr)
            self._printer.cut()
            
            self.logger.info("Impresión desde objeto de datos completada.")
            return True
        except Exception as e:
            printer_logger.error(f"Error en print_invoice desde objeto: {e}", exc_info=True)
            # Si hay un error de impresión, es buena idea cerrar la conexión
            # para forzar una reconexión en el siguiente intento.
            self.disconnect()
            return False

```

#### **Paso 2: Modificar `print_manager.py` para Usar la Conexión Persistente**

**Acción:**
Abre `print_manager.py`. Ahora el `worker` gestionará la conexión.

**Código Refactorizado para la función `printer_worker` en `print_manager.py`:**

```python
# print_manager.py

def printer_worker(q: queue.Queue):
    """
    Hilo trabajador con conexión de impresora persistente.
    """
    printer_logger.info("WORKER: Hilo de impresión iniciado.")
    
    # Creamos una ÚNICA instancia de la impresora para este worker.
    printer = ThermalPrinter()
    
    while True:
        try:
            factura_obj = q.get()
            if factura_obj is None: break

            printer_logger.info(f"WORKER: Nuevo trabajo recibido para factura N° {factura_obj.numero_factura}")
            st.session_state['print_status'] = f"⏱️ Procesando factura N° {factura_obj.numero_factura}..."
            
            # --- Generación de PDF (sin cambios) ---
            # ...

            # --- Impresión Térmica con Conexión Persistente ---
            try:
                # Conectamos solo si es necesario (la primera vez o si hubo un error)
                printer.connect()
                
                success = printer.print_invoice(factura_obj)
                if not success: raise Exception("print_invoice retornó False")
                
                printer_logger.info(f"WORKER: Impresión térmica para factura {factura_obj.numero_factura} completada.")
                st.session_state['print_status'] = f"✅ Factura N° {factura_obj.numero_factura} impresa exitosamente."
            except Exception as e:
                printer_logger.error(f"WORKER: Error de impresora para factura {factura_obj.numero_factura}: {e}", exc_info=True)
                st.session_state['print_status'] = f"⚠️ PDF de Factura {factura_obj.numero_factura} generado, pero la impresora falló."
                # Importante: Desconectamos para forzar un reintento de conexión en el próximo trabajo
                printer.disconnect()

            q.task_done()

        except Exception as e:
            # ... (manejo de error catastrófico se mantiene) ...

    # Al salir del bucle (si alguna vez lo hace), nos aseguramos de desconectar
    printer.disconnect()
    printer_logger.info("WORKER: Hilo de impresión finalizado.")

```

Con estos cambios, el `PrinterWorkerThread` se convierte en el "dueño" de la conexión a la impresora. La abre una vez y la reutiliza, evitando el ciclo de reclamar/liberar el recurso USB que causaba los bloqueos. Si la impresión falla, forzamos una desconexión para que el siguiente trabajo intente restablecer una conexión limpia.
