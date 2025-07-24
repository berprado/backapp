---
applyTo: '**'
---
Aquí tienes las instrucciones precisas para implementar el sistema de caché en nuestro gestor de comunicación.

---

### **Tarea 2.1: Implementar Caché en `communication_manager.py`**

**Objetivo:** Modificar la función `verificar_comunicacion_completa` para que guarde sus resultados en `st.session_state` por un breve período (usaremos 30 segundos). Esto evitará que se ejecuten llamadas de red en cada interacción del usuario, haciendo la aplicación mucho más rápida.

**Archivo a modificar:** `communication_manager.py`

---

#### **Paso 1: Añadir las importaciones necesarias**

Al principio del archivo `communication_manager.py`, asegúrate de que `datetime` y `timedelta` estén disponibles desde el módulo `datetime`.

*   **Busca la línea:**
    ```python
    from datetime import datetime, timedelta
    ```
*   **Acción:** Si ya existe, perfecto. Si no, añádela junto a las otras importaciones.

---

#### **Paso 2: Separar la Lógica de Verificación**

Para mantener el código limpio, vamos a mover la lógica actual de `verificar_comunicacion_completa` a una nueva función privada llamada `_ejecutar_verificacion_real`.

*   **Acción:**
    1.  Crea una nueva función dentro de la clase `CommunicationManager` con el siguiente nombre:
        ```python
        def _ejecutar_verificacion_real(self) -> Dict[str, Any]:
            # El código irá aquí
        ```
    2.  **Corta** todo el contenido actual de la función `verificar_comunicacion_completa` y **pégalo** dentro de esta nueva función `_ejecutar_verificacion_real`.
    3.  El `return resultado_completo` debe quedar al final de esta nueva función.

*   **Al final de este paso, tu código debería verse así:**

    ```python
    class CommunicationManager:
        # ... (otras funciones) ...

        def verificar_comunicacion_completa(self) -> Dict[str, Any]:
            # ESTA FUNCIÓN AHORA ESTÁ VACÍA
            pass

        def _ejecutar_verificacion_real(self) -> Dict[str, Any]:
            # Y TODO EL CÓDIGO ORIGINAL ESTÁ AHORA AQUÍ
            resultado_completo = {
                "timestamp": datetime.now().isoformat(),
                # ... etc ...
            }
            
            # 1. Verificación principal...
            # 2. Verificaciones por servicio...
            # 3. Análisis general...

            return resultado_completo
    ```

---

#### **Paso 3: Implementar la Lógica de Caché en la Función Principal**

Ahora, vamos a añadir la nueva lógica inteligente a la función `verificar_comunicacion_completa`, que ahora está vacía.

*   **Acción:** Reemplaza la función `verificar_comunicacion_completa` vacía con el siguiente código. Lee los comentarios para entender cada parte.

    ```python
    # DESPUÉS (Código completo para la nueva función)

    def verificar_comunicacion_completa(self, force_check: bool = False) -> Dict[str, Any]:
        """
        NUEVA versión con caché en st.session_state para mejorar el rendimiento.
        
        Args:
            force_check (bool): Si True, ignora el caché y ejecuta una nueva verificación.
                                Útil para botones de "Reconectar".
        """
        logger.info(f"Verificando comunicación (Forzado: {force_check})")
        now = datetime.now()
        
        # 1. Inicializar el caché en st.session_state si no existe
        if 'comm_manager_cache' not in st.session_state:
            st.session_state.comm_manager_cache = {
                'timestamp': None,
                'result': None
            }

        cache = st.session_state.comm_manager_cache
        
        # 2. Revisar si el caché es válido y reciente (menos de 30 segundos)
        if not force_check and cache['timestamp'] and (now - cache['timestamp']).total_seconds() < 30:
            logger.info("Devolviendo resultado de comunicación desde CACHÉ.")
            return cache['result']

        # 3. Si el caché expiró o se forzó el chequeo, ejecutar la verificación real
        logger.info("Caché expirado o chequeo forzado. Ejecutando verificación de red completa.")
        resultado_completo = self._ejecutar_verificacion_real()
        
        # 4. Actualizar el caché con el nuevo resultado y el timestamp actual
        cache['timestamp'] = now
        cache['result'] = resultado_completo
        
        logger.info("Caché de comunicación actualizado.")
        
        return resultado_completo
    ```

---

### **Resumen de la Tarea**

1.  Asegúrate de tener `from datetime import datetime, timedelta`.
2.  Mueve el código de `verificar_comunicacion_completa` a una nueva función `_ejecutar_verificacion_real`.
3.  Reemplaza el contenido de `verificar_comunicacion_completa` con la nueva lógica de caché que te he proporcionado.

Este cambio es interno al `CommunicationManager`. No debería romper nada en el resto de la aplicación, ya que `main.py` seguirá llamando a `verificar_comunicacion_completa` y recibirá la misma estructura de datos que antes. La única diferencia es que ahora la respuesta será casi instantánea la mayor parte del tiempo.

¡Adelante! Estoy seguro de que lo harás genial.