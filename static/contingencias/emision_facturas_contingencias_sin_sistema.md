#Guía de Autorización de Facturas Manuales de Contingencia

La solicitud de facturas emitidas por contingencia solo esta disponible para aquellos contribuyente que pertenezcan a una modalidad de facturación en Línea o al Portal Web. 
Permite realizar la solicitud de facturas de contingencia que podrán ser utilizadas solo en caso de emergencia.

  
   1) El Contribuyente ingresa al Portal de la Administración Tributaria utilizando las credenciales de oficina Virtual
   2) Solicita la autorización para la impresión de facturas de contingencia a través de la opción correspondiente (por actividad económica, sucursal, casa matriz o punto de venta)
   3) El SIN valida entre otras cosas que el contribuyente pertenezca a una modalidad en línea, de ser así, autoriza y genera el CAFC (Código de Autorización de Factura de Contingencia) más un PIN al Contribuyente
   4) Contribuyente recibe información de la solicitud de impresión + PIN (Acude a imprenta autorizada)
   5) Contribuyente ingresa en contingencia que impide la emisión de facturas electrónicas
   6) Se restablece la comunicación
   7) Emite facturas de contingencia
   8) Se recupera de la contingencia
   9) Contribuyente transcribe las facturas de contingencia
  10) Contribuyente envía facturas transcritas al SIN por paquete a través del servicio correspondiente

 

Nota: Las facturas por contingencia deberán registrase en el plazo de 72 horas posteriores al restablecimiento de la comunicación y conectividad con la Administración Tributaria, utilizando para ello sus sistemas y tomando en cuenta que se deben transcribir todos los campos solicitados en las tramas de XML correspondientes.

#Esquema de Interoperabilidad

1. El Sistema Informático de Facturación solicita al SIN el código único de facturación diaria (CUFD), que le habilita la emisión de Facturas por un periodo de 24 horas.

2. El SIN realiza verificaciones a la información del emisor y devuelve los códigos de Verificación y CUFD, además de la dirección de la sucursal o casa matriz.

3. El Sistema Informático de Facturación del Contribuyente utiliza el CUFD, junto con los datos de emisión para generar el archivo XML (factura digital), que debe ser firmado digitalmente y enviado a través de los servicios correspondientes del SIN.

4. El SIN recibe la solicitud de recepción y procede a validar la cabecera para devolver la siguiente información:

a)  i la validación es correcta y es un proceso individual en línea, retorna código de recepción. 

b)  Si la validación es correcta y es un proceso por paquete de contingencia o masivo, retorna el código de recepción.

c)   Si la validación presenta errores, retorna una lista de códigos y mensajes de error para que el emisor proceda a su corrección y posterior reenvío.

5.    El Sistema envía por correo u otra medio la representación gráfica y el XML al cliente, si este desea tener un respaldo de la emisión de la Factura Digital, el emisor podrá imprimir la Representación Gráfica.

6.  Cuando la emisión de la Factura Digital sea por paquete de contingencia o por emisión masiva, el SIN validará la información contenida en el paquete de manera individual, como resultado se tiene:

a)  Registrar y consolidar la Factura Digital para la emisión por contingencia o masiva en caso de no existir errores.

b) En caso de existir errores, se observa el paquete, se registran las facturas correctas y se rechazan las que contengan los errores. En caso de que el tipo de documento sea NIT y el  numero de documento no sea valido o no haya sido validado previamente a través del método de verificación de NIT, el emisor podrá enviar el código de excepción para que la factura no sea rechazada.

7.  El SIN retorna los resultados del proceso de validación descritos en el punto 6. En caso de existir observaciones deberá subsanarlas y posteriormente reenviar la Factura Digital. 

#Códigos de Autorización

Los Códigos de Autorización otorgados por el SIN o generados por el Sistema Informático de Facturación autorizan la emisión de Documentos Fiscales en función a parámetros establecidos. 
De acuerdo a su característica podrán o no ser consignados en los documentos fiscales autorizados por la Administración Tributaria, de acuerdo a la modalidad de facturación utilizada pueden ser:

*CUIS (Código Único de Inicio de Sistemas).* Dato alfanumérico generado por la Administración Tributaria que identifica la relación entre el Sistema de Facturación, credenciales, contribuyente, sucursal y opcionalmente al punto de venta. Tiene una vigencia de  365 días calendario. Para su obtención se utiliza Token para validar la autenticidad del contribuyente.

