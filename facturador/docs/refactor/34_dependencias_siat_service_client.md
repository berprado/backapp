# Dependencias internas de [facturador/siat_service_client.py](facturador/siat_service_client.py)

## Vision general
[facturador/siat_service_client.py](facturador/siat_service_client.py) centraliza la construccion y envio de solicitudes SOAP al SIAT (verificacion, reversion, anulacion) aplicando un singleton con manejo de errores y logging unificado.

## Modulos propios utilizados

1. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: inicializar el logger que etiqueta las operaciones como [SIAT Client] y captura errores HTTP o timeouts.

## Conclusion
El cliente reutiliza la configuracion de logs documentada en [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md) y reemplaza codigo duplicado en flujos descritos en [facturador/docs/refactor/11_dependencias_anulacion.md](facturador/docs/refactor/11_dependencias_anulacion.md) y [facturador/docs/refactor/31_dependencias_reversion.md](facturador/docs/refactor/31_dependencias_reversion.md), manteniendo un punto unico para integrarse con servicios SIAT.
