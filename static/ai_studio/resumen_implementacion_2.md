Perfecto. Con estos nuevos archivos, especialmente `invoice_xml_generator.py`, `zeeper.py` y `data_access.py`, podemos refinar significativamente el entendimiento del flujo de facturación, tanto online como offline.

**Análisis de los Nuevos Archivos Adjuntos (Continuación):**

7.  **`invoice_xml_generator.py`:**
    *   **Propósito:** Es el responsable exclusivo de generar el string XML de la factura electrónica, cumpliendo con el formato y los campos requeridos por el SIAT.
    *   **`generate_xml_invoice(...)`:**
        *   Recibe una gran cantidad de parámetros que representan todos los datos necesarios para la cabecera y el detalle de la factura.
        *   **Manejo de `xsi:nil`:** Correctamente maneja campos opcionales (nillable) como `telefono`, `codigoPuntoVenta`, `nombreRazonSocial`, `complemento`, `numeroTarjeta`, `montoGiftCard`, `descuentoAdicional`, `codigoExcepcion`, `cafc`, `montoDescuento` (en detalle), `numeroSerie`, `numeroImei`. Si el valor es `None` o no se proporciona, añade el atributo `xsi:nil="true"`.
        *   **Formato de Fechas:** Utiliza `validate_and_format_datetime()` para asegurar que `fechaEmision` esté en el formato `YYYY-MM-DDTHH:MM:SS.sss`.
        *   **Leyenda:** Obtiene una leyenda aleatoria desde `data_access.fetch_random_leyenda()`.
        *   **Unidad de Medida:** Mapea la descripción de la unidad de medida (ej: "Unid") a su código numérico correspondiente (`UNIDAD_MEDIDA_MAP`).
        *   **Cálculos y Formateo de Montos:** Formatea los montos numéricos a dos decimales. Calcula `montoTotalSujetoIva` restando `montoGiftCard` del `total`. Calcula `montoTotalMoneda`.
        *   **`codigoExcepcion`:** Lo establece a "1" si `tipo_emision == 2` (offline) y el tipo de documento es NIT (código 5), o si una variable global `excepcion_nit` está activa (lo que permitiría forzar la excepción manualmente). Esto es clave para el modo offline.
        *   **`cafc`:** Siempre se establece como `xsi:nil="true"` ya que el CAFC se usa para facturación manual o por contingencia con autorización previa, no para este flujo de facturación electrónica offline.
        *   **Datos para BD:** Prepara dos diccionarios, `cabecera_data` y `detalles_data`, que contienen los datos de la factura en un formato adecuado para ser guardados en la base de datos por `data_access.py`.
        *   **Manejo de Contingencia en `cabecera_data`:** Si `tipo_emision == 2` y se proporciona `evento_significativo`, añade `codigoEvento`, `descripcionEvento`, `fechaInicioEvento` y `estadoContingencia` a `cabecera_data`. Esto es crucial para asociar la factura offline al evento correcto en la BD.
        *   **Retorno:** Devuelve el string XML generado, y los diccionarios `cabecera_data` y `detalles_data`.
    *   **Logging:** Usa un logger específico para XML.

