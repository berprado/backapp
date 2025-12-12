# Dependencias internas de [facturador/tabs/diagnostico_tab.py](facturador/tabs/diagnostico_tab.py)

## Visión general
[facturador/tabs/diagnostico_tab.py](facturador/tabs/diagnostico_tab.py) expone el diagnóstico avanzado de comunicación, integrando el gestor centralizado y ofreciendo histórico de resultados.

## Módulos propios utilizados

1. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: registrar accesos, ejecuciones y fallos al cargar el diagnóstico.

2. **[facturador/communication_manager.py](facturador/communication_manager.py)**  
   - Componentes: communication_manager (importación diferida).  
   - Rol: ejecutar mostrar_diagnostico_completo, obtener_estado_persistente y exponer el estado consolidado de conectividad.

## Conclusión
[facturador/tabs/diagnostico_tab.py](facturador/tabs/diagnostico_tab.py) se basa en el gestor documentado en [facturador/docs/refactor/07_dependencias_communication_manager.md](facturador/docs/refactor/07_dependencias_communication_manager.md). Mantener este vínculo explícito facilita la evolución del monitoreo descrito en `contingencia_*.md` y el plan general [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).