La lógica implementada en el manejo de contingencias y eventos significativos en el sistema se centra en garantizar la continuidad operativa durante interrupciones en los servicios del SIAT (Sistema de Impuestos Nacionales) y en registrar adecuadamente los eventos significativos que justifican estas interrupciones. A continuación, se describe detalladamente la lógica:

---

### **1. Manejo de Contingencias**
El manejo de contingencias está diseñado para detectar problemas de conexión con los servicios del SIAT, activar un modo de contingencia cuando sea necesario, y sincronizar las facturas pendientes una vez que se restablezca la conexión.

#### **Componentes principales:**
1. **Estados de Contingencia (`ContingencyStatus`)**:
   - **NORMAL**: Operación normal, todos los servicios están disponibles.
   - **MONITORING**: Se detectaron problemas y se está monitoreando la conexión.
   - **CONTINGENCY**: Modo contingencia activado debido a problemas de conexión.
   - **RECOVERING**: Servicios recuperados, se están enviando las facturas pendientes.

2. **Activación de Contingencia**:
   - Se activa cuando se detectan fallos consecutivos en la conexión con los servicios del SIAT.
   - Requiere un tipo de evento significativo (`SignificantEventType`) y una descripción del evento.
   - Guarda el estado actual, incluyendo el CUFD vigente, para operar en modo offline.
   - Inicia un monitoreo continuo para detectar la recuperación de los servicios.

3. **Desactivación de Contingencia**:
   - Se registra un evento significativo que marca el fin de la contingencia.
   - Cambia el estado a **RECOVERING** y sincroniza las facturas pendientes.
   - Una vez completada la sincronización, el sistema vuelve al estado **NORMAL**.

4. **Monitoreo de Conexión**:
   - Verifica periódicamente la conexión con los servicios del SIAT mediante solicitudes SOAP.
   - Si se detectan problemas, incrementa un contador de fallos consecutivos.
   - Si se detecta una recuperación, incrementa un contador de éxitos consecutivos.
   - Cambia de estado según los umbrales configurados para fallos y éxitos consecutivos.

5. **Sincronización de Facturas Pendientes**:
   - Utiliza la clase `BatchSender` para enviar las facturas acumuladas durante la contingencia en lotes.
   - Registra los resultados de cada lote y actualiza el estado de las facturas en la base de datos.

---

### **2. Manejo de Eventos Significativos**
El manejo de eventos significativos asegura que se registren adecuadamente los eventos que justifican la activación del modo contingencia, cumpliendo con los requisitos del SIAT.

#### **Componentes principales:**
1. **Registro de Eventos Significativos**:
   - Se realiza mediante la función `register_significant_event`.
   - Valida que los parámetros requeridos (código del evento, descripción, fechas de inicio y fin) sean válidos.
   - Obtiene el CUFD vigente si no se proporciona explícitamente.
   - Envía una solicitud SOAP al servicio del SIAT para registrar el evento.
   - Si el registro es exitoso, guarda el evento en la base de datos local.

2. **Consulta de Eventos Registrados Localmente**:
   - La función `get_significant_events` permite obtener los eventos registrados en la base de datos local.
   - Devuelve una lista de eventos con detalles como código, descripción, fechas y CUFD asociado.

3. **Consulta de Eventos en el SIAT**:
   - La función `query_siat_significant_events` consulta los eventos registrados directamente en el SIAT.
   - Utiliza una solicitud SOAP para obtener la lista de eventos significativos registrados en el sistema del SIAT.

---

### **3. Registro y Recuperación del Estado**
El sistema guarda y restaura el estado del gestor de contingencias para garantizar la persistencia de la información entre reinicios.

- **Guardado del Estado**:
  - Se almacena en un archivo JSON (`contingency_state.json`) el estado actual, incluyendo:
    - Estado de contingencia.
    - Tiempos de inicio y última verificación.
    - Tipo y descripción del evento.
    - CUFD vigente durante la contingencia.

- **Restauración del Estado**:
  - Al iniciar el sistema, se carga el estado desde el archivo JSON.
  - Si el estado indica que el sistema estaba en contingencia o monitoreo, se reinicia el monitoreo automáticamente.

---

### **4. Lógica de Envío de Lotes**
La clase `BatchSender` se encarga de gestionar el envío de facturas acumuladas durante la contingencia.

1. **Preparación de Lotes**:
   - Agrupa las facturas pendientes en lotes de hasta 500 facturas (límite normativo).
   - Genera un archivo XML para cada lote y lo comprime.

2. **Cálculo de Hash y Codificación Base64**:
   - Calcula el hash SHA-256 del archivo comprimido.
   - Codifica el archivo en Base64 para enviarlo al SIAT.

3. **Envío de Lotes**:
   - Envía cada lote al SIAT mediante solicitudes SOAP.
   - Implementa un mecanismo de reintento para manejar errores transitorios.
   - Procesa las respuestas del SIAT y actualiza el estado de las facturas en la base de datos.

---

### **5. Registro de Logs**
El sistema utiliza un sistema de logging centralizado para registrar todas las operaciones relacionadas con contingencias y eventos significativos.

- **Loggers Específicos**:
  - `contingency`: Registra eventos relacionados con el manejo de contingencias.
  - `batch_sender`: Registra eventos relacionados con el envío de lotes.
  - `significant_events`: Registra eventos relacionados con el registro y consulta de eventos significativos.

- **Rotación de Logs**:
  - Los logs se rotan automáticamente para evitar el crecimiento excesivo de los archivos.

---

### **Resumen**
La lógica implementada asegura que el sistema pueda operar de manera confiable durante interrupciones en los servicios del SIAT, cumpliendo con los requisitos normativos y garantizando la integridad de los datos. El manejo de contingencias y eventos significativos está diseñado para ser robusto, modular y fácil de mantener.