A continuación, se presenta una guía integral para la implementación y manejo correcto de las contingencias y la emisión masiva de facturas en la modalidad de facturación electrónica en Bolivia. 
Esta guía integra la información normativa y los lineamientos técnicos que hemos documentado previamente, complementados con el contenido de los archivos adjuntos.

---

## 1. Introducción y Consideraciones Generales

La facturación electrónica en Bolivia, bajo el esquema del SIAT, contempla la posibilidad de enfrentar eventos que interrumpan la comunicación o la operatividad del sistema. Estos eventos—denominados **eventos significativos**—pueden originarse por fallas de conectividad, problemas en los servicios del SIN, fallas de hardware/software o cortes de energía. En tales casos, el contribuyente debe activar un modo de contingencia, lo que implica emitir facturas en **modo fuera de línea** o mediante facturas manuales de contingencia previamente autorizadas.

Esta guía aborda:
- La detección y el ingreso a contingencia.
- Los procedimientos para la emisión individual y el almacenamiento en modo offline.
- El proceso de agrupación y envío masivo de facturas una vez restaurada la comunicación.
- Recomendaciones para el manejo de errores en emisión, anulación y la renovación del CUFD.

---

## 2. Detección e Ingreso a Contingencia

### a. Detección de Fallas en la Comunicación

El sistema debe monitorear de forma constante el servicio de comunicación con el SIN. Si al consumir el servicio de verificación se obtiene alguno de los siguientes códigos o condiciones:
- **Time Out, -1, Java Null Point o HTTP 500.**
- Errores específicos como **400 o 404** al consumir servicios críticos.

Tras varios intentos (por lo general, un par de veces) y sin lograr una respuesta positiva, se determina que existe un problema de comunicación. En ese caso, se debe cambiar al modo **"Fuera de Línea"** para continuar las operaciones de facturación sin interrumpir el negocio.

> “Si ... la respuesta continúa siendo la misma indica que el servicio específico que estamos requiriendo tiene algún problema, por lo que para dar continuidad a nuestras operaciones debemos ingresar a Fuera de Línea. Se recomienda permanecer en fuera de línea por un tiempo prudencial ... (no mayor a dos horas)”  


### b. Procedimiento Durante el Ingreso a Contingencia

1. **Ingreso a Modo Fuera de Línea:**  
   - Activar la emisión de facturas en modo offline usando el último CUFD obtenido.  
   - Almacenar cada factura emitida (generando su XML, firma digital y validación contra XSD) de manera local, para su envío posterior.

2. **Verificación de Servicios Críticos:**  
   - Revisar también los servicios de emisión y anulación.  
   - Si durante la emisión de una factura se reciben errores (Time Out, -1, etc.), se debe obtener un **nuevo CUFD** y verificar el estado de la factura emitida en los servidores del SIN. Si se encuentra registrada, proceder a su anulación y posteriormente registrar el evento de contingencia.

3. **Reintento y Recuperación:**  
   - Permanecer en modo offline por un periodo prudencial (usualmente no mayor a dos horas) y reintentar el consumo de los servicios.  
   - Una vez recuperada la comunicación, obtener un nuevo CUFD, **registrar el evento significativo** y proceder con el envío de los paquetes de facturas generadas durante la contingencia.

> “Si ... la respuesta continúa siendo la misma ... debemos ingresar a Fuera de Línea y emitir facturas utilizando el último CUFD válido, pues en casos como este la duración del CUFD se amplía hasta a 72 horas.”  


---

## 3. Eventos Significativos y Acciones a Tomar

### a. Tipos de Eventos que Generan Contingencia

Según la información normativa y el archivo de eventos, los principales eventos son:

- **1) Corte del servicio de Internet:**  
  Se activa la emisión fuera de línea.

- **2) Inaccesibilidad al Servicio Web del SIN:**  
  Se procede a emitir documentos fuera de línea.

- **3) Ingreso a zonas sin Internet / 4) Venta en lugares sin Internet:**  
  Se emite con el CUFD vigente, almacenando las facturas para posterior envío.

- **5) Virus informático o falla de software:**  
  Se utilizan las **facturas por contingencia** autorizadas previamente o se emiten digitalmente en modo Portal Web.

- **6) Falla de infraestructura o hardware** y **7) Corte de suministro eléctrico:**  
  Si el sistema no es operativo, se deben emitir facturas manuales de contingencia preaprobadas, que posteriormente serán transcritas al sistema.

> “De producirse una contingencia, pero el sistema informático continúa operativo, éste deberá cambiar a la emisión de facturas fuera de línea ... En caso de que no pueda utilizarse el sistema informático ... se deberán emitir facturas manuales de contingencia previamente aprovisionadas.”  


