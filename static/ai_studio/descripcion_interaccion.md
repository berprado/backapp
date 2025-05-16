Este script Python (`ui_copy.py`) es el corazón de una aplicación de facturación electrónica construida con Streamlit, diseñada para interactuar con el sistema de impuestos de Bolivia (SIAT). A continuación, se detalla su estructura y funcionalidades:

**I. Propósito General:**

La aplicación permite a los usuarios:
1.  Generar facturas electrónicas cumpliendo con los requisitos del SIAT.
2.  Gestionar datos de clientes.
3.  Consultar, verificar y anular facturas emitidas.
4.  Manejar códigos CUIS y CUFD (necesarios para la facturación electrónica en Bolivia).
5.  Imprimir facturas en formato PDF y en impresoras térmicas.
6.  Operar en modo online (conectado al SIAT) y en modo offline/contingencia.

**II. Tecnologías y Librerías Clave:**

*   **Streamlit:** Para la interfaz de usuario web interactiva.
*   **SQLAlchemy:** ORM para la interacción con la base de datos (presumiblemente MySQL o similar, según `database.py` y `facturador.models`).
*   **Zeep:** Para la comunicación con servicios web SOAP del SIAT.
*   **Requests:** Para realizar peticiones HTTP.
*   **LXML y xml.etree.ElementTree:** Para la generación, manipulación y validación de archivos XML de facturas.
*   **Cryptography:** Para la firma digital de los XML con claves RSA y certificados X.509.
*   **Dotenv:** Para cargar variables de entorno (configuraciones sensibles como API keys, URLs de WSDL, datos del emisor).
*   **Num2words:** Para convertir números a palabras (literal del monto total).
*   **Threading:** Para operaciones de larga duración como la impresión, evitando bloquear la UI.
*   **Módulos Propios:** Una gran cantidad de módulos personalizados que encapsulan la lógica de negocio, acceso a datos, generación de códigos, interacción con SIAT, etc. (ej: `data_access`, `business_logic`, `invoice_xml_generator`, `generate_cuf`, `cufd`, `zeeper`, `thermal_printer`, `siat_pdf`, `logger_config`, `contingency_manager`).

**III. Estructura del Código y Componentes Principales:**

1.  **Importaciones:**
    *   Librerías estándar de Python.
    *   Librerías de terceros.
    *   Módulos propios del proyecto, cruciales para la funcionalidad.

2.  **Configuración Inicial:**
    *   **Paths:** Añade el directorio padre al `sys.path` para importaciones.
    *   **Loggers:** Configura múltiples loggers (`logger`, `printer_logger`, `facturacion_logger`, `xml_logger`) para diferentes partes de la aplicación, usando `logger_config`.
    *   **`gift_card_codes`:** Lista de códigos de método de pago que se consideran "gift card".
    *   **Directorio `pdfs`:** Crea el directorio si no existe y verifica permisos de escritura.
    *   **Variables de Entorno:** Carga variables desde un archivo `.env`.
    *   **Conectividad y Cliente SOAP:**
        *   Utiliza `contingency_manager.check_connectivity()` para verificar la conexión a internet y al servidor del SIAT.
        *   Inicializa el cliente SOAP (`zeep.Client`) solo si hay conectividad. Las funciones que dependen de este cliente (como `verificar_nit`) manejan el caso de `client=None`.

