# Automatización del Proceso de Impresión

Este documento resume los ajustes aplicados al flujo de impresión de BACKINVOICE.

## 1. Modelo de datos
- `facturador/data_models/invoice_data.py` define `DetalleFactura` y `FacturaProcesada`.
- `FacturaProcesada` es la fuente de verdad una vez que la factura fue validada (online u offline).
- Tras la validación, la UI crea una instancia y la guarda en `st.session_state['factura_a_procesar']` para impresión y consulta posterior.

## 2. Gestor de impresión (`print_manager.py`)
- `PrinterRuntime` encapsula cola, hilo y telemetria del worker.
- `_update_print_session()` mantiene sincronizados `print_status`, la estructura `print_status_info`, las banderas de progreso, el último trabajo y el heartbeat.
- Aplica un rate-limiting suave: solo descarta actualizaciones idénticas cuando llegan en menos de 0.5s, manteniendo visibles los cambios reales.
- `start_printer_worker()` arranca o reinicia el hilo y registra su estado en sesion.
- `solicitar_impresión()` serializa la factura, la encola y marca el estado `PrintStatusCode.QUEUED`.
- `initialize_print_state()` garantiza que las claves criticas existan en `st.session_state`.

### Ciclo del worker
1. Toma trabajos de la cola, valida que sean diccionarios y reconstruye `FacturaProcesada`.
2. Genera HTML+PDF mediante `PdfGenerator` (`print_services.PdfGenerator`), que envuelve `invoice_templates` y `siat_pdf`.
3. Ejecuta `ThermalPrintService.print_factura()` para enviar la orden a la impresora termica reutilizando la conexion USB.
4. Actualiza `print_status_info` con un `PrintStatusCode` tipado (`PROCESSING`, `PDF_ERROR`, `PRINTER_SUCCESS`, etc.) y ajusta `impresión_en_progreso` o `impresión_finalizada` segun corresponda.
5. Registra heartbeats para diagnóstico y devuelve `False` en progreso cuando ocurre un fallo, evitando estados bloqueados.

## 3. Servicios de impresión (`print_services.py`)
- `PdfGenerator` centraliza la generacion del PDF y levanta `PdfGenerationError` cuando algo falla.
- `ThermalPrintService` envuelve a `ThermalPrinter`, normaliza excepciones en `PrinterJobError` y reporta codigos (`connection_failed`, `job_failed`, `job_exception`).

## 4. UI de facturación (`tabs/facturacion_tab.py`)
- `_render_print_button()` dispara la impresión automática al validar y reutiliza el mensaje/severidad centralizados (`print_status_info`).
  - El banner conserva el mensaje principal y el panel añade detalles complementarios (cola, duración, recomendaciones y `status_detail`) sin duplicar textos.
  - Las advertencias y errores orientan al usuario sobre cómo resolver (`printer_warning` → reintentar, `printer_error` → revisar dispositivo).
- `_trigger_print_job()` centraliza la llamada a `solicitar_impresión()` y maneja errores de cola.

## 5. UI principal (`ui_copy.py`)
- El banner rápido usa `print_status_info.severity` para distinguir entre errores y advertencias reales, evitando falsos positivos por coincidencias de texto.
- `_schedule_auto_refresh()` compara versiones (`print_state_version` vs `_print_last_seen_version`) y dispara un único `st.rerun()` cuando llega un nuevo estado.
- La vista principal muestra el mismo mensaje que el banner y reserva los detalles técnicos para despliegues controlados (diagnóstico o panel complementario).

## 6. Verificador (`verificador_session_state.py`)
- Amplia las claves revisadas (`printer_worker_status`, `printer_worker_last_heartbeat`, `print_status_info`, `ultimo_trabajo_impresión`, `auto_print_last_id`).
- Trata claves opcionales (`factura_a_procesar`, `datos_impresión`, `cuf`) como informativas para evitar falsos positivos en el diagnóstico.
- Incorpora el nuevo codigo/severidad en el resumen para priorizar alertas y recomendaciones.

## 7. Flujo actual
1. La factura se valida y se guarda `FacturaProcesada` en sesion.
2. `_render_print_button()` detecta la validación y encola automáticamente el trabajo.
3. El worker genera el PDF, imprime y actualiza `print_status_info` con el resultado tipado.
4. Si la impresión falla, la UI muestra severidad `warning` o `error` segun el origen, y los flags se limpian para permitir reintentos controlados.

## 8. Pruebas sugeridas
- `python -m compileall -q facturador` despues de cambios de backend.
- Ciclo manual completo: emision, validación, generacion de PDF, impresión exitosa y manejo de error USB simulado.
- Validacion de impresiónes consecutivas para confirmar que `impresión_en_progreso` se libera.

## 9. Proximos pasos sugeridos
- Documentar el proceso para reinstalar o liberar el driver USB cuando libusb no pueda reclamar la interfaz.
- Agregar pruebas automatizadas para la cola y el worker (mock de `PdfGenerator` y `ThermalPrintService`).
- Registrar un identificador correlativo en logs para rastrear intentos de impresión end-to-end.