8.  **`zeeper.py`:**
    *   **Propósito:** Encapsula la lógica para la validación, compresión y envío de la factura al SIAT (específicamente para el servicio de recepción de facturas individuales en línea).
    *   **`validar_xml(xml_path, xsd_main_path)`:**
        *   Usa la librería `xmlschema` para validar un archivo XML contra el XSD principal (`facturaElectronicaCompraVenta.xsd`).
    *   **`comprimir_xml(xml_path)`:**
        *   Comprime el archivo XML en formato Gzip (`.gz`). Normaliza los saltos de línea antes de comprimir.
    *   **`obtener_hash(gzip_path)`:**
        *   Calcula el hash SHA-256 del archivo Gzip.
    *   **`construir_cuerpo_soap(...)`:**
        *   Crea el payload XML para la solicitud SOAP del servicio `recepcionFactura`. Incluye todos los parámetros requeridos por el SIAT (códigos de ambiente, sistema, sucursal, CUFD, CUIS, NIT, archivo Gzip en Base64, fecha de envío, hash del archivo).
    *   **`enviar_solicitud(xml_path, xsd_main_path, fecha_envio, cufd)`:**
        *   Orquesta el proceso de envío:
            1.  Valida el XML.
            2.  Comprime el XML.
            3.  Calcula el hash del Gzip.
            4.  Codifica el Gzip a Base64.
            5.  Construye el cuerpo SOAP.
            6.  Realiza la petición POST al endpoint del SIAT (`ServicioFacturacionCompraVenta`).
            7.  Incluye la `apikey` en las cabeceras.
            8.  **Implementa reintentos:** Intenta la solicitud hasta 3 veces con un retraso si ocurre un `requests.exceptions.Timeout`.
        *   Devuelve el objeto `response` de la librería `requests` o un diccionario con un error.
    *   **Logging:** Usa loggers para información general y específica de XML.

9.  **`data_access.py`:**
    *   **Propósito:** Es la capa de abstracción para todas las interacciones con la base de datos, utilizando SQLAlchemy ORM.
    *   **Conexión y Sesión:** Usa `SessionLocal` y `engine` definidos en `database.py`.
    *   **`fetch_comandas()`:**
        *   Intenta obtener comandas desde un `ENDPOINT_URL`.
        *   **Mecanismo de Caché de Archivo:** Si la petición al servidor falla, intenta cargar las comandas desde un archivo JSON local (`cache/comandas_cache.json`). Verifica la antigüedad del caché (24 horas).
        *   Usa `@st.cache_resource`, lo que significa que Streamlit gestionará el caché de esta función en memoria, pero también tiene su propio sistema de caché de archivo.
    *   **`fetch_metodos_pago()`, `fetch_tipos_documento()`, `obtener_motivos_anulacion()`:**
        *   Obtienen datos paramétricos desde las tablas de sincronización correspondientes (`SincronizarParametrica...`).
        *   Usan `@st.cache_data` para el caching de Streamlit.
    *   **`fetch_cliente(numero_documento)`:** Obtiene un cliente por su `codigo_cliente`.
    *   **`fetch_random_leyenda()`:** Obtiene una leyenda aleatoria de la tabla `SincronizarListaLeyendasFactura` filtrada por `codigoActividad` y una lista predefinida de IDs. Usa `@st.cache_data`.
    *   **`guardar_factura_cabecera(cabecera)`:**
        *   Recibe el diccionario `cabecera_data` de `invoice_xml_generator.py`.
        *   Inserta una nueva fila en la tabla `FacturaCabecera` usando SQLAlchemy ORM.
        *   Maneja explícitamente los campos de contingencia (`tipoEmision`, `codigoEvento`, etc.) si están presentes en `cabecera_data`.
        *   **Invalidación de Caché:** Si `USE_CACHE_MANAGER` es `True`, llama a `utils.cache_manager.invalidate_cache('facturas')` después de guardar, para que las listas de facturas se refresquen.
    *   **`guardar_factura_detalle(detalle)`:**
        *   Recibe un diccionario de la lista `detalles_data` de `invoice_xml_generator.py`.
        *   Inserta una nueva fila en la tabla `FacturaDetalle`.
    *   **`obtener_nombre_unidad_medida()`, `obtener_codigo_unidad_medida_sin()`:** Obtienen información de la tabla `ProductoSiat`.
    *   **`solicitar_cuis()`, `insertar_cuis_manual()`:** Manejan la obtención y guardado de CUIS. `solicitar_cuis` interactúa con el servicio SOAP del SIAT (usando `zeep.Client`).
    *   **`obtener_mensaje_por_codigo()`:** Obtiene descripciones de la tabla `SincronizarListaMensajesServicios`.
    *   **`obtener_cufd_vigente()`:** Obtiene el CUFD vigente de la tabla `Cufd`.
    *   **`obtener_cuf_por_numero_factura()`:** Obtiene el CUF y el objeto factura por número de factura.
    *   **`obtener_facturas_por_estado(estado=None, page=1, per_page=10)`:**
        *   Obtiene facturas paginadas, filtradas por estado (`PENDIENTE`, `VALIDADA`, `ANULADA`, o todas).
        *   Usa `@st.cache_data(ttl=60)` para cachear los resultados por 60 segundos.
    *   **`obtener_factura_completa(numero_factura)`:** Obtiene la cabecera y todos sus detalles.
    *   **Logging:** Usa el logger general.

