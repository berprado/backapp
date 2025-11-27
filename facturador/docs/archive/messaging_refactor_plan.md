# Plan de Refactorización de Mensajes para los Tabs

## Estado Actual y Problemas Detectados
- Cada módulo decide de forma independiente cómo renderizar los mensajes, generando diferencias visuales y de mantenimiento.
- `validar_nit_tab.py` delega en `verifica_stream` que usa `st.write`/`st.error`, rompiendo la consistencia con `show_message` y saturando la interfaz con historiales largos.
- No existe un contenedor común para agrupar transacciones, detalles y mensajes múltiples del SIN; los usuarios no distinguen fácilmente resultado vs. trazas.

## Objetivos de la Refactorización
- Unificar la presentación de mensajes (éxito, advertencia, error, info) en todos los tabs utilizando un mismo helper de UI.
- Permitir mostrar listas de mensajes y detalles técnicos sin sacrificar claridad visual.
- Mantener el historial relevante mediante logging, pero mostrar únicamente el resultado más reciente en la UI.
- Evitar duplicación de código y facilitar futuras extensiones (iconos, enlaces, diagnósticos).

## Enfoque Propuesto
1. Ampliar `ui_utils` con una API de renderización de mensajes compuesta.
2. Estandarizar el uso de placeholders (`st.empty()`) para limpiar y reusar el espacio donde se muestran resultados.
3. Ajustar cada módulo para generar estructuras de mensaje homogéneas y delegar la visualización al helper central.
4. Separar la lógica de llamada a servicios de la capa de presentación, especialmente en `verifica_stream`.

## Plan Detallado

### 1. Extender `ui_utils`
- Introducir una estructura ligera (por ejemplo `MessagePayload`) con campos `status`, `title`, `details`, `extra_items`.
- Crear un helper `render_message_block(payload, placeholder=None)` que:
  - Limpie el placeholder si se recibe.
  - Muestre un encabezado con ícono/color según `status` (`success`, `warning`, `error`, `info`).
  - Renderice listas de mensajes (iterando `extra_items`) con `st.markdown` o `st.dataframe` según necesidad.
  - Acepte opcionalmente un diccionario de metadatos para mostrarlos en columnas o acordeones.
- Mantener `show_message` como envoltura simple que delegue internamente al nuevo helper para compatibilidad.

### 2. Normalizar el flujo en los tabs
- En cada `render()` preparar `message_placeholder = st.empty()` antes de los botones de acción.
- Al iniciar una operación, limpiar el placeholder y registrar el intento en el logger correspondiente.
- Construir `MessagePayload` con la respuesta recibida y pasarlo a `render_message_block`.
- Garantizar que cada ruta de error/éxito registra el mismo mensaje que se muestra al usuario.

### 3. Ajustes específicos por módulo
- **`validar_nit_tab.py` / `verifica_stream.py`**
  - Extraer la lógica de comunicación en funciones que devuelvan payloads estructurados en lugar de escribir en la UI.
  - Procesar `mensajesList` y mapearlos a `extra_items` (tabla o lista numerada) con códigos y descripciones.
  - Reemplazar `st.stop()` por mensajes de error gestionados y permitir reintentos.
- **`verificar_factura_tab.py`**
  - Reutilizar el placeholder para agrupar los mensajes de verificación (respuesta SIAT + resultado final) dentro de un único bloque.
  - Añadir sub-secciones opcionales (por ejemplo, detalles técnicos) utilizando las capacidades extendidas del helper.
- **`anular_factura_tab.py`**
  - Consolidar mensajes de éxito/error en un mismo bloque y aprovechar `extra_items` para mostrar información de la factura o motivo seleccionado.
  - Validar datos faltantes con payloads de tipo `warning` para mantener consistencia visual.
- **`revertir_anulacion_tab.py`**
  - Mostrar la cadena completa de acciones (búsqueda de CUF, respuesta SIAT, procesamiento final) como una sola tarjeta con subsecciones.
  - En errores críticos, incluir en `extra_items` el mensaje devuelto por SIAT para evitar usar múltiples llamadas separadas a `show_message`.

### 4. Logging y Telemetría
- Confirmar que cada mensaje mostrado tenga una entrada correspondiente en el logger del módulo con la misma severidad.
- Evitar duplicar logs cuando se produzca la misma información en UI y archivo; centralizar en funciones helper que reciban el logger.

### 5. Pruebas y Validación
- Revisar `scripts/check_logging_imports.py` para asegurar que los módulos no reintroducen `import logging`.
- Ejecutar la aplicación en modo interactivo y validar:
  - Operaciones sucesivas no dejan residuos visuales.
  - Respuestas SIAT largas se muestran de forma legible (usar acordeones/tablas si es necesario).
- Recabar feedback de usuarios internos sobre la nueva presentación antes de cerrar la tarea.

## Entregables Esperados
- Actualización de `ui_utils` con la nueva API y compatibilidad con `show_message`.
- Refactor de los cuatro tabs para utilizar el flujo estandarizado.
- Ajuste de `verifica_stream` (o creación de un adaptador) para devolver estructuras reutilizables.
- Documentación y notas de despliegue que indiquen a otros equipos cómo adoptar el helper en futuros módulos.

## Consideraciones Futuras
- Evaluar la introducción de componentes reutilizables (por ejemplo `render_transaction_summary`) para otros flujos.
- Incluir tipado (dataclasses o `TypedDict`) para los payloads, facilitando validaciones estáticas con mypy.
- Explorar un sistema de traducciones centralizado si se proyecta localizar la aplicación.
