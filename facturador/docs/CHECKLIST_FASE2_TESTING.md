# ✅ Checklist de Testing - Fase 2

**Módulo:** `facturador/pages/1_Sincronizar.py`  
**Fecha:** Octubre 2025  
**Objetivo:** Validar que la refactorización completa funciona correctamente

---

## 🎯 Objetivo del Testing

Verificar que todas las funciones refactorizadas funcionan correctamente sin variables globales y que el sistema de gestión de estado centralizado opera como se espera.

---

## 📋 Test Cases

### ✅ Test Case 1: Verificar Eliminación de Variables Globales

**Objetivo:** Confirmar que no existen referencias a variables globales en el código

**Pasos:**
1. Abrir el archivo `1_Sincronizar.py`
2. Buscar la palabra `global` en todo el archivo (Ctrl+F)
3. Verificar que SOLO aparezca en el comentario explicativo (línea ~313)

**Resultado Esperado:**
- ✅ La única mención de `global` debe estar en el comentario:
  ```python
  # NOTA: Las variables globales remote_time, local_time y time_difference
  # han sido ELIMINADAS y reemplazadas por el sistema de gestion de estado
  ```
- ✅ No debe haber declaraciones `global remote_time, local_time, time_difference`

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

---

### ✅ Test Case 2: Sincronización de Fecha y Hora

**Objetivo:** Validar que `sincronizar_fecha_hora()` funciona correctamente

**Pre-condiciones:**
- Sistema con conexión a Internet
- Variables de entorno configuradas correctamente

**Pasos:**
1. Ejecutar la aplicación: `streamlit run facturador/main.py`
2. Navegar a la página "Sincronizar"
3. Hacer clic en "Sincronizar Servicio Seleccionado" con `sincronizarFechaHora`
4. Observar los mensajes en la UI

**Resultado Esperado:**
- ✅ Mensaje: "✅ Iniciando sincronización de Fecha y Hora"
- ✅ Mensaje: "✅ Sincronización de Fecha y Hora completada"
- ✅ Se muestra información de sincronización automáticamente
- ✅ No hay errores sobre variables globales no definidas

**Verificación en Logs:**
```python
# Buscar en logs/sincronizacion_YYYYMMDD.log:
# - "Estado sync actualizado: remote_time = ..."
# - "Estado sync actualizado: local_time = ..."
# - "Estado sync actualizado: time_difference = ..."
# - "Sincronización guardada exitosamente: ..."
```

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

---

### ✅ Test Case 3: Mostrar Información de Sincronización

**Objetivo:** Validar que `mostrar_informacion_sincronizacion()` lee correctamente del estado

**Pre-condiciones:**
- Debe haberse ejecutado una sincronización exitosa (Test Case 2)

**Pasos:**
1. En la página "Sincronizar"
2. Hacer clic en "Mostrar información de sincronización"
3. Observar la información mostrada

**Resultado Esperado:**
- ✅ Se muestra "Hora del servidor remoto (Bolivia)"
- ✅ Se muestra "Hora local"
- ✅ Se muestra "Diferencia de tiempo" en formato legible (ej: "+00:02:15.340")
- ✅ Se muestra "Total en segundos"
- ✅ No hay errores sobre variables globales

**Ejemplo de Salida Esperada:**
```
Hora del servidor remoto (Bolivia):
2025-10-09 14:30:45.123

Hora local:
2025-10-09 14:30:47.270

Diferencia de tiempo:
+00:02.147
Total en segundos: +2.147 segundos
```

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

---

### ✅ Test Case 4: Indicadores de Estado en Main

**Objetivo:** Verificar que `main()` muestra indicadores de última sincronización

**Escenario 4.1: Primera Vez (Sin Sincronización Previa)**

**Pasos:**
1. Limpiar la base de datos (opcional, si es posible)
2. Recargar la página "Sincronizar"

**Resultado Esperado:**
- ✅ El título "Sincronizar Datos" se muestra
- ✅ NO aparece indicador de última sincronización (porque no hay)
- ✅ Se puede continuar con la sincronización normalmente

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

---

