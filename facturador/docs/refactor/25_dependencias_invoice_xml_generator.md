# Dependencias internas de [facturador/invoice_xml_generator.py](facturador/invoice_xml_generator.py)

## Vision general
[facturador/invoice_xml_generator.py](facturador/invoice_xml_generator.py) construye el XML de facturacion electronica, valida fechas, aplica valores nillable y retorna la cabecera y detalles preparados para persistencia.

## Modulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: fetch_random_leyenda; guardar_factura_cabecera y guardar_factura_detalle (importacion diferida).  
   - Rol: insertar leyendas normativas en el XML y dejar preparadas las utilidades de persistencia para quien consuma la salida del generador.

2. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_xml_logger.  
   - Rol: emitir trazas y errores durante la validacion de fechas, construccion de nodos y armado de cabecera/detalle.

## Conclusion
El generador de XML reutiliza la infraestructura descrita en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md) y mantiene la trazabilidad de logs definida en [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md), apoyando el flujo normativo detallado en [facturador/docs/refactor/00_diagnostico_main.md](facturador/docs/refactor/00_diagnostico_main.md).
