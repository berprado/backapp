# Dependencias internas de [facturador/xml_signer.py](facturador/xml_signer.py)

## Vision general
[facturador/xml_signer.py](facturador/xml_signer.py) firma digitalmente XML de facturas: canonicaliza, calcula digest, construye Signature y adjunta certificado y firma RSA-SHA256 antes del envio al SIN.

## Modulos propios utilizados

1. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_xml_logger.  
   - Rol: registrar el flujo de firma, errores y trazas de tamanos de artefactos.

## Conclusion
El firmador se integra con los flujos de generacion/envio de XML documentados en [facturador/docs/refactor/25_dependencias_invoice_xml_generator.md](facturador/docs/refactor/25_dependencias_invoice_xml_generator.md) y utiliza la configuracion de logging descrita en [facturador/docs/refactor/08_dependencias_logger_config.md](facturador/docs/refactor/08_dependencias_logger_config.md).
