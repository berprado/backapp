# Dependencias internas de [facturador/significant_events.py](facturador/significant_events.py)

## Vision general
[facturador/significant_events.py](facturador/significant_events.py) gestiona el registro y consulta de eventos significativos ante SIAT y en la base local, validando duplicados abiertos y exponiendo cierres de eventos.

## Modulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Componentes: SessionLocal.  
   - Rol: abrir sesiones ORM para insertar y consultar eventos registrados.

2. **[facturador/models.py](facturador/models.py)**  
   - Modelos: EventoSignificativoRegistrado; Cufd (importacion diferida en query).  
   - Rol: mapear eventos almacenados y recuperar el CUFD vigente para consultas SIAT.

3. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: emitir logs de contingencia al registrar, consultar o cerrar eventos.

## Conclusion
El manejo de eventos se apoya en la capa de datos descrita en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md) y mantiene coherencia con la estrategia de contingencia documentada en [facturador/docs/refactor/16_dependencias_contingency_manager.md](facturador/docs/refactor/16_dependencias_contingency_manager.md), facilitando la trazabilidad frente a SIAT.
