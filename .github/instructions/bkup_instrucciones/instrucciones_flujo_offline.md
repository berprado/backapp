Verifica que el siguiente flujo de facturación offline esté correctamente implementado en el código. Asegúrate de que cada paso esté reflejado en las funciones y módulos correspondientes. Identifica y describe las diferencias, inconsistencias y/o errores que puedas identificar en la implementación actual. Si encuentras algún error, proporciona una descripción detallada de cómo debería ser el flujo correcto y qué cambios son necesarios para corregirlo.

# Instrucciones para el Flujo de Facturación Offline

## 🧾 Emisión y Envío de Paquetes por Fuera de Línea

El proceso de facturación **Offline** aplica cuando se presentan eventos significativos que impiden la emisión en línea de documentos fiscales. En estos casos, se debe seguir un procedimiento específico para emitir, almacenar y posteriormente enviar paquetes de facturas al SIN.

---

## 🛠 Primera Etapa – Durante la Contingencia

Mientras dure la contingencia:

1. Registrar internamente el inicio del evento, especificando el motivo.
2. Generar el archivo XML asociado a cada Documento Fiscal en modalidad **fuera de línea**.
3. Firmar el archivo según el estándar **XMLDSig** (sólo en la Modalidad Electrónica en Línea).
4. Validar el XML generado contra su esquema **XSD**.
5. Almacenar temporalmente cada factura de manera individual.

---

## 📦 Segunda Etapa – Post Contingencia

Una vez superada la contingencia:

1. Recuperar las facturas almacenadas en XML.
2. Agruparlas en paquetes de **hasta 500 facturas**.
3. Comprimir los paquetes usando **Gzip** (etiqueta: `archivo`).
4. Calcular el **HASH SHA-256** del archivo comprimido (etiqueta: `hashArchivo`).
5. Realizar el envío al SIN siguiendo este flujo:

   - Obtener un nuevo **CUFD**.
   - Registrar el evento significativo, especificando fecha de inicio y fin, junto con el CUFD usado en la emisión en contingencia.
   - Enviar los paquetes mediante el servicio **Recepción de Paquetes**.
   - Validar el envío usando el servicio **Validación de Paquetes**, que puede retornar los estados:

     - `901`: Pendiente
     - `904`: Observada
     - `908`: Validado

---

## 📌 Nota Final

- Mantener un registro actualizado de todas las facturas generadas que **no cuenten con código de respuesta**.
- Verificar su existencia en el SIN utilizando el servicio `verificacionEstadoFactura`.
- Si una factura no fue registrada, debe ser **anulada** conforme a lo establecido por normativa.

---