3.  **Funciones Auxiliares y de Lógica de Negocio:**
    *   **Validación de Datos:**
        *   `es_email_valido`, `es_telefono_valido`: Validaciones básicas de formato.
        *   `verificar_nit`: Consulta al SIAT para validar un NIT (solo online).
        *   `validar_factura_cabecera`, `validar_factura_detalle`: Verifica campos requeridos antes de guardar en BD.
    *   **Formato y Conversión:**
        *   `numero_a_palabras_con_decimales_como_fraccion`: Convierte el monto total a su representación literal.
    *   **Gestión de Número de Factura:**
        *   `get_next_invoice_number`, `increment_invoice_number`, `save_invoice_number`: Manejan la secuencia de números de factura leyéndolos y escribiéndolos en `invoice_number.txt`.
    *   **Gestión de Clientes:**
        *   `save_or_fetch_client_data`: Guarda un nuevo cliente o recupera uno existente.
    *   **Gestión de CUFD:**
        *   `get_cufd`: Obtiene el CUFD vigente de la BD.
        *   `verificar_y_obtener_cufd`: Verifica la vigencia del CUFD actual y solicita uno nuevo si es necesario.
    *   **Firma Digital de XML:**
        *   `load_private_key`, `load_certificate`: Cargan la clave privada y el certificado digital.
        *   `calculate_hash`: Calcula el hash SHA256 de un string.
        *   `sign_xml`: Proceso complejo que:
            1.  Canonicaliza el XML (C14N).
            2.  Calcula el digest SHA256 del XML canónico.
            3.  Construye la estructura `<Signature>` y `<SignedInfo>` del estándar XMLDSig.
            4.  Firma el `<SignedInfo>` canónico con la clave privada (RSA-SHA256).
            5.  Inserta el valor de la firma y el certificado X.509 en el XML.
            6.  Devuelve el XML firmado.
    *   **Generación de HTML para Factura:**
        *   `generate_html_invoice`: Genera una representación HTML detallada de la factura (parece ser para previsualización).
        *   `generate_compact_html_invoice` (usada en impresión): Genera una versión más compacta, probablemente optimizada para impresoras térmicas o PDF.
    *   **Impresión Asíncrona:**
        *   `imprimir_en_hilo`: Envuelve la lógica de generación de PDF (`html_to_pdf`) e impresión térmica (`ThermalPrinter`) en un hilo separado. Crea archivos de señal (`.signal`) para comunicar el estado.
        *   `monitorear_hilo_impresion`: Muestra el estado de la impresión en la UI y maneja timeouts, basándose en los archivos de señal.
    *   **Guardado en Base de Datos:**
        *   `guardar_factura_en_bd`: Llama a `guardar_factura_cabecera` y `guardar_factura_detalle` para persistir la factura. Maneja errores de SQLAlchemy, incluyendo un caso específico para la columna `tipoEmision` faltante.
    *   **Gestión de Estado de Streamlit:**
        *   `initialize_print_state`, `reiniciar_estados`: Funciones para inicializar y limpiar claves en `st.session_state`, con una opción para usar un "nuevo sistema de gestión de estado" (`utils.state_manager`).

4.  **Interfaz de Usuario (`main` función):**
    *   **Modo de Emisión:** Acepta `tipo_emision` (1=online, 2=offline) y `evento_contingencia`. Muestra un aviso en la sidebar si está en modo contingencia.
    *   **Pestañas (`st.tabs`):**
        *   **🧾Facturar (Tab 1):**
            *   **Sidebar:** Entradas para datos del cliente (NIT/CI, razón social, email, teléfono), tipo de documento, tipo de pago (con lógica para campos adicionales como "últimos dígitos tarjeta" o "monto giftcard" según el método). Selección de comandas. Aplicación de descuentos.
            *   **Lógica de Cliente:** Si se ingresa un N° de documento existente, carga los datos del cliente. Si no, permite ingresar nuevos datos y guardarlos. Realiza validación de NIT online si es aplicable.
            *   **Cálculos:** `calculate_totals` y `collect_product_lines` para obtener los montos y detalles de la factura a partir de las comandas seleccionadas.
            *   **Previsualización:** Muestra la factura en HTML usando `components.html(generate_html_invoice(...))`.
            *   **Botón "Facturar":**
                1.  Validaciones de campos.
                2.  Obtención/Renovación de CUFD.
                3.  Generación de CUF (`generate_cuf`).
                4.  Generación de XML (`generate_xml_invoice`).
                5.  Firma del XML (`sign_xml`).
                6.  Validación del XML contra XSD (`zeeper.validar_xml`).
                7.  Compresión GZIP del XML (`zeeper.comprimir_xml`).
                8.  Cálculo de Hash del archivo comprimido (`zeeper.obtener_hash`).
                9.  Envío al SIAT (`zeeper.enviar_solicitud`).
                10. Procesamiento de la respuesta del SIAT (`parse_siat_response`, `display_siat_response`).
                11. Si es exitoso: guarda en BD, incrementa número de factura, actualiza `st.session_state` para habilitar la impresión.
            *   **Botón "Imprimir Factura":** (Habilitado tras facturación exitosa)
                1.  Genera HTML compacto (`generate_compact_html_invoice`).
                2.  Llama a `imprimir_en_hilo`.
                3.  Monitorea con `monitorear_hilo_impresion`.
            *   **Botón "Generar Nueva Factura":** Reinicia el estado de la UI.
            *   **Enlace "Consultar factura":** Genera un enlace al portal del SIAT.
        *   **🔍Ver Facturas (Tab 2):**
            *   Usa `mostrar_lista_facturas` para mostrar facturas por estado (Todas, Pendientes, Validadas, Anuladas) en pestañas internas.
            *   Implementa paginación.
            *   Permite ver detalles, verificar estado (individual o masivo para pendientes) y anular facturas.
        *   **✅Validar NIT (Tab 3):** Llama a `verifica_stream.main()`.
        *   **😏Clientes (Tab 4):** Placeholder.
        *   **🔍Verificar Factura (Tab 5):** Llama a `estado_factura.verificar_estado_factura`.
        *   **🔍Gestionar CUIS (Tab 6):** Llama a `cuis.main()`.
        *   **❌Anular/Revertir (Tab 7):**
            *   Permite ingresar N° de factura y seleccionar motivo.
            *   Llama a `anulacion.anular_factura`.
        *   **❌Revertir Anulación (Tab 8):**
            *   Permite ingresar N° de factura.
            *   Llama a `reversion.enviar_solicitud_reversion` y `reversion.procesar_respuesta_reversion`.