**Funcionamiento Detallado del Sistema (Refinado con Nuevos Módulos):**

Refinemos el flujo, especialmente en la generación y envío online, y el manejo de datos para el modo offline:

**Fase 0: Arranque de la Aplicación (`main.py`)**
*   (Sin cambios respecto al análisis anterior, pero ahora sabemos que `database.py` configura las conexiones y `logger_config.py` los logs desde el inicio).

**Fase 1: Interfaz de Usuario y Facturación (`ui_copy.py`)**

*   **Al presionar "Facturar":**
    1.  **Validaciones y Recopilación de Datos:** (Como antes).
    2.  **Obtención Número Factura:** (Como antes).
    3.  **Configuración Emisor:** (Como antes).
    4.  **CUFD (Online):** `verificar_y_obtener_cufd()` (en `ui_copy.py`) se encarga de esto. Si necesita uno nuevo, llamará a `cufd.solicitar_cufd()` (no visible, pero es la función que interactuaría con `soap_services` para el CUFD y lo guardaría en BD vía `data_access`).
    5.  **Generación CUF:** `generate_cuf.generate_cuf()`.
    6.  **Generación del XML (`invoice_xml_generator.py`):**
        *   Se llama a `invoice_xml_generator.generate_xml_invoice()` pasándole todos los datos recolectados, incluyendo `tipo_emision` y `evento_significativo` (si es offline).
        *   **Si es Online (`tipo_emision=1`):** `codigoExcepcion` probablemente será `nil`.
        *   **Si es Offline (`tipo_emision=2`):**
            *   `codigoExcepcion` se establecerá a "1" si el documento es NIT.
            *   `cabecera_data` incluirá los campos del `evento_significativo` (`codigoEvento`, etc.).
        *   Esta función devuelve `xml_string`, `cabecera_data`, `detalles_data`.
    7.  **Firma Digital del XML (`ui_copy.py` -> `sign_xml`):**
        *   El `xml_string` devuelto por el generador se pasa a `sign_xml()`.
        *   Se obtiene `signed_xml_str`.
    8.  **Guardado Local del XML Firmado (`ui_copy.py`):**
        *   **Si es Online:** Se guarda en `xmls/factura_<num>_<cuf>_.xml`.
        *   **Si es Offline:** Se debería guardar en `offline/offline_<id_evento>_<num>_<cuf>_.xml` (esta lógica de guardado con prefijo "offline" y ID de evento debe estar en `ui_copy.py` o en una función que llame para ser consistente con `contingencia_auto.py`).

    *   **Flujo Específico para MODO ONLINE:**
        9.  **Validación XSD, Compresión, Hash, Envío (`zeeper.py`):**
            *   `ui_copy.py` llama a `zeeper.enviar_solicitud()` pasándole la ruta del XML firmado, la ruta del XSD, la `fecha_emision_str` y el `cufd` vigente.
            *   `zeeper.enviar_solicitud()` internamente llama a:
                *   `zeeper.validar_xml()`
                *   `zeeper.comprimir_xml()`
                *   `zeeper.obtener_hash()`
                *   Construye el SOAP y hace el POST al SIAT, con reintentos.
        10. **Procesamiento Respuesta SIAT (`ui_copy.py` -> `facturador.response_handler`):**
            *   Si `zeeper.enviar_solicitud()` devuelve una respuesta exitosa del SIAT:
                *   Se parsea la respuesta.
                *   `cabecera_data` se actualiza con el `resultadoValidacion` (ej: "VALIDADA") y `codigoRecepcion` del SIAT.
        11. **Guardado en Base de Datos (`data_access.py`):**
            *   `ui_copy.py` llama a `data_access.guardar_factura_cabecera(cabecera_data)`.
            *   Luego itera sobre `detalles_data` y llama a `data_access.guardar_factura_detalle(detalle)` para cada uno.
            *   `data_access.guardar_factura_cabecera()` invalida el caché de `obtener_facturas_por_estado`.
        12. **Incremento Número Factura:** (Como antes).
        13. **Habilitar Impresión/Consulta:** (Como antes).

    *   **Flujo Específico para MODO OFFLINE (`tipo_emision=2`):**
        9.  **(Opcional pero recomendado) Validación XSD Local:** `ui_copy.py` podría llamar a `zeeper.validar_xml()` para el XML offline antes de guardarlo.
        10. **Guardado en Base de Datos (`data_access.py`):**
            *   `ui_copy.py` llama a `data_access.guardar_factura_cabecera(cabecera_data)`. `cabecera_data` ya tiene `tipoEmision=2` y los datos del evento. El `resultadoValidacion` estaría vacío o "PENDIENTE".
            *   Luego itera sobre `detalles_data` y llama a `data_access.guardar_factura_detalle(detalle)`.
        11. **Incremento Número Factura:** (Como antes).
        12. **Habilitar Impresión:** (Como antes). No hay "Consulta factura" en SIAT aún.

