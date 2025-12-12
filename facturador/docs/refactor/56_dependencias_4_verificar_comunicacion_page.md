# Dependencias internas de [facturador/pages/4_Verificar_Comunicación.py](facturador/pages/4_Verificar_Comunicación.py)

## Visión general
[facturador/pages/4_Verificar_Comunicación.py](facturador/pages/4_Verificar_Comunicación.py) habilita un tablero de diagnóstico en Streamlit que consume el verificador central para mostrar métricas y recomendaciones de contingencia.

## Módulos propios utilizados

1. **[facturador/communication_manager.py](facturador/communication_manager.py)**  
   - Objetos: communication_manager.  
   - Rol: suministra el resultado cacheado de las verificaciones y permite lanzar diagnósticos forzados.

2. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: registra las interacciones de la página y unifica el seguimiento de errores y métricas mostradas.

## Conclusión
[facturador/pages/4_Verificar_Comunicación.py](facturador/pages/4_Verificar_Comunicación.py) materializa la centralización descrita en [facturador/docs/refactor/07_dependencias_communication_manager.md](facturador/docs/refactor/07_dependencias_communication_manager.md) y aprovecha la configuración de logging documentada en [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md). Con ello, la página se mantiene alineada con las mejoras de caché indicadas en `refactor_cache_5_fix.instructions.md` y `refactor_cache_6_fix.instructions.md`.
