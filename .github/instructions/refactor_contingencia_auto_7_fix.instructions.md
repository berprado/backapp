---
applyTo: '**'
---
Esta tarea es la que unificará todo nuestro trabajo anterior, asegurando que el sistema sea consistente y no tenga comportamientos contradictorios.

---

### **Tarea: Centralizar la Verificación de Conectividad**

**Objetivo:** Modificar el archivo `contingencia_auto.py` para que deje de usar su propia llamada de red y, en su lugar, utilice nuestro nuevo y optimizado `communication_manager`.

**Archivo a modificar:** `contingencia_auto.py`

**Función específica a modificar:** `finalizar_evento_si_conectado()`

---

### **Análisis del Código Actual (El Problema)**

Actualmente, al principio de `contingencia_auto.py`, tienes esto:

```python
# En contingencia_auto.py
from soap_services import verificar_comunicacion, enviar_evento_significativo

def finalizar_evento_si_conectado():
    """
    ...
    """
    # Esta es la llamada directa que vamos a reemplazar
    mensaje, conectado, _ = verificar_comunicacion() 
    if not conectado:
        print("[🛑] Aún no hay conexión con el SIN. No se puede finalizar evento.")
        return False
    # ... el resto de la función
```

Esta llamada a `verificar_comunicacion()` realiza una nueva petición de red, ignorando por completo nuestro `CommunicationManager` con su caché y su lógica de diagnóstico detallado. Esto es lo que vamos a corregir.

---

### **Instrucciones Precisas para la Modificación**

#### **Paso 1: Cambiar la Importación**

Primero, cambiaremos la dependencia. En lugar de importar desde `soap_services`, importaremos nuestro gestor central.

*   **Busca esta línea de importación:**
    ```python
    # ANTES
    from soap_services import verificar_comunicacion, enviar_evento_significativo
    ```

*   **Reemplázala por esta:**
    ```python
    # DESPUÉS
    # Importamos nuestro gestor central y mantenemos la otra función que sí necesitamos
    from communication_manager import communication_manager
    from soap_services import enviar_evento_significativo
    ```

#### **Paso 2: Reemplazar la Lógica de Verificación**

Ahora, usaremos el `communication_manager` para obtener el estado de la conexión. Esto aprovechará el caché y nos dará una respuesta mucho más rápida y consistente.

*   **Busca estas líneas dentro de la función `finalizar_evento_si_conectado`:**
    ```python
    # ANTES
    mensaje, conectado, _ = verificar_comunicacion()
    if not conectado:
        print("[🛑] Aún no hay conexión con el SIN. No se puede finalizar evento.")
        return False
    ```

*   **Reemplázalas por el siguiente bloque de código:**
    ```python
    # DESPUÉS (Lógica centralizada y optimizada)
    # Llamamos a nuestro gestor. La respuesta será casi instantánea si está en caché.
    resultado_completo = communication_manager.verificar_comunicacion_completa()
    
    # Extraemos el estado de conexión del diccionario de resultados.
    # Usamos .get() para evitar errores si la clave no existiera.
    principal = resultado_completo.get("verificacion_principal", {})
    conectado = principal.get("conectado", False)

    if not conectado:
        # El mensaje del logger es más informativo ahora
        logger.info("[🛑] Aún no hay conexión con el SIN según el CommunicationManager. No se puede finalizar evento.")
        return False
    ```
    **Importante:** Para que el `logger` funcione, asegúrate de que `contingencia_auto.py` tenga acceso a una instancia del logger. Si no la tiene, puedes añadir esto al principio del archivo:
    ```python
    from logger_config import get_logger
    logger = get_logger()
    ```
Si ya usas `print()`, puedes mantenerlo, pero usar el logger es una mejor práctica.

### **Resumen de la Tarea**

1.  **Cambia el import:** Deja de importar `verificar_comunicacion` de `soap_services` e importa el `communication_manager`.
2.  **Reemplaza la llamada:** En lugar de `verificar_comunicacion()`, llama a `communication_manager.verificar_comunicacion_completa()` y extrae el estado de conexión del diccionario resultante.
3.  **(Opcional pero recomendado):** Añade un logger para tener mensajes más consistentes.

Con este cambio, toda la aplicación utilizará una única y optimizada fuente de verdad para el estado de la conexión. Habrás eliminado la redundancia y hecho tu sistema más robusto, rápido y fácil de mantener.