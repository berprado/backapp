# Dependencias internas de [facturador/tabs/cuis_tab.py](facturador/tabs/cuis_tab.py)

## Visión general
[facturador/tabs/cuis_tab.py](facturador/tabs/cuis_tab.py) administra la UI para consultar y solicitar códigos CUIS, respetando el diagnóstico de conectividad centralizado.

## Módulos propios utilizados

1. **[facturador/cuis.py](facturador/cuis.py)**  
   - Funciones: main.  
   - Rol: ejecutar la lógica de solicitud e inserción de CUIS desde la pestaña.

2. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: registrar accesos y limitaciones según el modo online/offline.

3. **[facturador/api_clients.py](facturador/api_clients.py)**  
   - Funciones: is_soap_client_available.  
   - Rol: exponer comprobaciones de disponibilidad del cliente SOAP (soporte para mensajes de la interfaz).

## Conclusión
[facturador/tabs/cuis_tab.py](facturador/tabs/cuis_tab.py) depende de la funcionalidad documentada en [facturador/docs/refactor/18_dependencias_cuis.md](facturador/docs/refactor/18_dependencias_cuis.md) y de los servicios SOAP descritos en [facturador/docs/refactor/10_dependencias_api_clients.md](facturador/docs/refactor/10_dependencias_api_clients.md). Esta trazabilidad refuerza las guías de conectividad resumidas en [facturador/docs/refactor/07_dependencias_communication_manager.md](facturador/docs/refactor/07_dependencias_communication_manager.md).