5.  **`mostrar_lista_facturas` función:**
    *   Obtiene facturas paginadas por estado desde `data_access.obtener_facturas_por_estado`.
    *   Muestra las facturas en un `st.dataframe`.
    *   Permite seleccionar una factura para:
        *   Ver detalles completos (`data_access.obtener_factura_completa`).
        *   Verificar estado con SIAT.
        *   Anular.
    *   Incluye una opción de "Verificación Masiva" para facturas pendientes.

6.  **Punto de Entrada (`if __name__ == "__main__":`)**
    *   Inicializa el estado de impresión (`initialize_print_state`).
    *   Llama a `main()` para ejecutar la aplicación.

**IV. Flujo de Facturación Principal (Simplificado):**

1.  Usuario ingresa datos del cliente y selecciona comandas (productos/servicios).
2.  El sistema calcula totales y descuentos.
3.  Usuario presiona "Facturar".
4.  El sistema genera el XML, lo firma digitalmente.
5.  (Modo Online) El XML firmado y comprimido se envía al SIAT.
6.  (Modo Online) Si el SIAT valida la factura:
    *   La factura se guarda en la base de datos local.
    *   Se habilita la opción de imprimir.
7.  (Modo Offline) La factura se guarda localmente con un estado que indica que está pendiente de envío al SIAT.
8.  Usuario presiona "Imprimir Factura".
9.  Se genera un PDF y se envía a la impresora térmica (si está configurada) en un hilo separado.

**V. Consideraciones Adicionales:**

*   **Manejo de Errores:** Hay `try-except` bloques en puntos críticos y se usa `message_placeholder` para mostrar mensajes al usuario.
*   **Seguridad:** La carga de la clave privada (`private_key_ok.pem`) y el certificado (`certificado_ok.pem`) se realiza desde archivos locales. Las rutas están hardcodeadas pero podrían ser configurables. La `API_KEY` se carga desde variables de entorno.
*   **Dependencia de Módulos Externos:** La funcionalidad completa depende de la correcta implementación de los módulos importados (ej: `data_access`, `zeeper`, `cufd`, etc.).
*   **Contingencia:** El sistema está preparado para un modo de contingencia (`tipo_emision=2`), donde las facturas se generan offline y (presumiblemente) se envían al SIAT cuando se restablece la conexión, aunque la lógica de sincronización no está detallada en este archivo UI.
*   **Robustez:** La gestión de `invoice_number.txt` podría ser un punto de fallo si el archivo se corrompe o hay problemas de concurrencia (aunque Streamlit suele ser single-user por sesión).
*   **Base de Datos:** Se espera una estructura de BD específica para `FacturaCabecera`, `FacturaDetalle`, `Cliente`, `Cufd`, etc.

