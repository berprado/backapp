# Dependencias internas de [facturador/api_clients.py](facturador/api_clients.py)

## Visión general
Centraliza la creación y reutilización de clientes externos (principalmente SOAP) hacia los servicios del SIN. Controla inicialización thread-safe, reinicios y reporte de estado de conectividad.

## Módulos propios utilizados

1. **[facturador/contingency_manager.py](facturador/contingency_manager.py)**  
   - Funciones: `check_connectivity`.  
   - Rol: determinar si existe conexión con Internet y con los servidores del SIN antes de instanciar el cliente.

2. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: `get_logger`.  
   - Rol: registrar el ciclo de vida del cliente SOAP y los estados de conectividad.

## Conclusión
`api_clients.py` depende de utilidades internas para saber si es seguro crear o reiniciar el cliente SOAP y para registrar la operación. Al documentar estas relaciones mantenemos claras las rutas que afectan la reconexión desde la UI (`main.py`, `ui_copy.py`).
