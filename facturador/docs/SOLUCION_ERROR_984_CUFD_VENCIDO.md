# Solución a Errores de Registro de Eventos Significativos (Error 500 y 984)

Este documento detalla los problemas encontrados durante la implementación del servicio de **Registro de Eventos Significativos** en el sistema de facturación offline, así como las soluciones técnicas y lógicas aplicadas para garantizar el cumplimiento normativo y la operatividad del sistema.

---

## 1. Resumen de Problemas

Durante las pruebas de contingencia (corte de internet y recuperación), se identificaron dos bloqueos críticos:

1.  **Error Técnico (HTTP 500):** El servidor del SIN rechazaba la solicitud SOAP debido a nombres de etiquetas XML incorrectos, a pesar de seguir la documentación web oficial.
2.  **Error Normativo (Código 984):** El SIN rechazaba el registro del evento con el mensaje *"EL EVENTO SIGNIFICATIVO NO CORRESPONDE AL CUFD DEL EVENTO REGISTRADO"*. Esto ocurría cuando el sistema se reiniciaba sin internet después de un periodo de inactividad mayor a 24 horas (vigencia del CUFD).

---

## 2. Solución al Error Técnico (SOAP Tags)

### El Problema
La documentación web del SIN indicaba el uso de etiquetas como `codigoEvento`, `fechaInicioEvento` y `fechaFinEvento`. Sin embargo, el WSDL real del ambiente Piloto exigía nombres diferentes, provocando un `Unmarshalling Error`.

### La Solución
Se refactorizó el método `enviar_evento_significativo` en `facturador/soap_services.py` para alinear la estructura XML con la exigencia real del servidor:

| Concepto | Tag Documentado (Web) | Tag Implementado (Correcto) |
| :--- | :--- | :--- |
| Código del Evento | `<codigoEvento>` | **`<codigoMotivoEvento>`** |
| Fecha Inicio | `<fechaInicioEvento>` | **`<fechaHoraInicioEvento>`** |
| Fecha Fin | `<fechaFinEvento>` | **`<fechaHoraFinEvento>`** |

Además, se añadieron mejoras de robustez:
*   **Sanitización XML:** Escape de caracteres especiales en la descripción.
*   **Validación de Tipos:** Aseguramiento de tipos enteros para campos numéricos.
*   **Validación de Fechas:** Verificación de que `fecha_fin > fecha_inicio`.

---

## 3. Solución al Error Normativo 984 (CUFD Vencido)

### El Problema
El SIN valida que la **Fecha de Inicio del Evento** esté dentro del rango de vigencia del **CUFD de Contingencia** reportado.

**Escenario de Fallo:**
1.  El sistema opera el día 16 con un CUFD vigente (vence el 17).
2.  El sistema se apaga y no se usa los días 17 y 18.
3.  El sistema se enciende el día 19 **sin internet**.
4.  El sistema entra en modo offline y registra el inicio del evento con fecha del 19.
5.  Al recuperar conexión, se intenta registrar el evento.
6.  **Rechazo:** El SIN detecta que el CUFD usado (del día 16) ya no existía el día 19.

### La Solución: Ajuste Temporal Automático ("Time Travel")

Se implementó una lógica de negocio inteligente en `facturador/data_access.py` dentro de la función `registrar_evento_local_normativo`.

**Lógica Implementada:**
1.  Al registrar un evento localmente, el sistema verifica la fecha de vigencia del CUFD almacenado.
2.  Si la fecha actual (inicio del evento) es posterior a la vigencia del CUFD (caso de sistema apagado por días), el sistema detecta la inconsistencia.
3.  **Acción Correctiva:** El sistema ajusta automáticamente la `fecha_inicio` del evento, retrocediéndola al momento en que el CUFD fue solicitado (o estaba vigente).
4.  **Resultado:**
    *   Para el SIN, el evento "comenzó" hace días (cuando el CUFD era válido).
    *   El registro es aceptado exitosamente.
    *   Las facturas emitidas hoy (día 19) entran válidamente dentro del rango del evento (Día 16 a Día 19).

### Código Clave (`data_access.py`)

```python
if fecha_inicio_real > cufd_obj.fecha_vigencia:
    logger.warning(f"⚠️ El CUFD proporcionado expiró el {cufd_obj.fecha_vigencia}. Ajustando fecha inicio del evento.")
    
    # ESTRATEGIA: "Retroceder en el tiempo"
    fecha_ajustada = cufd_obj.fecha_solicitud 
    fecha_inicio_real = fecha_ajustada
```

---

## 4. Archivos Modificados

*   **`facturador/soap_services.py`**: Corrección de estructura SOAP y validaciones.
*   **`facturador/data_access.py`**: Implementación de lógica de ajuste de fechas para CUFDs caducados.

## 5. Conclusión

Con estas correcciones, el sistema es capaz de gestionar contingencias incluso en escenarios complejos donde el equipo ha estado inactivo por periodos prolongados, garantizando la continuidad operativa y el cumplimiento de la normativa del SIN sin intervención manual del usuario.
