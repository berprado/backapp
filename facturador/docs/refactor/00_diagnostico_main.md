# Diagnóstico inicial de `main.py`

## 1. Contexto
- Punto de entrada de la aplicación Streamlit.
- Orquesta la verificación de conectividad, la gestión de contingencias y la renderización de la UI.
- Enlaza con los servicios críticos: comunicación con el SIN, registro de eventos, impresión.

## 2. Hallazgos principales

### 2.1 Inconsistencias funcionales
- **Doble obtención de evento activo:** `evento_activo = obtener_evento_activo_actual()` se invoca antes y después del bloque que detecta contingencia, lo que provoca una segunda consulta innecesaria cuando ya se dispone del dato.
- **Reinvocación del diagnóstico offline:** al entrar en la rama offline se llama a `notificar_reconexion_si_aplica()`, que vuelve a ejecutar `communication_manager.verificar_comunicacion_completa()` sin aprovechar el resultado previo, degradando el beneficio del caché.
- **Constante duplicada:** `NON_OPERATIONAL_EVENT_CODES` también se define en `tabs/facturacion_tab.py`, generando riesgo de divergencia si cambia la paramétrica.

### 2.2 Redundancias y acoplamientos
- **Inicialización de servicios en import:** `start_printer_worker()` corre al cargar el módulo, lo que dificulta pruebas unitarias y reutilización del entry point en otros contextos.
- **Configuración de logging repetitiva:** la sección que reduce verbosidad externa está incrustada en `main.py`; otras partes del proyecto replican ajustes similares. Podría centralizarse en `logger_config`.
- **Uso directo de `st.session_state` disperso:** se manipulan flags (`_force_comm_check`, `evento_cafc`) en varias funciones del archivo. Agrupar la lógica facilitaría pruebas y reducción de errores.

### 2.3 Oportunidades de mejora estructural
- Extraer un helper que empaquete la verificación + render (por ejemplo `render_app_state(resultado_completo, evento_activo)`), simplificando la función `main()`.
- Encapsular la lógica de registro automático de eventos en un módulo dedicado para mejorar la separación de responsabilidades.
- Considerar un wrapper para `communication_manager` que entregue el diagnóstico una sola vez por ciclo de render y lo comparta con quienes lo necesiten (incluida `notificar_reconexion_si_aplica`).

## 3. Recomendaciones inmediatas
1. Reutilizar `evento_activo` calculado al inicio y evitar la consulta repetida.
2. Propagar el diagnóstico obtenido en `main()` hacia `notificar_reconexion_si_aplica()` mediante parámetros o estado compartido.
3. Consolidar `NON_OPERATIONAL_EVENT_CODES` en un único módulo de constantes.
4. Mover la inicialización del worker de impresión a una función `initialize_services()` llamada desde `main()` y protegida por un flag para evitar múltiples arranques.
5. Documentar el flujo de sesión (`st.session_state`) e introducir helpers para lectura/escritura segura de flags.

## 4. Próximos pasos sugeridos
- Ajustar `main.py` conforme a los puntos anteriores y actualizar el plan de refactorización general.
- Registrar los cambios planeados en documentos sucesivos dentro de `docs/refactor` siguiendo el esquema `NN_descripcion.md`.
- Validar manualmente la aplicación tras cada refactor para garantizar que el flujo online/offline se mantiene estable.
