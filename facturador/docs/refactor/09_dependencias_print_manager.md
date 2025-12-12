# Dependencias internas de [facturador/print_manager.py](facturador/print_manager.py)

## Visión general
Gestiona el servicio de impresión en segundo plano: cola, worker, generación de PDF y sincronización con el estado de la UI. Provee utilidades para inicializar el runtime y consultar resúmenes de estado.

## Módulos propios utilizados

1. **[facturador/data_models/__init__.py](facturador/data_models/__init__.py)**  
   - Modelos: `FacturaProcesada`.  
   - Rol: reconstruir las facturas recibidas en la cola de impresión.

2. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: `get_printer_logger`.  
   - Rol: obtener el logger específico para registrar eventos del worker.

3. **[facturador/print_services.py](facturador/print_services.py)**  
   - Componentes: `PdfGenerator`, `ThermalPrintService`, `PdfGenerationError`, `PrinterJobError`.  
   - Rol: generar PDFs y comunicarse con la impresora térmica.

4. **[facturador/print_status.py](facturador/print_status.py)**  
   - Componentes: `PrintStatusCode`, `PrintStatusPayload`, `build_status`, `infer_status_from_message`.  
   - Rol: construir estados normalizados para la UI y la sesión.

## Conclusión
`print_manager.py` se apoya en modelos internos, servicios de impresión y utilidades de estado para ofrecer un flujo robusto. Estas dependencias son clave para mantener el worker y la comunicación con la interfaz coherentes durante el refactor.
