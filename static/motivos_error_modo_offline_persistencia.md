# Análisis del Problema de Persistencia de Widgets en Modo Offline

Después de analizar el código en el commit previo, puedo identificar las causas específicas que generan el problema de persistencia de widgets en modo offline:

## Causas Principales

### 1. Manejo Diferenciado de Modos en main.py vs ui_copy.py

El problema base radica en cómo se maneja la transición entre modo online y offline:

- En main.py: Se detecta el modo adecuado (online/offline) y se llama a la función `ui_main()` de `ui_copy.py` con el parámetro `tipo_emision=2` para modo offline.
- En `ui_copy.py`: Se reciben estos parámetros pero no se preservan adecuadamente entre re-ejecuciones.

El sistema depende de que estos parámetros se mantengan durante toda la sesión, pero cuando Streamlit re-ejecuta el script (debido a un botón o interacción), estos parámetros se pierden si no están almacenados en `st.session_state`.

### 2. Falta de Persistencia en session_state para Contexto de Ejecución

Aunque en main.py existe:
```python
st.session_state['modo_offline'] = True
st.session_state['evento_activo'] = evento_activo
```

En `ui_copy.py`, no se recuperan correctamente estos valores para mantener el contexto entre re-ejecuciones:
```python
def main(tipo_emision=1, evento_contingencia=None):
    # Aquí se deberían guardar estos valores en session_state
    # Pero no se hace, por lo que al re-ejecutar se pierden
```

### 3. Importación Local dentro de offline_main() 

En main.py, la función `offline_main()` importa localmente la función `main` de `ui_copy`:
```python
from ui_copy import main as ui_main
ui_main(tipo_emision=2, evento_contingencia=evento)
```

Esta técnica evita importaciones circulares, pero no retiene el estado entre re-ejecuciones.

### 4. Falta de Estado Persistente para los Widgets del Sidebar

Cada widget creado en el sidebar de `ui_copy.py` no está enlazado con `st.session_state`, por lo que al re-ejecutarse el script, pierden sus valores:

```python
numero_documento = st.sidebar.text_input("Número de Documento:", key="numero_documento")
```

No hay un mecanismo para guardar/recuperar este valor desde `st.session_state` cuando ocurre una re-ejecución.

### 5. El Modo Offline No Mantiene su Estado de Forma Consistente

Aunque hay variables como `st.session_state['excepcion_nit'] = True` que se establecen en modo offline, no hay un mecanismo completo para mantener el estado de todos los widgets y del modo de operación.

### 6. Función reiniciar_estados() Incompleta

La función `reiniciar_estados()` existente en `ui_copy.py` no preserva adecuadamente los estados relacionados con el modo:

```python
def reiniciar_estados():
    keys_to_reset = ['factura_validada', 'print_status', ...]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]
    # Debería preservar modo_offline, tipo_emision, etc.
```

## Impacto en el Funcionamiento

Cuando el usuario está en modo offline:

1. En la primera carga, los widgets aparecen correctamente porque reciben los parámetros iniciales (`tipo_emision=2, evento_contingencia=evento`).
2. Al interactuar con cualquier elemento que cause una re-ejecución, estos parámetros se pierden.
3. Como resultado, `ui_copy.py` regresa a su comportamiento por defecto (`tipo_emision=1`), lo que provoca que los widgets desaparezcan o se muestren incorrectamente.

## Relación con el Modo Online

El modo online funciona mejor porque:
- Al estar conectado, muchos valores se cargan directamente desde la base de datos o API
- Hay validaciones en tiempo real que mantienen la coherencia de datos
- El flujo es más directo y no depende tanto del estado mantenido entre re-ejecuciones

## Solución Conceptual

Para corregir este problema, necesitamos:

1. **Persistir estado de modo**: Guardar `tipo_emision` y `evento_contingencia` en `st.session_state` al inicio de `ui_copy.main()`.
2. **Persistir valores de widgets**: Inicializar y mantener los valores de cada widget en `session_state`.
3. **Rehidratación coherente**: Usar esos valores persistidos como defaults al recrear los widgets.
4. **Reinicio selectivo**: Modificar `reiniciar_estados()` para preservar el modo mientras limpia datos específicos.

Estas modificaciones asegurarían que el sistema mantenga un comportamiento consistente tanto en modo online como offline, incluso después de múltiples re-ejecuciones del script.