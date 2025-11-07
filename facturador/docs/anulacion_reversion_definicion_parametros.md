# Anulación de Documentos Fiscales

De acuerdo a normativa vigente, la anulación de documentos Fiscales emitidos en la modalidad electrónica en linea se debe realizar de forma individual consumiendo el servicio proporcionado para tal efecto hasta el día nueve (9) del mes siguiente de su emisión.

Se podrá realizar siempre y cuando el documento original este registrado en la Base de Datos de la Administración Tributaria como un documento válido  y no haya sido utilizado en la presentación de alguna Declaración Jurada.

La anulación podrá ser realizada desde la misma sucursal en la cual se origino la transacción o desde otra sucursal habilitada. 

Toda anulación realizada debe ser  notificada al comprador a través del correo electrónico u otros medios electrónicos que garanticen la privacidad del mismo, informándole como mínimo el Código de Autorización, número de factura y  motivo de esta operación.

# Reversión de la Anulación de Documentos Fiscales

De acuerdo a normativa vigente, en caso de darse la anulación errónea de Documentos Fiscales, el Sujeto Pasivo del IVA podrá a través de su Sistema Informático de Facturación, revertir por única vez la anulación y cambiar el estado de un Documento Fiscal a “VALIDO”  hasta el día nueve (9) del mes siguiente de la emisión de la factura original.

Durante la reversión, de no existir observaciones el sistema devolverá el estado 907 (Reversión Anulada Conforme), 981 (factura no disponible para reversión), 924 (Factura no Existe en la Base de Datos), 3011 (Sistema no supero las pruebas de autorización para utilizar la reversión) ó 3012 (Solicitud de Reversión fuera de plazo).

La Reversión de la anulación podrá ser realizada desde la misma sucursal en la cual se origino la transacción o desde otra sucursal habilitada. 

Toda reversión debe ser notificada al comprador a través del correo electrónico u otros medios electrónicos que garanticen la privacidad del mismo informándole de esta operación.

Nota:  Los Documentos Fiscales revertidos no podrán volver a ser anulados.

# Anulación Factura Electrónica (PARAMETROS DEL SERVICIO)

Está compuesta por una serie de Servicios Web habilitados para recibir solicitudes de anulación de facturas individuales emitidas bajo la modalidad Electrónica en Línea, los mismos se hallan publicados de forma diferenciada por tipo de documentos sector.

Para la anulación de una Factura emitida en la modalidad Electrónica en Línea, la mencionada factura deberá estar previamente registrada y validada por la Administración Tributaria.

Dichos servicios previa validación de los parámetros enviados, registran la solicitud devolviendo un código de estado cuando la misma fue correcta o un código de error y advertencia en caso contrario.

El servicio implementado posee un objeto denominado ´SolicitudServicioAnulacionFactura´ el cual contiene la información descrita en el siguiente cuadro:

+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Nombre Método: AnulacionFactura                                                                                                                                                                                |
+------------------------+------------+--------------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |            |              |                                                                                                            |                    |                         |
| *Entrada*              | Tipo Dato  | Obligatorio  | Descripción                                                                                                | *Salida*           | Tipo Dato               |
+------------------------+------------+----+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| codigoAmbiente         | Numérico        | Si      | Describe el tipo de ambiente utilizado, los valores permitidos son:                                        | codigosRespuesta   |                         |
|                        |                 |         |                                                                                                            |                    |                         |
|                        |                 |         |     Producción: 1                                                                                          |                    | DTO [codigosRespuesta]  |
|                        |                 |         |                                                                                                            |                    |                         |
|                        |                 |         |     Pruebas y Piloto: 2                                                                                    |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |  codigoEstado      | Numérico                |
| codigoPuntoVenta       | Numérico        | No      | Solo se envía cuando la transacción se realiza utilizando un punto de venta. Caso contrario enviar 0.      |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| codigoSistema          | Alfanumérico    | Si      | Código de Sistema que le fue asignado al momento de realizar la solicitud de autorización.                 | transaccion        | Boolean                 |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            | codigoDescripcion  | Alfanumérico            |
| codigoSucursal         | Numérico        | Si      | Valor que identifica a la sucursal donde se realiza la emisión de la Factura:                              |                    |                         |
|                        |                 |         |                                                                                                            |                    |                         |
|                        |                 |         | Casa Matriz: 0                                                                                             |                    |                         |
|                        |                 |         |                                                                                                            |                    |                         |
|                        |                 |         | Sucursal:1,2,...,n                                                                                         |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| nit                    | Numérico        | Si      | NIT perteneciente al emisor de la Factura.                                                                 |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| codigoDocumentoSector  | Numérico        | Si      | Código que identifica el sector de la Factura.                                                             |                    |                         |
|                        |                 |         |                                                                                                            |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| codigoEmision          | Numérico        | Si      | Describe si la emisión se realizó en línea. El valor permitido es:                                         |                    |                         |
|                        |                 |         |                                                                                                            |                    |                         |
|                        |                 |         | Online: 1                                                                                                  |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| codigoModalidad        | Numérico        | Si      | Electrónica en línea: 1                                                                                    |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| cufd                   | Alfanumérico    | Si      | Valor diario otorgado por el SIN.                                                                          |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| cuis                   | Alfanumérico    | Si      | Valor único para una sucursal y/o punto de venta que se obtiene al realizar el inicio de uso de sistemas.  |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| tipoFacturaDocumento   | Numérico        | Si      | Código que identifica el Tipo de Factura o Documento de Ajuste que se está enviando.                       |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| codigoMotivo           | Numérico        | Si      | Paramétrica que indica el motivo por el cual la Factura está siendo anulada.                               |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| cuf                    | Alfanumérico    | Si      | Código único de factura que está siendo anulado.                                                           |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+

