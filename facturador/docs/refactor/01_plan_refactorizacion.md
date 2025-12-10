# Plan de refactorización de `ui_copy.py`

## 1. Contexto
- Archivo objetivo: `facturador/ui_copy.py`.
- Rol dentro del sistema: punto central de la interfaz Streamlit y orquestación de pestañas.
- Objetivo general: reducir ruido, aislar efectos secundarios y mejorar mantenibilidad sin alterar el comportamiento funcional.

## 2. Alcance de esta iteración
1. Eliminar código muerto y dependencias innecesarias.
2. Encapsular las operaciones de inicialización en funciones explícitas.
3. Modularizar la construcción de pestañas y paneles de estado.
4. Normalizar logs, mensajes y tipados.
5. Documentar helpers y definir constantes reutilizables.

## 3. Acciones planificadas

### 3.1 Limpieza de imports y variables
- Retirar los imports `time` y `reset_soap_client` si no se utilizan tras la revisión final.
- Reordenar imports por bloques (estándar, terceros, locales).
- Eliminar la variable `principal` en `render_full_ui` o utilizarla adecuadamente.

### 3.2 Aislamiento de efectos secundarios
- Mover `load_dotenv()` y la creación/verificación del directorio `pdfs` a una función `initialize_environment()`.
- Invocar `initialize_environment()` únicamente desde el entry point (`if __name__ == "__main__":`).

### 3.3 Modularización de la UI
- Crear helpers dedicados para:
  - Construir la configuración de pestañas (`build_tabs_config`).
  - Determinar pestañas disponibles según conectividad (`select_tabs_to_render`).
  - Renderizar el encabezado de estado (`render_status_panel`).
- Reducir la longitud de `render_full_ui` delegando en estos helpers.

### 3.4 Normalización de logs y mensajes
- Centralizar el mapeo de severidades a íconos y estilos en una constante.
- Asegurar que todos los logs usen `ui_logger` con mensajes consistentes.
- Añadir comentarios breves solo cuando la lógica no sea autoexplicativa.

### 3.5 Tipados y documentación
- Anotar firmas con `Dict[str, Any]`, `Callable` o tipos específicos donde aplique.
- Agregar docstrings concisos a `_schedule_auto_refresh`, `_show_status_toast`, `mostrar_boton_diagnostico_rapido` y helpers nuevos.
- Definir constantes para nombres de pestañas recurrentes.

## 4. Resultados esperados
- Código más legible y modular, con responsabilidades bien separadas.
- Menor probabilidad de efectos colaterales al importar el módulo.
- Facilidad para extender o modificar pestañas y paneles en futuras iteraciones.

## 5. Próximos pasos
- Implementar los cambios según las acciones listadas.
- Validar comportamiento manualmente en la aplicación Streamlit.
- Documentar cada iteración adicional dentro de `docs/refactor` siguiendo la convención `NN_descripcion.md`.
