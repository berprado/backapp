
**Flujo de Emisión de Factura Electrónica Online**

**Fase 1: Preparación y Recopilación de Datos (Interfaz de Usuario)**

1.  **Selección de Comandas:**
    *   Permitir al usuario seleccionar una o más "comandas" (representando productos/servicios vendidos) utilizando un componente `st.sidebar.multiselect`.

2.  **Ingreso y Gestión de Datos del Cliente:**
    *   Solicitar al usuario el "Número de Documento" del cliente.
    *   **Lógica de Cliente Existente/Nuevo:**
        *   Si el "Número de Documento" existe en la base de datos (BD) local:
            *   Cargar automáticamente los datos del cliente (Razón Social, Tipo de Documento, email, teléfono).
            *   Mostrar estos datos al usuario, preferiblemente en campos deshabilitados para edición.
        *   Si el "Número de Documento" no existe en la BD local:
            *   Permitir la selección del "Tipo de Documento".
            *   Permitir el ingreso de la "Razón Social".
            *   Permitir el ingreso opcional de "Complemento" (si aplica al tipo de documento), "Email" y "Teléfono".
            *   **Validación de NIT (Online):** Si el "Tipo de Documento" seleccionado es "NIT":
                *   Invocar la función `verificar_nit()` para consultar la validez del NIT contra el servicio del SIAT.
                *   Mostrar un mensaje de éxito o error de la validación en un placeholder designado (ej. `message_placeholder`).
            *   **Guardar Cliente Nuevo:**
                *   Habilitar un botón "Guardar Cliente".
                *   Al ser presionado, y si el NIT es válido (o no se requiere validación para otros tipos de documento), invocar la función `save_or_fetch_client_data()` para persistir los datos del nuevo cliente en la BD local.

3.  **Selección de Método de Pago:**
    *   Permitir al usuario seleccionar un "Tipo de Pago" desde un componente `st.sidebar.selectbox`.
    *   Poblar las opciones del selectbox invocando `fetch_metodos_pago()`.
    *   **Lógica Condicional por Método de Pago:**
        *   Si el método de pago seleccionado es "TARJETA":
            *   Solicitar al usuario el ingreso de los "últimos 4 dígitos de la tarjeta".
        *   Si el método de pago corresponde a un "Gift Card" (identificado según una lista predefinida, ej. `gift_card_codes`):
            *   Solicitar al usuario el "Monto Giftcard".

4.  **Aplicación de Descuentos Adicionales (Opcional):**
    *   Proveer una casilla de verificación "Aplicar Descuento".
    *   Si está marcada, permitir al usuario ingresar un valor para "Descuento Adicional".

5.  **Cálculos Preliminares de la Factura:**
    *   Invocar la función `calculate_totals()` para calcular: subtotal, descuento total (incluyendo descuento adicional), monto giftcard, total final, monto sujeto a IVA, etc. Estos cálculos se basan en las comandas seleccionadas, el descuento adicional, el monto giftcard y el método de pago.
    *   Invocar la función `collect_product_lines()` para recopilar y estructurar los detalles de cada producto/servicio de las comandas seleccionadas (ej. descripción, cantidad, precio unitario, subtotal por línea).

6.  **Previsualización de Factura en HTML:**
    *   Invocar la función `generate_html_invoice()` utilizando los datos recopilados y calculados para crear una representación HTML de la factura.
    *   Mostrar esta previsualización HTML en la interfaz de usuario (ej. en una pestaña "🧾Facturar") utilizando un componente como `components.html()`.

**Fase 2: Proceso de Generación y Envío al SIAT (Activado al presionar "Facturar")**

7.  **Validación de Entradas Requeridas:**
    *   Antes de proceder, verificar que todos los campos esenciales estén completos: método de pago, tipo de documento del cliente, número de documento del cliente, y que al menos una comanda haya sido seleccionada.
    *   Si alguna validación falla, mostrar un mensaje de error detallado en `message_placeholder` y detener el proceso.

