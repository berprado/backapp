# Dependencias internas de [facturador/main.py](facturador/main.py)

## Visión general
El archivo es el punto de entrada de la aplicación Streamlit. Coordina diagnóstico de conectividad, gestión de contingencias y render de la UI delegando responsabilidades en módulos especializados.

## Módulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: `obtener_cufd_vigente`, `registrar_evento_local_normativo`, `obtener_evento_activo_actual`, `obtener_evento_por_id`.  
   - Rol: consultar y registrar información normativa (CUFD y eventos significativos).

2. **[facturador/ui_copy.py](facturador/ui_copy.py)**  
   - Funciones: `render_full_ui`.  
   - Rol: orquestar la interfaz principal y sus pestañas.

3. **[facturador/contingencia_auto.py](facturador/contingencia_auto.py)**  
   - Funciones: `finalizar_evento_si_conectado`.  
   - Rol: automatizar el cierre de eventos significativos tras la reconexión.

4. **[facturador/communication_manager.py](facturador/communication_manager.py)**  
   - Componentes: `communication_manager`, `EstadoComunicacion`, `TipoContingencia`.  
   - Rol: ejecutar diagnósticos cacheados y clasificar el estado del sistema.

5. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: `get_logger`.  
   - Rol: obtener el logger central para registrar eventos de `main.py`.

6. **[facturador/print_manager.py](facturador/print_manager.py)**  
   - Funciones: `start_printer_worker`.  
   - Rol: iniciar el worker de impresión en segundo plano.

7. **[facturador/api_clients.py](facturador/api_clients.py)**  
   - Funciones: `reset_soap_client`.  
   - Rol: reiniciar el cliente SOAP cuando el usuario fuerza reconexión.

## Conclusión
Estas dependencias forman el flujo crítico de `main.py` y sustentan el refactor documentado en [00_diagnostico_main.md](facturador/docs/refactor/00_diagnostico_main.md) y [01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).
