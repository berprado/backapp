# INstrucciones para la correcta implementacion de la Emisión y Envío de Facturas Digitales

La documentación que se presenta a continuación tiene como propósito brindarte el contexto necesario sobre el proceso de **emisión y envío de Facturas Digitales en Bolivia**, conforme a la normativa del Servicio de Impuestos Nacionales (SIN).

Debes utilizar esta información para **completar, corregir, optimizar o refactorizar** el código fuente del sistema, asegurando que cumpla con las especificaciones técnicas y los pasos definidos por el SIN, tanto para la **modalidad en línea como fuera de línea**, incluyendo casos de **contingencia**.

Es fundamental seguir las instrucciones descritas aquí para garantizar una implementación correcta y normativa de todos los procesos involucrados.

> Responde siempre en español.  
> Si generas comandos que se deben aprobar para ser ejecutados en la terminal, no uses operadores como `&&` ni sintaxis propia de Bash o CMD. Asegúrate de que el comando esté formateado para PowerShell, ya que es el entorno que estamos utilizando.  
> ⚠️ **Importante:** Para evitar errores por tiempo de espera durante la ejecución, divide cualquier implementación, revisión o refactorización en **bloques funcionales pequeños y modulares**. Esta práctica es especialmente crítica para:  
> - Funciones extensas o encadenadas.  
> - Procesos que involucran acceso a servicios externos.  
> - Cargas de trabajo masivas (como validación o envío de múltiples facturas).  
> Aplica principios de separación de responsabilidades, reutilización de lógica y diseño testeable para cada bloque de código.  
> Antes de implementar una solución nueva, busca en la base de código si ya existe una función relacionada.  
> Si encuentras una función que cumple con el propósito, **utilízala en lugar de crear una nueva**.  
> Si se requiere una nueva implementación, asegúrate de que sea **modular y testeable**.  
> Responde a todas las preguntas como si fueras un colega, con un tono cercano y sin usar lenguaje demasiado formal.  
> ⚠️ **Importante:** Asegúrate de documentar cualquier cambio realizado en el código para facilitar futuras revisiones.  
> ⚠️ **Nota:** Recuerda revisar la documentación existente antes de realizar cambios significativos.

# Emisión y Envío de Facturas

La emisión y envío de Facturas Digitales puede realizarse de manera:

* Individual (en tiempo real, interactuando **en línea** con el SIN)
* Por paquetes (en modo fuera de línea)
* De forma masiva

Los pasos a seguir en cada caso se describen a continuación.

---

## Consideraciones antes de la Emisión

1. **Obtener Token Delegado**, a través del Portal SIAT, para consumir los servicios requeridos.
2. **Obtener el CUIS** (Código Único de Inicio de Sistemas) mediante el servicio web correspondiente (solo una vez al inicio o al vencer).
3. **Obtener el CUFD** (Código Único de Facturación Diario), **de forma diaria**, mediante el servicio web correspondiente.
4. **Sincronización de catálogos** (actividades, sectores, productos, fecha y hora, documento sector) **diariamente**, usando los servicios web correspondientes.

> **Nota:**
> Si un contribuyente tiene varias sucursales y/o puntos de venta:
>
> * Si el despliegue es **centralizado**, la sincronización puede hacerse solo en la Casa Matriz.
> * Si no, deberá hacerse por cada sucursal y/o punto de venta.

> **Recomendación:**
> Consumir periódicamente el servicio `Verifica Comunicación`.
> Si se recibe un código de error (`Falso`, `-1`, o códigos 400/500), el sistema debe entrar automáticamente en modo **fuera de línea**.

---

## Emisión y Envío Individual de facturas

