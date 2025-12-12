# Dependencias internas de [facturador/response_handler.py](facturador/response_handler.py)

## Vision general
[facturador/response_handler.py](facturador/response_handler.py) normaliza respuestas SOAP del SIAT, guarda XML segun configuracion y presenta mensajes legibles en la interfaz Streamlit.

## Modulos propios utilizados

1. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_response_logger.  
   - Rol: obtener el logger especializado para trazas de parseo y guardado de XML.

## Conclusion
Este manejador se apoya en la infraestructura de logging descrita en [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md) y complementa los flujos de respuesta usados por `anulacion` y `reversion` documentados en [facturador/docs/refactor/11_dependencias_anulacion.md](facturador/docs/refactor/11_dependencias_anulacion.md).
