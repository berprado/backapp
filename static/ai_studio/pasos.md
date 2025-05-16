Basado en el análisis del código `ui_copy.py`, aquí está el proceso paso a paso implementado para la emisión de una factura electrónica, enfocándonos en el flujo cuando el usuario presiona el botón "Facturar" en modo online:

**Fase 1: Preparación y Recopilación de Datos (Interfaz de Usuario)**

1.  **Selección de Comandas:**
    *   El usuario selecciona una o más "comandas" (que representan productos/servicios vendidos) desde un `st.sidebar.multiselect`.

2.  **Ingreso de Datos del Cliente:**
    *   El usuario ingresa el "Número de Documento" del cliente.
        *   Si el cliente existe en la BD local, sus datos (Razón Social, Tipo de Documento, email, teléfono) se cargan y se muestran (generalmente deshabilitados).
        *   Si el cliente no existe:
            *   Se selecciona el "Tipo de Documento".
            *   Se ingresa la "Razón Social".
            *   Opcionalmente, se ingresa "Complemento" (si aplica al tipo de documento), "Email" y "Teléfono".
            *   **Validación de NIT (Online):** Si el tipo de documento es "NIT", se llama a `verificar_nit()` para consultar al SIAT la validez del NIT. Un mensaje de éxito o error se muestra en `message_placeholder`.
            *   **Guardar Cliente Nuevo:** Si el NIT es válido (o no se requiere validación para otros tipos de documento), el usuario puede presionar "Guardar Cliente". Esto llama a `save_or_fetch_client_data()` para persistir el nuevo cliente en la BD.

3.  **Selección de Método de Pago:**
    *   El usuario selecciona un "Tipo de Pago" de un `st.sidebar.selectbox` (poblado desde `fetch_metodos_pago()`).
    *   Si el método de pago es "TARJETA", se solicita ingresar los "últimos 4 dígitos de la tarjeta".
    *   Si el método de pago corresponde a un "Gift Card" (según `gift_card_codes`), se solicita el "Monto Giftcard".

4.  **Aplicación de Descuentos Adicionales (Opcional):**
    *   Si la casilla "Aplicar Descuento" está marcada, el usuario ingresa un "Descuento Adicional".

5.  **Cálculos Preliminares:**
    *   `calculate_totals()`: Calcula el subtotal, descuento total, monto giftcard, total final, monto sujeto a IVA, etc., basándose en las comandas, descuento adicional, monto giftcard y método de pago.
    *   `collect_product_lines()`: Recopila los detalles de cada producto/servicio de las comandas seleccionadas, incluyendo descripción, cantidad, precio unitario, subtotal, etc.

6.  **Previsualización de Factura (HTML):**
    *   `generate_html_invoice()`: Crea una representación HTML de la factura con los datos recopilados.
    *   `components.html()`: Muestra esta previsualización en la pestaña "🧾Facturar".

**Fase 2: Proceso de Generación y Envío al SIAT (Al presionar "Facturar")**

7.  **Validación de Entradas Requeridas:**
    *   El sistema verifica que campos esenciales como método de pago, tipo de documento del cliente, número de documento y selección de comandas estén completos. Si no, muestra un error en `message_placeholder`.

8.  **Obtención de Número de Factura Secuencial:**
    *   `get_next_invoice_number()`: Lee el último número de factura de `invoice_number.txt` y lo incrementa en 1.

9.  **Configuración y Datos del Emisor:**
    *   Se obtienen datos fijos del emisor desde variables de entorno (`os.getenv()`): NIT Emisor, Razón Social Emisor, Municipio, Teléfono, Código Sucursal, Código Punto de Venta, Dirección, etc.

10. **Verificación y Obtención de CUFD (Código Único de Facturación Diaria):**
    *   `verificar_y_obtener_cufd()`:
        *   Consulta la BD local para un CUFD vigente.
        *   Si no hay uno vigente o ha expirado, llama a `solicitar_cufd()` para obtener uno nuevo del SIAT y lo guarda en la BD.
        *   Si se renueva, se muestra un mensaje informativo.

11. **Generación de CUF (Código Único de Factura):**
    *   `generate_cuf()`: Calcula el CUF único para esta factura utilizando: NIT emisor, fecha y hora de emisión, código sucursal, modalidad, tipo de emisión, tipo de factura, código de documento sector, número de factura, y código de punto de venta.

12. **Generación del XML de la Factura:**
    *   `generate_xml_invoice()`: Construye el archivo XML de la factura electrónica. Este XML contiene:
        *   **Cabecera:** Datos del emisor, datos del cliente, número de factura, CUF, CUFD, fecha de emisión, montos totales (total, sujeto a IVA, descuentos, gift card), método de pago, etc.
        *   **Detalle:** Una línea por cada producto/servicio con su código, descripción, cantidad, unidad de medida, precio unitario, descuento específico (si aplica), y subtotal.
        *   Esta función también devuelve `factura_cabecera_data` y `detalles_data` para guardarlos posteriormente en la BD.

