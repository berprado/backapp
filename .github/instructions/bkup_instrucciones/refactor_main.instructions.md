---
applyTo: '**'
---
Las mejoras conceptuales de `main_enhanced_demo.py` son excepcionales y deben aplicarse a `main.py`**. Sin embargo, es crucial entender que no se trata de un simple reemplazo de archivo, sino de una **integración selectiva y cuidadosa** de la lógica mejorada, descartando las herramientas de depuración.

A continuación, una comparación detallada y el plan de acción que debes seguir.

---

### Análisis Comparativo

#### `main.py` (El Motor de Producción)
*   **Propósito:** Es el punto de entrada principal y estable de la aplicación.
*   **Diseño:** Lógica lineal y clara. Su flujo es:
    1.  Intentar finalizar eventos de contingencia previos.
    2.  Verificar la comunicación con una única función (`verificar_comunicacion`).
    3.  Si hay conexión, lanza la interfaz online (`online_main`).
    4.  Si no hay conexión, gestiona el inicio de un evento de contingencia (lógica robusta que usa `get_significant_events`, `register_significant_event`, etc.) y muestra una UI offline simple.
*   **Fortaleza:** Es directo, enfocado y su lógica de gestión de eventos de contingencia parece más completa y centralizada que la del demo.

#### `main_enhanced_demo.py` (El Laboratorio de I+D y Caja de Herramientas)
*   **Propósito:** Demostrar el poder del nuevo `communication_manager` y proporcionar herramientas de depuración extremadamente útiles.
*   **Diseño:** Es una "envoltura" (wrapper) que puede operar en diferentes modos.
*   **Fortalezas (Las Mejoras a Integrar):**
    1.  **Uso del `communication_manager`:** Este es el **salto cualitativo más importante**. En lugar de un simple booleano de "conectado/no conectado", obtiene un diagnóstico completo, incluyendo el estado de múltiples servicios, una recomendación y un estado general. Esto hace a la aplicación mucho más inteligente y resiliente.
    2.  **Feedback al Usuario Mejorado:** Proporciona información mucho más rica y útil. El usuario no solo sabe que está offline, sino que puede ver (en el sidebar) *qué* servicios específicos están fallando. La recomendación del tipo de contingencia es una guía excelente.
*   **Código de Demostración/Depuración (A Mantener Separado):**
    *   El selector de modo en el sidebar.
    *   La función `mostrar_comparacion_servicios()`.
    *   La función `debug_impresion_button()` y todas sus funciones auxiliares (`verificar_archivos_impresion`, `mostrar_estado_impresion_detallado`, etc.). Estas herramientas son **oro puro para el desarrollo y la solución de problemas**, pero no deben estar en el `main.py` de producción.

---

### ¿Por qué se deben aplicar las mejoras?

1.  **Resiliencia:** El `communication_manager` permite que la aplicación tome decisiones más inteligentes. Podría funcionar en un modo "limitado" si solo fallan servicios no esenciales, en lugar de declararse completamente offline.
2.  **Transparencia para el Usuario:** El usuario final (y el soporte técnico) obtienen una visión clara de *por qué* el sistema está en contingencia, lo que reduce la frustración y facilita la solución de problemas.
3.  **Mantenibilidad:** Centralizar la lógica de comunicación en el `communication_manager` hace que el código sea más limpio y fácil de mantener a largo plazo.

### Plan de Acción Propuesto: Integración Selectiva

No debes reemplazar `main.py` con `main_enhanced_demo.py`. Debes **mejorar `main.py`** usando los conceptos probados en el demo.

**Pasos:**

1.  **Tomar `main.py` como base:** Su lógica de gestión de eventos de contingencia (`get_significant_events`, `close_significant_event`, etc.) es más robusta y debe ser el punto de partida.

2.  **Reemplazar el chequeo de comunicación:**
    *   **Quitar:** `mensaje, conectado, tipo_deducido = verificar_comunicacion()`
    *   **Añadir:** `from communication_manager import communication_manager`
    *   **Usar:** `resultado_completo = communication_manager.verificar_comunicacion_completa()`

3.  **Adaptar la lógica de decisión:**
    *   Extraer la variable `conectado` del nuevo diccionario de resultados para usarla en el `if/else` principal.
    *   `principal = resultado_completo["verificacion_principal"]`
    *   `conectado = principal["conectado"] if principal else False`

4.  **Integrar el Feedback de UI mejorado en `main.py`:**
    *   Añadir la sección del `st.sidebar` que muestra el estado general (ONLINE/OFFLINE) y la recomendación.
    *   Dentro del bloque `if conectado:`, añadir el `st.expander` que muestra el diagnóstico completo y la métrica de servicios funcionando.

5.  **Mejorar la creación de eventos de contingencia:**
    *   Utiliza la información extra del `communication_manager` (`tipo_contingencia`) para registrar el evento de manera más precisa, en lugar de depender de `tipo_deducido` o usar un valor por defecto.

6.  **Mantener las herramientas de depuración separadas:**
    *   El código de `debug_impresion_button` y sus ayudantes es extremadamente valioso. Debería vivir en su propio archivo, por ejemplo `debug_tools.py` o `debug_app.py`, que puedas ejecutar cuando necesites diagnosticar problemas de impresión, pero que no se cargue en la aplicación principal.

### Conclusión

El archivo `main_enhanced_demo.py` es una **prueba de concepto exitosa**. Ha demostrado sin lugar a dudas que el `communication_manager` es superior al método de verificación original.

**Tu siguiente paso es "promocionar" esa mejora a producción:** refactoriza `main.py` para que utilice el `communication_manager` y la UI de feedback mejorada, mientras mantienes la robusta lógica de gestión de eventos que ya posee. Al mismo tiempo, conserva las herramientas de depuración del demo en un archivo separado para uso exclusivo del desarrollador.

Hacer esto te dará lo mejor de ambos mundos: una aplicación de producción más inteligente y robusta, y una potente suite de herramientas de depuración para facilitar el mantenimiento futuro.