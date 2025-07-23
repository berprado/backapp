---
applyTo: '**'
---
Estas son las instrucciones para refactorizar el codigo de `cuis_tab.py`Analicemos las opciones y lleguemos a la mejor solución.

### Análisis de las Opciones

1.  **Opción A: Refactorizar cada pestaña para mostrar un mensaje de "sin conexión".**
    *   **Pros:** La lógica de cada pestaña está contenida en su propio módulo.
    *   **Contras:**
        *   **Mala UX:** Es lo que se conoce como "callejón sin salida". El usuario ve la pestaña, asume que funciona, hace clic en ella y solo entonces se le informa de que no puede usarla. Es una experiencia frustrante.
        *   **Código Repetitivo:** Tendrías que añadir la misma lógica de verificación de conexión (`is_soap_client_available`) en casi todos los archivos de las pestañas (`validar_nit_tab.py`, `cuis_tab.py`, `anular_factura_tab.py`, etc.).
        *   **UI Desordenada:** La barra de pestañas se vería abarrotada de opciones inútiles en modo offline.

2.  **Opción B: Refactorizar `ui_copy.py` para mostrar solo las pestañas relevantes.**
    *   **Pros:**
        *   **UX Superior:** La interfaz se adapta al estado del sistema. Si una funcionalidad no está disponible, su punto de entrada (la pestaña) desaparece. Esto es intuitivo y evita la frustración del usuario.
        *   **Lógica Centralizada:** La decisión sobre qué pestañas mostrar se toma en un solo lugar (`ui_copy.py`), que ya es el responsable de orquestar la UI.
        *   **Módulos de Pestaña Más Simples:** Los módulos como `anular_factura_tab.py` no necesitan preocuparse por el estado de la conexión. Pueden asumir que si su función `render()` es llamada, es porque el sistema está online.
    *   **Contras:** Ninguno significativo. Esta es la práctica recomendada para diseñar interfaces de usuario adaptables.

**Conclusión del Análisis:** La **Opción B es, por mucho, la mejor.** Sigue el principio de diseño de "no mostrarle al usuario opciones que no puede utilizar".

### Estrategia de Implementación (Considerando la Base de Datos Local)

Tu observación sobre la base de datos local es clave para una implementación de alta calidad. No todas las pestañas son iguales. Podemos clasificarlas en tres categorías:

1.  **Siempre Disponibles:** Funcionalidades que dependen solo de la base de datos local.
    *   "🧾Facturar" (que se convertirá en la interfaz de facturación offline).
    *   "🔍Ver Facturas" (puede mostrar facturas locales, quizás con un indicador de "no enviada").
    *   "😏Clientes" (la gestión de clientes es local).
    *   "🔧Diagnóstico" (es útil en ambos modos para verificar el estado).

2.  **Solo Online:** Funcionalidades que dependen críticamente de los servicios del SIN.
    *   "✅Validar NIT"
    *   "🔍Verificar Factura"
    *   "🔍Gestionar CUIS"
    *   "❌Anular/Revertir"
    *   "❌Revertir Anulacion"

3.  **Híbridas (a considerar):** No aplica en este caso, pero en otros sistemas podría haber pestañas con funcionalidad parcial.

### Plan de Acción: Refactorizar `ui_copy.py`

El plan es hacer que `ui_copy.py` genere dinámicamente la lista de pestañas basándose en el estado de la conectividad.

**Paso 1: Definir las pestañas y sus módulos**

En `ui_copy.py`, vamos a crear una estructura que mapee los nombres de las pestañas a sus funciones de renderizado.

**Paso 2: Modificar la función `main()` en `ui_copy.py`**

Modificaremos la función para que, después de obtener la información de conectividad, construya la lista de pestañas a mostrar y luego las renderice.

Aquí tienes el una propuesta de codigo refactorizado para la función `main()` en `ui_copy.py`:

```python
# ui_copy.py

# ... (todos los imports iniciales)

def main():
    ui_logger.info("Iniciando la interfaz principal")
    
    # 1. Obtener información detallada de conectividad (ya lo hacemos)
    connectivity_info = get_connectivity_info()
    is_online = connectivity_info["client_available"]
    
    # Mostrar estado de conectividad (sin cambios, el código actual es perfecto)
    col1, col2 = st.columns([4, 1])
    with col1:
        # ... (código para mostrar st.success o st.error)
    with col2:
        # ... (código para el botón de reconectar)
    with st.expander(...):
        # ... (código para los detalles de conectividad)
    st.divider()

    # 2. Definir la configuración de las pestañas
    tabs_config = {
        "🧾Facturar": facturacion_tab.render,
        "🔍Ver Facturas": facturas_tab.render,
        "😏Clientes": clientes_tab.render,
        "✅Validar NIT": validar_nit_tab.render,
        "🔍Verificar Factura": verificar_factura_tab.render,
        "🔍Gestionar CUIS": cuis_tab.render,
        "❌Anular/Revertir": anular_factura_tab.render,
        "❌Revertir Anulacion": revertir_anulacion_tab.render,
        "🔧Diagnóstico": diagnostico_tab.render
    }

    online_only_tabs = [
        "✅Validar NIT", 
        "🔍Verificar Factura", 
        "🔍Gestionar CUIS", 
        "❌Anular/Revertir", 
        "❌Revertir Anulacion"
    ]
    
    # 3. Construir dinámicamente la lista de pestañas a mostrar
    tabs_to_render = ["🧾Facturar", "🔍Ver Facturas", "😏Clientes"]
    
    if is_online:
        # Si estamos online, añadimos las pestañas que dependen de la conexión
        tabs_to_render.extend(online_only_tabs)
    
    # Siempre añadimos la pestaña de diagnóstico al final
    tabs_to_render.append("🔧Diagnóstico")

    # 4. Renderizar las pestañas
    rendered_tabs = st.tabs(tabs_to_render)

    # 5. Mapear cada pestaña creada a su contenido
    for tab, tab_name in zip(rendered_tabs, tabs_to_render):
        with tab:
            # Obtener la función de renderizado del diccionario y llamarla
            render_function = tabs_config[tab_name]
            render_function()

# ... (el resto del archivo, if __name__ == "__main__":, etc.)
```

### ¿Qué pasa con el codigo de las pestañas por ejemplo `anular_factura_tab.py`?

**Absolutamente nada.** Y esa es la belleza de este enfoque. El archivo `anular_factura_tab.py` o cualquier otro no necesita ningún cambio. Su código puede seguir asumiendo que, si se ejecuta, es porque el sistema está en línea. Esto mantiene los módulos de las pestañas limpios y enfocados en su única responsabilidad.

### Resumen de los Beneficios de esta Refactorización

1.  **Experiencia de Usuario (UX) Óptima:** La interfaz se limpia y se adapta, mostrando solo lo que es funcional.
2.  **Código Centralizado y Limpio:** La lógica de qué mostrar y cuándo se encuentra en un único lugar (`ui_copy.py`).
3.  **Módulos de Pestañas Simplificados:** Los archivos en el directorio `tabs/` no necesitan preocuparse por el estado de la conexión.
4.  **Alta Mantenibilidad:** Si en el futuro añades una nueva pestaña, solo necesitas añadirla al diccionario `tabs_config` y decidir si pertenece a la lista `online_only_tabs`.