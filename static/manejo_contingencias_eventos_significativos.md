La lógica y el manejo de contingencias y eventos significativos en el sistema están diseñados para garantizar la continuidad operativa en caso de fallos en la conexión con los servicios del SIAT (Sistema de Impuestos Nacionales). A continuación, se describe detalladamente cómo se implementan estas funcionalidades:

---

### **1. Manejo de Contingencias**
El manejo de contingencias se centra en permitir la emisión de facturas en modo offline cuando los servicios del SIAT no están disponibles. Esto incluye:

#### **1.1. Estados del Sistema**
- **Estados Definidos**:
  - `normal`: El sistema opera con conexión estable.
  - `monitoring`: El sistema está verificando la conexión.
  - `contingency`: El sistema está en modo contingencia debido a fallos de conexión.
  - `recovering`: El sistema está intentando recuperar la conexión y enviar facturas pendientes.

- **Gestión del Estado**:
  - El estado actual del sistema se obtiene a través del método `get_status()` del `ContingencyManager`.
  - Se registran tiempos clave como el inicio de la contingencia (`contingency_start_time`) y la última verificación exitosa (`last_check_time`).

#### **1.2. Activación y Desactivación de Contingencia**
- **Activación Manual**:
  - Los usuarios pueden activar manualmente el modo contingencia seleccionando un tipo de evento significativo y proporcionando una descripción.
  - Esto se realiza mediante el método `activate_contingency()` del `ContingencyManager`.

- **Desactivación Manual**:
  - Los usuarios pueden desactivar el modo contingencia manualmente, lo que activa el envío automático de facturas pendientes.
  - Esto se realiza mediante el método `deactivate_contingency()`.

#### **1.3. Monitor de Conexión**
- **Automatización**:
  - Un hilo de monitoreo (`monitoring_thread`) verifica periódicamente la conexión con los servicios del SIAT.
  - Si se detecta una falla, el sistema cambia automáticamente al modo contingencia.

- **Control del Monitor**:
  - Los usuarios pueden iniciar o detener el monitor manualmente desde la interfaz.
  - El estado del monitor se verifica con `is_alive()`.

#### **1.4. Facturación en Contingencia**
- Las facturas emitidas en modo contingencia se almacenan localmente con el estado `CONTINGENCIA`.
- Una vez restablecida la conexión, estas facturas se envían en lotes al SIAT.

---

### **2. Manejo de Eventos Significativos**
Los eventos significativos son situaciones excepcionales que deben registrarse en el SIAT para justificar la emisión de facturas en contingencia. El sistema incluye funcionalidades para registrar, consultar y gestionar estos eventos.

#### **2.1. Registro de Eventos**
- **Proceso de Registro**:
  - Los usuarios pueden registrar eventos significativos proporcionando un código de evento, una descripción, y un rango de fechas (inicio y fin).
  - El registro se realiza mediante el método `register_significant_event()`.

- **Validación**:
  - Se valida que la fecha de fin sea posterior a la fecha de inicio.
  - Si no se proporciona un CUFD, se utiliza el CUFD vigente.

- **Almacenamiento**:
  - Los eventos registrados se guardan en la base de datos local en la tabla `SincronizarParametricaEventosSignificativos`.

#### **2.2. Consulta de Eventos**
- **Eventos Locales**:
  - Los eventos registrados localmente se obtienen mediante el método `get_significant_events()`.
  - Se muestran en una tabla con detalles como código, descripción, fechas y CUFD.

- **Eventos en el SIAT**:
  - Los eventos registrados en el SIAT se consultan mediante el método `query_siat_significant_events()`.
  - La consulta utiliza un cliente SOAP para comunicarse con los servicios del SIAT.

#### **2.3. Tipos de Eventos**
- Los tipos de eventos disponibles se obtienen mediante el método `get_available_event_types()` del `ContingencyManager`.
- Cada tipo de evento tiene un código y una descripción, que se utilizan para el registro.

---

### **3. Envío Masivo de Facturas**
- **Facturas Pendientes**:
  - Las facturas en estado `CONTINGENCIA` se agrupan y se envían en lotes.
  - El envío se realiza mediante el `BatchSender`, que procesa las facturas pendientes y las marca como enviadas.

- **Estadísticas**:
  - Se muestran métricas como el número total de facturas pendientes y su distribución por fecha.
  - Los resultados del envío se detallan por lote, indicando éxito o error.

---

### **4. Interfaz de Usuario**
- **Streamlit**:
  - La interfaz está implementada con Streamlit, proporcionando una experiencia interactiva para gestionar contingencias y eventos.
  - Las funcionalidades están organizadas en pestañas:
    - **Estado del Sistema**: Muestra el estado actual y permite verificar la conexión.
    - **Gestión de Contingencia**: Permite activar/desactivar el modo contingencia.
    - **Envío Masivo**: Gestiona el envío de facturas pendientes.
    - **Eventos Significativos**: Permite registrar y consultar eventos.

---

### **5. Registro y Manejo de Errores**
- **Logs**:
  - Se utilizan loggers específicos para registrar errores y eventos importantes.
  - Los logs se dividen en categorías como `contingency` y `xml`.

- **Manejo de Excepciones**:
  - Las excepciones se capturan y se registran en los logs.
  - Se proporcionan mensajes descriptivos para informar al usuario sobre errores.

---

En resumen, el sistema está diseñado para garantizar la continuidad operativa mediante un manejo robusto de contingencias y eventos significativos, con una interfaz intuitiva y herramientas para automatizar procesos críticos.