Facturación en Contingencia y Eventos Significativos en el SIAT Bolivia: Preguntas Frecuentes

**¿Qué es un Evento Significativo según la normativa del SIAT y por qué es importante registrarlo?

Un Evento Significativo es un suceso (técnico o ambiental) que interrumpe el funcionamiento normal del sistema de facturación electrónica, impidiendo la emisión de facturas en línea. 
Esto podría ser un corte de internet, inaccesibilidad a los servicios del SIN, fallas de software o hardware, o incluso cortes de energía eléctrica. 
Es crucial registrar estos eventos ante el SIN (Servicio de Impuestos Nacionales) para justificar el uso de modos de emisión alternativos (como el modo fuera de línea) y mantener el cumplimiento normativo. El registro se debe realizar a través de un servicio web del SIN dentro de las 48 horas posteriores a la finalización del evento.

**¿Cómo habilita un Evento Significativo el uso de modos alternativos de facturación?

La ocurrencia y el registro de un Evento Significativo son lo que autoriza al contribuyente a utilizar modos de emisión de documentos fiscales distintos a la facturación en línea. 
Estos modos alternativos incluyen la emisión "fuera de línea" o "manual", permitiendo al negocio continuar operando y emitiendo facturas incluso cuando la conexión con el SIN está interrumpida. 
Esto garantiza la continuidad operativa del negocio durante periodos de contingencia.

**¿Cuáles son las dos etapas principales para la emisión de facturas durante y después de una contingencia?

La emisión de facturas durante una contingencia se divide en dos etapas:

    Primera Etapa (Durante la Contingencia - Modo Fuera de Línea): Mientras dura la contingencia, las facturas se emiten individualmente en modo fuera de línea.
	Esto implica registrar internamente el inicio del evento, generar un archivo XML para cada factura utilizando la modalidad fuera de línea y firmándolo digitalmente, validar el XML contra el esquema XSD localmente, y almacenar temporalmente cada factura generada de forma individual.
    Segunda Etapa (Una vez Superada la Contingencia): Cuando se restablece la conexión con el SIN, se recuperan las facturas almacenadas durante la contingencia. 
	Estas facturas se agrupan en paquetes (de hasta 500 facturas), se comprimen (usando Gzip), se calcula un HASH (SHA256) del archivo comprimido, y finalmente se envían estos paquetes al SIN utilizando el servicio correspondiente. También se debe obtener un nuevo CUFD en esta etapa y verificar el estado de las facturas sin código de respuesta.

**¿Cómo se maneja la emisión de facturas con NIT (Número de Identificación Tributaria) en modo fuera de línea?

Cuando se emite una factura en modo fuera de línea y el tipo de documento del receptor es NIT, se debe enviar un código de excepción con valor 1. 
Esto le indica al SIN que no debe validar el NIT en ese momento, ya que la emisión ocurrió durante una contingencia donde la validación en línea no era posible. En el modo online, este código por defecto es 0 y solo se cambia a 1 si se desea evitar la validación del NIT con el SIN. 
En el modo fuera de línea, el código de excepción para NITs siempre es 1.

**¿Qué información clave se requiere para registrar un Evento Significativo ante el SIN?

Para registrar un Evento Significativo a través del servicio web del SIN, se requiere proporcionar información como: el código del ambiente (Producción: 1, Pruebas/Piloto: 2), el código del motivo del evento (identificando la causa de la contingencia, como corte de internet, etc.), el código del sistema, el NIT del emisor, el CUIS (Código Único de Inicio de Sistemas), el CUFD (Código Único de Facturación Diaria) que se utilizó durante la contingencia, el código y la fecha de inicio del evento, y opcionalmente el código de sucursal y punto de venta. Esta información permite al SIN vincular las emisiones fuera de línea con el evento de contingencia correspondiente.

**¿Qué sucede con las facturas emitidas en modo fuera de línea una vez que se restablece la conexión con el SIN?

Una vez superada la contingencia y restablecida la conexión, las facturas emitidas en modo fuera de línea deben ser enviadas al SIN en paquetes. 
El SIN validará la información de cada factura dentro del paquete. Si una factura es correcta, se registrará. Si contiene errores, será rechazada y el emisor deberá subsanar las observaciones y reenviarla.
Además, se deben verificar las facturas que no recibieron un código de respuesta para determinar si fueron registradas por el SIN y proceder a su anulación si es necesario. 
Es fundamental mantener un registro de estas facturas pendientes de verificación.

**¿Qué son el CUIS y el CUFD y cuál es su rol en la facturación electrónica, incluyendo las contingencias?

    CUIS (Código Único de Inicio de Sistemas): Es un código alfanumérico único asignado por el SIN que identifica la relación entre el sistema de facturación, el contribuyente, la sucursal y opcionalmente el punto de venta. Tiene una vigencia de 365 días y se obtiene utilizando un Token para validar la autenticidad.
    CUFD (Código Único de Facturación Diaria): Es un código alfanumérico diario otorgado por el SIN que habilita la emisión de documentos fiscales electrónicos por 24 horas. Se obtiene utilizando un Token. En el contexto de contingencias, las facturas fuera de línea se asocian con el CUFD vigente hasta antes de que comenzara el evento significativo.

Ambos códigos son esenciales para la autorización y validación de documentos fiscales, tanto en modo en línea como para vincular las emisiones fuera de línea a un periodo autorizado.

**¿Cómo se garantiza que el sistema pueda operar sin consumir servicios externos durante el modo offline?

Para asegurar la operación en modo offline sin depender de servicios externos, el sistema implementa varias lógicas:

    Detección de Conectividad: Verifica constantemente la disponibilidad de conexión a internet y la accesibilidad a los servicios del SIN. La ausencia de conexión o errores en la comunicación activa el modo offline.
    Almacenamiento Local: Las facturas generadas en modo offline se almacenan localmente, tanto en una base de datos interna como archivos XML, sin intentar enviarlas al SIN inmediatamente.
    Validación Local: Las validaciones de formato de las facturas (por ejemplo, contra esquemas XSD) se realizan utilizando recursos locales, sin necesidad de conexión externa.
    Caché de Datos: Se implementan mecanismos de caché para almacenar datos importantes que normalmente se obtendrían de servicios externos (como información de clientes o comandas), permitiendo que el sistema acceda a esta información localmente durante la contingencia.
    Procesos Diferidos: Acciones que requieren interacción con el SIN (registro de eventos significativos, envío de facturas) se posponen y ejecutan en modo batch una vez que se restablece la conexión.

Este diseño permite que el sistema opere de manera autónoma durante las interrupciones, cumpliendo con la normativa de facturación electrónica boliviana.