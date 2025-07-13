---
applyTo: '**'
---
Tenemos una inconsistencia muy sutil pero crítica que surgió durante la refactorización. 

Al ejecutar la aplicacion en streamlit tenemos este error

ImportError: cannot import name 'close_significant_event' from 'significant_events' (C:\Users\Bernardo\Desktop\backapp\facturador\significant_events.py)

File "C:\Users\Bernardo\Desktop\backapp\facturador\main.py", line 13, in <module>
    from significant_events import register_significant_event, get_significant_events, close_significant_event

Creo que la clave está en cómo cada archivo maneja los eventos de contingencia. No es un problema en `main.py` en sí mismo, sino en las **dependencias que cada archivo utiliza**.

---

### Análisis de la Causa Raíz

El error es:
`ImportError: cannot import name 'close_significant_event' from 'significant_events'`

Esto nos dice de forma inequívoca: El archivo `main.py` está intentando importar la función `close_significant_event` desde el archivo `significant_events.py`, pero Python no la encuentra allí.

Ahora, comparemos por qué `main.py` falla y `main_enhanced_demo.py` no lo hacía.

#### ¿Cómo maneja los eventos `main_enhanced_demo.py`?

Vamos a revisar el código del demo cuando entra en modo de contingencia:

```python
# main_enhanced_demo.py

# Estos son los imports que usa:
from database import get_eventos_parametricos, get_cufd_vigente, obtener_evento_abierto, insertar_evento_local
# ...
def _verificar_comunicacion_original():
    # ...
    # Y estas son las funciones que llama:
    evento_existente = obtener_evento_abierto() 
    # ...
    insertar_evento_local(...)
```

**Observación clave:** El archivo `main_enhanced_demo.py` **NUNCA importa ni utiliza el módulo `significant_events.py`**. En su lugar, utiliza un conjunto de funciones más antiguas y directas desde `database.py` (`obtener_evento_abierto`, `insertar_evento_local`). Por lo tanto, nunca podría haber fallado por un problema en `significant_events.py`.

#### ¿Cómo maneja los eventos `main.py`?

Ahora veamos el nuevo y mejorado `main.py`:

```python
# main.py

# Este es el import que causa el problema:
from significant_events import register_significant_event, get_significant_events, close_significant_event
# ...
def main():
    # ...
    # Y estas son las funciones que llama:
    eventos_activos = get_significant_events(limit=5, only_open=True)
    # ...
    exito, mensaje = registrar_evento_significativo_automatico(...)
    # ...
    if st.button("🟢 Finalizar contingencia..."):
        # ...
        exito, mensaje = close_significant_event(event_id=evento['id'], end_time=fecha_fin)
```

**Observación clave:** `main.py` ha sido refactorizado correctamente para usar el **nuevo sistema centralizado** en `significant_events.py`. Delega toda la gestión de eventos a este módulo.

---

### El Veredicto: ¿Cuál es el Problema Real?

El problema no está en `main.py`. El problema está en el archivo **`significant_events.py`**.

Tu nuevo `main.py` está correctamente diseñado para usar este módulo centralizado, pero parece que al módulo `significant_events.py` le falta la implementación de la función `close_significant_event`, o quizás tiene un nombre diferente.

El error no apareció con el demo porque el demo, sin saberlo, estaba usando una lógica de contingencia "heredada" y nunca llamó a este nuevo módulo.

### Plan de Acción para la Solución

Necesitamos asegurarnos de que el módulo `significant_events.py` esté completo.

**Paso 1: Revisa tu archivo `significant_events.py`**

Por favor, abre el archivo `C:\Users\Bernardo\Desktop\backapp\facturador\significant_events.py` y verifica lo siguiente:
1.  ¿Existe una función llamada `close_significant_event`?
2.  Si existe, ¿está escrita correctamente o tiene un error de tipeo (ej. `close_event`)?
3.  ¿Está comentada por alguna razón?

**Paso 2: Implementar la función (si falta)**

Estoy casi seguro de que la función falta. Necesitas añadirla. Basado en el contexto de las otras funciones, probablemente debería verse así:

```python
# En significant_events.py

from datetime import datetime
from database import SessionLocal
from facturador.models import EventoSignificativo
from logger_config import get_logger

logger = get_logger()

# ... (aquí van tus funciones existentes register_significant_event y get_significant_events) ...

def close_significant_event(event_id: int, end_time: str) -> tuple[bool, str]:
    """
    Cierra un evento significativo existente actualizando su fecha de finalización.

    Args:
        event_id (int): El ID del evento a cerrar.
        end_time (str): La fecha y hora de finalización en formato ISO.

    Returns:
        tuple[bool, str]: Un booleano de éxito y un mensaje.
    """
    session = SessionLocal()
    try:
        evento = session.query(EventoSignificativo).filter(EventoSignificativo.id == event_id).first()
        
        if not evento:
            logger.error(f"No se encontró el evento con ID {event_id} para cerrar.")
            return False, f"No se encontró el evento con ID {event_id}."
            
        if evento.fecha_fin is not None:
            logger.warning(f"El evento {event_id} ya estaba cerrado.")
            return True, "El evento ya estaba cerrado."

        evento.fecha_fin = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        session.commit()
        
        logger.info(f"Evento significativo con ID {event_id} cerrado exitosamente.")
        return True, "Evento cerrado exitosamente."
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error al cerrar el evento significativo {event_id}: {e}", exc_info=True)
        return False, f"Error de base de datos al cerrar el evento: {str(e)}"
    finally:
        session.close()

```

### Resumen

1.  **El Diagnóstico:** `main.py` usa el nuevo y correcto módulo `significant_events`, pero a este módulo le falta la función `close_significant_event`.
2.  **La Causa de la Confusión:** El antiguo `main_enhanced_demo.py` funcionaba porque usaba una lógica de contingencia diferente y más antigua que no dependía de `significant_events.py`.
3.  **La Solución:** Completa el módulo `significant_events.py` añadiendo la función `close_significant_event` que te he proporcionado.

Una vez que añadas esa función a `significant_events.py`, el `ImportError` desaparecerá y tu comando `streamlit run main.py` debería funcionar correctamente.