8.  **Obtención de Número de Factura Secuencial:**
    *   Invocar la función `get_next_invoice_number()`. Esta función debe:
        *   Leer el último número de factura utilizado desde un archivo de persistencia (ej. `invoice_number.txt`).
        *   Incrementar este número en 1 para la factura actual.

9.  **Configuración y Recopilación de Datos del Emisor:**
    *   Obtener los datos fijos del emisor (NIT Emisor, Razón Social Emisor, Municipio, Teléfono, Código Sucursal, Código Punto de Venta, Dirección, etc.) desde variables de entorno utilizando `os.getenv()`.

10. **Verificación y Obtención de CUFD (Código Único de Facturación Diaria):**
    *   Invocar la función `verificar_y_obtener_cufd()`. Esta función debe:
        *   Consultar la BD local para un CUFD vigente para el punto de venta y sucursal.
        *   Si no existe un CUFD vigente o el existente ha expirado:
            *   Invocar la función `solicitar_cufd()` para obtener un nuevo CUFD del SIAT.
            *   Guardar el nuevo CUFD y su fecha de vigencia en la BD local.
            *   Si se renueva el CUFD, mostrar un mensaje informativo al usuario.

11. **Generación de CUF (Código Único de Factura):**
    *   Invocar la función `generate_cuf()` para calcular el CUF único para esta factura.
    *   Los parámetros para `generate_cuf()` incluyen: NIT emisor, fecha y hora de emisión (YYYYMMDDHHMMSSS), código sucursal, modalidad (ej. Electrónica en Línea), tipo de emisión (ej. Online), tipo de factura (ej. con Derecho a Crédito Fiscal), código de documento sector, número de factura, y código de punto de venta.

12. **Generación del XML de la Factura:**
    *   Invocar la función `generate_xml_invoice()` para construir el archivo XML de la factura electrónica.
    *   El XML debe contener:
        *   **Cabecera:** Datos del emisor, datos del cliente (obtenidos en Fase 1), número de factura, CUF, CUFD, fecha de emisión, montos totales (total, monto sujeto a IVA, descuentos, monto gift card), método de pago, etc.
        *   **Detalle:** Una sección por cada producto/servicio (obtenido de `collect_product_lines()`), incluyendo código de producto SIN, descripción, cantidad, unidad de medida, precio unitario, descuento específico de línea (si aplica), y subtotal de línea.
    *   La función `generate_xml_invoice()` también debe retornar los datos estructurados de la cabecera (`factura_cabecera_data`) y los detalles (`detalles_data`) para su posterior guardado en la BD.

13. **Firma Digital del XML:**
    *   Invocar la función `sign_xml()` para firmar digitalmente el XML generado.
    *   Esta función debe:
        *   Cargar la clave privada del emisor (ej. desde `private_key_ok.pem`) y el certificado digital (ej. desde `certificado_ok.pem`).
        *   Aplicar el estándar XMLDSig (XML Digital Signature):
            *   Canonicalizar el XML (transformación C14N).
            *   Calcular el hash (SHA-256) del XML canónico.
            *   Crear la estructura `<ds:Signature>` incluyendo `<ds:SignedInfo>`.
            *   Firmar el contenido de `<ds:SignedInfo>` utilizando la clave privada (algoritmo RSA-SHA256).
            *   Incrustar el valor de la firma (`<ds:SignatureValue>`) y el certificado X.509 (`<ds:X509Data>`) en el XML.
        *   El resultado es el string del XML firmado (`signed_xml_str`).

14. **Guardado Local del XML Firmado (para Referencia/Auditoría):**
    *   Guardar el `signed_xml_str` en un archivo local, típicamente en un directorio `xmls/`.
    *   El nombre del archivo debe ser único e informativo, incluyendo, por ejemplo, el número de factura y el CUF.