**Escenario 4.2: Sincronización Reciente (< 1 hora)**

**Pasos:**
1. Realizar una sincronización completa
2. Inmediatamente recargar la página

**Resultado Esperado:**
- ✅ Mensaje verde: "✅ Última sincronización: hace X minutos"
- ✅ X debe ser un número pequeño (< 60)

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

---

**Escenario 4.3: Sincronización del Día (1-24 horas)**

**Pasos:**
1. Modificar manualmente `ultima_sincronizacion` en BD para que tenga 5 horas de antigüedad
   ```sql
   UPDATE sincronizacion_estado 
   SET ultima_sincronizacion = NOW() - INTERVAL '5 hours';
   ```
2. Recargar la página

**Resultado Esperado:**
- ✅ Mensaje azul: "ℹ️ Última sincronización: hace 5 horas"

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

---

**Escenario 4.4: Sincronización Desactualizada (> 24 horas)**

**Pasos:**
1. Modificar manualmente `ultima_sincronizacion` en BD para que tenga 2 días de antigüedad
   ```sql
   UPDATE sincronizacion_estado 
   SET ultima_sincronizacion = NOW() - INTERVAL '2 days';
   ```
2. Recargar la página

**Resultado Esperado:**
- ✅ Mensaje amarillo: "⚠️ Última sincronización: hace 2 días"
- ✅ Texto de recomendación: "Se recomienda sincronizar al menos una vez al día"

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

---

### ✅ Test Case 5: Persistencia entre Recargas

**Objetivo:** Verificar que el estado persiste correctamente entre recargas de Streamlit

**Pasos:**
1. Realizar una sincronización completa
2. Recargar la página completamente (F5)
3. Hacer clic en "Mostrar información de sincronización"

**Resultado Esperado:**
- ✅ La información de sincronización sigue disponible
- ✅ Los valores mostrados son los mismos que antes de recargar
- ✅ El indicador de "última sincronización" es correcto

**Verificación en Logs:**
```python
# Buscar en logs:
# - "Ultima sincronizacion cargada desde BD: ..."
# Esto confirma que el estado se recuperó de la BD
```

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

---

### ✅ Test Case 6: Sincronizar Todo

**Objetivo:** Validar que "Sincronizar Todo" funciona con el nuevo sistema

**Pasos:**
1. En la página "Sincronizar"
2. Hacer clic en "Sincronizar Todo"
3. Esperar a que complete (puede tomar varios minutos)

**Resultado Esperado:**
- ✅ Sincronización de fecha/hora se completa primero
- ✅ Todas las tablas paramétricas se sincronizan sin errores
- ✅ Se muestra el resumen final con [OK] o [ERROR] para cada servicio
- ✅ El indicador de "última sincronización" se actualiza

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

---

### ✅ Test Case 7: Corrección de Diferencia Horaria Anormal

**Objetivo:** Verificar que la corrección manual de diferencias sigue funcionando

**Pre-condiciones:**
- Este test requiere forzar una diferencia horaria anormal (>24 horas)
- Puede requerir modificar temporalmente el código o la hora del sistema

**Pasos:**
1. (Opcional) Modificar temporalmente `calcular_diferencia_horaria()` para retornar una diferencia de 25 horas
2. Realizar una sincronización
3. Observar el mensaje de advertencia
4. Hacer clic en "Corregir diferencia horaria" si aparece el botón

**Resultado Esperado:**
- ✅ Aparece mensaje: "⚠️ Diferencia de tiempo anormal detectada"
- ✅ El botón "Corregir diferencia horaria" es visible
- ✅ Al hacer clic, la diferencia se establece en 0
- ✅ Mensaje: "✅ Diferencia horaria corregida manualmente"

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido | [x] Omitido (requiere setup especial)

---

### ✅ Test Case 8: Verificación en Inspector de Estado

**Objetivo:** Inspeccionar directamente `st.session_state` para verificar la estructura

**Pasos:**
1. Añadir temporalmente al final de `main()`:
   ```python
   with st.expander("🔍 Inspector de Estado (DEBUG)"):
       st.write("Estado completo de sincronización:")
       st.json(st.session_state.sync_state if 'sync_state' in st.session_state else {})
   ```
