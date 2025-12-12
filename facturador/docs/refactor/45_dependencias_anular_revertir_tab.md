# Dependencias internas de [facturador/tabs/anular_revertir_tab.py](facturador/tabs/anular_revertir_tab.py)

## Visión general
[facturador/tabs/anular_revertir_tab.py](facturador/tabs/anular_revertir_tab.py) unifica la interfaz de anulación y reversión de facturas, coordinando validaciones normativas y flujos de UI en Streamlit.

## Módulos propios utilizados

1. **[facturador/anulacion.py](facturador/anulacion.py)**  
   - Funciones: anular_factura.  
   - Rol: ejecutar el protocolo SIAT de anulación cuando el usuario confirma la operación.

2. **[facturador/reversion.py](facturador/reversion.py)**  
   - Funciones: enviar_solicitud_reversion, procesar_respuesta_reversion.  
   - Rol: gestionar la reversión de anulaciones y actualizar la base de datos.

3. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: obtener_cuf_por_numero_factura, obtener_motivos_anulacion.  
   - Rol: recuperar el contexto de la factura y los motivos normativos disponibles.

4. **[facturador/ui_utils.py](facturador/ui_utils.py)**  
   - Funciones: show_message.  
   - Rol: mostrar feedback consistente en la interfaz.

5. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: registrar eventos y advertencias de la pestaña.

## Conclusión
[facturador/tabs/anular_revertir_tab.py](facturador/tabs/anular_revertir_tab.py) se apoya en los flujos normativos descritos en [facturador/docs/refactor/11_dependencias_anulacion.md](facturador/docs/refactor/11_dependencias_anulacion.md) y [facturador/docs/refactor/31_dependencias_reversion.md](facturador/docs/refactor/31_dependencias_reversion.md). Este mapeo de dependencias respalda la refactorización planificada en [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).