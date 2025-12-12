# Dependencias internas de [facturador/reversion.py](facturador/reversion.py)

## Vision general
[facturador/reversion.py](facturador/reversion.py) construye solicitudes SOAP para revertir anulaciones, ejecuta el protocolo oficial de timeouts SIAT y sincroniza el estado local de la factura tras la respuesta.

## Modulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Componentes: SessionLocal; funciones obtener_mensaje_por_codigo, obtener_cuf_por_numero_factura, obtener_cufd_vigente.  
   - Rol: recuperar datos normativos y facturas, y traducir codigos SIAT a descripciones locales antes de actualizar la BD.

2. **[facturador/models.py](facturador/models.py)**  
   - Modelos: FacturaCabecera.  
   - Rol: mapear la factura que se actualiza tras la reversión y para detectar tipo de emisión.

3. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: centralizar el logging con prefijos [REVERSION] en todo el flujo.

4. **[facturador/timeout_handler.py](facturador/timeout_handler.py)**  
   - Funciones: ejecutar_reversion_con_protocolo.  
   - Rol: aplicar el protocolo de reintentos y verificación posterior cuando hay timeouts.

5. **[facturador/estado_factura.py](facturador/estado_factura.py)**  
   - Funciones: verificar_estado_factura.  
   - Rol: consultar el estado real de la factura en SIAT como parte del protocolo de timeout.

6. **[facturador/utils/estado_utils.py](facturador/utils/estado_utils.py)** *(importacion diferida)*  
   - Funciones: aplicar_reversion.  
   - Rol: normalizar la actualización del estado de negocio y campos de anulacion al confirmar una reversión.

## Conclusion
El proceso de reversión combina la capa de datos descrita en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md) con la gestión de estado registrada en [facturador/docs/refactor/20_dependencias_estado_factura.md](facturador/docs/refactor/20_dependencias_estado_factura.md) y mantiene trazabilidad de logs según [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md).
