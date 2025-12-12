# Dependencias internas de `facturador/main.py`

## Visión general
`main.py` es el punto de entrada de la aplicación Streamlit. Coordina la verificación de conectividad con el SIN, la gestión de eventos de contingencia y el renderizado de la interfaz principal, delegando responsabilidades en módulos internos especializados.

## Lista de módulos y responsabilidades

1. **`data_access`**  
   - Funciones utilizadas: `obtener_cufd_vigente`, `registrar_evento_local_normativo`, `obtener_evento_activo_actual`, `obtener_evento_por_id`.  
   - Responsabilidad: interacción con la base de datos para obtener y registrar información normativa (CUFD, eventos significativos).

2. **`ui_copy`**  
   - Función utilizada: `render_full_ui`.  
   - Responsabilidad: orquestar la interfaz principal, renderizando pestañas y mostrando el estado del sistema.

3. **`contingencia_auto`**  
   - Función utilizada: `finalizar_evento_si_conectado`.  
   - Responsabilidad: automatizar el cierre de eventos significativos cuando se restablece la conexión con el SIN.

4. **`communication_manager`**  
   - Componentes utilizados: `communication_manager`, `EstadoComunicacion`, `TipoContingencia`.  
   - Responsabilidad: ejecutar diagnósticos de conectividad con caché y proveer la clasificación del estado del sistema.

5. **`logger_config`**  
   - Función utilizada: `get_logger`.  
   - Responsabilidad: obtener el logger central utilizado para registrar eventos en `main.py`.

6. **`print_manager`**  
   - Función utilizada: `start_printer_worker`.  
   - Responsabilidad: arrancar el worker de impresión en segundo plano que procesa trabajos de facturas.

7. **`api_clients`**  
   - Función utilizada: `reset_soap_client`.  
   - Responsabilidad: reiniciar el cliente SOAP cuando el usuario solicita una reconexión.

## Conclusión
Todos los módulos anteriores forman parte del flujo crítico de `main.py`. Mantenerlos bien definidos y documentados facilita comprender cómo se conecta el diagnóstico de red, la contingencia y la UI, y sirve de base para futuras refactorizaciones descritas en `00_diagnostico_main.md` y `01_plan_refactorizacion_ui.md`.
