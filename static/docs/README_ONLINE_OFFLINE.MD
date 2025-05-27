# Módulo Principal - `main.py`

Este documento describe el propósito, flujo y estructura del archivo `main.py`, el punto de entrada del sistema de facturación.

## Propósito

El archivo `main.py` coordina y dirige la interfaz gráfica y la lógica del sistema, eligiendo entre modo online y offline dependiendo del estado de conexión con el sistema tributario (SIAT).

## Flujo General

1. **Inicialización del sistema**

   * Configura la interfaz con `streamlit`.
   * Inicializa el estado de sesión usando `state_manager` si está disponible.

2. **Verificación de conexión y evento**

   * Llama a `finalizar_evento_si_conectado()` para verificar conexión y estado del evento.
   * Determina si hay un evento significativo activo.

3. **Modo Offline (Contingencia)**

   * Si existe un evento activo o si no hay conexión:

     * Muestra alerta en la interfaz.
     * Carga la interfaz offline (`offline_main`).
     * Guarda el evento en estado de sesión.

4. **Modo Online**

   * Si hay conexión y no existe evento:

     * Llama a `online_main()` para mostrar la interfaz online.

## Componentes Utilizados

* `streamlit`: Interfaz de usuario web.
* `verificar_comunicacion`: Verifica conexión al SIAT.
* `get_cufd_vigente`: Consulta CUFD actual.
* `obtener_evento_abierto`, `insertar_evento_local`: Gestores de eventos.
* `offline_main`, `online_main`: UIs principales según el modo de emisión.
* `state_manager`: Manejo avanzado de sesión.
* `logger_config`: Registro de actividad para auditoría.

## Características Clave

* Alterna automáticamente entre emisión online y offline.
* Manejo robusto de eventos de contingencia.
* Registro de logs en cada decisión clave.
* Utiliza arquitectura modular, delegando UI a `ui_copy.py` y `ui_offline.py`.

## Integración

* Utiliza funciones del backend (`soap_services`, `database`, `contingencia_auto`).
* Controla flujo principal pero delega la lógica a módulos especializados.

## Conclusión

`main.py` es el orquestador del sistema de facturación, definiendo la ruta que seguirá el usuario según el estado del sistema. Garantiza que siempre se ofrezca una interfaz adecuada para emitir facturas, sin interrumpir el flujo operativo ante caídas de conexión.


# Facturación Online - Flujo Completo del Sistema

Este documento describe el flujo completo del sistema de emisión de facturas en modo en línea (online) conforme a la normativa SIAT.

## Etapas del Flujo ONLINE

### 1. Generación del Documento Fiscal

* Se ingresan los datos del cliente y productos desde la interfaz.
* Se genera el archivo XML de la factura electrónica en base al sector económico.

### 2. Firma Digital del XML

* El XML generado es firmado digitalmente conforme al estándar XMLDSig.
* Se utilizan certificados digitales válidos y claves privadas protegidas.

### 3. Validación contra XSD

* El XML firmado se valida contra el esquema XSD oficial proporcionado por el SIAT.
* Esta validación asegura estructura correcta y cumplimiento con el estándar.

### 4. Compresión y Cálculo de HASH

* El archivo XML validado se comprime en formato GZIP.
* Se calcula el hash SHA-256 del archivo comprimido para garantizar su integridad.

### 5. Envio al SIAT

* Se codifica el GZIP en base64 y se construye la solicitud SOAP.
* Se consume el servicio `recepcionFactura` del SIAT.
* Se manejan las respuestas:

  * Estado `908` indica factura validada
  * Estado `904` indica observaciones, se registran los errores recibidos

### 6. Almacenamiento y Trazabilidad

* La respuesta del SIAT se guarda en la base de datos junto al estado de la factura.
* El archivo XML y su firma se almacenan en disco para auditoría.

## Módulos Involucrados

