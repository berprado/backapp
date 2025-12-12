# Dependencias internas de [facturador/anulacion.py](facturador/anulacion.py)

## Visión general
[facturador/anulacion.py](facturador/anulacion.py) aplica el protocolo oficial SIAT para anular facturas electrónicas, coordinando clientes SOAP, consultas normativas y sincronización con la base de datos.

## Módulos propios utilizados

1. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Componentes: get_logger.  
   - Rol: inicializar el logger estructurado sin emojis.

2. **[facturador/siat_service_client.py](facturador/siat_service_client.py)**  
   - Componentes: get_siat_client.  
   - Rol: obtener el cliente centralizado para construir y enviar solicitudes SOAP.

3. **[facturador/database.py](facturador/database.py)**  
   - Componentes: SessionLocal.  
   - Rol: crear sesiones ORM para leer y actualizar facturas y parámetros normativos.

4. **[facturador/models.py](facturador/models.py)**  
   - Modelos: SincronizarParametricaMotivoAnulacion, FacturaCabecera.  
   - Rol: mapear tablas utilizadas en las validaciones y actualizaciones de anulación.

5. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: obtener_mensaje_por_codigo, obtener_cuf_por_numero_factura, obtener_cufd_vigente.  
   - Rol: reutilizar consultas normativas y obtención de CUF/CUFD.

6. **[facturador/timeout_handler.py](facturador/timeout_handler.py)**  
   - Funciones: ejecutar_anulacion_con_protocolo.  
   - Rol: encapsular el flujo de repetición y verificación ante timeouts del SIAT.

7. **[facturador/estado_factura.py](facturador/estado_factura.py)**  
   - Funciones: verificar_estado_factura.  
   - Rol: solicitar al SIAT el estado real de la factura cuando se detectan timeouts.

8. **[facturador/utils/estado_utils.py](facturador/utils/estado_utils.py)**  
   - Funciones: aplicar_anulacion (importación diferida).  
   - Rol: normalizar la persistencia del estado Anulada en la base de datos.

## Conclusión
[facturador/anulacion.py](facturador/anulacion.py) depende de módulos de infraestructura, acceso normativo y utilitarios ya cubiertos por el plan descrito en [facturador/docs/refactor/00_diagnostico_main.md](facturador/docs/refactor/00_diagnostico_main.md) y [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md). Mantener estas integraciones coherentes asegura futuras refactorizaciones sin perder trazabilidad normativa.