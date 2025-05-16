
# CARACTERISTICAS DEL SISTEMA #

El Sistema Informáticos de Facturación, para interactuar con los servicios de la Administración Tributaria de Bolivia, deberá contar como mínimo con los siguientes componentes o funcionalidades:


# a)      Emisor de Facturas Digitales:

Permite generar Facturas Digitales en formato XML.

Este componente debe poseer por lo menos la emisión individual de facturas y la emision por contingencia, en función al rubro del negocio puede tener la capacidad de emitir facturas de forma masiva:

** Emisión Individual **

Este componente debe emitir la Factura Digital en base a la siguiente secuencia de pasos:

* 1)     Generar Archivo XML asociado a la Factura de acuerdo a su actividad económica. 

* 2)     Firmar el archivo obtenido conforme estándar XMLDSig.

* 3)     Validar contra el XSD asociado.

* 4)     Comprimir el archivo XML en formato Gzip, mismo que debe ser enviado en la etiqueta archivo de la solicitud.

* 5)     Obtener el HASH (SHA256) del archivo compreso obtenido en el paso anterior, mismo que debe ser enviado en la etiqueta hashArchivo.

 

** Emisión de Paquetes por Contingencia **

Cuando el Sistema Informático de Facturación tenga un evento de contingencia que obligue a la emisión de facturas fuera de línea (offline), almacenará las mismas en paquetes de máximo 500 Facturas. Posterior a la recuperación del evento de contingencia, el Sistema Informático deberá registrar el mismo a través del Servicio Web habilitado para el efecto y proceder al envío de los paquetes consumiendo para ello los servicios correspondientes.


** Emisión de Paquetes por emisión Masiva **

La emisión masiva es utilizada por empresas que, por su giro de negocio, realizan procesos automatizados de emisión de Facturas Digitales en horarios extraordinarios, como entidades financieras, servicios de telecomunicaciones, luz, agua y otros. Por lo que el Sistema Informático de Facturación autorizado deberá generar paquetes de hasta 1000 Facturas y proceder al envío de los mismos a través de los servicios correspondientes.

# b)     Gestor de  Facturas Digitales:

Su función principal es enviar y validar transacciones de registro como la anulación de las Facturas. En el apartado correspondiente a la implementación de Servicios de Facturación se muestra en detalle la implementación de los mismos, y el apartado de Archivos XML/XSD de Facturas contiene una descripción detallada de cada tipo de documento sector a ser gestionado.

# c)    Sincronización de catálogos:

Funcionalidad que permite la descarga y actualización de los diferentes catálogos del Sistema de Facturación, códigos de productos y servicios, países, códigos de eventos significativos, códigos de mensajes de servicios y otros. La sincronización de catálogos se realizará de forma diaria. Para obtener mayor información, diríjase al siguiente enlace: implementación de Servicios de Facturación - Sincronización.

# d)      Sincronización de fecha y hora: (Debe obligatoriamente efectuarse a Diario)

Permite la sincronización de la fecha y hora de los Sistemas Informáticos de Facturación (Contribuyente) con la fecha y hora de la Administración Tributaria. Esta sincronización será utilizada para realizar los controles de plazos de envíos y registros en las diferentes casuísticas de emisión de Facturas Digitales. La sincronización puede ser realizada varias veces al día, recomendándose se la efectúe antes de la obtención del Código Único de Facturación Diaria - CUFD, a través del servicio web correspondiente.

 
# e)     Registro de eventos significativos:

Funcionalidad que permite el registro de eventos significativos que se hubieren producido y que se detallan en la sección Contingencia.


# f)     Gestor de envío de documentos digitales e impresión:

Su función principal es gestionar la impresión, envío o publicación de la representación gráfica y el XML de la factura digital. Si bien la impresión no es obligatoria, cuando el sistema informático de facturación no tenga la capacidad de enviar la representación gráfica y el XML de la factura digital, el sistema informático deberá poder realizar la impresión física de la representación grafica y posterior envío de esta y el XML a través de algún medio tecnológico. Adicionalmente podría poner a disposición de los clientes tanto la representación como el XML a traves de un portal web u otro medio para que el cliente pueda consultar y obtener sus facturas digitales.

# Emisión y Envío de Facturas #

La emisión y envío de Facturas Digitales puede realizarse de manera individual (en tiempo real interactuando en línea con el SIN), por paquetes (en fuera de linea) o de forma masiva. Los pasos a seguir en cada caso se describen a continuación: 

