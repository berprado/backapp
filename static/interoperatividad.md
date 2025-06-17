+++markdown

# Sistema Informático de Facturación

Los Sistemas Informáticos de Facturación para interactuar con los servicios de la Administración Tributaria, deberán estar autorizados por el Servicio de Impuestos Nacionales (SIN) y contar como mínimo con los siguientes componentes o funcionalidades:

## a) Emisor de Facturas Digitales

Permite generar Facturas Digitales en formato XML.

Este componente debe poseer por lo menos la emisión individual y por contingencia. En función del giro del negocio, puede tener la capacidad de emisión masiva:

### Emisión Individual

Este componente debe emitir una Factura Digital en base a la siguiente secuencia de pasos:

1. Generar archivo XML asociado a la factura de acuerdo a su actividad económica.
2. Firmar el archivo obtenido conforme estándar **XMLDSig**.
3. Validar contra el **XSD** asociado.
4. Comprimir el archivo XML en formato **Gzip**, el cual debe ser enviado en la etiqueta `archivo`.
5. Obtener el **HASH (SHA256)** del archivo comprimido obtenido en el paso anterior, mismo que debe ser enviado en la etiqueta `hashArchivo`.

### Emisión de Paquetes por Contingencia

Cuando el Sistema Informático de Facturación autorizado tenga un evento de contingencia que obligue a la emisión de facturas fuera de línea (offline), almacenará las mismas en paquetes de máximo **500 facturas**. Posterior a la recuperación del evento de contingencia, el sistema deberá registrar el mismo a través del **Servicio Web** habilitado para el efecto y proceder al envío de los paquetes consumiendo para ello los servicios correspondientes.

### Emisión de Paquetes por Emisión Masiva

La emisión masiva es utilizada por empresas que, por su giro de negocio, realizan procesos automatizados de emisión de Facturas Digitales en horarios extraordinarios, como:

* Entidades financieras
* Servicios de telecomunicaciones
* Luz, agua, y otros

El Sistema Informático de Facturación autorizado deberá generar paquetes de hasta **1000 facturas** y proceder al envío de los mismos a través de los servicios correspondientes.

## b) Gestor de Facturas Digitales

Su función principal es **enviar y validar transacciones** de registro como la anulación de las facturas. 

## c) Sincronización de Catálogos

Funcionalidad que permite la descarga y actualización de los diferentes catálogos del Sistema de Facturación:

* Códigos de productos y servicios
* Países
* Códigos de eventos significativos
* Códigos de mensajes de servicios
* Otros

La sincronización de catálogos se realizará de forma **diaria**.

## d) Sincronización de Fecha y Hora *(Debe efectuarse obligatoriamente a diario)*

Permite la sincronización de la fecha y hora de los Sistemas Informáticos de Facturación (Contribuyente) con la de la Administración Tributaria.

Esta sincronización se utilizará para realizar los controles de plazos de envíos y registros en las diferentes casuísticas de emisión de Facturas Digitales. Puede realizarse varias veces al día, siendo **recomendado efectuarla antes de la obtención del Código Único de Facturación Diaria - CUFD**, a través del servicio web correspondiente.

## e) Registro de Eventos Significativos

Funcionalidad que permite el **registro de eventos significativos** que se hubieren producido.

## f) Gestor de Envío de Documentos Digitales e Impresión

Su función principal es **gestionar la impresión, envío o publicación** de la representación gráfica y el XML de la factura digital.

* Aunque la impresión no es obligatoria, si el sistema no puede enviar la representación gráfica y el XML, deberá poder realizar la **impresión física** y posterior envío de ambos a través de un medio tecnológico.
* Adicionalmente, podría poner a disposición de los clientes la representación gráfica y el XML a través de un **portal web u otro medio** para su consulta y descarga.

+++