* `ui_copy.py`: Interfaz para emisión online, captura de datos
* `invoice_xml_generator.py`: Generación del XML de la factura
* `zeeper.py`: Validación XSD, compresión GZIP, hash y envío SOAP
* `generate_cuf.py`: Generación del CUF (código único de factura)
* `cufd.py`: Obtención del CUFD vigente del SIAT
* `data_access.py`: Guardado y recuperación de datos de la factura y respuesta

## Carpetas y Archivos

* `xmls/`: XMLs individuales firmados y enviados
* `log/` o `reportes/`: Archivos de respuesta del SIAT

## Consideraciones

* El flujo está preparado para manejo de errores con reintentos
* Permite identificación de errores del SIAT para resolución manual
* Todos los datos enviados están protegidos y validados según normas vigentes

# Facturación Offline - Flujo Completo del Sistema

Este documento describe el flujo completo del sistema de emisión de facturas en modo contingencia (offline) implementado en el sistema de facturación SIAT.

## Etapas del Flujo OFFLINE

### Primera Etapa - Emisión Durante la Contingencia

1. **Registro del Evento Significativo**

   * Se inicia el evento significativo en el sistema.
   * Se registra el motivo y se asocia el CUFD activo.

2. **Generación de Facturas**

   * Se genera el archivo XML del documento fiscal.
   * Se firma el XML usando estándares XMLDSig.
   * Se valida contra el archivo XSD correspondiente.
   * Se guarda el archivo firmado localmente en `xmls_offline/`.
   * Se registra la factura con estado `CONTINGENCIA` en la base de datos.

### Segunda Etapa - Post Contingencia

1. **Agrupación y Envio de Facturas**

   * Se recuperan todas las facturas con estado `CONTINGENCIA`.
   * Se agrupan en paquetes de hasta 500 facturas.
   * Se genera un archivo XML consolidado por paquete.
   * Se comprime el archivo XML usando GZIP.
   * Se calcula el hash SHA-256 del archivo comprimido.
   * Se codifica en base64.
   * Se envía al SIAT usando el servicio `recepcionPaqueteFactura`.
   * Se registra la respuesta y se actualiza cada factura a `ENVIADA` y `EN_VALIDACION`.

2. **Verificación del Estado Real**

   * Se consultan las facturas con estado `EN_VALIDACION`, `ERROR_VALIDACION`, `DUPLICADA`.
   * Se usa `verificacionEstadoFactura` para consultar el SIAT.
   * Se actualiza el estado real: `VALIDADA`, `ANULADA`, `DUPLICADA`, `NO_ENCONTRADA`, etc.
   * Se genera un reporte por factura (`.json`) y uno consolidado (`.html`).

## Módulos Involucrados

* `offline_billing.py`: Generación de XML, firma, validación y almacenamiento local
* `paquetes_offline.py`: Agrupación, compresión, cálculo de hash y envío de paquetes
* `post_sync.py`: Verificación y actualización del estado real de las facturas

## Carpetas Generadas

* `xmls_offline/`: Archivos XML de facturas individuales
* `xmls_batch/`: Paquetes XML agrupados y comprimidos
* `reportes_offline/`: Registros de respuestas, estados y reportes HTML
# Módulos de Utilidad - State Manager y Logger

Este documento describe los componentes auxiliares `state_manager.py` y `logger_config.py`, fundamentales para la gestión de estado de sesión y trazabilidad del sistema de facturación.

---

## Módulo: `state_manager.py`

### Propósito

Centraliza la manipulación de `streamlit.session_state`, permitiendo:

* Inicialización de todos los estados requeridos por la aplicación.
* Acceso y modificación de estado con validación.
* Reseteo por contexto (`factura`, `formulario`, `all`).

### Funciones Clave

* `initialize_app_state()`

  * Define e inicializa los bloques de estado: formulario, impresión, interfaz.
* `get_state(key)`, `set_state(key, value)`

  * Acceso seguro a `session_state`.
* `get_decimal_state(key)`

  * Retorna valores como `Decimal` (precisión monetaria).
