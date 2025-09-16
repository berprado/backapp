# Tipos de Eventos Significativos y Envío de Paquetes

## 1. Tipos de Eventos Significativos

Los eventos significativos son situaciones excepcionales que afectan la emisión normal de facturas electrónicas. Se clasifican en dos grandes grupos según la normativa del SIN:

### A. Eventos que permiten emisión fuera de línea (Sistema operativo)

| Código | Descripción                                                        |
|--------|--------------------------------------------------------------------|
| 1      | Corte del servicio de Internet                                    |
| 2      | Inaccesibilidad al Servicio Web de la Administración Tributaria    |
| 3      | Ingreso a zonas sin Internet por despliegue de punto de venta      |
| 4      | Venta en lugares sin Internet                                     |

**Características:**
- El sistema de facturación sigue operativo.
- El usuario puede emitir facturas en modo offline desde el sistema.
- Las facturas se almacenan localmente y, una vez superada la contingencia, se envían en paquetes al SIN.

### B. Eventos que requieren emisión por contingencia (Sistema NO operativo)

| Código | Descripción                                                        |
|--------|--------------------------------------------------------------------|
| 5      | Virus informático o falla de software                              |
| 6      | Cambio de infraestructura de sistema o falla de hardware           |
| 7      | Corte de suministro de energía eléctrica                           |

**Características:**
- El sistema de facturación NO está operativo (equipo apagado, dañado, robado, etc.).
- El usuario debe emitir facturas manuales de contingencia o usar el portal web del SIN.
- Una vez superada la contingencia, las facturas manuales deben ser transcritas al sistema y enviadas al SIN como paquetes de contingencia.

---

## 2. Envío de Paquetes: Características y Diferencias

### A. Emisión y envío de Paquetes por Fuera de Línea

- **Motivo:** Falta de conectividad, pero el sistema está operativo.
- **Facturación:** Se emiten facturas offline desde el sistema.
- **Registro de evento:** Se registra el evento significativo, pero se sigue usando el sistema.
- **Envío de paquetes:** Cuando se recupera la conectividad, se agrupan las facturas en paquetes (máx. 500) y se envían al SIN.
- **Normativa:** Modalidad fuera de línea, sistema operativo.

### B. Emisión y envío de Paquetes por Contingencia

- **Motivo:** El sistema NO está operativo (falla grave, corte de energía, etc.).
- **Facturación:** Se emiten facturas manuales o por portal web del SIN.
- **Registro de evento:** Se registra el evento significativo, pero NO se puede usar el sistema; se emiten facturas manuales.
- **Envío de paquetes:** Cuando se recupera el sistema, se transcriben y envían las facturas manuales como paquetes de contingencia.
- **Normativa:** Modalidad de contingencia, sistema NO operativo.

---

## 3. Tabla Comparativa

| Característica                  | Paquetes por Fuera de Línea           | Paquetes por Contingencia                |
|----------------------------------|---------------------------------------|------------------------------------------|
| **Motivo**                      | Eventos 1-4: El sistema está operativo, solo falta conectividad | Eventos 5-7: El sistema NO está operativo, se emiten facturas manuales o por portal web |
| **Registro de evento**           | Se registra el evento significativo, pero se sigue usando el sistema | Se registra el evento significativo, pero NO se puede usar el sistema; se emiten facturas manuales |
| **Autorización**                | El sistema está autorizado para emitir offline | Se requiere autorización para emitir manualmente o por portal web |
| **CUFD utilizado**              | CUFD vigente antes del corte, usado en el sistema | CUFD vigente antes del corte, usado para transcribir facturas manuales |
| **Envío de paquetes**           | Cuando se recupera la conectividad, desde el sistema | Cuando se recupera el sistema, se transcriben y envían las facturas manuales como paquetes |
| **Código de evento en envío**    | Se incluye el código de evento significativo | Se incluye el código de evento significativo |
| **Normativa**                   | Modalidad fuera de línea, sistema operativo | Modalidad de contingencia, sistema NO operativo |

---

## 4. ¿Cuándo usar cada proceso?

- **Paquetes por fuera de línea:**
  - Cuando el sistema está operativo pero no hay conectividad.
  - El usuario sigue emitiendo facturas desde el sistema y luego las envía en paquetes.

- **Paquetes por contingencia:**
  - Cuando el sistema NO está operativo.
  - El usuario emite facturas manuales o por portal web y, una vez recuperado el sistema, transcribe y envía esas facturas como paquetes de contingencia.

---

**Referencia normativa:**
- Documentación oficial SIAT: https://siatinfo.impuestos.gob.bo/index.php/facturacion-en-linea/emision-y-envio-de-facturas/emision-y-envio
- Documentación sobre contingencia y eventos significativos: https://siatinfo.impuestos.gob.bo/index.php/facturacion-en-linea/emision-y-envio-de-facturas/contingencia-y-eventos-significativos
- Documentación sobre ingreso a contingencia: https://siatinfo.impuestos.gob.bo/index.php/facturacion-en-linea/emision-y-envio-de-facturas/ingreso-a-contingencia