15. **Validación del XML contra Esquema XSD:**
    *   Invocar una función de validación (ej. `zeeper.validar_xml()`) para comprobar que el `signed_xml_str` cumple con la estructura definida por el esquema XSD proporcionado por el SIAT (ej. `facturaElectronicaCompraVenta.xsd`).

16. **Compresión del XML:**
    *   Invocar una función de compresión (ej. `zeeper.comprimir_xml()`) para comprimir el `signed_xml_str` en formato GZIP. El SIAT requiere el archivo en este formato para el envío.

17. **Cálculo del Hash del Archivo Comprimido:**
    *   Invocar una función de hashing (ej. `zeeper.obtener_hash()`) para calcular el hash SHA-256 del archivo GZIP resultante del paso anterior. Este hash también es requerido por el SIAT.

18. **Envío de la Factura al SIAT:**
    *   Invocar la función `zeeper.enviar_solicitud()` para realizar la petición SOAP al servicio web de "Recepción de Facturas" del SIAT.
    *   La solicitud debe incluir el archivo GZIP, su hash SHA-256, el CUFD, la fecha de envío, y otros parámetros necesarios según la especificación del servicio.

19. **Procesamiento de la Respuesta del SIAT:**
    *   Invocar la función `parse_siat_response()` para analizar la respuesta XML recibida del SIAT.
    *   Invocar la función `display_siat_response()` para interpretar los códigos y mensajes de la respuesta y mostrarlos al usuario en `message_placeholder`.
    *   **Lógica basada en la respuesta:**
        *   **Si la transacción es exitosa (Factura VALIDADA por SIAT, ej. código 908):**
            *   Establecer `st.session_state['factura_validada'] = True`.
            *   Guardar el CUF y el número de factura en `st.session_state` para referencia futura.
            *   Almacenar los datos necesarios para la impresión (ej. `factura_cabecera_data`, `detalles_data`, CUF, etc.) en `st.session_state['datos_impresion']`.
            *   **Guardado en Base de Datos Local:**
                *   Realizar validaciones internas de los datos con `validar_factura_cabecera(factura_cabecera_data)` y `validar_factura_detalle(detalle_data)`.
                *   Invocar `guardar_factura_cabecera(factura_cabecera_data)` para guardar los datos de la cabecera de la factura en la BD.
                *   Iterar sobre `detalles_data` e invocar `guardar_factura_detalle(detalle)` para cada línea de detalle.
            *   **Incremento del Número de Factura:** Invocar `increment_invoice_number()` para actualizar el archivo `invoice_number.txt` con el número de factura recién utilizado y validado.
        *   **Si la transacción falla o hay observaciones (Factura RECHAZADA u OBSERVADA por SIAT, ej. código 904):**
            *   Mostrar los mensajes de error o las observaciones del SIAT al usuario.
            *   La factura no se considera emitida correctamente. No se debe habilitar la impresión ni el guardado final como "VALIDADA". El número de factura no debería incrementarse o debería manejarse para reutilización/anulación lógica.

**Fase 3: Post-Emisión (Si la factura fue VALIDADA por SIAT)**

20. **Habilitación de Acciones Post-Facturación:**
    *   Si `st.session_state['factura_validada']` es `True`, habilitar los botones "Imprimir Factura" y el enlace "Consultar factura" en la interfaz de usuario.

21. **Impresión de Factura (Opcional, si el usuario presiona "Imprimir Factura"):**
    *   Invocar `generate_compact_html_invoice()` para generar una versión HTML de la factura, optimizada para la impresión (usando `st.session_state['datos_impresion']`).
    *   Invocar la función `imprimir_en_hilo()`. Esta función debe:
        *   Iniciar un nuevo hilo de ejecución para no bloquear la interfaz de usuario principal.
        *   Dentro del hilo:
            *   Invocar `html_to_pdf()` para convertir el HTML compacto a un archivo PDF.
            *   Guardar el archivo PDF en una carpeta designada (ej. pdfs).
            *   Invocar `ThermalPrinter().print_invoice()` para enviar los datos de la factura (posiblemente el HTML, el PDF o datos estructurados) a la impresora térmica configurada.
        *   Actualizar `st.session_state['print_status']` con el estado del proceso de impresión (ej. "Imprimiendo...", "Impreso", "Error de impresión").
    *   Invocar `monitorear_hilo_impresion()` para mostrar el progreso o estado de la impresión en la interfaz de usuario, basándose en `st.session_state['print_status']`.

