# MVP SISTEMA DE FACTURACION

a)     *Emisor de Facturas Digitales:

Permite generar Facturas Digitales en formato XML
 

Este componente debe poseer por lo menos la emisión individual y la emisión por contingencia, en función del giro del negocio puede tener la capacidad de emisión masiva de facturas:

Emisión Individual

Este componente debe emitir una Factura Digital en base a la siguiente secuencia de pasos:

1)     Generar Archivo XML asociado a la Factura. 

2)     Firmar el archivo obtenido conforme estándar XMLDSig.

3)     Validar contra el XSD asociado.

4)     Comprimir el archivo XML en formato Gzip, mismo que debe ser enviado en la etiqueta archivo.

5)     Obtener el HASH (SHA256) del archivo compreso obtenido en el paso anterior, mismo que debe ser enviado en la etiqueta hashArchivo.


**Emisión de Paquetes por Contingencia**

Cuando el Sistema Informático de Facturación tenga un evento de contingencia que obligue a la emisión de facturas fuera de línea (offline), almacenará las mismas en paquetes de máximo 500 Facturas. Posterior a la recuperación del evento de contingencia, el Sistema Informático deberá registrar el mismo a través del Servicio Web habilitado para el efecto y proceder al envío de los paquetes consumiendo para ello los servicios correspondientes.


**Emisión de Paquetes por emisión Masiva**

La emisión masiva es utilizada por empresas que, por su giro de negocio, realizan procesos automatizados de emisión de Facturas Digitales en horarios extraordinarios, como entidades financieras, servicios de telecomunicaciones, luz, agua y otros. Por lo que el Sistema Informático de Facturación autorizado deberá generar paquetes de hasta 1000 Facturas y proceder al envío de los mismos a través de los servicios correspondientes.

b)    *Gestor de  Facturas Digitales:

Su función principal es enviar y validar transacciones de registro como la anulación de las Facturas. 
 
c)    *Sincronización de catálogos:

Funcionalidad que permite la descarga y actualización de los diferentes catálogos del Sistema de Facturación, códigos de productos y servicios, países, códigos de eventos significativos, códigos de mensajes de servicios y otros. La sincronización de catálogos se realizará de forma diaria. 

d)    *Sincronización de fecha y hora: (Debe obligatoriamente efectuarse a Diario)

Permite la sincronización de la fecha y hora de los Sistemas Informáticos de Facturación (Contribuyente) con la fecha y hora de la Administración Tributaria. Esta sincronización será utilizada para realizar los controles de plazos de envíos y registros en las diferentes casuísticas de emisión de Facturas Digitales. La sincronización puede ser realizada varias veces al día, recomendándose se la efectúe antes de la obtención del Código Único de Facturación Diaria - CUFD, a través del servicio web correspondiente.

e)     *Registro de eventos significativos:

Funcionalidad que permite el registro de eventos significativos que se hubieren producido y que se detallan en la sección Contingencia.

f)     *Gestor de envío de documentos digitales e impresión:

Su función principal es gestionar la impresión, envío o publicación de la representación gráfica y el XML de la factura digital. 
Si bien la impresión no es obligatoria, cuando el sistema informático de facturación no tenga la capacidad de enviar la representación gráfica y el XML de la factura digital, el sistema informático deberá poder realizar la impresión física de la representación grafica y posterior envío de esta y el XML a través de algún medio tecnológico. Adicionalmente podría poner a disposición de los clientes tanto la representación como el XML a traves de un portal web u otro medio para que el cliente pueda consultar y obtener sus facturas digitales. 