En resumen, `ui_copy.py` es un script Streamlit complejo y bien estructurado que actúa como la interfaz de usuario y orquestador para un sistema de facturación electrónica boliviano. Integra múltiples funcionalidades, desde la captura de datos y generación de XML hasta la comunicación con el SIAT y la impresión física.

Okay, basándome en el análisis del archivo `ui_copy.py`, aquí tienes una lista de los módulos propios (personalizados para este proyecto) con los que interactúa:

1.  **`data_access`**:
    *   Utilizado para todas las operaciones de obtención de datos desde la base de datos (ej: `fetch_comandas`, `fetch_metodos_pago`, `fetch_cliente`, `guardar_factura_cabecera`, `obtener_facturas_por_estado`, etc.).

2.  **`business_logic`**:
    *   Contiene lógica de negocio como `calculate_totals`, `collect_product_lines`, `generate_invoice_link`, `generate_qr`.

3.  **`invoice_xml_generator`**:
    *   Responsable de generar el string XML de la factura (`generate_xml_invoice`).

4.  **`database`**:
    *   Probablemente define la conexión a la base de datos y la sesión (ej: `SessionLocal`).

5.  **`facturador.models`**:
    *   Define los modelos ORM (SQLAlchemy) para las tablas de la base de datos (ej: `Cufd`, `Cliente`).

6.  **`contingency_manager`**:
    *   Utilizado para verificar la conectividad (`check_connectivity`), probablemente relacionado con el manejo de modos online/offline.

7.  **`generate_cuf`**:
    *   Contiene la lógica para generar el Código Único de Factura (`generate_cuf`).

8.  **`cufd`**:
    *   Maneja la solicitud y gestión de CUFDs (`solicitar_cufd`).

9.  **`cuis`**:
    *   Maneja la gestión de CUIS (Código Único de Inicio de Sistemas), se llama a `cuis.main()`.

10. **`zeeper`**: (Nombre similar a "Zeep", pero parece ser un módulo personalizado para interactuar con SIAT)
    *   Contiene funciones para validar XML contra XSD, comprimir XML, obtener hash y enviar solicitudes al SIAT (ej: `validar_xml`, `comprimir_xml`, `obtener_hash`, `enviar_solicitud`).

11. **`verifica_stream`**:
    *   Un módulo cuya funcionalidad principal (`verifica_stream.main()`) se invoca en una de las pestañas, probablemente para alguna verificación o flujo específico.

12. **`estado_factura`**:
    *   Utilizado para verificar el estado de una factura en el SIAT (`verificar_estado_factura`).

13. **`anulacion`**:
    *   Maneja la lógica para anular facturas (`anular_factura`).

14. **`reversion`**:
    *   Contiene la lógica para revertir la anulación de facturas (`enviar_solicitud_reversion`, `procesar_respuesta_reversion`).

15. **`facturador.response_handler`**:
    *   Se encarga de parsear y mostrar las respuestas del SIAT (`parse_siat_response`, `display_siat_response`).

16. **`invoice_templates`**:
    *   Contiene plantillas o funciones para generar representaciones HTML de la factura (ej: `generate_compact_html_invoice`).

17. **`thermal_printer`**:
    *   Interfaz para interactuar con una impresora térmica (`ThermalPrinter`).

18. **`siat_pdf`**:
    *   Contiene la funcionalidad para convertir HTML a PDF (`html_to_pdf`).

19. **`logger_config`**:
    *   Configura y proporciona instancias de loggers para diferentes partes de la aplicación.

20. **`utils.state_compat`**:
    *   Parte de un sistema de gestión de estado personalizado (se intenta importar `initialize_print_state` y `reiniciar_estados` desde aquí).

21. **`utils.state_manager`**:
    *   Parte de un sistema de gestión de estado personalizado (se intenta importar `get_state`, `set_state`, `get_decimal_state`).

Estos módulos encapsulan diferentes responsabilidades dentro de la aplicación de facturación.