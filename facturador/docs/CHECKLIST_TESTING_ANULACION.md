# ✅ Checklist de Testing - Refactorización de Anulación

## 📋 Información General

**Fecha de testing:** _____________  
**Tester:** _____________  
**Versión del módulo:** 2.0.0  
**Ambiente:** ☐ Desarrollo  ☐ Piloto  ☐ Producción

---

## 🎯 Objetivos del Testing

Verificar que el módulo `anulacion.py` refactorizado:
1. Funcione correctamente en todos los escenarios
2. Muestre mensajes consistentes con `reversion.py`
3. No tenga errores de encoding o sesión
4. Integre correctamente con la UI

---

## 🔧 Pre-requisitos

### Ambiente Técnico
- [ ] Python 3.12 activado
- [ ] Base de datos sincronizada con SIAT
- [ ] CUFD vigente disponible
- [ ] Certificado digital configurado
- [ ] Variables de entorno (.env) correctas

### Datos de Prueba
- [ ] Al menos 3 facturas válidas en BD
- [ ] Al menos 1 factura ya anulada
- [ ] Al menos 1 factura fuera de plazo
- [ ] Conexión al ambiente piloto SIAT activa

---

## 📊 Casos de Prueba

### Caso 1: Anulación Exitosa (Código 905)

**Objetivo:** Verificar anulación normal de factura válida dentro del plazo

**Datos de entrada:**
- Número de factura: _______________
- Estado inicial: Válida
- Dentro del plazo: Sí
- Motivo: "Emitido con error"

**Pasos:**
1. [ ] Abrir Streamlit: `streamlit run main.py`
2. [ ] Navegar a pestaña "Anular o Revertir"
3. [ ] Seleccionar "Anular Factura"
4. [ ] Ingresar número de factura
5. [ ] Seleccionar motivo de anulación
6. [ ] Hacer clic en "Anular Factura"

**Verificaciones:**
- [ ] No hay errores en terminal/logs
- [ ] Mensaje de éxito aparece con formato Markdown
- [ ] Mensaje incluye: ✅ + descripción + número de factura + fecha + motivo
- [ ] **NO hay emojis duplicados** (ej: ❌ "✅ ✅ ANULACION...")
- [ ] Estado en BD cambió a "Anulada"
- [ ] Campo `fechaAnulacion` actualizado
- [ ] Campo `motivoAnulacion` guardado correctamente

**Logs esperados:**
```
[INFO] Iniciando proceso de anulacion para factura #XXX
[INFO] [BD] Factura #XXX encontrada. Estado actual: Valida
[INFO] [VALIDACION] Factura dentro del plazo de anulacion
[INFO] [CUFD] Obtenido exitosamente: ...
[INFO] [MOTIVO] Codigo de motivo: 1 - Emitido con error
[INFO] [SIAT] Enviando solicitud de anulacion...
[INFO] [EXITO] Solicitud de anulacion enviada correctamente.
[INFO] [PROCESAMIENTO] Iniciando analisis de respuesta para factura #XXX
[INFO] [PROCESAMIENTO] Codigo de estado: 905
[INFO] [EXITO] Anulacion confirmada para factura #XXX
[INFO] [BD] Factura #XXX actualizada exitosamente.
```

**Resultado:** ☐ PASS  ☐ FAIL  
**Observaciones:** _______________________________________________

---

### Caso 2: Rechazo - Factura Ya Anulada (Código 936)

**Objetivo:** Verificar que no se puede anular una factura múltiples veces

**Datos de entrada:**
- Número de factura: _______________ (usar la del Caso 1)
- Estado inicial: Anulada
- Motivo: "Cualquiera"

**Pasos:**
1. [ ] Intentar anular la misma factura del Caso 1

**Verificaciones:**
- [ ] Validación local rechaza antes de enviar al SIAT
- [ ] Mensaje muestra: ⚠️ "Factura ya anulada"
- [ ] Mensaje explica: "No es posible anular una factura múltiples veces"
- [ ] No se envía solicitud al SIAT (verificar logs)

**Logs esperados:**
```
[INFO] Iniciando proceso de anulacion para factura #XXX
[INFO] [BD] Factura #XXX encontrada. Estado actual: Anulada
[WARNING] [RECHAZO] Factura #XXX ya esta anulada
```

**Resultado:** ☐ PASS  ☐ FAIL  
**Observaciones:** _______________________________________________

