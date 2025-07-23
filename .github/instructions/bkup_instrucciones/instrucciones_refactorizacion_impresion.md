
# Sugerencias y Recomendaciones para Centralizar la Impresión y Mantener Feedback en la UI

---

## 1. Diagnóstico inmediato

- **El síntoma**: Tras la refactorización, el flujo "desaparece": NO se genera HTML, PDF, ni se imprime la factura.
- **Causa probable**: Al mover el control y monitoreo fuera de la UI, algo dejó de actualizar el estado de impresión en la interfaz o no lanza el procedimiento correctamente. Además, es posible que los errores se estén registrando en logs pero **NO se muestran en la UI** (por lo tanto, el usuario no sabe qué está pasando).

---

## 2. ¿Qué hacía bien el código anterior?

- **La UI monitoreaba directamente** el hilo de impresión y respondía en vivo a los cambios de estado (usando archivos `.signal`, `.error`).
- **Actualizaba el estado y mensajes en tiempo real** usando placeholders de Streamlit.
- Si ocurría un error, lo mostraba **de inmediato** en la interfaz, no solo en el log.

---

## 3. ¿Qué debes mantener tras refactorizar?

- **La UI debe seguir siendo responsable de mostrar el estado de impresión en tiempo real** (esperando, éxito, error).
- **La lógica de backend puede estar centralizada,** pero debe exponer claramente el estado/resultados a la UI para que los muestre.
- Si ocurre un error, **la UI debe mostrarlo** al usuario final, NO solo escribirlo en archivos de log.

---

## 4. Recomendaciones prácticas y pasos para corregir el flujo

### A. Mantén el monitoreo en la UI

- Puedes tener el procedimiento de impresión centralizado, **pero la UI debe monitorear el estado**, por ejemplo, llamando regularmente a una función de consulta o revisando señales.

### B. Agrega un mecanismo claro para comunicar errores

- Cuando se capture un error en el backend, asegúrate de **actualizar una variable** (ej: `st.session_state['print_status']`) y/o crear un archivo de señalización de error **que la UI pueda leer** y mostrar en pantalla.
- Opcional: retorna el error directamente en la función llamada desde la UI.

### C. Usa logs SOLO como respaldo, no como único mecanismo

- Nunca dependas de logs en archivo para comunicar estado a la UI.
- Todos los errores críticos deben reflejarse en la interfaz, para feedback inmediato.

### D. Centraliza el procedimiento, pero expón el estado

- Deja la impresión, generación de HTML y PDF en `print_manager.py`.
- Pero provee funciones tipo:
    - `get_print_status(numero_factura)`
    - `get_last_print_error(numero_factura)`
  para que la UI pueda actualizar los mensajes y feedback al usuario.

---

## 5. Ejemplo de patrón ideal tras refactorización

**En la UI:**
```python
if st.button("Imprimir Factura"):
    thread = imprimir_en_hilo(html_content, cuf, nit, numero_factura)
    monitorear_hilo_impresion(numero_factura)
````

**En print\_manager.py:**

```python
def imprimir_en_hilo(html_content, cuf, nit, numero_factura):
    # ... lógica centralizada ...
    # Escribir archivos de señalización o actualizar session_state según corresponda
    ...
```

* Así, la UI monitorea el estado, pero toda la lógica está centralizada.

---

## 6. ¿Qué NO hacer?

* **No ocultar errores** solo en logs.
* **No depender únicamente de session\_state** si hay riesgo de que varios hilos/procesos actualicen la misma variable.
* **No hacer polling directo sobre archivos de log** en vez de archivos de señalización o session\_state.

---

## 7. Checklist para migrar y testear

* [ ] **Asegúrate de que todas las rutas y permisos existen** (`debug/` debe existir y ser escribible).
* [ ] **Actualiza la UI para no depender de la lógica interna**, solo de los archivos de señalización o session\_state.
* [ ] **Elimina cualquier monitoreo de hilos duplicado** en la UI o backend.
* [ ] **Opcional:** agrega limpieza automática de archivos de señalización viejos.


