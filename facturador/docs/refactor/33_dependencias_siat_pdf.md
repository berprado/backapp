# Dependencias internas de [facturador/siat_pdf.py](facturador/siat_pdf.py)

## Vision general
[facturador/siat_pdf.py](facturador/siat_pdf.py) ofrece un helper delgado para convertir HTML en PDF mediante WeasyPrint, registrando el resultado en el logger de impresion.

## Modulos propios utilizados

1. Ningun modulo interno adicional.  
   - Rol: solo usa logging estandar y WeasyPrint; la integracion con el proyecto ocurre via `print_services`.

## Conclusion
Este helper se integra en el flujo de impresion documentado en [facturador/docs/refactor/28_dependencias_print_services.md](facturador/docs/refactor/28_dependencias_print_services.md) y mantiene coherencia con la configuracion de logs de [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md).
