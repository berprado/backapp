## Emisión y Envío Individual de Facturas Electrónicas
- Analiza y verifica si el codigo que tenemos implementado para la emision de facturas en modo online cumple con todos estos pasos al momento de emitir facturas: 


1. Se genera el archivo XML del Documento Fiscal.
2. Se firma el archivo obtenido conforme estándar XMLDSig.
3. Se valida contra el XSD a objeto de comprobar que el XML está bien formado y se ajusta a una estructura definida.
4. Se comprime el archivo XML en formato Gzip, mismo que debe ser enviado en la etiqueta `archivo`.
5. Se obtiene el HASH (SHA 256) del archivo compreso obtenido en el paso anterior, mismo que debe ser enviado en la etiqueta `hashArchivo`.
6. Se envia individualmente usando el servicio **Recepción de Factura** Si el envio no tuviera observaciones, se devuelve una respuesta con el estado 908 (validado), en caso contrario se devuelve el estado 904 (observado), junto con el código de recepción del mismo, la lista de errores o advertencias (en caso de obtener 904), y la transacción con valor True o False cuando corresponda.