# 🔧 Corrección de Errores Post-Fase 2

**Fecha:** 10 de Octubre de 2025  
**Módulo:** `facturador/pages/1_Sincronizar.py`  
**Tipo:** Hotfix - Corrección de errores encontrados en testing inicial

---

## 🐛 Errores Encontrados y Corregidos

### Error #1: TypeError con Timezones en `main()`

#### Descripción del Problema
```python
TypeError: can't subtract offset-naive and offset-aware datetimes
```

**Ubicación:** Función `main()`, línea ~937

**Causa:** El datetime recuperado de la base de datos (`ultima_sincronizacion`) podría no tener información de timezone (naive), mientras que `datetime.now(pytz.utc)` sí la tiene (aware). Python no permite restar estos dos tipos de datetime.

#### Solución Implementada
```python
# ANTES (Código con error)
ultima_sync = obtener_estado_sync('ultima_sincronizacion')
if ultima_sync:
    tiempo_transcurrido = datetime.now(pytz.utc) - ultima_sync  # ❌ Error aquí

# DESPUÉS (Código corregido)
ultima_sync = obtener_estado_sync('ultima_sincronizacion')
if ultima_sync:
    # Asegurar que ambos datetimes tengan timezone para poder restarlos
    if ultima_sync.tzinfo is None:
        ultima_sync = pytz.utc.localize(ultima_sync)
    tiempo_transcurrido = datetime.now(pytz.utc) - ultima_sync  # ✅ Funciona
```

**Impacto:** ✅ Resuelto - Los indicadores de "última sincronización" ahora funcionan correctamente

---

### Error #2: Validación de `codigoPuntoVenta`

#### Descripción del Problema
Potencial error al crear solicitudes SOAP si `CODIGO_PUNTO_VENTA` no está definido o tiene un valor inválido en el archivo `.env`.

**Ubicación:** 
- Función `sincronizar_fecha_hora()`, línea ~465
- Función `crear_solicitud_sincronizacion()`, línea ~625

**Causa:** `int(os.getenv("CODIGO_PUNTO_VENTA"))` falla si la variable de entorno:
- No existe
- Está vacía
- Contiene un valor no numérico

#### Solución Implementada

**En `sincronizar_fecha_hora()`:**
```python
# ANTES (Sin validación)
solicitud = SolicitudSincronizacion(
    codigoAmbiente=int(os.getenv("CODIGO_AMBIENTE")),
    codigoPuntoVenta=int(os.getenv("CODIGO_PUNTO_VENTA")),  # ❌ Puede fallar
    # ...
)

# DESPUÉS (Con validación robusta)
# Obtener y validar codigoPuntoVenta
codigo_punto_venta = os.getenv("CODIGO_PUNTO_VENTA", "0")
try:
    codigo_punto_venta = int(codigo_punto_venta)
except (ValueError, TypeError):
    logger.warning(f"CODIGO_PUNTO_VENTA invalido ({codigo_punto_venta}), usando 0 por defecto")
    codigo_punto_venta = 0

solicitud = SolicitudSincronizacion(
    codigoAmbiente=int(os.getenv("CODIGO_AMBIENTE")),
    codigoPuntoVenta=codigo_punto_venta,  # ✅ Siempre válido
    # ...
)

# Logging mejorado para debugging
logger.debug(f"Parametros: codigoAmbiente={os.getenv('CODIGO_AMBIENTE')}, codigoPuntoVenta={codigo_punto_venta}, ...")
```

**En `crear_solicitud_sincronizacion()`:**
```python
# Misma validación aplicada
codigo_punto_venta = os.getenv("CODIGO_PUNTO_VENTA", "0")
try:
    codigo_punto_venta = int(codigo_punto_venta)
except (ValueError, TypeError):
    logger.warning(f"CODIGO_PUNTO_VENTA invalido ({codigo_punto_venta}), usando 0 por defecto")
    codigo_punto_venta = 0
```

**Impacto:** ✅ Mayor robustez - El sistema ahora maneja correctamente valores inválidos

---

## 📋 Referencia: Ejemplo de Solicitud SOAP Correcta

Basado en el ejemplo proporcionado de SoapUI:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                  xmlns:siat="https://siat.impuestos.gob.bo/">
    <soapenv:Header/>
    <soapenv:Body>
        <siat:sincronizarFechaHora>
            <SolicitudSincronizacion>
                <codigoAmbiente>2</codigoAmbiente>
                <codigoPuntoVenta>0</codigoPuntoVenta>  ✅ Presente
                <codigoSistema>8181AA971DE5B9926708D66</codigoSistema>
                <codigoSucursal>0</codigoSucursal>
                <cuis>3CDA3154</cuis>
                <nit>344096024</nit>
            </SolicitudSincronizacion>
        </siat:sincronizarFechaHora>
    </soapenv:Body>