22. **Consulta de Factura en Portal SIAT (Opcional):**
    *   Si se proporciona un enlace o botón "Consultar factura":
        *   Invocar `generate_invoice_link()` para crear una URL que permita al usuario consultar la factura directamente en el portal del SIAT (usualmente requiere parámetros como NIT emisor, número de factura, CUF).

**Flujo de Emisión de Factura Electrónica en Modo Offline (Contingencia)**

**Contexto Previo:**
*   El sistema ha detectado una pérdida de conexión con los servicios del SIAT.
*   Se ha registrado un "evento significativo" de inicio de contingencia, utilizando un **CUFD (Código Único de Facturación Diaria) que estaba vigente** en el momento de la desconexión. Este CUFD es crucial para las facturas emitidas durante este periodo.
*   El `tipoEmision` para todas las facturas generadas en este modo será `2` (Offline).

---

**Fase 1: Preparación y Recopilación de Datos (Interfaz de Usuario) - Similar al modo Online con ajustes**

1.  **Selección de Comandas:**
    *   El usuario selecciona una o más "comandas" desde un `st.sidebar.multiselect`.

2.  **Ingreso de Datos del Cliente:**
    *   El usuario ingresa el "Número de Documento" del cliente.
        *   Si el cliente existe en la BD local, sus datos se cargan.
        *   Si el cliente no existe:
            *   Se selecciona el "Tipo de Documento".
            *   Se ingresa la "Razón Social".
            *   Opcionalmente, "Complemento", "Email" y "Teléfono".
            *   **Importante (Offline):** La validación de NIT online (`verificar_nit()`) contra el SIAT **no se ejecuta** debido a la falta de conexión.
            *   El guardado del cliente nuevo (`save_or_fetch_client_data()`) opera sobre la BD local.

3.  **Selección de Método de Pago:**
    *   El usuario selecciona un "Tipo de Pago" (poblado desde `fetch_metodos_pago()`).
    *   Se manejan casos especiales como "TARJETA" o "Gift Card" de forma idéntica al modo online.

4.  **Aplicación de Descuentos Adicionales (Opcional):**
    *   Funciona igual que en el modo online.

5.  **Cálculos Preliminares:**
    *   `calculate_totals()`: Calcula totales.
    *   `collect_product_lines()`: Recopila detalles de productos/servicios.
    *   Estos funcionan igual que en el modo online.

6.  **Previsualización de Factura (HTML):**
    *   `generate_html_invoice()`: Crea la previsualización HTML.
    *   `components.html()`: Muestra la previsualización.
    *   Funciona igual que en el modo online.

---

**Fase 2: Proceso de Generación y Guardado Local (Al presionar "Facturar" en Modo OFFLINE)**

7.  **Validación de Entradas Requeridas:**
    *   El sistema verifica que los campos esenciales estén completos (igual que en online). Si no, muestra error en `message_placeholder`.

8.  **Obtención de Número de Factura Secuencial:**
    *   `get_next_invoice_number()`: Lee el último número de factura de `invoice_number.txt` y lo incrementa.
        *   *Consideración de Riesgo (según guía):* Asegurar la atomicidad de esta operación para evitar duplicados, especialmente si hay múltiples instancias o accesos.

9.  **Configuración y Datos del Emisor:**
    *   Se obtienen datos fijos del emisor desde variables de entorno (`os.getenv()`).