2. Recargar la página
3. Expandir el inspector
4. Verificar la estructura de datos

**Resultado Esperado:**
```json
{
  "remote_time": "2025-10-09T14:30:45.123000-04:00",
  "local_time": "2025-10-09T14:30:47.270000-04:00",
  "time_difference": "0:00:02.147000",
  "ultima_sincronizacion": "2025-10-09T18:30:47.500000+00:00",
  "estado_comunicacion": "no_verificado",
  "ultima_verificacion": null,
  "sincronizaciones_completadas": []
}
```

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

---

### ✅ Test Case 9: Logs de Depuración

**Objetivo:** Verificar que los logs contienen toda la información necesaria para debugging

**Pasos:**
1. Realizar una sincronización completa
2. Abrir `logs/sincronizacion_YYYYMMDD.log`
3. Buscar las siguientes entradas

**Resultado Esperado:**
- ✅ `"Estado de sincronizacion inicializado en session_state"`
- ✅ `"Estado sync actualizado: remote_time = ..."`
- ✅ `"Estado sync actualizado: local_time = ..."`
- ✅ `"Estado sync actualizado: time_difference = ..."`
- ✅ `"Sincronización guardada exitosamente: ..."`
- ✅ No hay mensajes de error sobre variables globales

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

---

### ✅ Test Case 10: Modo Offline

**Objetivo:** Verificar que el sistema funciona correctamente sin conexión

**Pasos:**
1. Desconectar la red o detener el servicio SIAT
2. Navegar a la página "Sincronizar"
3. Intentar sincronizar

**Resultado Esperado:**
- ✅ Mensaje de advertencia sobre modo offline
- ✅ No hay errores de variables globales
- ✅ La aplicación no se bloquea
- ✅ Se muestran instrucciones claras al usuario

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

---

## 📊 Resumen de Resultados

| Test Case | Estado | Notas |
|-----------|--------|-------|
| TC1: Variables Globales | [ ] | |
| TC2: Sincronización | [ ] | |
| TC3: Mostrar Info | [ ] | |
| TC4.1: Primera Vez | [ ] | |
| TC4.2: Reciente | [ ] | |
| TC4.3: Del Día | [ ] | |
| TC4.4: Desactualizada | [ ] | |
| TC5: Persistencia | [ ] | |
| TC6: Sincronizar Todo | [ ] | |
| TC7: Corrección Anormal | [ ] | |
| TC8: Inspector | [ ] | |
| TC9: Logs | [ ] | |
| TC10: Modo Offline | [ ] | |

**Total Aprobados:** 0 / 13  
**Total Fallidos:** 0 / 13  
**Total Omitidos:** 0 / 13

---

## 🐛 Registro de Bugs Encontrados

### Bug #1
**Descripción:**  
**Severidad:** [ ] Crítico | [ ] Alto | [ ] Medio | [ ] Bajo  
**Pasos para Reproducir:**  
**Resultado Esperado:**  
**Resultado Actual:**  
**Estado:** [ ] Abierto | [ ] En Progreso | [ ] Resuelto

---

---

## 🆕 Test Cases Adicionales - Corrección de Botón

### ✅ Test Case 11: Botón Visible en Modo Offline

**Objetivo:** Verificar que el botón "Mostrar Información..." sea visible sin conexión

**Pre-condiciones:**
- Sincronización previa exitosa (datos en caché)
- Conexión a internet desconectada

**Pasos:**
1. Desconectar internet (físicamente o en configuración de red)
2. Reiniciar la aplicación Streamlit
3. Navegar a "Sincronizar"
4. Observar la presencia del botón

**Resultado Esperado:**
- ✅ El botón "📊 Mostrar Información de Última Sincronización" es visible
- ✅ El botón aparece ANTES del mensaje de error de conectividad
- ✅ El botón tiene emoji 📊 y tooltip explicativo

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

**Documentación Relacionada:** `CORRECCION_BOTON_SINCRONIZACION.md` - TC-BOTON-001

---

