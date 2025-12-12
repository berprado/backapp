# Dependencias internas de [facturador/print_status.py](facturador/print_status.py)

## Vision general
[facturador/print_status.py](facturador/print_status.py) define enums y payloads tipados para representar estados de impresion en Streamlit, mapeando severidades y mensajes por defecto para el UI.

## Modulos propios utilizados

1. Ningun modulo interno adicional.  
   - Rol: el archivo opera solo con tipado estandar y no requiere otras dependencias del proyecto.

## Conclusion
El tipado de estados sirve de contrato para los flujos de impresion documentados en [facturador/docs/refactor/09_dependencias_print_manager.md](facturador/docs/refactor/09_dependencias_print_manager.md) y los servicios descritos en [facturador/docs/refactor/28_dependencias_print_services.md](facturador/docs/refactor/28_dependencias_print_services.md), manteniendo coherencia con el plan de UI de [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).
