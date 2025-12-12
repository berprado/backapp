# Dependencias internas de [facturador/verificador_session_state.py](facturador/verificador_session_state.py)

## Vision general
[facturador/verificador_session_state.py](facturador/verificador_session_state.py) diagnostica y sanea el `session_state` de Streamlit para el flujo de impresion, detectando claves faltantes, tipos incorrectos, procesos fantasma y artefactos residuales.

## Modulos propios utilizados

1. **[facturador/print_manager.py](facturador/print_manager.py)** *(importacion diferida)*  
   - Funciones: reiniciar_estados.  
   - Rol: limpiar el estado de impresion desde la UI de diagnostico cuando el usuario lo solicita.

## Conclusion
El verificador complementa la operacion del worker documentada en [facturador/docs/refactor/09_dependencias_print_manager.md](facturador/docs/refactor/09_dependencias_print_manager.md) y sirve como herramienta de soporte alineada con el plan de UI de [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).