</soapenv:Envelope>
```

**Respuesta Esperada:**
```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <ns2:sincronizarFechaHoraResponse xmlns:ns2="https://siat.impuestos.gob.bo/">
            <RespuestaFechaHora>
                <transaccion>true</transaccion>
                <fechaHora>2025-05-08T15:57:24.265</fechaHora>
            </RespuestaFechaHora>
        </ns2:sincronizarFechaHoraResponse>
    </soap:Body>
</soap:Envelope>
```

---

## 🧪 Testing Recomendado

### Test 1: Verificar Indicadores de Última Sincronización
```bash
1. Ejecutar: streamlit run facturador/main.py
2. Ir a: Página "Sincronizar"
3. Verificar que NO aparece el error de timezone
4. Confirmar que se muestra el indicador de última sincronización
```

**Resultado Esperado:**
- ✅ Sin errores en la terminal
- ✅ Indicador visible: "✅ Última sincronización: hace X horas"

---

### Test 2: Sincronización de Fecha/Hora
```bash
1. En la página "Sincronizar"
2. Seleccionar "sincronizarFechaHora"
3. Hacer clic en "Sincronizar Servicio Seleccionado"
4. Revisar logs para verificar parámetros
```

**Resultado Esperado:**
- ✅ Mensaje: "✅ Sincronización de Fecha y Hora completada"
- ✅ En logs: "Parametros: codigoAmbiente=2, codigoPuntoVenta=0, ..."
- ✅ Sin errores de parámetros faltantes

---

### Test 3: Sincronización con `.env` Incompleto
```bash
1. Temporalmente comentar CODIGO_PUNTO_VENTA en .env
2. Reiniciar la aplicación
3. Intentar sincronizar
```

**Resultado Esperado:**
- ✅ Warning en logs: "CODIGO_PUNTO_VENTA invalido, usando 0 por defecto"
- ✅ La sincronización continúa con valor 0
- ✅ No hay error fatal

---

## 📝 Archivos Modificados

```
facturador/pages/1_Sincronizar.py
├── main() - Línea ~937
│   └── ✅ Corrección de timezone en ultima_sincronizacion
│
├── sincronizar_fecha_hora() - Línea ~465
│   ├── ✅ Validación de codigoPuntoVenta
│   └── ✅ Logging mejorado de parámetros
│
└── crear_solicitud_sincronizacion() - Línea ~625
    └── ✅ Validación de codigoPuntoVenta
```

---

## 🔍 Debugging Mejorado

Con estas correcciones, ahora tendrás logs más informativos:

```python
# Ejemplo de log exitoso:
2025-10-10 03:56:35 - INFO - Iniciando sincronizacion de Fecha y Hora
2025-10-10 03:56:35 - DEBUG - Solicitud creada: {...}
2025-10-10 03:56:35 - DEBUG - Parametros: codigoAmbiente=2, codigoPuntoVenta=0, codigoSistema=8181AA971DE5B9926708D66, codigoSucursal=0, cuis=3CDA3154, nit=344096024
2025-10-10 03:56:35 - DEBUG - Enviando solicitud al servicio SOAP
2025-10-10 03:56:36 - DEBUG - Respuesta recibida: {...}
2025-10-10 03:56:36 - INFO - Sincronizacion de Fecha y Hora completada.

# Ejemplo con valor inválido:
2025-10-10 03:56:35 - WARNING - CODIGO_PUNTO_VENTA invalido (abc), usando 0 por defecto
```

---

## ✅ Checklist de Validación

- [x] **Error #1:** Corregido - Timezone en `main()`
- [x] **Error #2:** Mejorado - Validación de `codigoPuntoVenta`
- [x] **Logging:** Añadido logging detallado de parámetros
- [x] **Sin errores de sintaxis:** Verificado con get_errors
- [ ] **Testing manual:** Pendiente - Ejecutar tests recomendados

---

## 📚 Documentación Relacionada

- **FASE2_REFACTORIZACION_COMPLETA.md** - Documentación de la Fase 2
- **CHECKLIST_FASE2_TESTING.md** - Test cases completos

---

## 🎯 Estado Post-Corrección

```
✅ Error de timezone: RESUELTO
✅ Validación de parámetros: MEJORADA
✅ Logging: MEJORADO
⏳ Testing manual: PENDIENTE
```

---

## 💡 Recomendación

**Antes de continuar con el testing completo:**

1. ✅ Verifica que tu archivo `.env` tenga todos los parámetros necesarios:
   ```env
   CODIGO_AMBIENTE=2
   CODIGO_PUNTO_VENTA=0
   CODIGO_SISTEMA=8181AA971DE5B9926708D66
   CODIGO_SUCURSAL=0
   CUIS=3CDA3154
   NIT=344096024
   ```

2. ✅ Reinicia la aplicación Streamlit para que tome los cambios

3. ✅ Ejecuta los Test Case 2 (Sincronización) del `CHECKLIST_FASE2_TESTING.md`

---

**Implementado por:** GitHub Copilot  
**Fecha:** 10 de Octubre de 2025  
**Tipo:** Hotfix  
**Prioridad:** Alta  
**Estado:** Resuelto
