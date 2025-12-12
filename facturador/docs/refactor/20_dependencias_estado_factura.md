# Dependencias internas de [facturador/estado_factura.py](facturador/estado_factura.py)

## Visión general
[facturador/estado_factura.py](facturador/estado_factura.py) verifica el estado normativo de las facturas ante el SIAT, implementa un caché híbrido de 30 segundos y sincroniza los resultados en la base de datos.

## Módulos propios utilizados

1. **[facturador/database.py](facturador/database.py)**  
   - Componentes: SessionLocal.  
   - Rol: persistir los cambios de estado y mensajes asociados a las facturas.

2. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: obtener_cuf_por_numero_factura.  
   - Rol: recuperar el CUF y la factura antes de consultar al SIAT.

3. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger, get_facturacion_logger.  
   - Rol: emitir logs diferenciados para diagnósticos y operaciones de facturación.

4. **[facturador/siat_service_client.py](facturador/siat_service_client.py)**  
   - Funciones: get_siat_client.  
   - Rol: construir y enviar solicitudes SOAP reutilizando el cliente centralizado.

## Conclusión
[facturador/estado_factura.py](facturador/estado_factura.py) se integra con la infraestructura documentada en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md) y [facturador/docs/refactor/07_dependencias_communication_manager.md](facturador/docs/refactor/07_dependencias_communication_manager.md). Esta trazabilidad respalda las mejoras de caché descritas en `refactor_cache_*.md`.