10. **Obtención de CUFD (Código Único de Facturación Diaria) para Contingencia:**
    *   **NO se invoca `verificar_y_obtener_cufd()` para solicitar un nuevo CUFD al SIAT.**
    *   Se debe utilizar el **CUFD que se registró al iniciar el evento de contingencia**. Este CUFD debe ser recuperado de la configuración o estado de la aplicación donde se almacenó al entrar en modo offline (ej. `get_cufd_contingencia_vigente()`).

11. **Generación de CUF (Código Único de Factura):**
    *   `generate_cuf()`: Calcula el CUF.
    *   Parámetros cruciales para el modo offline:
        *   `tipoEmision`: Debe ser `2` (Offline).
        *   El CUFD utilizado debe ser el del inicio de la contingencia.

12. **Generación del XML de la Factura:**
    *   `generate_xml_invoice()`: Construye el archivo XML.
    *   **Modificaciones específicas para Offline:**
        *   En la cabecera del XML, el campo `tipoEmision` debe ser `2`.
        *   **Obligación Normativa:** Si el "Tipo de Documento" del cliente es "NIT" (código `5` en el sistema SIAT), se debe incluir el campo `codigoExcepcion` con valor `1` en la cabecera del XML.
            *   Ejemplo de lógica a incorporar en `generate_xml_invoice()`:
                ````python
                // filepath: facturador/invoice_xml_generator.py
                // ...existing code...
                if tipo_emision == 2 and datos_cliente.get('tipo_documento_id') == '5': // Asumiendo '5' es NIT
                    cabecera_xml.update({'codigoExcepcion': 1})
                // ...existing code...
                ````
        *   Devuelve `factura_cabecera_data` y `detalles_data`.

13. **Firma Digital del XML:**
    *   `sign_xml()`: Firma el XML generado. Este proceso es idéntico al modo online (carga de claves, canonicalización, hash, firma, incrustación). El `signed_xml_str` es el resultado.

14. **Guardado Local del XML Firmado:**
    *   El `signed_xml_str` se guarda en un archivo en el directorio `xmls/` (o una subcarpeta designada para facturas pendientes/offline).
    *   El nombre del archivo debe ser único e informativo.

15. **Validación del XML contra Esquema XSD:**
    *   `zeeper.validar_xml()`: Comprueba que el XML firmado cumpla con el XSD (`facturaElectronicaCompraVenta.xsd`). Este paso es local y no requiere conexión.

16. **NO SE COMPRIME EL XML individualmente en este punto.** (La compresión GZIP se realizará al agrupar en paquetes para el envío masivo posterior).

17. **NO SE CALCULA EL HASH del XML individual para envío inmediato.** (El hash se calculará sobre el paquete comprimido).

18. **NO SE ENVÍA LA FACTURA AL SIAT en este punto.** (Las llamadas a `zeeper.enviar_solicitud()` se omiten).

19. **Procesamiento de Respuesta del SIAT y Guardado en Base de Datos Local:**
    *   **NO hay respuesta del SIAT** para procesar en este momento.
    *   **Guardado en Base de Datos Local con Estado "PENDIENTE":**
        *   `validar_factura_cabecera()` y `validar_factura_detalle()`: Se realizan validaciones internas.
        *   Al guardar la cabecera de la factura (`guardar_factura_cabecera()`), se debe incluir un campo de `estado_siat` (o similar) con el valor `"PENDIENTE"` o un código numérico que lo represente. El `codigoRecepcion` del SIAT estaría vacío.
        *   `guardar_factura_detalle()`: Guarda los detalles.
    *   **Incremento del Número de Factura:** `increment_invoice_number()` actualiza `invoice_number.txt`.
    *   Se muestra un mensaje al usuario indicando que la factura se ha generado en modo offline y está pendiente de envío al SIAT (ej. en `message_placeholder`).
    *   `st.session_state['factura_validada']` se establecería a `False` o un estado que indique "pendiente offline", para no habilitar la impresión como si fuera una factura ya validada por SIAT (a menos que se decida permitir una impresión provisional con leyenda de contingencia).

