# Dependencias internas de [facturador/facturacion_sidebar.py](facturador/facturacion_sidebar.py)

## Visión general
[facturador/facturacion_sidebar.py](facturador/facturacion_sidebar.py) renderiza la barra lateral de facturación en Streamlit, permitiendo gestionar datos de clientes, comandas y métodos de pago tanto en modo online como offline.

## Módulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: fetch_comandas, fetch_metodos_pago, fetch_tipos_documento, fetch_cliente.  
   - Rol: obtener la información base mostrada en la interfaz.

2. **[facturador/client_manager.py](facturador/client_manager.py)**  
   - Funciones: save_or_fetch_client_data, verificar_nit_cliente.  
   - Rol: centralizar la persistencia y validación de clientes.

3. **[facturador/ui_utils.py](facturador/ui_utils.py)**  
   - Funciones: init_session_state, show_message.  
   - Rol: inicializar estados y mostrar mensajes contextualizados en la UI.

4. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: registrar eventos y errores de la interacción lateral.

5. **[facturador/shared_utils.py](facturador/shared_utils.py)**  
   - Constantes: GIFT_CARD_CODES.  
   - Rol: reutilizar la lista de códigos de métodos de pago asociados a gift cards.

## Conclusión
[facturador/facturacion_sidebar.py](facturador/facturacion_sidebar.py) depende de la capa de datos y utilitarios descritos en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md) y [facturador/docs/refactor/14_dependencias_client_manager.md](facturador/docs/refactor/14_dependencias_client_manager.md). Mantener este mapa facilita avanzar con las tareas de UI definidas en [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).