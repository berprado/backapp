# Automatizacion del Proceso de Impresion

Este documento resume los ajustes aplicados al flujo de impresion de BACKINVOICE.

## 1. Modelo de datos
- `facturador/data_models/invoice_data.py` define `DetalleFactura` y `FacturaProcesada`.
- `FacturaProcesada` es la fuente de verdad una vez que la factura fue validada (online u offline).
- Tras la validacion, la UI crea una instancia y la guarda en `st.session_state['factura_a_procesar']` para impresion y consulta posterior.

## 2. Gestor de impresion (`print_manager.py`)
- `PrinterRuntime` encapsula cola, hilo y telemetria del worker.
- `_update_print_session()` mantiene sincronizados `print_status`, la estructura `print_status_info`, las banderas de progreso, el ultimo trabajo y el heartbeat.
- `start_printer_worker()` arranca o reinicia el hilo y registra su estado en sesion.
- `solicitar_impresion()` serializa la factura, la encola y marca el estado `PrintStatusCode.QUEUED`.
- `initialize_print_state()` garantiza que las claves criticas existan en `st.session_state`.

### Ciclo del worker
1. Toma trabajos de la cola, valida que sean diccionarios y reconstruye `FacturaProcesada`.
2. Genera HTML+PDF mediante `PdfGenerator` (`print_services.PdfGenerator`), que envuelve `invoice_templates` y `siat_pdf`.
3. Ejecuta `ThermalPrintService.print_factura()` para enviar la orden a la impresora termica reutilizando la conexion USB.
4. Actualiza `print_status_info` con un `PrintStatusCode` tipado (`PROCESSING`, `PDF_ERROR`, `PRINTER_SUCCESS`, etc.) y ajusta `impresion_en_progreso` o `impresion_finalizada` segun corresponda.
5. Registra heartbeats para diagnostico y devuelve `False` en progreso cuando ocurre un fallo, evitando estados bloqueados.

## 3. Servicios de impresion (`print_services.py`)
- `PdfGenerator` centraliza la generacion del PDF y levanta `PdfGenerationError` cuando algo falla.
- `ThermalPrintService` envuelve a `ThermalPrinter`, normaliza excepciones en `PrinterJobError` y reporta codigos (`connection_failed`, `job_failed`, `job_exception`).

## 4. UI de facturacion (`tabs/facturacion_tab.py`)
- `_render_print_button()` dispara la impresion automatica al validar:
  - Inicializa el estado del worker y `auto_print_last_id`.
  - Identifica la factura por `CUF`/numero, la envia a impresion y ejecuta `st.rerun()`.
  - Clasifica la severidad por `print_status_info.severity` y limpia `impresion_en_progreso` cuando el estado del trabajo termina (`printer_success`, `printer_warning`, `printer_error`, `pdf_error`, `data_error`, `critical_error`).
- `_trigger_print_job()` centraliza la llamada a `solicitar_impresion()` y maneja errores de cola.

## 5. UI principal (`ui_copy.py`)
- El banner rapido usa `print_status_info.severity` para distinguir entre errores y advertencias reales, evitando falsos positivos por coincidencias de texto.
- El diagnostico rapido se activa cuando hay progreso pendiente, una severidad de alerta o el worker reporta un estado distinto de `running`.

## 6. Verificador (`verificador_session_state.py`)
- Amplia las claves revisadas (`printer_worker_status`, `printer_worker_last_heartbeat`, `print_status_info`, `ultimo_trabajo_impresion`, `auto_print_last_id`).
- Trata claves opcionales (`factura_a_procesar`, `datos_impresion`, `cuf`) como informativas para evitar falsos positivos en el diagnostico.
- Incorpora el nuevo codigo/severidad en el resumen para priorizar alertas y recomendaciones.

## 7. Flujo actual
1. La factura se valida y se guarda `FacturaProcesada` en sesion.
2. `_render_print_button()` detecta la validacion y encola automaticamente el trabajo.
3. El worker genera el PDF, imprime y actualiza `print_status_info` con el resultado tipado.
4. Si la impresion falla, la UI muestra severidad `warning` o `error` segun el origen, y los flags se limpian para permitir reintentos controlados.

## 8. Pruebas sugeridas
- `python -m compileall -q facturador` despues de cambios de backend.
- Ciclo manual completo: emision, validacion, generacion de PDF, impresion exitosa y manejo de error USB simulado.
- Validacion de impresiones consecutivas para confirmar que `impresion_en_progreso` se libera.

## 9. Proximos pasos sugeridos
- Documentar el proceso para reinstalar o liberar el driver USB cuando libusb no pueda reclamar la interfaz.
- Agregar pruebas automatizadas para la cola y el worker (mock de `PdfGenerator` y `ThermalPrintService`).
- Registrar un identificador correlativo en logs para rastrear intentos de impresion end-to-end.