### b. Registro del Evento Significativo

Antes de enviar las facturas almacenadas, es obligatorio:
- Obtener un nuevo CUFD.
- Registrar el evento significativo (indicando fecha/hora de inicio y fin, el código del evento, y el CUFD usado durante la contingencia).
- Esto evita inconvenientes relacionados con el tiempo de vigencia del CUFD y vincula las facturas emitidas durante la contingencia con el evento.

---

## 4. Proceso de Emisión y Envío de Facturas en Contingencia

El proceso se divide en dos etapas: **durante la contingencia** y **posterior a la recuperación de la comunicación**.

### Etapa 1: Emisión Durante la Contingencia

- **Emisión Individual:**  
  - Cada factura se genera en modo offline, creando su archivo XML.
  - Se firma digitalmente (si la modalidad lo requiere), se valida el XML contra el XSD y se almacena localmente.
  
- **Almacenamiento Local:**  
  - Todas las facturas emitidas se guardan individualmente para ser agrupadas en un paquete cuando se restablezca la conexión.

> “Se recurre a la emisión de Facturas fuera de línea ... las facturas se emiten individualmente y se agrupan en paquetes de hasta 500 documentos fiscales, para que luego de superada la contingencia se envíen a la Administración Tributaria.”  


### Etapa 2: Envío de Facturas Emitidas Durante la Contingencia

1. **Recuperación y Agrupación:**  
   - Recuperar los XML almacenados.
   - Formar paquetes de hasta **500 facturas** (o el tamaño definido según la modalidad; en emisión masiva pueden ser hasta 1000 facturas).

2. **Preparación del Paquete:**  
   - Comprimir el archivo XML agrupado en formato **Gzip**.
   - Calcular el **HASH (SHA256)** del archivo comprimido para enviarlo en la etiqueta `hashArchivo`.

3. **Obtención de Nuevo CUFD y Registro del Evento:**  
   - Antes de enviar los paquetes, se debe consumir el servicio para obtener un nuevo CUFD.
   - Registrar el evento significativo, indicando el periodo de contingencia y el CUFD usado durante la emisión offline.

4. **Envío del Paquete:**  
   - Consumir el servicio de **Recepción de Paquetes** para enviar el lote de facturas.
   - Verificar la respuesta:  
     - **Estado 901:** Paquete pendiente.  
     - **Estado 904:** Observado (se incluirán errores o advertencias).  
     - **Estado 908:** Validado.

5. **Validación Posterior:**  
   - Consumir el servicio de **Validación de Paquetes** para confirmar la recepción correcta de cada factura.
   - Mantener un registro de facturas sin código de respuesta para, posteriormente, consumir el servicio de verificación de estado y proceder a la anulación en caso necesario.

> “Una vez superada la contingencia ... recuperar las facturas almacenadas, formar paquetes, comprimir con Gzip, obtener el HASH y enviar los paquetes consumiendo el servicio ‘Recepción de Paquetes de facturas electrónicas o computarizadas’.”  


---

## 5. Procedimientos para Facturación Manual de Contingencia

Si la contingencia impide el uso del sistema informático (por falla de hardware, software o corte de energía), se debe recurrir a la **emisión manual de facturas de contingencia**:

1. **Emisión Manual Preaprobada:**  
   - Emitir facturas manuales utilizando talonarios previamente autorizados (con CAFC asignado).
  
2. **Transcripción de Facturas Manuales:**  
   - Una vez restaurada la operatividad, transcribir cada factura manual al sistema generando su XML.  
   - Utilizar el tipo de emisión "fuera de línea" (valor 2) y el CUFD que estaba vigente al momento de la contingencia.

3. **Procedimiento de Transcripción y Envío:**  
   - **Primera Etapa (Transcripción):**  
     - Generar, firmar y validar el XML de la factura manual.  
     - Almacenar de forma individual.
   - **Segunda Etapa (Armado de Paquetes):**  
     - Agrupar las facturas transcritas en paquetes de hasta 500 documentos.  
     - Comprimir, obtener el HASH y enviar mediante el servicio de recepción de paquetes, incluyendo el CAFC de las facturas transcritas.

> “En caso de que no pueda utilizarse el sistema informático por falla ... se deberán emitir facturas manuales de contingencia previamente aprovisionadas, superada la contingencia estas deberán ser transcritas utilizando para ello el CUFD que estaba vigente al ingresar en contingencia y enviadas a la Administración Tributaria.”  


---

## 6. Manejo de Errores en Emisión, Anulación y Obtención de CUFD

