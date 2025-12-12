# Dependencias internas de [facturador/soap_services.py](facturador/soap_services.py)

## Vision general
[facturador/soap_services.py](facturador/soap_services.py) implementa llamadas SOAP directas al SIN para verificar comunicacion y registrar eventos significativos, aplicando clasificacion normativa de errores y medicion de tiempo.

## Modulos propios utilizados

1. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger, timed_call.  
   - Rol: centralizar logs del canal SIAT y medir duracion de peticiones HTTP.

## Conclusion
Este modulo complementa los flujos de contingencia descritos en [facturador/docs/refactor/16_dependencias_contingency_manager.md](facturador/docs/refactor/16_dependencias_contingency_manager.md) y comparte la misma configuracion de logging resumida en [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md).