**Fase 2: Visualización y Gestión de Facturas (`ui_copy.py` - Pestaña "Ver Facturas")**
*   Usa `data_access.obtener_facturas_por_estado()` que ahora sabemos que tiene un caché de 60 segundos y es invalidado por `guardar_factura_cabecera`.
*   Usa `data_access.obtener_factura_completa()` para los detalles.

**Fase 3: Gestión de Contingencias (Manual - `contingencia_auto.py`)**
*   **Proceso de Finalización Manual:**
    1.  (Como antes) Verifica conexión (`soap_services`), obtiene evento (`database`), obtiene CUFD actual (`database`).
    2.  Llama a `soap_services.enviar_evento_significativo()` para notificar al SIAT.
    3.  Si es exitoso, actualiza BD (`database.actualizar_evento_final()`).
    4.  **Compresión de Facturas Offline:**
        *   Busca en `offline/` los XML con el patrón `offline_<id_evento>_...xml` o `factura_offline_<id_evento>_...xml`. Esto confirma que los XML offline *deben* guardarse con este prefijo y el ID del evento.
        *   Los comprime en `offline_archivos/<id_evento>_<codigo_recepcion>.zip`.

**Conclusiones Adicionales con los Nuevos Módulos:**

*   **Generación de XML Detallada:** `invoice_xml_generator.py` es muy completo en cuanto a los campos del XSD de CompraVenta y el manejo de opcionales. Su preparación de `cabecera_data` y `detalles_data` es clave para la persistencia.
*   **Flujo Online Claro:** `zeeper.py` define claramente los pasos para el envío de una factura individual online.
*   **Capa de Acceso a Datos Robusta:** `data_access.py` maneja bien la interacción con la BD usando ORM, implementa caching de Streamlit y tiene su propio caché de archivo para las comandas. La invalidación de caché al guardar facturas es una buena práctica.
*   **Consistencia en Modo Offline:** La clave es que `invoice_xml_generator.py` genere el XML correctamente para offline (tipoEmision, codigoExcepcion) y que `ui_copy.py` guarde los archivos XML en la carpeta `offline/` con el formato de nombre esperado por `contingencia_auto.py`. Además, `cabecera_data` debe llevar la información del evento para que `data_access.guardar_factura_cabecera` lo persista correctamente.

El sistema está bien estructurado y cubre la mayoría de los aspectos críticos de la facturación electrónica, incluyendo un manejo de contingencias bastante desarrollado, aunque la parte de envío y validación de paquetes offline aún no está visible.