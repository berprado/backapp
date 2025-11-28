# 🛠️ Corrección de Numeración de Facturas y Manejo de Errores

Este documento detalla las correcciones implementadas para solucionar el problema de "quema" de números de factura cuando ocurre un error durante la generación o validación del XML, así como las mejoras en la interfaz de usuario para previsualizar el número de factura.

---

## 1. El Problema Identificado

En el flujo anterior, el sistema asignaba e incrementaba el número de factura **antes** de validar si la factura podía generarse correctamente. Esto causaba que, si ocurría un error (por ejemplo, validación XSD fallida por montos en cero), el número de factura se perdía ("quemaba"), rompiendo la secuencia correlativa exigida por la normativa.

**Ejemplo del fallo:**
1. Factura 862: Generada OK.
2. Intento Factura 863: Falla validación XSD. El sistema ya había incrementado el contador a 864.
3. Siguiente intento exitoso: Se genera con el número 864.
4. **Resultado:** Salto en la numeración (falta la 863).

---

## 2. Solución Implementada: Mecanismo de Rollback

Se implementó una estrategia de **"Validación Temprana y Reversión (Rollback)"** que garantiza la integridad de la secuencia numérica.

### 2.1. Cambios en `invoice_manager.py`

Se añadió la función `revertir_incremento_numero_factura(numero_fallido)` que permite retroceder el contador de manera segura.

*   **Lógica de seguridad:** La función verifica si el contador actual es exactamente `numero_fallido + 1`. Solo si esta condición se cumple, se realiza la reversión. Esto evita condiciones de carrera si otro proceso hubiera generado una factura en el interín.

### 2.2. Cambios en `facturacion_tab.py` (Lógica de Negocio)

Se modificó el flujo de emisión tanto para modo **Online** como **Offline**:

1.  **Validación Previa:** Se verifican condiciones críticas (como `total > 0`) **antes** de solicitar un número de factura.
2.  **Manejo de Excepciones:** Se envolvió el proceso de generación en un bloque `try-except` robusto.
3.  **Ejecución de Rollback:** Si ocurre cualquier error durante la generación, firma o validación del XML:
    *   Se elimina el archivo XML parcial si existe.
    *   Se llama a `revertir_incremento_numero_factura`.
    *   Se informa al usuario si el número fue recuperado exitosamente.

---

## 3. Mejora en la Interfaz de Usuario (UI)

Se aprovechó el acceso al archivo contador para mejorar la experiencia del usuario en la pestaña de facturación.

### 3.1. Previsualización del Número de Factura

Anteriormente, la vista previa de la factura mostraba el texto `(se asignará al emitir)` en el campo de número.

**Cambio realizado:**
*   El sistema ahora lee el archivo `invoice_number.txt` en modo de solo lectura.
*   Muestra en la vista previa el **número exacto** que tendrá la factura si se emite en ese momento.
*   Esto brinda mayor certeza al operador sobre la secuencia que se está siguiendo.

---

## 4. Archivos Modificados

| Archivo | Descripción del Cambio |
| :--- | :--- |
| `facturador/invoice_manager.py` | Implementación de `revertir_incremento_numero_factura`. |
| `facturador/tabs/facturacion_tab.py` | Implementación de lógica de rollback en `_handle_offline_submission` y `_handle_online_submission`. Implementación de lectura de número para previsualización. |

---

## 5. Conclusión

Con estas mejoras, el sistema garantiza que **solo se consumen números de factura para documentos válidos y generados exitosamente**, manteniendo la integridad de la secuencia correlativa y cumpliendo con la normativa de facturación.
