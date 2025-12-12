# Dependencias internas de [facturador/pages/1_Sincronizar.py](facturador/pages/1_Sincronizar.py)

## Visión general
[facturador/pages/1_Sincronizar.py](facturador/pages/1_Sincronizar.py) ofrece la página de Streamlit que controla la sincronización normativa con SIAT, consolidando el estado en memoria, las llamadas SOAP y la persistencia de tablas paramétricas.

## Módulos propios utilizados

1. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_sincronizacion_logger.  
   - Rol: expone el logger especializado que centraliza los mensajes de sincronización.

2. **[facturador/database.py](facturador/database.py)**  
   - Funciones: get_db, Base.  
   - Rol: abre sesiones SQLAlchemy y permite reflejar la metadata usada al guardar el estado normativo.

3. **[facturador/models.py](facturador/models.py)**  
   - Clases: SincronizacionEstado y todas las entidades `Sincronizar*` necesarias para paramétricas.  
   - Rol: define los ORM que reciben la data recuperada del SIAT durante cada sincronización.

4. **[facturador/communication_manager.py](facturador/communication_manager.py)** *(importación diferida)*  
   - Objetos: communication_manager.  
   - Rol: ejecuta la verificación inicial cacheada para confirmar conectividad antes de habilitar acciones.

## Conclusión
[facturador/pages/1_Sincronizar.py](facturador/pages/1_Sincronizar.py) aplica los lineamientos descritos en [facturador/docs/refactor/07_dependencias_communication_manager.md](facturador/docs/refactor/07_dependencias_communication_manager.md) y en [facturador/docs/refactor/19_dependencias_database.md](facturador/docs/refactor/19_dependencias_database.md). Esta cartografía facilita mantener alineadas las optimizaciones de caché y logging documentadas en [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md) y sostiene el ciclo de sincronización planificado en [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).