### a. Durante la Emisión de Facturas
- **Error en emisión:**  
  Si se produce un error (Time Out, -1, Java Null, HTTP 500) al emitir una factura, se debe:
  - Obtener un **nuevo CUFD**.
  - Verificar el estado de la factura a través del servicio de consulta correspondiente.
  - Si la factura figura registrada en el SIN, proceder a su anulación.
  - Registrar el evento significativo y, posteriormente, incluir la factura en el paquete de envío.

### b. En el Proceso de Anulación
- **Error en anulación:**  
  Ante respuestas erróneas al consumir el servicio de anulación, se recomienda:
  - Esperar un tiempo prudencial antes de reintentar.
  - Verificar el estado de la factura; si ya figura como anulada en el SIN, completar la anulación de forma local.  
  - En caso contrario, reintentar la anulación.

### c. Obtención del CUFD
- **Error al solicitar CUFD:**  
  Si al solicitar el CUFD se recibe error (Time Out, -1, etc.):
  - Ingresar a modo offline y continuar emitiendo facturas con el último CUFD válido, el cual se extiende hasta 72 horas.
  - Reintentar la solicitud después de un periodo prudencial (máximo dos horas).
  - Una vez exitosa, registrar el evento significativo y enviar los paquetes de facturas pendientes.

> “Si al consumir el servicio de solicitud de CUFD ... debemos ingresar a Fuera de Línea y emitir facturas utilizando el último CUFD válido.”  


---

## 7. Recomendaciones y Buenas Prácticas

- **Monitoreo y Verificación Constante:**  
  Implementar un sistema de monitoreo que verifique la comunicación con el SIN de forma periódica a través del servicio “Verifica Comunicación”. Esto permitirá detectar la necesidad de ingresar a modo contingencia de forma oportuna.

- **Registro Detallado de Operaciones:**  
  Mantener logs detallados de:
  - La emisión de cada factura.
  - Los eventos significativos (con fechas y CUFD utilizado).
  - Las respuestas de los servicios (recepción, validación, anulación).
  - Los casos de facturas sin código de respuesta, para su posterior verificación y anulación si fuera necesario.

- **Uso del Ambiente de Pruebas del SIN:**  
  Realizar pruebas en el entorno de piloto para simular escenarios de contingencia y validar el proceso de emisión, agrupación y envío masivo de facturas.

- **Capacitación y Procedimientos Internos:**  
  Capacitar al personal sobre la operación del sistema en contingencia, incluyendo la emisión manual y la transcripción posterior de las facturas emitidas en ese modo.

- **Documentación y Actualización Constante:**  
  Consultar periódicamente la documentación oficial del SIAT y los anexos técnicos para estar al tanto de actualizaciones normativas o técnicas que puedan afectar los procesos de contingencia y envío masivo.

> “Como buena práctica, debe mantenerse un registro de facturas sin código de respuesta, a objeto de que una vez superada la contingencia las mismas se verifiquen consumiendo el servicio verificaciónEstadoFactura ...”  


---

## 8. Resumen del Flujo de Trabajo

1. **Detección de falla:**  
   - Consumo de servicios (verificación, emisión, anulación) que arrojan errores → Ingreso a modo offline.

2. **Durante la contingencia:**  
   - Emisión individual de facturas en modo offline utilizando el último CUFD.
   - Almacenamiento local de los XML emitidos.


3. **Recuperación y regularización:**  
   - Recuperar la comunicación: obtener un nuevo CUFD.
   - Registrar el evento significativo (con fechas, CUFD y descripción).
   - Agrupar los XML almacenados en paquetes (hasta 500 o 1000 facturas, según el caso).
   - Comprimir, obtener hash y enviar los paquetes mediante el servicio “Recepción de Paquetes”.
   - Validar la recepción de cada factura y, en caso de error, gestionar la anulación o reenvío.

4. **Para facturación manual de contingencia:**  
   - Emisión manual con talonarios preaprobados (CAFC).
   - Transcribir al sistema una vez restablecida la operatividad y enviar en paquetes.

---

## Conclusión

La implementación de un sistema robusto para el manejo de contingencias en facturación electrónica requiere:
- Detectar rápidamente las fallas de comunicación.
- Alternar entre modos en línea y fuera de línea de forma transparente.
- Garantizar que, una vez restablecida la comunicación, todas las facturas emitidas durante la contingencia sean enviadas, registradas y validadas correctamente ante el SIN.

Integrar estos procesos siguiendo los lineamientos aquí descritos—apoyándose en los procedimientos detallados en los archivos de ingreso a contingencia, eventos significativos y emisión/envío de facturas—garantizará el cumplimiento normativo y la continuidad operativa del negocio en escenarios adversos.

---

Esta guía integra los conceptos teóricos y prácticos necesarios para una correcta implementación, brindando una referencia clara para el desarrollo y operación del sistema de facturación electrónica en situaciones de contingencia.