---

### Caso 3: Rechazo - Factura Fuera de Plazo (Código 970)

**Objetivo:** Verificar validación de plazo (hasta día 9 del mes siguiente)

**Datos de entrada:**
- Número de factura: _______________ (emitida hace más de 1 mes y 9 días)
- Estado inicial: Válida
- Motivo: "Emitido con error"

**Pasos:**
1. [ ] Intentar anular factura antigua

**Verificaciones:**
- [ ] Validación local rechaza antes de enviar al SIAT
- [ ] Mensaje muestra: ⏰ "Fuera de plazo"
- [ ] Mensaje incluye fecha de emisión
- [ ] Mensaje cita la normativa (día 9 del mes siguiente)
- [ ] No se envía solicitud al SIAT

**Logs esperados:**
```
[INFO] Iniciando proceso de anulacion para factura #XXX
[INFO] [BD] Factura #XXX encontrada. Estado actual: Valida
[WARNING] [RECHAZO] Factura #XXX fuera de plazo
```

**Resultado:** ☐ PASS  ☐ FAIL  
**Observaciones:** _______________________________________________

---

### Caso 4: Rechazo - Factura Revertida

**Objetivo:** Verificar que factura revertida no puede ser anulada

**Datos de entrada:**
- Número de factura: _______________ (que tenga fechaValidacion != NULL)
- Estado inicial: Válida
- Condición: fechaValidacion IS NOT NULL
- Motivo: "Emitido con error"

**Pasos:**
1. [ ] Intentar anular factura que fue revertida

**Verificaciones:**
- [ ] Validación local rechaza
- [ ] Mensaje muestra: ⚠️ "Operación no permitida"
- [ ] Mensaje explica: "ya fue revertida y no puede ser anulada nuevamente"

**Logs esperados:**
```
[INFO] Iniciando proceso de anulacion para factura #XXX
[INFO] [BD] Factura #XXX encontrada. Estado actual: Valida
[WARNING] [RECHAZO] Factura #XXX fue revertida, no se puede anular
```

**Resultado:** ☐ PASS  ☐ FAIL  
**Observaciones:** _______________________________________________

---

### Caso 5: Error - Factura No Existe

**Objetivo:** Verificar manejo de factura inexistente

**Datos de entrada:**
- Número de factura: 999999 (no existe en BD)
- Motivo: "Cualquiera"

**Pasos:**
1. [ ] Intentar anular factura inexistente

**Verificaciones:**
- [ ] Mensaje de error claro: "No se encontró la factura"
- [ ] No se envía solicitud al SIAT
- [ ] No hay excepciones no manejadas

**Logs esperados:**
```
[INFO] Iniciando proceso de anulacion para factura #999999
[ERROR] [ERROR] No se encontro la factura #999999
```

**Resultado:** ☐ PASS  ☐ FAIL  
**Observaciones:** _______________________________________________

---

### Caso 6: Error - CUFD No Vigente

**Objetivo:** Verificar manejo cuando no hay CUFD vigente

**Pre-condición:**
- [ ] Marcar todos los CUFD en BD como vigente=0 (temporal)

**Datos de entrada:**
- Número de factura: _______________ (válida)
- Motivo: "Emitido con error"

**Pasos:**
1. [ ] Intentar anular factura sin CUFD vigente

**Verificaciones:**
- [ ] Mensaje de error: "No se pudo obtener el CUFD vigente"
- [ ] Sugiere verificar sincronización
- [ ] No se envía solicitud al SIAT

**Post-condición:**
- [ ] Restaurar CUFD vigente en BD

**Resultado:** ☐ PASS  ☐ FAIL  
**Observaciones:** _______________________________________________

---

### Caso 7: Consistencia con Reversión

**Objetivo:** Verificar que mensajes y flujo son idénticos a reversion.py

**Pasos:**
1. [ ] Revertir una factura (usar pestaña "Revertir Anulación")
2. [ ] Anular una factura (usar pestaña "Anular Factura")
3. [ ] Comparar ambos mensajes de éxito

**Verificaciones:**
- [ ] Formato Markdown idéntico (negrita, emojis, saltos de línea)
- [ ] Estructura del mensaje igual (título + detalles + fecha)
- [ ] Prefijos de logs idénticos ([PROCESAMIENTO], [EXITO], [ERROR])
- [ ] Emojis sin duplicación en ambos casos
- [ ] Logging estructurado igual

