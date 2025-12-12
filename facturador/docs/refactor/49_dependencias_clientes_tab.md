# Dependencias internas de [facturador/tabs/clientes_tab.py](facturador/tabs/clientes_tab.py)

## Visión general
[facturador/tabs/clientes_tab.py](facturador/tabs/clientes_tab.py) muestra y pagina el catálogo de clientes desde Streamlit, permitiendo búsquedas y consultas detalladas.

## Módulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: fetch_all_clientes, fetch_cliente.  
   - Rol: obtener la lista paginada y los detalles puntuales de cada cliente.

2. **[facturador/ui_utils.py](facturador/ui_utils.py)**  
   - Funciones: init_session_state.  
   - Rol: inicializar claves de `st.session_state` usadas en la paginación y búsquedas.

3. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: registrar accesos, búsquedas y errores de la pestaña.

## Conclusión
[facturador/tabs/clientes_tab.py](facturador/tabs/clientes_tab.py) se apoya en la capa de datos documentada en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md) y en utilitarios descritos en [facturador/docs/refactor/39_dependencias_ui_utils.md](facturador/docs/refactor/39_dependencias_ui_utils.md). Conservar esta relación simplifica los refactors planificados en [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).