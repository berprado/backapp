# Dependencias internas de [facturador/ui_copy.py](facturador/ui_copy.py)

## Visión general
El módulo coordina la interfaz principal de Streamlit, orquestando pestañas, diagnósticos y estado de impresión. Se apoya en servicios internos para impresión, logging y gestión de pestañas específicas.

## Módulos propios utilizados

1. **[facturador/print_manager.py](facturador/print_manager.py)**  
   - Componentes: initialize_print_state, get_print_state_summary.  
   - Rol: inicializar y consultar el estado del servicio de impresión.

2. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Componentes: get_logger.  
   - Rol: obtener loggers específicos para la interfaz.

3. **Pestañas de la UI**  
   - Módulos: [facturador/tabs/facturacion_tab.py](facturador/tabs/facturacion_tab.py), [facturador/tabs/facturas_tab.py](facturador/tabs/facturas_tab.py), [facturador/tabs/clientes_tab.py](facturador/tabs/clientes_tab.py), [facturador/tabs/validar_nit_tab.py](facturador/tabs/validar_nit_tab.py), [facturador/tabs/verificar_factura_tab.py](facturador/tabs/verificar_factura_tab.py), [facturador/tabs/cuis_tab.py](facturador/tabs/cuis_tab.py), [facturador/tabs/anular_revertir_tab.py](facturador/tabs/anular_revertir_tab.py), [facturador/tabs/diagnostico_tab.py](facturador/tabs/diagnostico_tab.py).  
   - Rol: funciones render que se invocan según la pestaña seleccionada.

4. **[facturador/verificador_session_state.py](facturador/verificador_session_state.py)**  
   - Componentes: ejecutar_diagnostico_completo.  
   - Rol: exponer diagnósticos detallados del estado de impresión.

5. **[facturador/api_clients.py](facturador/api_clients.py)**  
   - Componentes: reset_soap_client.  
   - Rol: reiniciar el cliente SOAP durante acciones de reconexión.

## Conclusión
`ui_copy.py` es un orquestador de UI que depende de módulos especializados para impresión y diagnóstico, así como de las pestañas del sistema. Documentar estas relaciones facilita el refactor y la modularización planificada en `01_plan_refactorizacion_ui.md`.