* `reset_states(mode)`

  * Limpia el estado según el contexto operativo.
* `is_offline_mode()` / `get_active_event()`

  * Detecta modo de operación actual y evento activo.
* `save_form_data()`

  * Captura un snapshot del formulario actual.

---

## Módulo: `logger_config.py`

### Propósito

Establece la infraestructura de logging del sistema con:

* Archivos rotativos por componente.
* Consola opcional.
* Prefijos modulares: `facturador.*`

### Estructura de Logging

* `setup_logger(...)`: Define cada logger con nivel, formato, archivo y consola.
* `setup_application_loggers(log_dir)`:

  * Inicializa los loggers por defecto al importar.
  * Genera logs por componente: `printer`, `facturacion`, `cliente`, `xml`, `siat`, etc.

### Funciones Clave

* `get_logger(name)`: Acceso genérico.
* Específicos: `get_facturacion_logger()`, `get_eventos_logger()`, `get_siat_logger()`, etc.

### Archivos de Log

* Directorio: `logs/`
* Archivos: `app_YYYYMMDD.log`, `facturacion_YYYYMMDD.log`, `eventos_significativos.log`, etc.
* Tamaño máximo: 10MB con 3 copias de respaldo

---

## Conclusión

`state_manager.py` mejora la estabilidad de interfaz y `logger_config.py` fortalece la trazabilidad del sistema. Juntos permiten una operación fiable, auditable y mantenible, crucial para una plataforma de facturación profesional.
# Módulos Críticos - Generador de XML y Zeeper (Enviador SIAT)

Este documento cubre los módulos `invoice_xml_generator.py` y `zeeper.py`, encargados de la generación, validación y envío de las facturas electrónicas conforme a la normativa del SIAT.

---

## Módulo: `invoice_xml_generator.py`

### Propósito

Genera el documento fiscal XML con los datos de la factura conforme al esquema definido por el SIAT.

### Funciones Principales

* `generate_xml_invoice(...)`

  * Recibe los datos completos de la factura y el cliente
  * Genera el XML con etiquetas estructuradas
  * Aplica valores nillable cuando corresponde
  * Incluye información del evento si `tipo_emision = 2`
  * Retorna:

    * `xml_string`: contenido XML como cadena
    * `cabecera_data`: diccionario de datos de cabecera
    * `detalles_data`: lista de diccionarios por línea

### Características

* Aplica formato estricto ISO-8601 con milisegundos
* Mapea unidades de medida a códigos numéricos
* Valida internamente la estructura antes de firmar
* Maneja firma, datos nulos, y estructura XSD

---

## Módulo: `zeeper.py`

### Propósito

Valida el XML contra el XSD, comprime, genera hash y envía la factura al SIAT mediante SOAP.

### Funciones Principales

* `validar_xml(xml_path, xsd_main_path)`

  * Verifica el XML contra el XSD oficial usando `xmlschema`
* `comprimir_xml(xml_path)`

  * Crea un archivo `.gz` desde el XML
* `obtener_hash(gzip_path)`

  * Genera el hash SHA-256 del GZIP
* `enviar_solicitud(xml_path, xsd_main_path, fecha_envio, cufd)`

  * Envía el XML en formato base64 empaquetado dentro de una solicitud SOAP
  * Maneja errores HTTP, tiempo de espera y respuesta SIAT

### Características

* SOAP construido manualmente con etiquetas requeridas por SIAT
* Reintentos automáticos en caso de `Timeout`
* Uso de variables de entorno para CUIS, API\_KEY, NIT, etc.
* Loggers dedicados por operación (XML, general)

---

## Conclusión

Estos dos módulos forman el núcleo del flujo de emisión en línea:

* `invoice_xml_generator.py`: estructura y contenido legal
* `zeeper.py`: validación y envío al SIAT

Ambos cumplen con los requerimientos de interoperabilidad del sistema tributario y son componentes críticos para el éxito del proceso de facturación electrónica.
