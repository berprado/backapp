
## ¿Qué es la verificación de comunicación?

La **verificación de comunicación** es un proceso mediante el cual el sistema realiza una consulta a los servicios web del SIAT (Servicio de Impuestos Nacionales) para asegurarse de que existe conectividad y que los servicios SOAP requeridos están disponibles y respondiendo correctamente.

### ¿Cómo se realiza?

- El sistema envía una solicitud SOAP estándar (`verificarComunicacion`) a cada uno de los endpoints configurados (por ejemplo: Facturación Códigos, Operaciones, Sincronización, etc.).
- Espera una respuesta del servicio. Si la respuesta es exitosa y contiene los códigos esperados (por ejemplo, código 926 o transacción=true), se considera que el servicio está **operativo**.
- Si ocurre un error (timeout, error HTTP 500, problemas de red, etc.), el sistema detecta que el servicio está **no disponible**.

En el archivo `4_Verificar_Comunicación.py`, esto se implementa en la función `verificar_servicio`, que:
- Envía la solicitud SOAP.
- Procesa la respuesta.
- Muestra el resultado en la interfaz de usuario.

---

## ¿Cuál es el rol de la verificación de comunicación en el sistema?

La verificación de comunicación cumple un papel **crítico** en la robustez y confiabilidad del sistema de facturación electrónica. Sus principales funciones son:

1. **Monitoreo preventivo:** Permite detectar de manera proactiva si los servicios del SIAT están disponibles antes de intentar emitir o validar facturas.
2. **Cambio automático a modo contingencia:** Si la verificación falla (por ejemplo, por problemas de red o caídas del servicio), el sistema puede cambiar automáticamente al **modo offline/contingencia**. Esto asegura que la operación del negocio no se detenga y que las facturas puedan seguir emitiéndose localmente hasta que se restablezca la conexión.
3. **Diagnóstico y soporte:** Facilita la identificación rápida de problemas de conectividad, permitiendo al usuario o al soporte técnico saber exactamente qué servicio está fallando y por qué.
4. **Cumplimiento normativo:** La normativa exige que, ante la imposibilidad de comunicarse con el SIAT, el sistema debe registrar el evento y operar en modo contingencia, para luego sincronizar las facturas pendientes cuando vuelva la conexión.

---

## Resumen visual del flujo

1. **Inicio del sistema o antes de emitir una factura:**
   - Se ejecuta la verificación de comunicación.
2. **Si la comunicación es exitosa:**
   - El sistema opera en modo online y puede emitir facturas normalmente.
3. **Si la comunicación falla:**
   - El sistema activa el modo contingencia/offline.
   - Se registra el evento significativo.
   - Las facturas se almacenan localmente para su posterior envío.

---