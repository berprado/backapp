# Automatización del Proceso de Impresión

Este documento resume los ajustes aplicados al flujo de impresión de BACKINVOICE.

## 1. Modelo de datos
- `facturador/data_models/invoice_data.py` define `DetalleFactura` y `FacturaProcesada`.
- `FacturaProcesada` es la fuente de verdad una vez que la factura fue validada (online u offline).
- Tras la validación, la UI crea una instancia y la guarda en `st.session_state['factura_a_procesar']` para impresión/consulta.

## 2. Gestor de impresión (`print_manager.py`)
- Se implementó `PrinterRuntime` que encapsula cola, hilo y estado del worker.
- `_update_print_session()` mantiene sincronizados `print_status`, flags de progreso, último trabajo y heartbeat.
- `start_printer_worker()` arranca o reinicia el hilo y registra su estado.
- `solicitar_impresion()` serializa la factura, la encola y marca el estado `[ENVIADO]`.
- `initialize_print_state()` asegura que las claves críticas existan en `st.session_state`.

### Ciclo del worker
1. Toma trabajos de la cola y reconstruye `FacturaProcesada`.
2. Genera HTML+PDF en `pdfs/` mediante `invoice_templates` y `siat_pdf`.
3. Ejecuta `ThermalPrinter.print_invoice()` reutilizando la conexión USB persistente.
4. Actualiza `print_status` a `[OK]`, `[ADVERTENCIA]` o `[ERROR]` según el resultado.
5. Registra heartbeats para diagnóstico y libera la impresora cuando ocurre un fallo.

## 3. Driver de impresora (`thermal_printer.py`)
- Consume `FacturaProcesada` y produce el ticket (encabezados, detalle, totales, QR).
- En caso de error desconecta la impresora para forzar reconexión limpia en el próximo trabajo.

## 4. UI de facturación (`tabs/facturacion_tab.py`)
- `_render_print_button()` ahora dispara la impresión automática al validar:
  - Inicializa el estado del worker y `auto_print_last_id`.
  - Identifica la factura por `CUF`/número, la envía a impresión y hace `st.rerun()`.
  - Cuando `print_status` refleja `[OK]`, `[ADVERTENCIA]` o `[ERROR]` limpia `impresion_en_progreso` y, en el caso de éxito, marca `impresion_finalizada` para permitir nuevas impresiones.
- `_trigger_print_job()` centraliza la llamada a `solicitar_impresion()` y maneja errores de cola.

## 5. UI principal (`ui_copy.py`)
- Muestra el estado general (conectividad + impresión) empleando los nuevos campos de `session_state`.
- Activa el banner de diagnóstico únicamente si hay indicadores reales de problema (`impresion_en_progreso` atascado, `print_status` con error, worker detenido, etc.).

## 6. Verificador (`verificador_session_state.py`)
- Amplía las claves revisadas (`printer_worker_status`, `printer_worker_last_heartbeat`, `ultimo_trabajo_impresion`, `auto_print_last_id`).
- Ajusta las recomendaciones según el estado del worker y los heartbeats.

## 7. Flujo actual
1. Factura validada → se crea `FacturaProcesada` y se guarda en sesión.
2. `_render_print_button()` detecta la validación y encola automáticamente el trabajo.
3. El worker procesa PDF + impresión y actualiza el estado.
4. Si la impresión falla, el estado queda en `[ADVERTENCIA]` y la UI lo muestra; si tiene éxito, los flags se limpian y queda lista para la siguiente factura sin reiniciar.

## 8. Pruebas
- `python -m compileall -q facturador` tras cada serie de cambios.
- Ciclo manual completo: emisión, validación, generación de PDF, impresión exitosa y manejo de error USB.
- Validación de múltiples impresiones consecutivas para comprobar que `impresion_en_progreso` se libera.

## 9. Próximos pasos sugeridos
- Documentar el proceso para reinstalar o liberar el driver USB cuando libusb no pueda reclamar la interfaz.
- Agregar pruebas automatizadas para la cola de impresión (mock del worker y de ThermalPrinter).
- Registrar un identificador correlativo en logs para rastrear los intentos de impresión end-to-end.