# Consideraciones antes de la Emisión

    * Obtener Token Delegado que permite el consumo de los servicios requeridos, el mismo se puede obtener a través del Portal SIAT.
    * Obtener el CUIS (Código Único de Inicio de Sistemas) consumiendo para ello el servicio web correspondiente solo una vez al inicio o cuando se haya vencido la duración del mismo.
    * Obtener el CUFD (Código Único de Facturación Diario) de forma diaria consumiendo el servicio web correspondiente para poder emitir documentos fiscales.
    * Sincronización de catálogos (Actividades, sectores, productos,fecha hora, documento sector) diariamente consumiendo los servicios web correspondientes.

*Nota:* Si un contribuyente posee varias sucursales y/o puntos de venta, la sincronización de catálogos, puede realizarse una sola vez con la Casa Matriz si el esquema de despliegue es centralizado caso contrario deberá realizar la sincronización por cada sucursal y/o punto de venta.

Como buena práctica se recomienda periódicamente consumir el servicio Verifica Comunicación. Si como respuesta recibe un valor código de error  (Falso, -1, error de la serie 400 o 500) ingresar automáticamente a modo de facturación fuera de Linea. Asimismo, considere que este método existe en cada recurso disponible, por lo que su implementación debe hacerse por recurso.

# Emisión y envío Individual 

    Generar Archivo XML asociado al Documento Fiscal, de acuerdo a su actividad económica.
    Firmar el archivo obtenido conforme estándar XMLDSig (sólo en el caso de la Modalidad Electrónica en Línea).
    Validar contra el XSD asociado a objeto de comprobar que el XML está bien formado y se ajusta a una estructura definida.
    Comprimir el archivo XML en formato Gzip, mismo que debe ser enviado en la etiqueta archivo.
    Obtener el HASH (SHA 256) del archivo compreso obtenido en el paso anterior, mismo que debe ser enviado en la etiqueta hashArchivo. (también llamado Huella Digital).
    Envío Individual consumiendo el servicio de "Recepción de Factura", si no tuviera observaciones, devolverá el estado 908 (validado), en caso contrario devolverá 904 (observado), junto con el código de recepción del mismo, la lista de errores o advertencias (en caso de obtener 904), y la transacción con valor True o False cuando corresponda.

# Emisión y envío de Paquetes por Fuera de Linea

Se recurre a la emisión de Facturas fuera de línea (OFFLINE), cuando sucede algún evento significativos que impida la emisión de documentos fiscales en línea. En este caso las facturas se emiten individualmente y se agrupan en paquetes de hasta 500 documentos fiscales, para que luego de superada la contingencia se envíen los mismos a la Administración Tributaria a través de los servicios web correspondientes. El procedimiento a seguir es el siguiente:

*Primera Etapa* (Mientras dure la contingencia, proceder a emitir las facturas de manera individual)

    * Registar internamente el inicio del evento, junto con el motivo, para posteriormente
    * Generar Archivo XML asociado al Documento Fiscal, de acuerdo a su actividad económica (utilizar modalidad fuera de linea).
    * Firmar el archivo obtenido conforme estándar XMLDSig (sólo en el caso de la Modalidad Electrónica en Línea).
    * Validar contra el XSD asociado a objeto de comprobar que el XML está bien formado y se ajusta a una estructura definida.
    * Almacenar temporalmente de manera individual las Facturas generadas.

 *Segunda Etapa (una vez superada la contingencia)*

    * Recuperar las Facturas almacenadas en formato XML durante la etapa anterior.
    * Formar paquetes de hasta 500 Facturas.
    * Comprimir con Gzip, el archivo resultante debe ser enviado utilizando para ello la etiqueta archivo.
    * Obtener el HASH (SHA256) del archivo compreso obtenido en el paso anterior, mismo que debe ser enviado en la etiqueta hashArchivo.
    * Envío de Paquetes de Facturas:*
      * Consumir el servicio correspondiente para obtener un nuevo CUFD.
      * Registrar el evento significativo a través del servicio web correspondiente, indicando la fecha de inicio y fin del evento, así como el CUFD que fue usado para la emisión de facturas de contingencia.
      * Enviar los paquetes consumiendo el servicio "Recepción de Paquetes de facturas electrónicas o computarizadas". Si la transacción es exitosa, se devolverá el estado 901 (pendiente), el código de recepción del mismo y la transacción en True.
      * Validar la recepción consumiendo el servicio de "Validación de Paquetes de facturas electrónicas o computarizadas", mismo que devolverá el código de estado que puede ser 901 (pendiente), 904 (observada) o 908 (validado). En el caso de que existan observaciones se incluirá una lista de mensajes con códigos, descripciones, número de archivo y número de detalle de los errores y/o advertencias detectados en cada una de las facturas.

