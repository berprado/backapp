# Dependencias internas de [facturador/verifica_stream.py](facturador/verifica_stream.py)

## Vision general
[facturador/verifica_stream.py](facturador/verifica_stream.py) ofrece una interfaz Streamlit para probar conectividad con el SIN y verificar NIT consumiendo el cliente SOAP centralizado.

## Modulos propios utilizados

1. **[facturador/api_clients.py](facturador/api_clients.py)**  
   - Funciones: get_soap_client.  
   - Rol: obtener el cliente SOAP compartido para invocar verificarComunicacion y verificarNit.

## Conclusion
La utilidad de verificacion en Streamlit se apoya en el cliente centralizado documentado en [facturador/docs/refactor/10_dependencias_api_clients.md](facturador/docs/refactor/10_dependencias_api_clients.md) y facilita pruebas de conectividad dentro de la UI, alineada con el plan de interfaz de [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).
