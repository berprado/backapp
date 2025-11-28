# Manejo de Rechazos del SIN (Código 902)

## Contexto
Anteriormente, cuando una factura era rechazada por el SIN (Servicio de Impuestos Nacionales), el sistema no tenía un manejo específico para diferenciar entre un error de comunicación y un rechazo definitivo de la validación.

## Problema
Si el SIN rechaza una factura (por ejemplo, por un error en los datos del cliente, un cálculo incorrecto que pasó la validación local pero no la del SIN, etc.), el número de factura ya ha sido "usado" en el intento de envío. Según la normativa, si el SIN procesa la solicitud y devuelve un rechazo explícito, ese número de factura no debe reutilizarse ni "revertirse", sino que debe quedar registrado como anulado o rechazado para mantener la correlatividad y la trazabilidad.

## Solución Implementada

Se ha modificado el flujo de emisión en línea (`_handle_online_submission` en `facturacion_tab.py`) para manejar específicamente el código de estado **902 (Rechazada)**.

### Flujo:
1.  **Envío:** Se envía la factura al SIN.
2.  **Respuesta 902:** Si el SIN responde con `codigoEstado: 902`:
    *   **No se revierte el número:** A diferencia de los errores locales (XML mal formado, firma fallida), aquí **NO** se llama a `revertir_incremento_numero_factura`. El número se considera consumido.
    *   **Extracción de Errores:** Se extraen los mensajes de error detallados de la lista `mensajesList` de la respuesta del SIN.
    *   **Registro en BD:** Se guarda la factura en la base de datos (`factura_cabecera`) con los siguientes estados:
        *   `estado`: **"RECHAZADA"**
        *   `resultadoValidacion`: **"RECHAZADA"**
        *   `mensajeError`: Se concatena la lista de errores devueltos por el SIN (ej. "EL CALCULO DEL MONTO TOTAL ES ERRONEO...").
    *   **Notificación:** Se muestra un mensaje de error claro al usuario indicando que la factura fue rechazada y el número consumido.

### Ejemplo Real (Caso de Prueba)

| N° Factura | Estado | Mensaje de Error Guardado | Causa |
| :--- | :--- | :--- | :--- |
| **893** | RECHAZADA | `Rechazada por el SIN sin detalle.` | Parser antiguo (no leía `mensajesList`). |
| **894** | RECHAZADA | `EL CALCULO DEL MONTO TOTAL ES ERRONEO Monto total esperado 170.00 enviado 120.00` | **Parser corregido.** Error de lógica de negocio detectado por el SIN. |
| **895** | VALIDADA | `(null)` | Factura emitida correctamente. |

### Beneficios
*   **Cumplimiento Normativo:** Se respeta la secuencia de facturación al no reutilizar números que el SIN ya ha "visto" y rechazado.
*   **Auditoría:** Queda un registro permanente en la base de datos de por qué falló una factura específica.
*   **Claridad:** El usuario sabe exactamente qué pasó y por qué no se generó la factura válida.

## Archivos Modificados
*   `facturador/tabs/facturacion_tab.py`: Lógica de manejo de respuesta SOAP (detección de código 902).
*   `facturador/response_handler.py`: Mejora en `parse_siat_response` para extraer correctamente la estructura `mensajesList` del XML de respuesta.
*   `facturador/data_access.py`: (Verificación) Soporte para guardar `mensajeError`.