---

**Fase 3: Sincronización Post-Contingencia (Proceso Separado y Posterior)**

*   Esta fase **no se ejecuta inmediatamente** al presionar "Facturar" en modo offline, sino cuando se restablece la conexión y se inicia un proceso de envío de paquetes.
*   **Pasos generales de la sincronización (a implementar en un módulo como `paquetes_offline.py`):**
    1.  **Obtener Nuevo CUFD:** Al restablecer la conexión, obtener un nuevo CUFD para el punto de venta.
    2.  **Cerrar Evento de Contingencia:** Registrar el fin del evento de contingencia ante el SIAT, utilizando el CUFD con el que se inició la contingencia y el nuevo CUFD.
    3.  **Seleccionar Facturas Pendientes:** Consultar la BD local por facturas con estado "PENDIENTE" y `tipoEmision = 2`.
    4.  **Agrupar XMLs:** Agrupar los archivos XML firmados (guardados en el paso 14) en paquetes de hasta 500 facturas.
    5.  **Comprimir Paquete:** Comprimir cada paquete de XMLs en formato GZIP.
    6.  **Calcular Hash del Paquete:** Calcular el hash SHA-256 del archivo GZIP del paquete.
    7.  **Enviar Paquete al SIAT:** Utilizar el servicio web de "Recepción de Paquetes de Facturas" del SIAT, enviando el paquete GZIP, su hash, y el CUFD (el nuevo, obtenido tras restablecer conexión).
    8.  **Procesar Respuesta del Paquete:** El SIAT devolverá un código de recepción para el paquete.
    9.  **Verificar Estado de Facturas del Paquete:** Utilizar el servicio "Validación Recepción Paquete Factura" del SIAT para conocer el estado individual (VALIDADA, OBSERVADA, RECHAZADA) de cada factura dentro del paquete enviado.
    10. **Actualizar BD Local:** Actualizar el estado de cada factura en la BD local según la respuesta del SIAT.
    11. **Manejo de Errores y Reintentos:** Implementar lógica para manejar errores en el envío o validación de paquetes.
    12. **Verificación Adicional:** Para facturas sin código de respuesta claro, usar `verificacionEstadoFactura`.


**Diferencias Detalladas entre Flujo Online y Offline**

Aquí te presento una comparación paso a paso, resaltando dónde divergen los procesos:

