---
applyTo: '**'
---

### **Plan de Acción **

**Objetivo:** Implementar un caché con un TTL de 30 segundos en la función que realiza la verificación de red, usando `@st.cache_data`.

**Archivo a modificar:** `communication_manager.py`

---

#### **Instrucciones Precisas**

#### **Paso 1: Separar la Lógica de Verificación **

Esto es fundamental para que el caché funcione correctamente. El decorador de caché debe aplicarse a la función que realiza el trabajo "pesado" (la llamada de red), no a la función principal que podría tener otros argumentos.

*   **Acción:**
    1.  Crea una nueva función **privada y fuera de la clase `CommunicationManager`** (esto es importante para que el caché funcione de manera más simple). La llamaremos `_execute_full_check`.
    2.  **Corta** todo el contenido de la función `CommunicationManager.verificar_comunicacion_completa` y **pégalo** dentro de esta nueva función `_execute_full_check`.
    3.  Esta nueva función necesitará recibir la instancia del `CommunicationManager` para poder llamar a las funciones de verificación internas.

*   **El resultado debería ser algo así:**

    ```python
    # Al principio del archivo, junto a los imports...
    
    # Esta es la nueva función que hará el trabajo pesado.
    # La definimos FUERA de la clase.
    def _execute_full_check(manager_instance):
        # El código que antes estaba en verificar_comunicacion_completa está aquí.
        # ...
        # Llama a las funciones de verificación usando la instancia del manager:
        mensaje, conectado, tipo = manager_instance.verificar_comunicacion_principal()
        # ...
        return resultado_completo

    class CommunicationManager:
        def verificar_comunicacion_completa(self, force_check: bool = False) -> Dict[str, Any]:
            # Esta función ahora solo orquestará la llamada a la función cacheada.
            pass
        
        # ... el resto de la clase
    ```

#### **Paso 2: Aplicar el Decorador `@st.cache_data`**

Ahora, vamos a "decorar" nuestra nueva función de trabajo para que Streamlit gestione el caché automáticamente.

*   **Acción:**
    1.  Asegúrate de tener `import streamlit as st` al principio del archivo.
    2.  Añade el decorador `@st.cache_data(ttl=30)` justo encima de la definición de la función `_execute_full_check`. El `ttl=30` le dice a Streamlit que el resultado de esta función solo es válido por 30 segundos.

*   **El resultado será:**

    ```python
    @st.cache_data(ttl=30)
    def _execute_full_check(manager_instance):
        # ... (código de la función)
    ```

#### **Paso 3: Modificar la Función Pública para Usar el Caché**

Finalmente, la función pública `verificar_comunicacion_completa` se vuelve muy simple. Su trabajo es decidir si debe limpiar el caché (si `force_check=True`) y luego llamar a la función cacheada.

*   **Acción:** Reemplaza el contenido de `CommunicationManager.verificar_comunicacion_completa` con esto:

    ```python
    def verificar_comunicacion_completa(self, force_check: bool = False) -> Dict[str, Any]:
        """
        Versión con caché idiomático de Streamlit.
        """
        logger.info(f"Verificando comunicación (Forzado: {force_check})")
        
        # Si se fuerza la verificación, limpiamos el caché de nuestra función específica.
        if force_check:
            _execute_full_check.clear()
            logger.info("Caché de comunicación limpiado forzosamente.")

        # Llamamos a la función cacheada. 
        # Streamlit decidirá si ejecuta el código o devuelve el resultado del caché.
        # Le pasamos 'self' para que la función externa pueda usar los métodos de esta instancia.
        return _execute_full_check(self)
    ```

### **Resumen de la Tarea**

1.  Mueve la lógica de verificación a una función global privada `_execute_full_check(manager_instance)`.
2.  Decórala con `@st.cache_data(ttl=30)`.
3.  Simplifica la función pública `verificar_comunicacion_completa` para que maneje el `force_check` (limpiando el caché) y llame a la nueva función global.

Este enfoque es más limpio, más moderno y aprovecha al máximo las capacidades de la versión de Streamlit que estamos utilizando que es la 1.47.0