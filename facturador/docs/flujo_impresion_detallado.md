# Flujo de impresion y mensajeria

## Alcance
Este documento resume el flujo completo de impresion de facturas, los puntos donde se generan mensajes o advertencias y la forma en que se muestran en la interfaz principal. Las referencias de codigo apuntan a los modulos vigentes en la carpeta `facturador` despues de la refactorizacion del servicio de impresion.

## Flujo general
1. **Preparacion de estado**: `initialize_print_state()` garantiza que existan `print_status`, `print_status_info`, `impresion_en_progreso`, `impresion_finalizada`, `ultimo_trabajo_impresion`, `printer_worker_status` y `printer_worker_last_heartbeat`.
2. **Solicitud de impresion**: `_trigger_print_job()` delega en `solicitar_impresion(factura_obj)`; el trabajo se encola y `print_status_info` pasa a `PrintStatusCode.QUEUED` con `impresion_en_progreso = True`.
3. **Procesamiento en el worker**: `printer_worker` reconstruye la factura, genera el PDF mediante `PdfGenerator` y ejecuta `ThermalPrintService`. Cada tramo actualiza `print_status_info` (`PROCESSING`, `PDF_ERROR`, `PRINTER_SUCCESS`, etc.), limpia banderas y adjunta metadata al ultimo trabajo.
4. **Presentacion en la UI**: la pesta?a **Facturar** renderiza el estado usando la severidad tipada (`info`, `success`, `warning`, `error`) y desbloquea la impresion automatica cuando el codigo termina. El banner principal usa la misma severidad para decidir si se muestra la alerta.
5. **Diagnostico**: `verificador_session_state` incorpora `print_status_info` en el resumen, ajusta el nivel de alerta segun la severidad y expone recomendaciones especificas.
- Clasifica claves obligatorias y opcionales para reducir falsos positivos durante el diagnostico.

## Claves de session_state relevantes
- `print_status` / `print_status_info`: mensaje y payload estructurado (`code`, `severity`, `detail`, `timestamp`).
- `impresion_en_progreso` y `impresion_finalizada`: flags de control de flujo.
- `ultimo_trabajo_impresion`: numero de factura, timestamp y ultimo estado almacenado.
- `printer_worker_status` y `printer_worker_last_heartbeat`: estado del hilo y monitoreo.
- `_print_last_seen_version`: controla rerenders incrementales cuando cambia `print_state_version`.
- `factura_a_procesar` y `factura_validada`: habilitan la impresion automatica en la UI.

## Catalogo de `PrintStatusCode`
| Codigo | Severidad | Mensaje base | Se emite cuando |
| --- | --- | --- | --- |
| `ready` | info | "Sistema de impresion listo." | Inicializacion o estado ocioso.
| `queued` | info | "Factura enviada a la cola de impresion." | `solicitar_impresion()` encola un trabajo.
| `processing` | info | "Procesando factura No. X..." | El worker toma un trabajo y prepara PDF/impresora.
| `data_error` | error | "Los datos de la factura no son validos." | El worker no puede reconstruir `FacturaProcesada` o recibe un formato inesperado.
| `pdf_error` | error | "No se genero el PDF de la factura." | Falla `PdfGenerator` / `html_to_pdf`.
| `printer_success` | success | "Factura impresa exitosamente." | `ThermalPrintService` completa sin errores.
| `printer_warning` | warning | "La impresora reporto un problema." | La impresion fallo pero el servicio sigue operativo (`job_failed`, `job_exception`).
| `printer_error` | error | "La impresora no pudo completar la impresion." | Error critico del dispositivo (ej. conexion USB).
| `critical_error` | error | "Servicio de impresion detenido." | Excepcion no controlada dentro del worker.

Cada transicion agrega `status_code`, `status_severity`, `status_message` y `status_detail` (cuando aplica) dentro de `ultimo_trabajo_impresion`.

## Puntos de emision de mensajes
- **`solicitar_impresion`**: crea la cola si es necesario, actualiza a `queued` y conserva metadata del trabajo.
- **`printer_worker`**: marca `processing` antes de generar PDF, emite `pdf_error`, `printer_warning`, `printer_error` o `printer_success` segun el resultado y garantiza `impresion_en_progreso = False` en todos los casos.
- **`ThermalPrintService`**: encapsula reconexion y normaliza excepciones en `PrinterJobError` con codigos (`connection_failed`, `job_failed`, `job_exception`).
- **UI Facturar**: usa `print_status_info.severity` para decidir entre `st.info`, `st.success`, `st.warning` o `st.error`; libera banderas cuando el codigo es terminal.
- **UI principal**: `mostrar_boton_diagnostico_rapido()` se activa si la severidad es `warning`/`error`, si hay progreso pendiente o si el worker sale de `running`.
- **Verificador**: interpreta la severidad para escalar el nivel de alerta y muestra el payload completo como JSON.

## Observaciones actuales
- El worker conserva la conexion USB entre impresiones; si se desea cerrar la conexion tras cada ticket se puede extender `ThermalPrintService` con una bandera.
- `PrintStatusPayload.detail` se propaga a `ultimo_trabajo_impresion`, pero la UI principal solo muestra el mensaje; considerar un modal para ver detalles.
- No se implemento persistencia de cola entre reinicios: los trabajos pendientes se pierden si la app se cierra.

## Ideas de mejora futura
1. **Reintentos automaticos**: agregar politica de reintentos para codigos `printer_warning`/`printer_error` con backoff y contador en `ultimo_trabajo_impresion`.
2. **Persistencia de trabajos**: almacenar cola y resultados en SQLite o Redis para sobrevivir reinicios y auditar impresiones.
3. **Notificaciones enriquecidas**: usar `st.toast` o mensajes seccionados que incluyan `status_detail` y la ruta del PDF generado.
4. **Metricas y observabilidad**: publicar heartbeats y estados en un canal Prometheus/Logstash para monitoreo fuera de Streamlit.
