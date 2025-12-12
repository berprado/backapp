# Dependencias internas de [facturador/invoice_manager.py](facturador/invoice_manager.py)

## Vision general
[facturador/invoice_manager.py](facturador/invoice_manager.py) administra la escritura y consulta de facturas desde la interfaz Streamlit, controla el folio incremental con bloqueo de hilo y maneja mensajes normativos frente a errores de base de datos.

## Modulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: guardar_factura_cabecera, guardar_factura_detalle, obtener_facturas_por_estado, obtener_factura_completa, obtener_cuf_por_numero_factura.  
   - Rol: persistir cabecera y detalle de facturas, recuperar listados paginados y consultar CUF asociados para la vista de gestion.

2. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_facturacion_logger.  
   - Rol: inicializar el logger usado para registrar errores SQL, advertencias de esquema y trazas de control de folios.

## Conclusion
El modulo se apoya en la capa de datos documentada en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md) y sigue las guias de UI definidas en [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md) para mantener la trazabilidad de las operaciones de facturacion desde la aplicacion principal.
