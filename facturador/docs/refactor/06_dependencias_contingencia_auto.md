# Dependencias internas de [facturador/contingencia_auto.py](facturador/contingencia_auto.py)

## Visión general
El módulo automatiza el cierre de eventos significativos al restablecer la conectividad con el SIN. Coordina diagnósticos, obtención de CUFD, empaquetado de facturas offline y actualización de registros normativos.

## Módulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: `obtener_evento_activo_actual`, `cerrar_evento_significativo`, `obtener_evento_por_id`.  
   - Rol: consultar y actualizar información de eventos en la base de datos.

2. **[facturador/communication_manager.py](facturador/communication_manager.py)**  
   - Componentes: `communication_manager`.  
   - Rol: verificar el estado de conectividad antes de intentar cerrar eventos.

3. **[facturador/soap_services.py](facturador/soap_services.py)**  
   - Funciones: `enviar_evento_significativo`.  
   - Rol: registrar el cierre del evento frente al SIN.

4. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: `get_logger`.  
   - Rol: registrar trazas normativas y errores durante el proceso.

5. **[facturador/cufd.py](facturador/cufd.py)**  
   - Funciones: `solicitar_cufd`.  
   - Rol: obtener un nuevo CUFD necesario para finalizar eventos.

6. **[facturador/batch_sender.py](facturador/batch_sender.py)**  
   - Clases/funciones: `BatchSender`, `process_and_validate_batch`.  
   - Rol: empaquetar facturas offline y validar su envío post contingencia.

7. **[facturador/data_access.py](facturador/data_access.py)** *(uso adicional)*  
   - Funciones: `obtener_evento_por_id` (validar `codigo_recepcion`).  
   - Rol: asegurar consistencia antes de empaquetar facturas.

## Conclusión
`contingencia_auto.py` depende de la capa de datos, del gestor de comunicación y de servicios SOAP para cumplir la normativa. Esta visión ayuda a coordinar refactors que impactan la contingencia automatizada y el envío de paquetes.
