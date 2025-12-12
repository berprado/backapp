# Dependencias internas de [facturador/tabs/facturas_tab.py](facturador/tabs/facturas_tab.py)

## Visión general
[facturador/tabs/facturas_tab.py](facturador/tabs/facturas_tab.py) agrupa la consulta de facturas emitidas, segmentándolas por estado para facilitar el monitoreo operativo.

## Módulos propios utilizados

1. **[facturador/invoice_manager.py](facturador/invoice_manager.py)**  
   - Funciones: mostrar_lista_facturas.  
   - Rol: renderizar las tablas de facturas según el estado solicitado.

2. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: registrar accesos y filtros aplicados en la pestaña.

## Conclusión
[facturador/tabs/facturas_tab.py](facturador/tabs/facturas_tab.py) reutiliza la lógica inventariada en [facturador/docs/refactor/23_dependencias_invoice_manager.md](facturador/docs/refactor/23_dependencias_invoice_manager.md), manteniendo coherencia con la estrategia de UI delineada en [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).