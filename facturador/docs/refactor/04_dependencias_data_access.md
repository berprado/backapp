# Dependencias internas de `facturador/data_access.py`

## Visión general
`data_access.py` centraliza la interacción con la base de datos y los servicios normativos del SIN.
Expone funciones para eventos significativos, obtención de CUFD/CUIS, manejo de clientes, facturación y actualización de paquetes offline.

## Módulos propios utilizados

1. **[facturador/database.py](facturador/database.py)**  
   - Componentes: `SessionLocal`, `engine`, `URL_DATABASE`.  
   - Rol: gestionar la conexión con la base de datos y crear sesiones ORM.

2. **[facturador/models.py](facturador/models.py)**  
   - Modelos: `SincronizarListaLeyendasFactura`, `SincronizarParametricaTipoMetodoPago`, `Cliente`, `FacturaCabecera`, `FacturaDetalle`, entre otros.  
   - Rol: mapear tablas necesarias para consultas y actualizaciones.

3. **[facturador/config.py](facturador/config.py)**  
   - Constantes: `ENDPOINT_URL`.  
   - Rol: acceder a valores de configuración compartidos.

4. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: `get_logger`.  
   - Rol: registrar operaciones y errores de la capa de datos.

5. **[facturador/api_clients.py](facturador/api_clients.py)**  
   - Funciones: `get_soap_client`.  
   - Rol: reutilizar el cliente SOAP centralizado al realizar solicitudes normativas.

## Conclusión
`data_access.py` se apoya en módulos de infraestructura para interactuar con la base de datos y los servicios del SIN. Mantener estos contratos claros es clave para el refactor documentado en `00_diagnostico_main.md` y `01_plan_refactorizacion_ui.md`.
