# Dependencias internas de [facturador/validators.py](facturador/validators.py)

## Vision general
[facturador/validators.py](facturador/validators.py) valida formatos basicos (email, telefono), verifica NIT contra SIAT y comprueba campos obligatorios de cabecera/detalle de factura.

## Modulos propios utilizados

1. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: registrar errores al verificar NIT o validar datos.

2. **[facturador/api_clients.py](facturador/api_clients.py)**  
   - Funciones: get_soap_client.  
   - Rol: obtener el cliente SOAP centralizado para la verificacion de NIT.

## Conclusion
Las validaciones sostienen los flujos de captura de datos descritos en [facturador/docs/refactor/14_dependencias_client_manager.md](facturador/docs/refactor/14_dependencias_client_manager.md) y las operaciones SIAT, reutilizando la infraestructura de logging de [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md).