*Nota:* Como buena practica, debe mantenerse un registro de facturas sin código de respuesta, una vez superada la contingencia las mismas se verifiquen consumiendo el servicio verificaciónEstadoFactura a objeto de identificar si tienen registro o no en el Servicio de Impuestos Nacionales y proceder a su anulación en caso de ser necesario.

# Emisión y envío de Paquetes Masivos

Se utiliza el envío masivo cuando por el giro de negocio de la empresa, se requiere de la generación de Facturas en grandes cantidades por lotes como es el caso de las entidades financieras, empresas de telecomunicaciones y de servicios básicos. Para poder utilizar la emisión de esta forma se debe registrar a través del Portal Web de la Administración Tributaria:

    * Periodicidad con la que se enviará: diario, semanal o mensual.
    * Tamaño de los paquetes: máximo 1000 Facturas.

*Primera Etapa*

    * Generar Archivo XML asociado al Documento Fiscal, de acuerdo a su actividad económica (utilizar modalidad en linea).
    * Firmar el archivo obtenido conforme estándar XMLDSig (sólo en el caso de la Modalidad Electrónica en Línea).
    * Validar contra el XSD asociado a objeto de comprobar que el XML está bien formado y se ajusta a una estructura definida.
    * Almacenar temporalmente de manera individual las Facturas generadas.

*Segunda Etapa*

    * Recuperar las Facturas almacenadas en formato XML durante la etapa anterior.
    * Formar paquetes de hasta 1000 Facturas.
    * Comprimir con Gzip el archivo resultante debe ser enviado en la etiqueta archivo.
    * Obtener el HASH (SHA256) del archivo compreso obtenido en el paso anterior, mismo que debe ser enviado en la etiqueta hashArchivo.
    *Envío de Paquetes de Facturas:
      *Consumir el servicio correspondiente para obtener un nuevo CUFD .
      *Enviar los paquetes consumiendo el servicio "Recepción de Paquetes de facturas electrónicas o computarizadas". Si la transacción es exitosa, se devolverá el estado 901 (pendiente), el código de recepción del mismo y la transacción en True.
      *Validar la recepción consumiendo el servicio de "Validación de Paquetes de facturas electrónicas o computarizadas", mismo que devolverá el código de estado que puede ser 901 (pendiente), 904 (observada) o 908 (validado). En el caso de que existan observaciones se incluirá una lista de mensajes con códigos, descripciones, número de archivo y número de detalle de los errores y/o advertencias detectados en cada una de las facturas. 

# Emisión y envío de Paquetes por Contingencia

La emisión de Facturas Manuales de Contingencia se produce cuando el sistema que genera las facturas no esta disponible debido a un evento significativo de tipo (corte de energía, falla de software o falla de hardware). En este caso y para no parar el negocio, se puede recurrir a la emisión de Facturas Manuales de Contingencia (previamente solicitadas e impresas a través de una imprenta autorizada).  Superada el evento de contingencia se puede proceder de la siguiente manera:

**0. Envío del evento:**

    * Se debe registrar el evento a través del servicio disponible para el efecto indicando:

      * fecha de inicio (hasta el minuto mínimamente)
      * fecha de fin (hasta el minuto mínimamente)
      * código de evento (5,6 o 7)
      * cufd del evento (debe corresponder a la fecha en la cual se tuvo el evento)
      * cufd del envío 
      * descripción (descripción del evento ocurrido)

**1. Primera Etapa (Transcripción):**

    * Generar Archivo XML transcribiendo la información contenida en la factura manual, con tipo de emisión "fuera de linea" (2), utilizar el CUFD que estaba vigente al ingresar en contingencia y registrado en el evento (completar todos los campos requeridos)
    * Firmar el archivo obtenido conforme estándar XMLDSig (sólo en el caso de la Modalidad Electrónica en Línea).
    * Validar contra el XSD asociado a objeto de comprobar que el XML está bien formado y se ajusta a una estructura definida.
    * Almacenar temporalmente de manera individual las Facturas generadas.

