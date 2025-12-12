# Dependencias internas de [facturador/pages/2_Eventos_Significativos.py](facturador/pages/2_Eventos_Significativos.py)

## Visión general
[facturador/pages/2_Eventos_Significativos.py](facturador/pages/2_Eventos_Significativos.py) administra la apertura y el cierre de eventos significativos desde Streamlit, aplicando el flujo normativo de contingencia y validando la comunicación antes de contactar al SIN.

## Módulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: get_eventos_parametricos, obtener_evento_activo_actual, registrar_evento_local_normativo, obtener_cufd_vigente.  
   - Rol: consulta y persiste los eventos registrados, además de recuperar el CUFD vigente ligado a la contingencia.

2. **[facturador/contingencia_auto.py](facturador/contingencia_auto.py)**  
   - Funciones: finalizar_evento_si_conectado.  
   - Rol: ejecuta el cierre normativo cuando la página confirma que la conectividad volvió a estar disponible.

3. **[facturador/communication_manager.py](facturador/communication_manager.py)**  
   - Objetos: communication_manager.  
   - Rol: provee el diagnóstico cacheado que determina si se puede registrar o finalizar un evento.

4. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger, timed_call.  
   - Rol: centraliza los registros y mide la duración de las llamadas clave para auditar el flujo de eventos.

## Conclusión
[facturador/pages/2_Eventos_Significativos.py](facturador/pages/2_Eventos_Significativos.py) es la cara de las instrucciones recogidas en [facturador/docs/refactor/06_dependencias_contingencia_auto.md](facturador/docs/refactor/06_dependencias_contingencia_auto.md) y en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md). Este resumen mantiene la trazabilidad con las guías de contingencia (`contingencia_1.instructions.md` y `contingencia_2.instructions.md`) y asegura coherencia con la monitorización central descrita en [facturador/docs/refactor/07_dependencias_communication_manager.md](facturador/docs/refactor/07_dependencias_communication_manager.md).
