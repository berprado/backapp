# Dependencias internas de [facturador/pages/3_Puntos_de_Venta.py](facturador/pages/3_Puntos_de_Venta.py)

## Visión general
[facturador/pages/3_Puntos_de_Venta.py](facturador/pages/3_Puntos_de_Venta.py) presenta la pantalla de administración de puntos de venta, coordinando sincronización, consulta y alta/cierre contra el servicio de Operaciones.

## Módulos propios utilizados

1. **[facturador/business_logic.py](facturador/business_logic.py)**  
   - Funciones: verificar_comunicacion.  
   - Rol: valida la disponibilidad del servicio de Operaciones antes de ejecutar cualquier acción en la página.

## Conclusión
[facturador/pages/3_Puntos_de_Venta.py](facturador/pages/3_Puntos_de_Venta.py) se apoya en la lógica central ya descrita en [facturador/docs/refactor/13_dependencias_business_logic.md](facturador/docs/refactor/13_dependencias_business_logic.md) para garantizar que la interfaz cumpla el flujo normativo antes de consumir servicios SOAP. Esta documentación mantiene coherente la hoja de ruta definida en [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).