# Reversión Anulación Factura Electrónica (PARAMETROS DEL SERVICIO)
De acuerdo a RND Nº 102300000034 que indica “Asimismo, en caso de darse la anulación errónea de Documentos Fiscales, el Sujeto Pasivo del IVA a traves de su Sistema Informático de Facturación, podrá revertir por única vez la anulación y cambiar el estado de un Documento Fiscal a “VALIDO”  hasta el día nueve (9) del mes siguiente de la emisión de la factura original. 
Los Documentos Fiscales revertidos no podrán ser anulados”. Este servicio permite revertir el estado de las facturas digitales que fueron anuladas por error y por una sola vez.
El servicio implementado posee un objeto denominado SolicitudServicioReversionAnulacionFactura el cual contiene la información descrita en el siguiente cuadro:

+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Nombre Método: ReversionAnulacionFactura                                                                                                                                                                       |
+------------------------+------------+--------------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |            |              |                                                                                                            |                    |                         |
| *Entrada*              | Tipo Dato  | Obligatorio  | Descripción                                                                                                | *Salida*           | Tipo Dato               |
+------------------------+------------+----+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| codigoAmbiente         | Numérico        | Si      | Describe el tipo de ambiente utilizado, los valores permitidos son:                                        | codigoEstado       |                         |
|                        |                 |         |                                                                                                            |                    |                         |
|                        |                 |         |       Producción: 1                                                                                        |                    | Numérico                |
|                        |                 |         |                                                                                                            |                    |                         |
|                        |                 |         |       Pruebas y Piloto: 2                                                                                  |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |  codigosRespuesta  |  DTO [codigosRespuesta] |
| codigoPuntoVenta       | Numérico        | No      | Solo se envía cuando la transacción se realiza utilizando un punto de venta. Caso contrario enviar 0.      |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| codigoSistema          | Alfanumérico    | Si      | Código de Sistema que le fue asignado al momento de realizar la solicitud de autorización.                 | transaccion        | Boolean                 |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    | Alfanumérico            |
| codigoSucursal         | Numérico        | Si      | Valor que identifica a la sucursal donde se realiza la emisión de la Factura:                              |                    |                         |
|                        |                 |         |                                                                                                            |                    |                         |
|                        |                 |         |         Casa Matriz: 0                                                                                     | codigoDescripcion  |                         |
|                        |                 |         |                                                                                                            |                    |                         |
|                        |                 |         |         Sucursal: 1,2,...,n                                                                                |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| nit                    | Numérico        | Si      | NIT perteneciente al emisor de la Factura.                                                                 |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| codigoDocumentoSector  | Numérico        | Si      | Código que identifica el sector de la Factura.                                                             |                    |                         |
|                        |                 |         |                                                                                                            |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| codigoEmision          | Numérico        | Si      | Describe si la emisión se realizó en línea. El valor permitido es:                                         |                    |                         |
|                        |                 |         |                                                                                                            |                    |                         |
|                        |                 |         |        Online: 1                                                                                           |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| codigoModalidad        | Numérico        | Si      | Electrónica en línea: 1                                                                                    |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| cufd                   | Alfanumérico    | Si      | Valor diario otorgado por el SIN.                                                                          |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| cuis                   | Alfanumérico    | Si      | Valor único para una sucursal y/o punto de venta que se obtiene al realizar el inicio de uso de sistemas.  |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| tipoFacturaDocumento   | Numérico        | Si      | Código que identifica el Tipo de Factura o Documento de Ajuste que se está revirtiendo.                    |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+
|                        |                 |         |                                                                                                            |                    |                         |
| cuf                    | Alfanumérico    | Si      | Código único de factura que está siendo revertida.                                                         |                    |                         |
+------------------------+-----------------+---------+------------------------------------------------------------------------------------------------------------+--------------------+-------------------------+

Nota: Todos los sistemas ya autorizados que deseen utilizar este servicio deberán completar las pruebas para el mismo en ambiente piloto. Superadas las mismas y al presionar el botón de finalizar pruebas serán habilitados automáticamente para usar el servicio en producción.

Los sistemas en las etapas iniciales o en proceso de autorización deberán completar este set de pruebas obligatoriamente.

Los sistemas que se hallen ya en proceso de inspección, deberán terminar el proceso de forma normal y cuando el sistema este en producción solicitar el nuevo servicio via correo a soporte.aplicaciones@impuestos.gob.bo.