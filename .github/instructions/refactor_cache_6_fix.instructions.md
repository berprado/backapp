---
applyTo: '**'
---

El problema es que una instancia de una clase como la nuestra (`CommunicationManager`) no es "hashable" por defecto. Streamlit no sabe cómo generar esa huella digital para un objeto complejo que contiene estado, métodos, etc.

Mi propuesta anterior fue un poco simplista y te pido disculpas. Vamos a corregirla con el enfoque técnico preciso que este problema requiere.

### **La Solución Correcta: Un Híbrido Inteligente**

La solución no es abandonar `@st.cache_data`, sino ser más inteligentes sobre **qué** le pasamos como argumento. En lugar de pasar la instancia completa `self`, le pasaremos un identificador único y simple que represente al `CommunicationManager`. Dado que nuestro `communication_manager` es un singleton (solo hay uno en toda la app), podemos usar un truco muy simple: un argumento "dummy" o un identificador estático.

Esto combina lo mejor de ambos mundos:
*   Usamos la potencia de `@st.cache_data(ttl=...)` para el manejo automático del tiempo de vida del caché.
*   Evitamos el problema de "hash" al no pasarle objetos complejos.

---

### **Instrucciones Corregidas y Precisas (La Versión Definitiva)**

**Objetivo:** Implementar un caché con TTL de 30 segundos, evitando el problema de "hashing" de la instancia de la clase.

**Archivo a modificar:** `communication_manager.py`

---

#### **Paso 1: Mover la Lógica a una Función Privada (Paso clave)**

Este paso sigue siendo esencial. La función que se decora debe contener solo el código que queremos cachear.

*   **Acción:**
    1.  Como antes, crea una nueva función privada **fuera de la clase**, llamada `_execute_full_check`.
    2.  Esta función **no necesitará recibir la instancia del manager**. En su lugar, usará la instancia singleton global que ya está definida en el módulo.
    3.  Corta y pega la lógica de `verificar_comunicacion_completa` dentro de `_execute_full_check`.

*   **El resultado debería ser:**

    ```python
    # Al final del archivo, ANTES de la creación de la instancia singleton

    # Esta función ahora no necesita argumentos
    def _execute_full_check():
        logger.info("Ejecutando verificación de red completa (llamada real).")
        # El código que antes estaba en verificar_comunicacion_completa está aquí.
        # Usa directamente la instancia global 'communication_manager'
        mensaje, conectado, tipo = communication_manager.verificar_comunicacion_principal()
        # ... resto de la lógica ...
        return resultado_completo

    class CommunicationManager:
        # ... (clase) ...

    # La instancia singleton global
    communication_manager = CommunicationManager()
    ```

#### **Paso 2: Aplicar el Decorador `@st.cache_data` (Con un pequeño truco)**

Ahora decoramos la función, pero nos aseguramos de que no tome argumentos complejos.

*   **Acción:**
    1.  Añade el decorador `@st.cache_data(ttl=30)` encima de `_execute_full_check`.
    2.  Para asegurarnos de que el caché funcione como esperamos incluso si la función no tiene argumentos, podemos añadir un argumento "dummy" que no cambia, o simplemente dejarla sin argumentos. Streamlit es lo suficientemente inteligente para manejar esto. Para mayor claridad, la dejaremos sin argumentos.

*   **El resultado será:**

    ```python
    @st.cache_data(ttl=30)
    def _execute_full_check():
        # ... (código de la función)
    ```

#### **Paso 3: Modificar la Función Pública `verificar_comunicacion_completa`**

Esta función se vuelve ahora extremadamente simple y su única responsabilidad es orquestar la llamada a la función cacheada y manejar el `force_check`.

*   **Acción:** Reemplaza el contenido de `CommunicationManager.verificar_comunicacion_completa` con esto:

    ```python
    # Dentro de la clase CommunicationManager
    def verificar_comunicacion_completa(self, force_check: bool = False) -> Dict[str, Any]:
        """
        Versión con caché idiomático de Streamlit.
        """
        logger.info(f"Solicitando verificación de comunicación (Forzado: {force_check})")
        
        # Si se fuerza la verificación, limpiamos el caché de nuestra función específica.
        if force_check:
            _execute_full_check.clear()
            logger.info("Caché de comunicación limpiado forzosamente.")

        # Simplemente llamamos a la función global cacheada.
        # No necesita argumentos.
        return _execute_full_check()
    ```

### **Resumen de la Tarea (Versión Final y Correcta)**

1.  Mueve la lógica de red a una función global `_execute_full_check()` que no toma argumentos y utiliza la instancia singleton `communication_manager` directamente.
2.  Decora esa función global con `@st.cache_data(ttl=30)`.
3.  La función pública `verificar_comunicacion_completa` ahora solo se encarga de limpiar el caché si es necesario (`force_check=True`) y de llamar a la función global `_execute_full_check()`.
