Verifica que el siguiente flujo de facturación online esté correctamente implementado en el código del repositorio. Asegúrate de que cada paso esté reflejado en las funciones y módulos correspondientes. Identifica y describe las diferencias, inconsistencias y/o errores que puedas identificar en la implementación actual. Si encuentras algún error, proporciona una descripción detallada de cómo debería ser el flujo correcto y qué cambios son necesarios para corregirlo.

# Instrucciones para el Flujo de Facturación Online
## 1. Flujo de Facturación Online

### Descripción del Flujo

1. **Inicialización**

   * Desde `main.py` se llama a `verificar_comunicacion()` definida en `soap_services.py` para comprobar conexión con el SIN.
   * Si hay un evento offline pendiente, se cierra mediante la función `finalizar_evento_si_conectado()` ubicada en `contingencia_auto.py`.

2. **Preparación de Datos**

   * En la interfaz de `ui_copy.py`, se recogen datos del cliente y las comandas seleccionadas.
   * Se definen el método de pago, descuentos adicionales y monto de gift card si corresponde.

3. **Generación de Identificadores**

   * Se obtiene el `CUFD` vigente desde la base de datos a través de `verificar_y_obtener_cufd()`.
   * Se genera el `CUF` utilizando la función `generate_cuf()` en base a los datos del emisor y factura.

4. **Generación del XML**

   * Se utiliza la función `generate_xml_invoice()` definida en `invoice_xml_generator.py` para construir el XML completo.
   * El campo `codigoEmision` se establece con valor `1`, indicando emisión en línea.

5. **Firma Digital**

   * El XML se firma digitalmente usando la función `sign_xml()` implementada en `ui_copy.py`, siguiendo el estándar **XMLDSig**.

6. **Validación XSD**

   * Se valida el XML contra el esquema oficial del SIN mediante `validar_xml()` definida en `zeeper.py`.

7. **Compresión y Hash**

   * Se comprime el XML con `comprimir_xml()` en formato GZIP.
   * Se calcula el hash SHA-256 del archivo comprimido mediante `obtener_hash()`.

8. **Envío al SIN**

   * El XML firmado y comprimido se envía al SIN usando `enviar_solicitud()` hacia el servicio `recepcionFactura`.

9. **Procesamiento de la Respuesta**

   * Se analiza el estado devuelto por el SIN (`908`, `904`, etc.).
   * Si es exitoso, se actualiza la base de datos y se habilita la impresión o generación del PDF.