| Característica/Paso                 | Flujo Online                                                                                                                               | Flujo Offline (Contingencia)                                                                                                                                                              |
| :---------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Fase 1: Preparación y Recopilación de Datos** |                                                                                                                            |                                                                                                                                                                                           |
| Validación de NIT del Cliente       | Se invoca `verificar_nit()` para consultar al SIAT en tiempo real. El guardado del cliente puede depender de esta validación.             | **NO se consulta al SIAT.** La validación de NIT online se omite. El cliente se guarda localmente sin esta verificación externa. Se podría marcar para validación posterior.                |
| **Fase 2: Proceso de Generación y Envío/Guardado (Al presionar "Facturar")** |                                                                                                                            |                                                                                                                                                                                           |
| 1. Obtención de CUFD                | Se invoca `verificar_y_obtener_cufd()`. Si el CUFD local no es vigente, se solicita uno **nuevo al SIAT** y se guarda.                     | **NO se solicita un nuevo CUFD al SIAT.** Se utiliza el CUFD que fue registrado y estaba vigente al **inicio del evento de contingencia**.                                                  |
| 2. Generación de CUF                | El parámetro `tipoEmision` en `generate_cuf()` es `1` (Online).                                                                            | El parámetro `tipoEmision` en `generate_cuf()` es `2` (Offline).                                                                                                                          |
| 3. Generación del XML               | El campo `tipoEmision` en el XML es `1`.                                                                                                   | El campo `tipoEmision` en el XML es `2`. **Obligatorio:** Si el tipo de documento del cliente es NIT, se debe incluir el campo `codigoExcepcion` con valor `1` en la cabecera del XML. |
| 4. Compresión del XML               | `zeeper.comprimir_xml()`: El XML individual firmado se comprime en GZIP.                                                                   | **NO se comprime el XML individualmente en este punto.** La compresión se hará por paquetes más adelante.                                                                                 |
| 5. Cálculo de Hash                  | `zeeper.obtener_hash()`: Se calcula el hash SHA-256 del archivo GZIP individual.                                                           | **NO se calcula el hash del XML individual en este punto.** El hash se calculará sobre el paquete comprimido.                                                                            |
| 6. Envío al SIAT                    | `zeeper.enviar_solicitud()`: El archivo GZIP individual y su hash se envían al servicio de "Recepción de Facturas" del SIAT.              | **NO se envía la factura individual al SIAT.**                                                                                                                                            |
| 7. Procesamiento Respuesta SIAT     | Se analiza la respuesta del SIAT (`parse_siat_response()`, `display_siat_response()`).                                                     | **NO hay respuesta inmediata del SIAT** ya que no hubo envío.                                                                                                                             |
| 8. Estado de la Factura             | Si es VALIDADA (ej. código 908): `st.session_state['factura_validada'] = True`. Se guarda en BD con el código de recepción del SIAT.        | La factura se guarda localmente en la BD con un estado como **"PENDIENTE"** o similar, indicando que no ha sido enviada ni validada por el SIAT. `codigoRecepcion` estaría vacío.        |
| 9. Incremento Nro. Factura        | `increment_invoice_number()` actualiza el contador tras la validación exitosa del SIAT.                                                    | `increment_invoice_number()` actualiza el contador tras el guardado local de la factura offline.                                                                                          |
| **Fase 3: Post-Emisión / Sincronización** |                                                                                                                            |                                                                                                                                                                                           |
| Habilitación de Acciones            | Si `factura_validada` es `True`, se habilitan "Imprimir Factura" y "Consultar factura".                                                    | La impresión podría habilitarse con una leyenda de "Factura en Contingencia - Pendiente de Envío" o estar deshabilitada hasta la sincronización. "Consultar factura" no aplicaría aún. |
| Impresión                           | Se puede imprimir la factura validada por el SIAT.                                                                                         | Si se permite, sería una impresión provisional. La impresión "oficial" con validez fiscal completa se daría tras la sincronización exitosa.                                             |
| Sincronización con SIAT             | No aplica, la factura ya fue procesada individualmente.                                                                                    | **Es la fase CRUCIAL y DIFERENTE.** Ocurre cuando se restablece la conexión:<ul><li>Se cierra el evento de contingencia ante el SIAT.</li><li>Las facturas "PENDIENTES" se agrupan en paquetes (hasta 500).</li><li>Cada paquete se comprime (GZIP) y se calcula su hash.</li><li>Los paquetes se envían al servicio de "Recepción de Paquetes de Facturas" del SIAT.</li><li>Se verifica el estado de cada factura del paquete.</li><li>Se actualiza el estado en la BD local (VALIDADA, OBSERVADA, RECHAZADA).</li></ul> |

**En resumen, las diferencias clave son:**

*   **Conectividad con SIAT:** Online interactúa constantemente; Offline opera localmente durante la contingencia.
*   **CUFD:** Online obtiene/valida al momento; Offline usa el CUFD del inicio de la contingencia.
*   **Tipo de Emisión:** `1` para Online, `2` para Offline (impacta CUF y XML).
*   **`codigoExcepcion`:** Obligatorio para NITs en Offline.
*   **Envío y Validación:** Online es individual e inmediato; Offline es por paquetes y diferido.
*   **Estado Inicial de Factura:** Online busca validación inmediata; Offline guarda como "PENDIENTE".
*   **Proceso Post-Contingencia:** Offline requiere una fase completa de sincronización de paquetes que no existe en el flujo online.

