# Dependencias internas de [facturador/client_manager.py](facturador/client_manager.py)

## Visión general
[facturador/client_manager.py](facturador/client_manager.py) centraliza las operaciones CRUD de clientes, validaciones básicas y verificación de NIT ante el SIAT.

## Módulos propios utilizados

1. **[facturador/database.py](facturador/database.py)**  
   - Componentes: SessionLocal.  
   - Rol: abrir sesiones ORM para crear o recuperar clientes.

2. **[facturador/models.py](facturador/models.py)**  
   - Modelos: Cliente.  
   - Rol: representar a nivel ORM los registros de clientes.

3. **[facturador/validators.py](facturador/validators.py)**  
   - Funciones: es_email_valido, es_telefono_valido, verificar_nit.  
   - Rol: ejecutar validaciones de datos y consumo de servicios de verificación de NIT.

4. **[facturador/api_clients.py](facturador/api_clients.py)**  
   - Funciones: get_soap_client.  
   - Rol: obtener el cliente SOAP configurado para validar NIT en línea.

5. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: inicializar el logger usado en las operaciones de clientes.

6. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: fetch_cliente (importación diferida).  
   - Rol: reutilizar la consulta principal de clientes desde la capa de datos.

## Conclusión
[facturador/client_manager.py](facturador/client_manager.py) depende de la infraestructura documentada en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md), [facturador/docs/refactor/09_dependencias_print_manager.md](facturador/docs/refactor/09_dependencias_print_manager.md) y [facturador/docs/refactor/10_dependencias_api_clients.md](facturador/docs/refactor/10_dependencias_api_clients.md). Este inventario facilita futuros refactors siguiendo [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).