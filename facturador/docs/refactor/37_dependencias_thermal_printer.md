# Dependencias internas de [facturador/thermal_printer.py](facturador/thermal_printer.py)

## Vision general
[facturador/thermal_printer.py](facturador/thermal_printer.py) encapsula la conexion USB y la impresion termica de facturas `FacturaProcesada`, administrando reconexiones y registro detallado de errores.

## Modulos propios utilizados

1. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger, get_printer_logger.  
   - Rol: obtener loggers dedicados para diagnosticar conexion, impresion y reconexion de la impresora.

2. **[facturador/data_models.py](facturador/data_models.py)**  
   - Modelos: FacturaProcesada.  
   - Rol: tipar los datos de factura que se imprimen linea a linea y alimentan el QR.

## Conclusion
El driver termico se integra con el flujo de impresion documentado en [facturador/docs/refactor/28_dependencias_print_services.md](facturador/docs/refactor/28_dependencias_print_services.md) y reutiliza la configuracion de logging detallada en [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md), asegurando coherencia operativa con el worker de impresion.
