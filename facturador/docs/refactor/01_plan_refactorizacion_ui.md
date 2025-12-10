# Plan de refactorización para la capa UI (`main.py` + `ui_copy.py`)

## 1. Contexto ampliado
- El flujo principal arranca en `main.py`, que diagnostica conectividad, gestiona eventos y delega la UI a `ui_copy.py`.
- `ui_copy.py` orquesta pestañas y servicios de impresión. Ambos forman el núcleo de interacción con el usuario.
- Objetivo general: reducir redundancias, aislar efectos secundarios y mejorar mantenibilidad sin alterar el comportamiento funcional.

## 2. Alcance de la iteración
1. Eliminar código muerto y dependencias innecesarias en ambos archivos.
2. Encapsular inicializaciones con efectos secundarios (`start_printer_worker`, `load_dotenv`, creación de `pdfs/`).
3. Modularizar flujos de UI para que `main.py` y `ui_copy.py` tengan responsabilidades claras.
4. Normalizar logs, constantes y uso de `st.session_state`.
5. Documentar con precisión los helpers y los puntos de extensión.

## 3. Acciones planificadas

### 3.1 Limpieza de imports y constantes
- Quitar `time` en `ui_copy.py` y cualquier otro import sin uso tras la refactorización.
- Consolidar `NON_OPERATIONAL_EVENT_CODES` en un módulo de constantes reutilizable.
- Reordenar imports por grupos (estándar, terceros, locales) en ambos archivos.

### 3.2 Aislamiento de efectos secundarios
- Crear `initialize_environment()` en `ui_copy.py` para `load_dotenv()` y la creación de `pdfs/`.
- Mover `start_printer_worker()` a un helper `initialize_services()` en `main.py`, con flag que evite múltiples arranques.
- Inyectar dependencias (diagnóstico de comunicación, evento activo) mediante parámetros en lugar de recalcular dentro de funciones auxiliares.

### 3.3 Modularización del flujo de UI
- Extraer en `main.py` un helper `render_app_state(diagnostico, evento_activo)` que encapsule la bifurcación online/offline.
- En `ui_copy.py`, crear helpers dedicados para:
  - Construcción de tabs (`build_tabs_config`).
  - Selección dinámica de pestañas (`select_tabs_to_render`).
  - Render del encabezado de estado (`render_status_panel`).
- Reducir la longitud de `render_full_ui`, delegando en estos helpers y usando docstrings claros.

### 3.4 Normalización de logs y session state
- Centralizar el acceso a `st.session_state` con funciones utilitarias (`get_flag`, `set_flag`).
- Alinear los mensajes de log (`ui_logger`, `logger`) con prefijos consistentes y contexto.
- Evitar duplicar diagnósticos: reutilizar el resultado de `communication_manager.verificar_comunicacion_completa()` en todo el ciclo de render.

### 3.5 Documentación y tipados
- Añadir anotaciones (`Dict[str, Any]`, `Callable[..., None]`) donde aplique.
- Documentar `_schedule_auto_refresh`, `_show_status_toast`, `mostrar_boton_diagnostico_rapido`, así como los nuevos helpers.
- Explicar en docstrings el flujo entre `main.py` y `ui_copy.py`, incluyendo la gestión de estado y contingencia.

## 4. Resultados esperados
- Código más modular y testeable; menor acoplamiento entre diagnóstico y UI.
- Eliminación de consultas repetidas a la base de datos y al SIN durante el render.
- Inicializaciones controladas (printer worker, `.env`, directorio `pdfs`) seguras para pruebas y despliegues.
- Logs y flags unificados, facilitando el monitoreo y la depuración.

## 5. Próximos pasos
- Implementar los cambios siguiendo las acciones listadas.
- Validar manualmente los modos online/offline tras cada refactor parcial.
- Registrar ajustes adicionales en nuevos documentos dentro de `docs/refactor` respetando el formato `NN_descripcion.md`.
