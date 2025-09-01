---
applyTo: '**'
---
Revisa cuidadosamente el contenido de este documento para asegurarte de que entiendes el proceso de emisión y envío de facturas en contingencia.

# Emisión y envío de Paquetes por Fuera de Linea

Se recurre a la emisión de Facturas fuera de línea (**OFFLINE**), cuando sucede algún evento significativos que impida la emisión de documentos fiscales en línea. En este caso las facturas se emiten individualmente y se agrupan en paquetes de hasta **500 documentos fiscales**, para que luego de superada la contingencia se envíen los mismos a la Administración Tributaria a través de los servicios web correspondientes. El procedimiento a seguir es el siguiente:

### Primera Etapa (Mientras dure la contingencia, proceder a emitir las facturas de manera individual)

* Registar internamente el inicio del evento, junto con el motivo, para posteriormente
* Generar Archivo XML asociado al Documento Fiscal, de acuerdo a su actividad económica (utilizar modalidad fuera de linea).
* Firmar el archivo obtenido conforme estándar XMLDSig (sólo en el caso de la Modalidad Electrónica en Línea).
* Validar contra el XSD asociado a objeto de comprobar que el XML está bien formado y se ajusta a una estructura definida.
* Almacenar temporalmente de manera individual las Facturas generadas.

### Segunda Etapa (una vez superada la contingencia)

* Recuperar las Facturas almacenadas en formato XML durante la etapa anterior.
* Formar paquetes de hasta 500 Facturas.
* Comprimir con Gzip, el archivo resultante debe ser enviado utilizando para ello la etiqueta `archivo`.
* Obtener el **HASH (SHA256)** del archivo compreso obtenido en el paso anterior, mismo que debe ser enviado en la etiqueta `hashArchivo`.

**Envío de Paquetes de Facturas:**

* Consumir el servicio correspondiente para obtener un nuevo CUFD.
* Registrar el evento significativo a través del servicio "Registro de Evento Significativo", indicando la fecha de inicio y fin del evento, así como el CUFD que fue usado para la emisión de facturas de contingencia.
* Enviar los paquetes consumiendo el servicio "Recepción Paquete Facturas Electrónicas". Si la transacción es exitosa, se devolverá el estado **901** (pendiente), el código de recepción del mismo y la transacción en **True**.
* Validar la recepción consumiendo el servicio de "Validación Recepción Paquete Facturas", mismo que devolverá el código de estado que puede ser **901** (pendiente), **904** (observada) o **908** (validado). En el caso de que existan observaciones se incluirá una lista de mensajes con códigos, descripciones, número de archivo y número de detalle de los errores y/o advertencias detectados en cada una de las facturas.

**Nota:** Como buena practica, debe mantenerse un registro de facturas sin código de respuesta, una vez superada la contingencia las mismas se verifiquen consumiendo el servicio **verificaciónEstadoFactura** a objeto de identificar si tienen registro o no en el Servicio de Impuestos Nacionales y proceder a su anulación en caso de ser necesario.

---

## Solicitud del Código Único de Facturación Diaria - CUFD

A continuación se describen los parámetros de entrada y salida relacionados con el CUFD:

| Entrada | Tipo Dato | Obligatorio | Descripción | Salida | Tipo Dato |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Nombre Método** | **solicitudCufd** | | | | |
| | | | | | |
| codigoAmbiente | Numérico | Si | Describe el tipo de ambiente utilizado, los valores permitidos son: Producción: 1, Pruebas y Piloto: 2 | codigoCUFD | Alfanumérico |
| codigoSistema | Alfanumérico | Si | Código de Sistema que le fue asignado al momento de realizar la solicitud de autorización. | fechaVigencia | Fecha UTC Extendida |
| nit | Numérico | Si | NIT perteneciente al emisor de la factura. | transaccion | Boolean |
| codigoModalidad | Numérico | Si | Modalidad utilizada por el Sistema Informático de Facturación para la emisión de facturas, pudiendo ser: Electrónica en Línea: 1, Computarizada en Línea: 2 | codigosRespuestas | DTO[codigosRespuesta] |
| cuis | Alfanumérico | Si | Valor único para una sucursal y/o punto de venta que se obtiene al realizar el inicio de uso de sistemas. | codigoControl | Alfanumérico |
| codigoSucursal | Numérico | Si | Valor que identifica la sucursal donde se realiza la emisión de la Factura: Casa Matriz: 0, Sucursal: 1,2,..,n | direccion | Alfanumérico |
| codigoPuntoVenta | Numérico | No | Solo se envía este valor cuando se desea obtener un CUFD para el punto de venta (1, 2,..,n). Caso contrario enviar 0. | | |