*CUFD (Código Único de Facturación Diaria).* Dato alfanumérico generado por la Administración Tributaria con la información del Sistema de Facturación, que permite al Sujeto Pasivo o Tercero Responsable la emisión de Documentos Fiscales Electrónicos durante 24 horas. Para su obtención se utiliza Token para validar la autenticidad del contribuyente.

*CUF (Código Único de Factura).* Generado de forma automática al momento de la emisión de la Factura por el Sistema Informático de Facturación, en las Modalidades de Facturación en Línea,  permite la individualización de cada factura.

*CAED (Código Autorización para la Emisión de Documentos Fiscales).* Generado por la Administración Tributaria para la emisión de Documentos Fiscales en las modalidades de facturación Manual y Prevalorada Preimpresa.

*CAFC (Código Autorización Facturas Contingencia).* Generado por la Administración Tributaria para la impresión y posterior emisión de facturas de contingencia. Se lo obtiene cuando al efectuar la solicitud de impresión de facturas manuales de contingencia.

Número de Autorización. Generado Automáticamente para la emisión de Facturas en la modalidad Computarizada SFV.

*Nota.* En el caso del uso de Prevaloradas en Línea, el sistema informático de facturación deberá solicitar la autorización de emisión para este tipo de documento, considerando el periodo, los rangos de emisión y precios fijos para dichos documentos. Esta solicitud devolverá un código de autorización que deberá ser incluido en la solicitud de emisión.

En los registros obligatorios a enviar a la Administración Tributaria, excepto en el Registro de Compras y Ventas o aplicativos SIAT o Mis facturas, donde se solicite el Numero de Autorización deberá registrarse el valor noventa y nueve (99) cuando las citadas facturas consignen Códigos de Autorización emitidas en la Modalidad de Facturación Electrónica en Línea, Computarizada en Línea o Portal Web en Línea o Modalidad Manual del Sistema de Facturación vigente.

#Facturas Manuales de Contingencia

Este tipo de facturas se pueden utilizar a objeto de no parar el negocio y dar continuidad a las actividades del mismo, cuando el sistema que se encarga de la emisión de las facturas en linea esta fuera de servicio debido a  que se produjo alguno de los eventos significativos catalogados como 5, 6 o 7.
Las facturas emitidas de esta manera deben ser transcritas y enviadas al SIN a través de su sistema en un plazo máximo de 72 horas posteriores al restablecimiento de la comunicación y conectividad con la Administración Tributaria.

*Operativa*

Una vez superada la contingencia que impedía la emisión de facturas en linea, se debe proceder de la siguiente manera:

*Primera Etapa (Transcripción)*

    1) Generar Archivo XML transcribiendo la información contenida en la factura manual (completar todos los campos requeridos)
    2) Firmar el archivo obtenido conforme estándar XMLDSig (sólo en el caso de la Modalidad Electrónica en Línea).
    3) Validar contra el XSD asociado a objeto de comprobar que el XML está bien formado y se ajusta a una estructura definida.
    4) Almacenar temporalmente de manera individual las Facturas generadas.

*Segunda Etapa (Armado de paquetes)*

    1) Recuperar las Facturas transcritas en formato XML durante la etapa anterior.
    2) Formar paquetes de hasta 500 Facturas (Todas del mismo documento sector).
    3) Comprimir con Gzip (Se envía en la etiqueta archivo).
    4) Obtener el HASH (SHA256) del archivo comprimido (se envía en la etiqueta hashArchivo).
   
*Envío del Paquete de Facturas:*

    1) Consumir el servicio correspondiente para obtener un nuevo CUFD.
    2) Registrar el evento significativo a través del servicio web correspondiente, indicando la fecha de inicio y fin del evento, así como el CAFC de las facturas manuales de contingencia utilizado. (Si se utilizaron diferentes CAFC se deben registrar dos eventos significativos uno por cada CAFC).
    3) Enviar los paquetes consumiendo el servicio "Recepción de Paquetes de facturas electrónicas o computarizadas". Si la transacción es exitosa, se devolverá el estado 901 (pendiente), el código de recepción del mismo y la transacción en True.
    4) Validar la recepción consumiendo el servicio de "Validación de Paquetes de facturas electrónicas o computarizadas"
    5) El código de estado devuelto puede tener los valores 901 (pendiente), 904 (observada) o 908 (validada). En el caso de que el paquete haya sido observado, se incluirá una lista de mensajes con códigos, descripciones, número de archivo y número de detalle de los errores y/o advertencias detectados en cada una de las facturas

*Nota:* Estas facturas deben ser haber sido previamente solicitadas e impresas a través de una imprenta autorizada, manteniendo el formato de las facturas en linea.
