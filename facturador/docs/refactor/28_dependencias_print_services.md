# Dependencias internas de [facturador/print_services.py](facturador/print_services.py)

## Vision general
[facturador/print_services.py](facturador/print_services.py) encapsula la generacion de PDFs de factura y el envio a la impresora termica, elevando errores tipados para coordinar con el flujo de UI.

## Modulos propios utilizados

1. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_printer_logger.  
   - Rol: obtener el logger especializado que registra tiempos y fallas del worker de impresion.

2. **[facturador/invoice_templates.py](facturador/invoice_templates.py)**  
   - Funciones: generate_html_invoice.  
   - Rol: generar el HTML base a convertir en PDF para una `FacturaProcesada`.

3. **[facturador/siat_pdf.py](facturador/siat_pdf.py)**  
   - Funciones: html_to_pdf.  
   - Rol: transformar el HTML en un archivo PDF almacenado en disco.

4. **[facturador/thermal_printer.py](facturador/thermal_printer.py)**  
   - Clases: ThermalPrinter.  
   - Rol: manejar la conexion USB y ejecutar `print_invoice` para el dispositivo termico.

## Conclusion
El servicio de impresion reutiliza las plantillas documentadas en [facturador/docs/refactor/24_dependencias_invoice_templates.md](facturador/docs/refactor/24_dependencias_invoice_templates.md) y los registros de log descritos en [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md), aportando la capa operativa sobre la que se apoya el worker definido en [facturador/docs/refactor/09_dependencias_print_manager.md](facturador/docs/refactor/09_dependencias_print_manager.md).
