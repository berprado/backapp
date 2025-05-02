#Facturas Manuales de Contingencia

Este tipo de facturas se pueden utilizar a objeto de no parar el negocio y dar continuidad a las actividades del mismo, cuando el sistema que se encarga de la emisión de las facturas en linea esta fuera de servicio debido a  que se produjo alguno de los eventos significativos catalogados como 5, 6 o 7.

Las facturas emitidas de esta manera deben ser transcritas y enviadas al SIN a través de su sistema en un plazo máximo de 72 horas posteriores al restablecimiento de la comunicación y conectividad con la Administración Tributaria.

#Operativa

Una vez superada la contingencia que impedía la emisión de facturas en linea, se debe proceder de la siguiente manera:

*Primera Etapa (Transcripción)*

    Generar Archivo XML transcribiendo la información contenida en la factura manual (completar todos los campos requeridos)
    Firmar el archivo obtenido conforme estándar XMLDSig (sólo en el caso de la Modalidad Electrónica en Línea).
    Validar contra el XSD asociado a objeto de comprobar que el XML está bien formado y se ajusta a una estructura definida.
    Almacenar temporalmente de manera individual las Facturas generadas.

*Segunda Etapa (Armado de paquetes)*

    Recuperar las Facturas transcritas en formato XML durante la etapa anterior.
    Formar paquetes de hasta 500 Facturas (Todas del mismo documento sector).
    Comprimir con Gzip ( Se envía en la etiqueta archivo).
    Obtener el HASH (SHA256) del archivo comprimido (se envía en la etiqueta hashArchivo).
    Envío del Paquete de Facturas:

    Consumir el servicio correspondiente para obtener un nuevo CUFD.
    Registrar el evento significativo a través del servicio web correspondiente, indicando la fecha de inicio y fin del evento, así como el CAFC  de las facturas manuales de contingencia utilizado. (si se utilizaron diferentes CAFC se deben registrar dos eventos significativos uno por cada CAFC).
    Enviar los paquetes consumiendo el servicio "Recepción de Paquetes de facturas electrónicas o computarizadas". Si la transacción es exitosa, se devolverá el estado 901 (pendiente), el código de recepción del mismo y la transacción en True.
    Validar la recepción consumiendo el servicio de "Validación de Paquetes de facturas electrónicas o computarizadas"
    El código de estado devuelto puede tener los valores 901 (pendiente), 904 (observada) o 908 (validada). En el caso de que el paquete haya sido observado, se incluirá una lista de mensajes con códigos, descripciones, número de archivo y número de detalle de los errores y/o advertencias detectados en cada una de las facturas

**Nota. Estas facturas  deben ser haber sido previamente solicitadas e impresas a través de una imprenta autorizada según el procedimiento detallado a continuación**

#Guía de Autorización para la impresión de Facturas de Contingencia (manuales)

Permite realizar la solicitud de facturas de contingencia que podrán ser utilizadas solo en caso de emergencia.  
