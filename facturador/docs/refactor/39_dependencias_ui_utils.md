# Dependencias internas de [facturador/ui_utils.py](facturador/ui_utils.py)

## Vision general
[facturador/ui_utils.py](facturador/ui_utils.py) agrupa utilidades simples para Streamlit (inicializar session_state, limpiar claves, mostrar mensajes) con logging centralizado opcional.

## Modulos propios utilizados

1. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: obtener el logger de UI para registrar eventos de inicializacion o mensajes.

## Conclusion
Estas utilidades se alinean con el plan de UI en [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md) y reutilizan la configuracion de logging documentada en [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md).
