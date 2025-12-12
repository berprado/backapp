# Dependencias internas de [facturador/business_logic.py](facturador/business_logic.py)

## Visión general
[facturador/business_logic.py](facturador/business_logic.py) concentra utilidades de cálculo comercial, generación de enlaces y diagnósticos básicos de comunicación para la facturación electrónica.

## Módulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: obtener_nombre_unidad_medida.  
   - Rol: resolver descripciones de unidades de medida para las líneas de productos.

## Conclusión
[facturador/business_logic.py](facturador/business_logic.py) mantiene una dependencia directa con la capa de acceso a datos descrita en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md). Esta relación mínima facilita aislar la lógica de negocio dentro del plan definido en [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).