**2. Segunda Etapa (Armado de paquetes):**

    * Recuperar las Facturas transcritas y en formato XML durante la etapa anterior.
    * Formar paquetes de hasta 500 Facturas.
    * Comprimir con Gzip, el archivo resultante debe ser enviado en la etiqueta archivo.
    * Obtener el HASH (SHA256) del archivo compreso obtenido en el paso anterior, mismo que debe ser enviado en la etiqueta hashArchivo.
    * Envío de Paquetes de Facturas:
      * Consumir el servicio correspondiente para obtener un nuevo CUFD .
      * Enviar los paquetes consumiendo el servicio "Recepción de Paquetes de facturas electrónicas o computarizadas", incluyendo el código de recepción del evento y el CAFC de las facturas transcritas. Si la transacción es exitosa, se devolverá el estado 901 (pendiente), el código de recepción del mismo y la transacción en True.
      * Validar la recepción consumiendo el servicio de "Validación de Paquetes de facturas electrónicas o computarizadas", mismo que devolverá el código de estado que puede ser 901 (pendiente), 904 (observada) o 908 (validado). En el caso de que existan observaciones se incluirá una lista de mensajes con códigos, descripciones, número de archivo y número de detalle de los errores y/o advertencias detectados en cada una de las facturas.

**Nota.**

    * Para el ambiente de pruebas (PILOTO) deberá solicitar CAFC para los documentos que esta autorizando, así como para las sucursales que probaran.
    * Los Códigos Especiales 99001 (Utilizado para consulados, embajadas, etc), el 99002 (Control Tributario) y el 99003 (Ventas Menores del Día) se deben enviar con el tipo de documento NIT y el código de Excepción en 1.
    * Si durante la emisión  se utiliza como tipo de documento C.I. o NIT el sistema emisor debe validar que el valor que se envia sea numérico.
    * El código de excepción debe enviarse por defecto con un valor de 0 (cero). Se envía con un valor de 1 (uno) solo si el Tipo de documento es un NIT pidiendo de esta manera al SIN no validar el mismo. Por otro lado, si la emisión es en fuera de linea y el tipo de documento NIT siempre enviar el código de excepción  con un valor de 1.
    * El tipo de emisión "CONTINGENCIA" que se obtiene al realizar la sincronización de catalogos es para uso exclusivo del SIN.

# CODIGOS DE AUTORIZACION #

Los Códigos de Autorización otorgados por el SIN o generados por el Sistema Informático de Facturación autorizan la emisión de Documentos Fiscales en función a parámetros establecidos. De acuerdo a su característica podrán o no ser consignados en los documentos fiscales autorizados por la Administración Tributaria. Estos son los Códigos de Autorización definidos para la Modalidad de Facturación Electrónica:

**CUIS (Código Único de Inicio de Sistemas)**. Dato alfanumérico generado por la Administración Tributaria que identifica la relación entre el Sistema de Facturación, credenciales, contribuyente, sucursal y opcionalmente al punto de venta. Tiene una vigencia de 365 días calendario. Para su obtención se utiliza un Token que valida la autenticidad del contribuyente.
**CUFD (Código Único de Facturación Diaria).** Dato alfanumérico generado por la Administración Tributaria con la información del Sistema de Facturación, que permite al Sujeto Pasivo o Tercero Responsable la emisión de Documentos Fiscales Electrónicos durante 24 horas. Para su obtención se utiliza Token que la autenticidad del contribuyente.
**CUF (Código Único de Factura).** Generado de forma automática al momento de la emisión de la Factura por el Sistema Informático de Facturación que permite la individualización de cada factura.
**CAFC (Código Autorización Facturas Contingencia).** Generado por la Administración Tributaria para la impresión y posterior emisión de facturas de contingencia. Se lo obtiene al efectuar la solicitud de impresión de facturas manuales de contingencia.

**Nota.** En el caso del uso de Facturas Prevaloradas en Línea, el sistema informático de facturación deberá solicitar la autorización de emisión para este tipo de documento, considerando el periodo, los rangos de emisión y precios fijos para dichos documentos. Esta solicitud devolverá un código de autorización que deberá ser incluido en la solicitud de emisión.
En los registros obligatorios a enviar a la Administración Tributaria, excepto en el Registro de Compras y Ventas o aplicativos SIAT o Mis facturas, donde se solicite el Numero de Autorización, deberá registrarse el valor noventa y nueve (99) cuando las citadas facturas consignen Códigos de Autorización emitidos en la Modalidad de Facturación Electrónica en Línea.

