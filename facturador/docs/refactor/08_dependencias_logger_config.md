# Dependencias internas de [facturador/logger_config.py](facturador/logger_config.py)

## Visión general
`logger_config.py` define la configuración centralizada de logging para toda la aplicación: crea manejadores rotativos, prepara loggers por dominio y expone funciones utilitarias (`get_logger`, `get_printer_logger`, etc.).

## Módulos propios utilizados

- El módulo no importa componentes de otros archivos internos; opera únicamente con librerías estándar (`logging`, `os`, `datetime`, etc.).

## Conclusión
Aunque no depende de otros módulos del proyecto, `logger_config.py` es consumido por la mayoría de las capas. Mantenerlo desacoplado simplifica pruebas y permite ajustar políticas de logging sin afectar dependencias cruzadas.