**Resultado:** ☐ PASS  ☐ FAIL  
**Observaciones:** _______________________________________________

---

## 🐛 Verificaciones Técnicas

### Prevención de Errores

**UnicodeEncodeError (Emojis en logs):**
- [ ] Logs no contienen emojis (✅ ❌ ⚠️)
- [ ] Solo texto ASCII en logs: [EXITO], [ERROR], [RECHAZADO]
- [ ] No hay errores de encoding en terminal Windows

**DetachedInstanceError (SQLAlchemy):**
- [ ] No hay error al acceder a `factura.numeroFactura` después de session.close()
- [ ] Variable `numero_factura` guardada antes de operaciones de sesión
- [ ] Todos los accesos a atributos de factura usan variables guardadas

**Logging:**
- [ ] No se usa `anulacion_logger` (deprecado)
- [ ] Solo se usa `logger` de `logger_config`
- [ ] Todos los logs tienen prefijos estructurados

---

## 📊 Verificación de BD

Después de anulación exitosa (Caso 1), verificar en BD:

```sql
SELECT 
    numeroFactura,
    estado,
    fechaAnulacion,
    motivoAnulacion,
    fechaValidacion
FROM factura_cabecera
WHERE numeroFactura = XXX;
```

**Resultados esperados:**
- [ ] `estado` = 'Anulada'
- [ ] `fechaAnulacion` = timestamp reciente
- [ ] `motivoAnulacion` = texto del motivo seleccionado
- [ ] `fechaValidacion` = NULL (no debe tener valor)

---

## 🎨 Verificación de UI

### Mensajes de Éxito
- [ ] Fondo verde claro (st.success)
- [ ] Texto en negrita para títulos (`**texto**`)
- [ ] Emojis visibles y únicos (no duplicados)
- [ ] Saltos de línea correctos
- [ ] Legible y profesional

### Mensajes de Error
- [ ] Fondo rojo claro (st.error)
- [ ] Texto explicativo claro
- [ ] Sugerencias de acción cuando aplica

### Mensajes de Advertencia
- [ ] Fondo amarillo claro (st.warning)
- [ ] Contexto adecuado

---

## 📝 Testing Adicional Opcional

### Test de Rendimiento
- [ ] Anulación completa en < 5 segundos
- [ ] Validaciones locales en < 100ms
- [ ] Logs no impactan rendimiento

### Test de Stress
- [ ] 10 anulaciones consecutivas sin error
- [ ] Sin memory leaks (verificar uso de RAM)
- [ ] Sesiones de BD cerradas correctamente

### Test de Integración
- [ ] Anular → Verificar estado (en pestaña "Verificar Factura")
- [ ] Anular → Intentar revertir (debe fallar)
- [ ] Anular → Intentar anular de nuevo (debe fallar)

---

## 🚦 Criterios de Aceptación

### ✅ Test APROBADO si:
1. Todos los casos 1-7 pasan exitosamente
2. No hay errores de UnicodeEncodeError o DetachedInstanceError
3. Mensajes son consistentes con reversion.py
4. BD se actualiza correctamente
5. Logs son claros y estructurados

### ❌ Test RECHAZADO si:
1. Cualquier caso de prueba falla
2. Hay errores no manejados
3. Mensajes tienen emojis duplicados
4. Inconsistencias con reversion.py
5. BD no se actualiza o se corrompe

---

## 📋 Reporte Final

**Casos pasados:** _____ / 7  
**Estado general:** ☐ APROBADO  ☐ RECHAZADO  ☐ CON OBSERVACIONES  

**Bugs encontrados:**
1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________

**Mejoras sugeridas:**
1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________

**Firma del tester:** _______________  
**Fecha de aprobación:** _______________

---

## 🔄 Próximos Pasos Después del Testing

Si el test es APROBADO:
- [ ] Documentar resultados en REFACTORIZACION_ANULACION.md
- [ ] Hacer commit con mensaje descriptivo
- [ ] Actualizar CHANGELOG.md
- [ ] Notificar al equipo sobre cambios
- [ ] Desplegar en ambiente piloto

Si el test es RECHAZADO:
- [ ] Crear tickets de bugs en sistema de seguimiento
- [ ] Priorizar correcciones
- [ ] Volver a ejecutar checklist después de correcciones

---

**Versión del checklist:** 1.0.0  
**Última actualización:** 15 de octubre de 2025