---

## Registro de Evento Significativo
El proceso de registro de evento significativo permite informar al SIN de la contingencia del Sistema Informático de Facturación autorizado. El servicio implementado posee un objeto denominado `SolicitudEventoSignificativo` el cual contiene la información descrita en el siguiente cuadro:

| Entrada | Tipo Dato | Obligatorio | Descripción | Salida | Tipo Dato |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Nombre Método** | **registroEventoSignificativo** | | | | |
| | | | | | |
| codigoAmbiente | Numérico | Si | Describe el tipo de ambiente utilizado, los valores permitidos son: Producción: 1, Pruebas y Piloto: 2 | codigoRecepcion | Alfanumérico |
| codigoSistema | Alfanumérico | Si | Código de Sistema que le fue asignado al momento de realizar la solicitud de autorización. | transaccion | Boolean |
| nit | Numérico | Si | NIT perteneciente al emisor de la Factura. | mensajes | Lista |
| cuis | Alfanumérico | Si | Valor único para una sucursal y/o punto de venta que se obtiene al realizar el inicio de uso de sistemas. | | |
| cufd | Alfanumérico | | Valor diario otorgado por el SIN. | | |
| codigoSucursal | Numérico | No | Valor que identifica a la sucursal donde se realiza la emisión de la Factura: Casa Matriz: 0, Sucursal: 1,2,..,n | | |
| codigoPuntoVenta | Numérico | No | Solo se envía cuando la transacción se realiza utilizando un punto de venta. Caso contrario enviar 0. | | |
| codigoEvento | Numérico | Si | Paramétrica que identifica el tipo de evento. | | |
| descripcion | Alfanumérico | Si | Descripción del evento significativo. | | |
| fechaInicioEvento | String | Si | El formato que debe tener es:"yyyy-MM-dd'T'HH:mm:ss.SSS" | | |
| fechaFinEvento | String | Si | El formato que debe tener es:"yyyy-MM-dd'T'HH:mm:ss.SSS" | | |
| cufdEvento | Alfanumérico | Si | Valor del CUFD que se uso en la contingencia. | | |

---

## Recepción Paquete Facturas Electrónicas
Está compuesta por una serie de Servicios Web habilitados para recibir paquetes de hasta 500 facturas. Dichos servicios reciben el paquete verificando que los parámetros enviados sean válidos, analizan si el paquete recibido es correcto. Si el paquete recibido supera esta etapa, el servicio devuelve el código de recepción. Caso contrario, se devuelve los código de error o advertencia. El servicio implementado posee un objeto denominado `SolicitudServicioRecepcionPaquete` el cual contiene la información descrita en el siguiente cuadro:

