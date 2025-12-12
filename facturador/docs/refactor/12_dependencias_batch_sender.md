# Dependencias internas de [facturador/batch_sender.py](facturador/batch_sender.py)

## Visión general
[facturador/batch_sender.py](facturador/batch_sender.py) empaqueta facturas de contingencia, envía los lotes al SIAT y coordina la validación posterior para actualizar los estados normativos.

## Módulos propios utilizados

1. **[facturador/database.py](facturador/database.py)**  
   - Componentes: SessionLocal.  
   - Rol: abrir sesiones ORM para consultar facturas en contingencia y persistir cambios.

2. **[facturador/models.py](facturador/models.py)**  
   - Modelos: FacturaCabecera, Cufd.  
   - Rol: mapear registros usados al construir lotes y verificar CUFD.

3. **[facturador/offline_billing.py](facturador/offline_billing.py)**  
   - Funciones: update_invoice_status_after_sending.  
   - Rol: reutilizar la lógica que sincroniza estados tras el envío.

4. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Componentes: get_logger.  
   - Rol: emitir trazas con el canal contingency para auditoría de paquetes.

5. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: obtener_evento_por_id, actualizar_estado_paquete, actualizar_estado_facturas (importaciones diferidas).  
   - Rol: consultar metadatos normativos del evento y consolidar los estados de facturas y eventos.

## Conclusión
[facturador/batch_sender.py](facturador/batch_sender.py) articula infraestructura de base de datos, helpers de contingencia y utilitarios ya contemplados en [facturador/docs/refactor/00_diagnostico_main.md](facturador/docs/refactor/00_diagnostico_main.md) y [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md). Documentar estas dependencias facilita completar el flujo offline conforme a las guías de contingencia.