1. Generar archivo XML del Documento Fiscal según la actividad económica.
2. Firmar el archivo conforme al estándar **XMLDSig** (solo para modalidad Electrónica en Línea).
3. Validar contra el **XSD** asociado.
4. Comprimir el archivo XML en formato **Gzip** (etiqueta: `archivo`).
5. Obtener el **HASH (SHA-256)** del archivo comprimido (etiqueta: `hashArchivo`).
6. Enviar individualmente mediante el servicio **Recepción de Factura**.

   * **Estado 908**: Validado
   * **Estado 904**: Observado (incluye código de recepción, lista de errores/advertencias, y transacción con valor `True` o `False`)

---

## Emisión y Envío de Paquetes por Fuera de Línea

### Primera Etapa (Durante la contingencia)

1. Registrar internamente el evento y su motivo.
2. Generar archivo XML con modalidad **fuera de línea**.
3. Firmar y validar el archivo como en emisión individual.
4. Almacenar las facturas generadas.

### Segunda Etapa (Post-contingencia)

1. Recuperar las facturas XML almacenadas.
2. Formar paquetes de **hasta 500 facturas**.
3. Comprimir en Gzip (etiqueta: `archivo`).
4. Obtener HASH (SHA-256) (etiqueta: `hashArchivo`).
5. Enviar los paquetes:

   * Obtener nuevo **CUFD**.
   * Registrar evento significativo (fecha inicio/fin, CUFD usado).
   * Enviar paquetes usando servicio **Recepción de Paquetes**.
   * Validar recepción usando **Validación de Paquetes**:

     * **Estado 901**: Pendiente
     * **Estado 904**: Observada
     * **Estado 908**: Validado

> **Nota:**
> Mantener un registro de facturas sin código de respuesta.
> Superada la contingencia, usar `verificaciónEstadoFactura` para verificar su existencia en el SIN y anular si corresponde.

---

## Emisión y Envío de Paquetes por Contingencia

Utilizado cuando el sistema no está disponible por eventos como:

* Corte de energía
* Falla de software/hardware

Se recurre a **Facturas Manuales de Contingencia** (previamente autorizadas e impresas).

### 0. Registro del Evento

Registrar el evento indicando:

* Fecha de inicio y fin (hasta el minuto)
* Código de evento (5 = VIRUS INFORMÁTICO O FALLA DE SOFTWARE, 6 = CAMBIO DE INFRAESTRUCTURA DE SISTEMA O FALLA DE HARDWARE o 7 = CORTE DE SUMINISTRO DE ENERGIA ELÉCTRICA)
* CUFD del evento
* CUFD del envío
* Descripción del evento

### 1. Primera Etapa (Transcripción)

1. Transcribir la información a archivo XML, tipo de emisión **"fuera de línea" (2)**, usando el CUFD vigente al momento del evento.
2. Firmar, validar y almacenar temporalmente.

### 2. Segunda Etapa (Armado de Paquetes)

1. Recuperar facturas transcritas en XML.
2. Formar paquetes de hasta **500 facturas**.
3. Comprimir en Gzip (etiqueta: `archivo`).
4. Obtener HASH (SHA-256) (etiqueta: `hashArchivo`).
5. Enviar paquetes:

   * Obtener nuevo **CUFD**
   * Enviar usando **Recepción de Paquetes** (incluir código de recepción del evento y CAFC)
   * Validar con **Validación de Paquetes**

---

## Notas Finales

* En **ambiente de pruebas (PILOTO)**, solicitar **CAFC** para documentos y sucursales involucradas.

* Códigos Especiales:

  * **99001**: Consulados, embajadas, etc.
  * **99002**: Control Tributario
  * **99003**: Ventas Menores del Día

  Se deben enviar con:

  * Tipo de documento: **NIT**
  * Código de Excepción: **1**

* Si se usa tipo de documento **C.I. o NIT**, el sistema debe validar que el valor sea **numérico**.

* **Código de Excepción**:

  * Por defecto: **0**
  * Si tipo de documento es **NIT** y se quiere evitar validación: **1**
  * Para emisión fuera de línea con tipo **NIT**: **1**

* El tipo de emisión "CONTINGENCIA" es de uso exclusivo del **SIN**.