| Entrada | Tipo Dato | Obligatorio | Descripción | Salida | Tipo Dato |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Nombre Método: RecepcionPaqueteFactura** | | | | | |
| codigoAmbiente | Numérico | Si | Describe el tipo de ambiente utilizado, los valores permitidos son: Producción: 1, Pruebas y Piloto: 2 | codigoEstado | Numérico |
| codigoPuntoVenta | Numérico | No | Solo se envía cuando la transacción se realiza utilizando un punto de venta. Caso contrario enviar 0. | codigoRecepcion | Alfanumérico |
| codigoSistema | Alfanumérico | Si | Código de Sistema que le fue asignado al momento de realizar la solicitud de autorización. | CodigosRespuestas | DTO[codigosRespuesta] |
| codigoSucursal | Numérico | Si | Valor que identifica a la sucursal donde se realiza la emisión de la Factura: Casa Matriz: 0, Sucursal: 1,2,...,n | transaccion | Boolean |
| nit | Numérico | Si | NIT perteneciente al emisor de la Factura. | codigoDescripcion | Alfanumérico |
| codigoDocumentoSector | Numérico | Si | Código que identifica el sector de la Factura. | | |
| codigoEmision | Numérico | Si | Describe si la emisión se realizó fuera de línea. El valor permitido es: Offline : 2 | | |
| codigoModalidad | Numérico | Si | Electrónica en Línea: 1 | | |
| cufd | Alfanumérico | Si | Valor diario otorgado por el SIN. | | |
| cuis | Alfanumérico | Si | Valor único para una sucursal y/o punto de venta que se obtiene al realizar el inicio de uso de sistemas. | | |
| tipoFacturaDocumento | Numérico | Si | Código que identifica el Tipo de Factura o Documento de Ajuste que se está enviando. | | |
| archivo | Alfanumérico | Si | Paquete de Facturas que son enviadas para su validación. | | |
| fechaEnvio | TimeStamp | Si | Fecha y hora en la cual se envía la Factura. | | |
| hashArchivo | Alfanumérico | Si | Sha256 de la cadena Archivo que se envía. | | |
| cafc | Alfanumérico | No | Código de autorización de emisión de facturas manuales de contingencia. Nulo si son facturas normales | | |
| cantidadFacturas | Numérico | Si | Cantidad de Facturas enviadas en el paquete. | | |
| codigoEvento | Numérico | Si | Código que devolvió el método de registro de evento. | | |

---

## Validación Recepción Paquete Facturas
Está compuesta por una serie de Servicios Web habilitados para verificar el estado de los paquetes de facturas emitidos y enviadas al SIN. Dichos servicios previa validación de los parámetros enviados, verifican el estado en el cual se encuentra los paquetes de facturas. Si todas las facturas pasaron las validaciones y no se encontraron errores se devuelve un código de aceptación, caso contrario se devuelve un codigo de rechazo junto a una lista con el detalle de aquellas Facturas con problemas y los errores o advertencias detectados en cada uno de ellos. El servicio implementado posee un objeto denominado `SolicitudServicioValidacionRecepcionPaquete` el cual contiene la información descrita en el siguiente cuadro:

| Entrada | Tipo Dato | Obligatorio | Descripción | Salida | Tipo Dato |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Nombre Método: validacionRecepcionPaqueteFactura** | | | | | |
| codigoAmbiente | Numérico | Si | Describe el tipo de ambiente utilizado, los valores permitidos son: Producción: 1, Pruebas y Piloto: 2 | codigoEstado | Numérico |
| codigoPuntoVenta | Numérico | No | Solo se envía cuando la transacción se realiza utilizando un punto de venta. Caso contrario enviar 0. | codigoDescripcion | Alfanumérico |
| codigoSistema | Alfanumérico | Si | Código de Sistema que le fue asignado al momento de realizar la solicitud de autorización. | codigoRecepcion | Alfanumérico |
| codigoSucursal | Numérico | Si | Valor que identifica a la sucursal donde se realiza la emisión de la Factura: Casa Matriz: 0, Sucursal: 1,2,..,n | transaccion | Boolean |
| nit | Numérico | Si | NIT perteneciente al emisor de la Factura. | codigosRespuestas | DTO[codigosRespuesta] |
| codigoDocumentoSector | Numérico | Si | Código que identifica el sector de la Factura. | | |
| codigoEmision | Numérico | Si | Describe si la emisión se realizó fuera de línea. El valor permitido es: Offline: 2 | | |
| codigoModalidad | Numérico | Si | Uno (1) Electrónica y dos (2) Computarizada en línea | | |
| cufd | Alfanumérico | Si | Valor diario otorgado por el SIN. | | |
| cuis | Alfanumérico | Si | Valor único para una sucursal y/o punto de venta que se obtiene al realizar el inicio de uso de sistemas. | | |
| tipoFacturaDocumento | Numérico | Si | Código que identifica el Tipo de Factura o Documento de Ajuste que se está enviando. | | |
| codigoRecepcion | Alfanumérico | Si | Código Recepción enviado por el SIN. | | |