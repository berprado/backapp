# Dependencias internas de [facturador/zeeper.py](facturador/zeeper.py)

## Vision general
[facturador/zeeper.py](facturador/zeeper.py) valida XML contra XSD, comprime en Gzip, calcula hash y envia paquetes Base64 al servicio SIAT con reintentos y logging detallado.

## Modulos propios utilizados

1. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_xml_logger, get_zeeper_logger.  
   - Rol: registrar la validacion, compresion, hash y envio SOAP con distintos canales de log.

## Conclusion
El flujo de empaquetado y envio reutiliza la infraestructura de logging descrita en [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md) y complementa la generacion de XML documentada en [facturador/docs/refactor/25_dependencias_invoice_xml_generator.md](facturador/docs/refactor/25_dependencias_invoice_xml_generator.md), aportando el paso de transporte hacia SIAT.