### ✅ Test Case 12: Funcionalidad del Botón Offline

**Objetivo:** Validar que el botón funcione correctamente sin conexión

**Pre-condiciones:**
- Modo offline confirmado (TC-11 pasado)
- Botón visible en pantalla

**Pasos:**
1. Estar en modo offline
2. Hacer clic en "📊 Mostrar Información de Última Sincronización"
3. Observar la respuesta de la aplicación

**Resultado Esperado:**
- ✅ El botón responde al clic inmediatamente
- ✅ Se muestra un `st.info()` con:
  - Hora remota del SIN (última registrada)
  - Hora local del sistema (última registrada)
  - Diferencia horaria (última calculada)
- ✅ NO se genera error de conexión
- ✅ NO se intenta comunicación con SIAT
- ✅ Los datos provienen de `st.session_state`

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

**Documentación Relacionada:** `CORRECCION_BOTON_SINCRONIZACION.md` - TC-BOTON-002

---

### ✅ Test Case 13: Botón No Duplicado

**Objetivo:** Asegurar que el botón antiguo fue eliminado correctamente

**Pasos:**
1. Conectar internet
2. Navegar a "Sincronizar"
3. Realizar una sincronización exitosa
4. Contar cuántas veces aparece el botón de información en la UI

**Resultado Esperado:**
- ✅ El botón aparece UNA SOLA VEZ en la página
- ✅ El botón está ubicado después de los indicadores visuales
- ✅ El botón está ubicado ANTES de la verificación de disponibilidad
- ✅ NO hay botón duplicado dentro del bloque `if exito:`

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

**Documentación Relacionada:** `CORRECCION_BOTON_SINCRONIZACION.md` - TC-BOTON-003

---

### ✅ Test Case 14: Persistencia entre Sesiones

**Objetivo:** Verificar que los datos mostrados persistan correctamente

**Pasos:**
1. Realizar una sincronización exitosa
2. Hacer clic en el botón y anotar los datos mostrados
3. Cerrar completamente Streamlit
4. Reiniciar la aplicación
5. Sin sincronizar nuevamente, hacer clic en el botón

**Resultado Esperado:**
- ✅ Los datos mostrados son idénticos a los anotados
- ✅ La aplicación recuperó datos de la base de datos correctamente
- ✅ `inicializar_estado_sincronizacion()` funcionó
- ✅ NO hay pérdida de información entre sesiones

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

**Documentación Relacionada:** `CORRECCION_BOTON_SINCRONIZACION.md` - TC-BOTON-005

---

### ✅ Test Case 15: Caché Vacío (Edge Case)

**Objetivo:** Validar comportamiento cuando no hay sincronizaciones previas

**Pre-condiciones:**
- Base de datos limpia o tabla `sincronizacion_estado` vacía

**Pasos:**
1. Limpiar datos previos de sincronización
2. Reiniciar la aplicación
3. Navegar a "Sincronizar"
4. Hacer clic en el botón SIN haber sincronizado antes

**Resultado Esperado:**
- ✅ El botón es visible y clicable
- ✅ Al hacer clic, muestra mensaje informativo:
  ```
  ℹ️ No hay información de sincronización disponible.
  Realiza una sincronización para ver los datos.
  ```
- ✅ NO se genera error de ejecución
- ✅ La aplicación maneja correctamente `None` values

**Estado:** [ ] Pendiente | [ ] Aprobado | [ ] Fallido

**Documentación Relacionada:** `CORRECCION_BOTON_SINCRONIZACION.md` - TC-BOTON-006

---

## ✅ Aprobación Final

**Testing Completado Por:** _________________  
**Fecha:** _________________  
**Resultado:** [ ] Aprobado | [ ] Rechazado | [ ] Aprobado con Observaciones

**Comentarios:**

---

**Notas:**
- Marcar cada test como [x] cuando se complete
- Documentar cualquier comportamiento inesperado en la sección de bugs
- **IMPORTANTE:** Los Test Cases 11-15 corresponden a la corrección del botón (27 ene 2025)
- Este checklist debe completarse ANTES de mergear la Fase 2
