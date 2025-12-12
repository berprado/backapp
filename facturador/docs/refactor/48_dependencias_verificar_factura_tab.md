# Dependencias internas de [facturador/tabs/verificar_factura_tab.py](facturador/tabs/verificar_factura_tab.py)

## Visión general
[facturador/tabs/verificar_factura_tab.py](facturador/tabs/verificar_factura_tab.py) brinda la interfaz de verificación de estado de facturas, reutilizando el caché híbrido de `estado_factura.py` y mostrando feedback detallado.

## Módulos propios utilizados

1. **[facturador/estado_factura.py](facturador/estado_factura.py)**  
   - Funciones: verificar_estado_factura.  
   - Rol: consultar el SIAT con el sistema de caché de 30 segundos.

2. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: obtener_cuf_por_numero_factura, obtener_mensaje_por_codigo.  
   - Rol: recuperar la factura local y mensajes normativos asociados a códigos SIAT.

3. **[facturador/ui_utils.py](facturador/ui_utils.py)**  
   - Funciones: show_message.  
   - Rol: unificar la presentación de mensajes al usuario.

4. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: registrar accesos, avisos y errores de la pestaña.

## Conclusión
[facturador/tabs/verificar_factura_tab.py](facturador/tabs/verificar_factura_tab.py) se integra con los componentes ya inventariados en [facturador/docs/refactor/20_dependencias_estado_factura.md](facturador/docs/refactor/20_dependencias_estado_factura.md) y [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md). Esta documentación preserva la coherencia con el plan descrito en [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).