# CONTINGENCIA Y EVENTOS SIGNIFICATIVOS #

Los eventos significativos son hechos inherentes al Sistema informático de Facturación que intervienen en su funcionamiento o que podrían afectar la emisión de las Facturas Digitales. Deben ser registrados hasta 48 horas posteriores de finalizada la contingencia, a través del sistema autorizado por la Administración Tributaria y enviados automáticamente a través del servicio Web correspondiente.

Tipos de Eventos Significativos que generan contingencia

+----------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **EVENTO SIGNIFICATIVO **                                            |                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      | **DETALLE DE ACCIÓN**                                                                                                                                                                                                                                                                                                                                                                |
+----------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
| *1) Corte del servicio de Internet*                                  |                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
+----------------------------------------------------------------------+                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      | Emitir Documentos Fiscales digitales fuera de línea, conforme lo establecido en el Anexo Técnico de la presente Resolución.                                                                                                                                                                                                                                                       |
| *2) Inaccesibilidad al Servicio Web de la Administración Tributaria.*|                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
+----------------------------------------------------------------------+                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
|*3) Ingreso a zonas sin Internet por despliegue de puntos de venta.*  |                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
+----------------------------------------------------------------------+                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
| *4) Venta en Lugares sin internet.*                                  |                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
+----------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
| *5) Virus informático o falla de software.*                          | Emitir  Facturas por Contingencia autorizadas por la Administración Tributaria, solicitadas con anterioridad por el Sujeto Pasivo del IVA o emitir  Documentos Fiscales Digitales usando de manera transitoria y por  contingencia la Modalidad de Facturación Portal Web en línea conforme  los aspectos técnicos establecidos en el Anexo Técnico de la presente  Resolución.  |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
+----------------------------------------------------------------------+                                                                                                                                                                                                                                                                                                                                                                                   |
|                                                                      |                                                                                                                                                                                                                                                                                                                                                                                   |
| *6) Cambio de infraestructura de sistema o falla de hardware.*       |                                                                                                                                                                                                                                                                                                                                                                                   |
+----------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                      | Emitir  Facturas por Contingencia autorizadas por la Administración Tributaria,  solicitadas con anterioridad por el Sujeto Pasivo del IVA.                                                                                                                                                                                                                                       |
| *7) Corte de suministro de energía eléctrica.*                       |                                                                                                                                                                                                                                                                                                                                                                                   |
+----------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

De producirse una contingencia, pero el sistema informático continua operativo, este deberá cambiar a la emisión de facturas fuera de línea, las facturas se emiten con el CUFD vigente hasta antes del corte. Las facturas emitidas se almacenan en paquetes que posteriormente serán enviados a la administración Tributaria, cuando la contingencia se haya superado. (Obtener un nuevo CUFD antes de registrar el evento significativo y enviar los paquetes, a fin de evitar posibles inconvenientes relacionados al tiempo de vigencia del CUFD durante el envío de los mismos de no hacerlo).

En caso de que no pueda utilizarse el sistema informático por falla de hardware, software o por corte de energía eléctrica, se deberán emitir facturas manuales de contingencia previamente aprovisionadas, superada la contingencia estas deberán ser transcritas utilizando para ello el CUFD que estaba vigente al ingresar en contingencia y enviadas a la Administración Tributaria a través del mismo sistema informático de facturación. (Obtener un nuevo CUFD antes de registrar el evento significativo y enviar los paquetes, a fin de evitar posibles inconvenientes relacionados al tiempo de vigencia del CUFD durante el envío de los mismos de no hacerlo).

Nota: Como buena practica, debe mantenerse un registro de facturas sin código de respuesta, a objeto de que una vez superada la contingencia se verifiquen las mismas consumiendo el servicio verificaciónEstadoFactura a objeto de identificar si fueron registradas o no en el Servicio de Impuestos Nacionales y de ser asi proceder a su anulación de ser necesario evitando duplicidades.

SI el tipo de documento utilizado en la emisión de una factura en fuera de linea es el NIT, se debe enviar el código de excepción con valor uno.