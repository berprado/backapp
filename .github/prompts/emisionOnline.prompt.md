## Emisión y Envío Individual de Facturas Electrónicas
- Analiza y verifica si el codigo que tenemos implementado cumple con todos estos pasos al momento de emitir facturas: 

1. Generar el archivo XML del Documento Fiscal.
2. Firmar el XML conforme a XMLDSig (solo en modalidad Electrónica en Línea).
3. Validar contra el XSD correspondiente.
4. Comprimir en Gzip (etiqueta `archivo`).
5. Generar HASH SHA256 (etiqueta `hashArchivo`, Huella Digital).
6. Enviar individualmente usando el servicio **Recepción de Factura**:
   - Código de estado `908`: Validado.
   - Código de estado `904`: Observado (se adjunta lista de errores o advertencias).
   - Transacción devuelta como `True` o `False`.