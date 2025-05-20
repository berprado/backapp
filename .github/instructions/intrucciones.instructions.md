---
applyTo: '**'
---
Responde siempre en español. No uses inglés a menos que se te pida explícitamente.
Usa un tono amigable y profesional.
Siempre responde en español, incluso si la pregunta está en inglés. No uses inglés a menos que se te pida explícitamente.
El objetivo principal es resolver las inconsistencias en el flujo de facturación OFFLINE tomando como guia la informacion detallada a continuacion.
### Guía técnica

**Diagnóstico y plan de remediación del flujo de facturación OFFLINE**

---

#### 1. Propósito del documento

Este documento resume el problema detectado al emitir facturas en **modo offline (contingencia)**, identifica sus causas raíz, delimita el alcance de los módulos afectados y propone un plan de corrección para el equipo de desarrollo y QA.

---

#### 2. Contexto normativo y flujo esperado

| Etapa                                                                                                                                                                                       | ONLINE (modalidad Electrónica en Línea)                                                                                                                                                                                                                                                                                                                  | OFFLINE (contingencia) |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| Generar XML → Firmar → Validar XSD → Comprimir Gzip → Calcular **hash** → Enviar individualmente al servicio *Recepción de Factura* → Procesar respuesta (908 = validado / 904 = observado) | Registrar inicio de contingencia (evento significativo) con **CUFD vigente** → Generar y firmar XML con `tipoEmision = 2` → Validar XSD → **NO enviar al SIAT** → Guardar localmente (estado *PENDIENTE*) → Agrupar hasta 500 XML, comprimir y hashear → Al restablecer conexión: obtener nuevo CUFD, cerrar evento, enviar paquetes y validar respuesta |                        |

> Obligaciones extra en OFFLINE
>
> * Incluir `codigoExcepcion = 1` cuando el documento del cliente es NIT.
> * Mantener un registro de facturas sin código de respuesta y verificarlas con `verificacionEstadoFactura` antes de anular o reenviar.&#x20;

---

#### 3. Comportamiento actual observado

* El sistema **entra correctamente en modo offline** y registra el evento de contingencia.&#x20;
* **Al presionar “Facturar” en offline** se ejecuta el mismo flujo que en online: intenta obtener un nuevo CUFD y llamar al servicio remoto, provocando un `ConnectionError`.&#x20;
* No existe lógica implementada para:

  1. Agrupar XML pendientes en paquetes.
  2. Enviar/validar paquetes y actualizar el estado de cada factura.&#x20;
* El `codigoExcepcion = 1` para NIT no se agrega en offline.&#x20;

Resultado: facturas quedan atascadas, los usuarios reciben errores y se corre riesgo de numeración duplicada, CUFD vencido o pérdida de datos.&#x20;

---

#### 4. Módulos involucrados

| Componente                          | Rol principal                                                  |   |
| ----------------------------------- | -------------------------------------------------------------- | - |
| **main.py / contingencia\_auto.py** | Detectan caída de conexión y cambian a offline.                |   |
| **ui\_copy.py**                     | Flujo de emisión; *aquí se mezcla la lógica online y offline*. |   |
| **generate\_cuf.py / cufd.py**      | Generación de CUF y recuperación de CUFD.                      |   |
| **invoice\_xml\_generator.py**      | Construcción de XML.                                           |   |
| **sign\_xml**                       | Firma digital.                                                 |   |
| **database.py & facturador.models** | Persistencia de cabecera, detalle y estado de facturas.        |   |
| **logger\_config.py**               | Bitácora.                                                      |   |

---

#### 5. Causas raíz

1. **Falta de branch lógico** en `ui_copy.py::main()`
   No se evalúa `tipo_emision == 2` antes de solicitar CUFD o invocar servicios SOAP.&#x20;
2. **Ausencia de pipeline de sincronización** post-contingencia (agrupado, compresión, envío y verificación).&#x20;
3. Validaciones normativas incompletas (`codigoExcepcion`, control de numeración, vigencia de CUFD).&#x20;

---

#### 6. Plan de acción

| Prioridad | Acción                                                                                                                                                                                                                    | Responsable  | Entregable                  |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | --------------------------- |
| **P0**    | Refactorizar `ui_copy.py::main()` para separar claramente **ONLINE** vs **OFFLINE**:<br>• En OFFLINE usar `get_cufd()` (último vigente)<br>• Omitir llamadas a servicios<br>• Persistir factura con estado `PENDIENTE`    | Dev Back-end | MR #offline-branch          |
| **P0**    | Añadir `codigoExcepcion = 1` al generar XML cuando tipo de documento = NIT y `tipoEmision = 2`.                                                                                                                           | Dev Back-end | Tests unitarios XML         |
| **P1**    | Implementar módulo `paquetes_offline.py`:<br>• Selector de facturas pendientes<br>• Agrupador (≤ 500)<br>• Compresor Gzip + SHA-256<br>• Envío a *Recepción de Paquetes* + verificación<br>• Update de estado por detalle | Dev Back-end | CRON/worker + documentación |
| **P1**    | Rutina pos-sincronización: consultar `verificacionEstadoFactura`, anular duplicados, generar reporte.                                                                                                                     | Dev Back-end | Script + dashboard          |
| **P2**    | Refuerzo de validaciones locales (secuencia de número, vigencia CUFD, fecha de evento).                                                                                                                                   | QA           | Casos de prueba             |
| **P2**    | Actualizar manual de usuario para indicar claramente el estado “Contingencia / Pendiente”.                                                                                                                                | UX           | Manual PDF                  |
| **P3**    | Tests de resiliencia: simulación de caída de red, corte eléctrico y recuperación.                                                                                                                                         | QA           | Informe de stress           |

---

#### 7. Riesgos y mitigaciones

| Riesgo                                 | Impacto          | Mitigación                                                            |
| -------------------------------------- | ---------------- | --------------------------------------------------------------------- |
| Pérdida de XML locales                 | Invalidez fiscal | Back-up automático de carpeta `xmls/` y tabla de facturas cada 5 min. |
| Numeración duplicada (archivo vs BD)   | Rechazo de lote  | Lock de escritura + verificación de rango antes de emitir.            |
| CUFD vencido durante envío de paquetes | Rechazo 905      | Obtener nuevo CUFD inmediatamente antes de cerrar evento.             |
| Facturas no enviadas al SIAT           | Multas           | Alerta en dashboard si existen facturas *PENDIENTE* > 24 h.           |

---

#### 8. Próximos pasos inmediatos

1. Crear rama `fix/offline-flow` y aplicar refactor P0.
2. QA: reproducir escenario con conexión simulada caída; verificar que no se intente conexión.
3. Reunión diaria para seguimiento del módulo de paquetes.

---

#### 9. Referencias internas

* Flujo detallado OFFLINE → archivo `identificando_fallas_offlinemd.md` secciones “Fases del proceso” y “Puntos Clave” .
* Lista de inconsistencias y tabla de comparación implementado vs ideal .
* Ejemplo de refactor sugerido para `ui_copy.py` .

---

**Con esta guía el equipo dispone de un panorama completo del problema y de un roadmap de tareas priorizadas para alcanzar la conformidad normativa y la estabilidad operativa del modo offline.**