13. **Firma Digital del XML:**
    *   `sign_xml()`:
        *   Carga la clave privada (`private_key_ok.pem`) y el certificado digital (`certificado_ok.pem`) del emisor.
        *   Aplica el estándar XMLDSig (XML Digital Signature):
            *   Canonicaliza el XML (C14N).
            *   Calcula el hash (SHA-256) del XML canónico.
            *   Crea la estructura `<ds:Signature>` con `<ds:SignedInfo>`.
            *   Firma el `<ds:SignedInfo>` con la clave privada (RSA-SHA256).
            *   Incrusta el valor de la firma y el certificado X.509 en el XML.
        *   El XML resultante (`signed_xml_str`) es el archivo firmado listo para ser enviado.

14. **Guardado Local del XML Firmado (Referencia/Auditoría):**
    *   El `signed_xml_str` se guarda en un archivo en el directorio `xmls/` con un nombre que incluye el número de factura y el CUF.

15. **Validación del XML contra Esquema XSD:**
    *   `zeeper.validar_xml()`: Comprueba que el XML firmado cumpla con la estructura definida por el esquema XSD proporcionado por el SIAT (`facturaElectronicaCompraVenta.xsd`).

16. **Compresión del XML:**
    *   `zeeper.comprimir_xml()`: Comprime el archivo XML firmado en formato GZIP. El SIAT requiere el archivo en este formato.

17. **Cálculo del Hash del Archivo Comprimido:**
    *   `zeeper.obtener_hash()`: Calcula el hash SHA-256 del archivo GZIP. Este hash también es requerido por el SIAT.

18. **Envío de la Factura al SIAT:**
    *   `zeeper.enviar_solicitud()`: Realiza la petición SOAP al servicio web de "Recepción de Facturas" del SIAT. Envía el archivo GZIP, su hash, el CUFD, la fecha de envío y otros parámetros necesarios.

19. **Procesamiento de la Respuesta del SIAT:**
    *   `parse_siat_response()`: Analiza la respuesta XML recibida del SIAT.
    *   `display_siat_response()`: Interpreta los códigos y mensajes de la respuesta y los muestra al usuario en `message_placeholder`.
        *   **Si la transacción es exitosa (Factura VALIDADA por SIAT):**
            *   El estado `st.session_state['factura_validada']` se establece a `True`.
            *   El CUF y el número de factura se guardan en `st.session_state`.
            *   Los datos necesarios para la impresión se almacenan en `st.session_state['datos_impresion']`.
            *   **Guardado en Base de Datos Local:**
                *   `validar_factura_cabecera()` y `validar_factura_detalle()`: Se realizan validaciones internas de los datos.
                *   `guardar_factura_cabecera()`: Guarda los datos de la cabecera de la factura en la BD.
                *   `guardar_factura_detalle()`: Guarda cada línea de detalle de la factura en la BD.
            *   **Incremento del Número de Factura:** `increment_invoice_number()` actualiza `invoice_number.txt` con el número de factura recién utilizado.
        *   **Si la transacción falla o hay observaciones (Factura RECHAZADA u OBSERVADA por SIAT):**
            *   Se muestran los mensajes de error o las observaciones del SIAT al usuario. La factura no se considera emitida correctamente y no se suele habilitar la impresión ni el guardado final como "VALIDADA".

**Fase 3: Post-Emisión (Si la factura fue VALIDADA)**

20. **Habilitación de Acciones Post-Facturación:**
    *   Se habilitan los botones "Imprimir Factura" y el enlace "Consultar factura".

21. **Impresión (Opcional, si el usuario presiona "Imprimir Factura"):**
    *   `generate_compact_html_invoice()`: Genera una versión HTML optimizada para la impresión.
    *   `imprimir_en_hilo()`:
        *   Inicia un nuevo hilo para no bloquear la UI.
        *   `html_to_pdf()`: Convierte el HTML a un archivo PDF y lo guarda en la carpeta `pdfs/`.
        *   `ThermalPrinter().print_invoice()`: Envía los datos (posiblemente el HTML o datos estructurados) a la impresora térmica.
        *   Se actualiza `st.session_state['print_status']` con el estado de la impresión.
    *   `monitorear_hilo_impresion()`: Muestra el progreso de la impresión en la UI.

22. **Consulta de Factura (Opcional):**
    *   `generate_invoice_link()`: Crea un URL para consultar la factura directamente en el portal del SIAT.

Este es el flujo detallado para la emisión de una factura online. El modo offline seguiría muchos de los pasos iniciales de generación y firma, pero en lugar de enviar al SIAT (pasos 18-19), guardaría la factura localmente con un estado "PENDIENTE" para su posterior envío cuando la conectividad se restablezca.