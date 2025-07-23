---
applyTo: '**'
---
A continuación, se detalla una descripción resumida del flujo implementado para emitir una factura cuando el sistema esta en linea, debes generar un archivo que se llame README_ONLINE.md en el cual describas detalladamente el flujo actualmente implementado para la emision de facturas en modo online a partir de main.py asegurandote de mencionar los archivos .py que participan en cada uno de los pasos descritos a continuación:

# Flujo de Facturación Electrónica ONLINE
El **Flujo ONLINE** de facturación electrónica es un proceso secuencial y en tiempo real que garantiza la emisión, validación y registro de facturas cuando existe **conectividad con el Servicio de Impuestos Nacionales (SIAT)**.

1.  **Generación de la factura**:
    *   **Preparación de datos**: Se recopilan los datos del cliente (nombre, NIT/CI), se seleccionan las comandas, se calculan subtotales, descuentos y el total a pagar, y se obtiene el método de pago e información adicional.
    *   **Generación del CUF (Código Único de Facturación)**: El sistema obtiene el siguiente número de factura y un CUFD (Código Único de Facturación Diaria) válido del SIAT. Luego, se genera el CUF concatenando estos y otros elementos mediante una función específica.
    *   **Creación del XML**: Se genera un documento XML con la estructura requerida por Impuestos Nacionales, incluyendo la cabecera (información general) y los detalles (productos/servicios), y se incorpora una leyenda aleatoria de la base de datos.

2.  **Firma digital del XML**:
    *   El XML generado se **firma digitalmente** utilizando el certificado del contribuyente. Este proceso implica la canonicalización del XML, el cálculo del hash SHA-256, la firma con la clave privada del contribuyente y la incorporación de los elementos de firma y certificado dentro del propio XML.

3.  **Envío de la factura al servicio SIAT**:
    *   El XML firmado se **comprime en formato Gzip**, se calcula su hash SHA-256 y se codifica en Base64.
    *   Se construye una **solicitud SOAP** que contiene esta información y **se envía al servicio web de Impuestos Nacionales**. El sistema realiza reintentos automáticos en caso de fallos de comunicación.

4.  **Recepción y procesamiento de la respuesta**:
    *   Se recibe y **analiza la respuesta del servicio SIAT** para determinar si la transacción fue exitosa, obtener el código de recepción y cualquier mensaje de error o informativo.
    *   El **estado de la factura se actualiza** según esta respuesta, pudiendo ser VALIDADA, OBSERVADA o RECHAZADA.

5.  **Almacenamiento en base de datos**:
    *   Los datos de la cabecera y detalles de la factura se **guardan localmente** en la base de datos.
    *   Se **incrementa el contador de facturación** y se actualiza el estado de validación de la factura.

6.  **Impresión de la factura**:
    *   Se genera el **HTML de la factura**, se incluye el CUF y se genera el **código QR**.
    *   Un hilo independiente se encarga de guardar una copia del HTML, generar un PDF y **enviar la factura a la impresora térmica**. Este proceso se monitorea para actualizar la interfaz y detectar errores. La impresión está generalmente habilitada tras la validación por parte del SIAT.

7.  **Manejo de errores**:
    *   Durante todo el flujo, se implementan mecanismos de control de errores como el **registro detallado de logs**, el manejo de excepciones, la visualización de mensajes para el usuario y el almacenamiento de información de diagnóstico.

Este proceso garantiza el cumplimiento normativo y un registro completo para futuras auditorías.