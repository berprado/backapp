# Dependencias internas de [facturador/contingency_manager.py](facturador/contingency_manager.py)

## Visión general
[facturador/contingency_manager.py](facturador/contingency_manager.py) detecta fallos de comunicación con el SIAT, administra el modo contingencia y coordina la sincronización posterior de facturas pendientes.

## Módulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Componentes: SessionLocal.  
   - Rol: crear sesiones ORM para consultar y registrar eventos significativos.

2. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Componentes: get_logger.  
   - Rol: emitir trazas con el canal contingency.

3. **[facturador/models.py](facturador/models.py)**  
   - Modelos: FacturaCabecera, Cufd, SincronizarParametricaEventosSignificativos, SincronizarParametricaTipoEmision, EventoSignificativoRegistrado (importación diferida).  
   - Rol: mapear entidades utilizadas al registrar eventos y consultar parámetros normativos.

4. **[facturador/response_handler.py](facturador/response_handler.py)**  
   - Funciones: parse_siat_response.  
   - Rol: interpretar las respuestas SOAP de verificación.

5. **[facturador/significant_events.py](facturador/significant_events.py)**  
   - Funciones: register_significant_event.  
   - Rol: consumar la notificación de eventos al SIAT.

6. **[facturador/utils/log_cleaner.py](facturador/utils/log_cleaner.py)**  
   - Funciones: clean_xml_responses.  
   - Rol: depurar archivos temporales de respuestas SOAP.

7. **[facturador/batch_sender.py](facturador/batch_sender.py)**  
   - Clases: BatchSender (importación diferida).  
   - Rol: reenviar los paquetes de facturas pendientes al recuperar la conectividad.

## Conclusión
[facturador/contingency_manager.py](facturador/contingency_manager.py) integra infraestructura, utilitarios y servicios especializados ya cubiertos por [facturador/docs/refactor/00_diagnostico_main.md](facturador/docs/refactor/00_diagnostico_main.md) y [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md). Documentar estas dependencias permite continuar el refactor de contingencia siguiendo las guías normativas en `contingencia_*.md`.