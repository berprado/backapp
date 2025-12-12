# Dependencias internas de [facturador/tabs/validar_nit_tab.py](facturador/tabs/validar_nit_tab.py)

## Visión general
[facturador/tabs/validar_nit_tab.py](facturador/tabs/validar_nit_tab.py) ofrece la interfaz Streamlit para validar NITs aprovechando el diagnóstico centralizado de conectividad.

## Módulos propios utilizados

1. **[facturador/verifica_stream.py](facturador/verifica_stream.py)**  
   - Funciones: main.  
   - Rol: ejecutar la lógica principal de verificación de NIT dentro de la pestaña.

2. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: registrar accesos y advertencias de la pestaña.

3. **[facturador/api_clients.py](facturador/api_clients.py)**  
   - Funciones: is_soap_client_available.  
   - Rol: exponer utilidades para verificar la disponibilidad del cliente SOAP (soporte opcional para la UI).

## Conclusión
[facturador/tabs/validar_nit_tab.py](facturador/tabs/validar_nit_tab.py) depende de la infraestructura documentada en [facturador/docs/refactor/41_dependencias_verifica_stream.md](facturador/docs/refactor/41_dependencias_verifica_stream.md) y [facturador/docs/refactor/10_dependencias_api_clients.md](facturador/docs/refactor/10_dependencias_api_clients.md). Mantener esta relación clara asegura coherencia con el flujo de conectividad central descrito en [facturador/docs/refactor/07_dependencias_communication_manager.md](facturador/docs/refactor/07_dependencias_communication_manager.md).