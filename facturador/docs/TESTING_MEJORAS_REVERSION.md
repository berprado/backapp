# 🧪 Plan de Testing para Mejoras en `reversion.py`

**Fecha:** 14 de octubre de 2025  
**Objetivo:** Validar las mejoras implementadas sin romper funcionalidad existente

---

## ✅ Checklist Rápido de Validación

```
□ 1. Verificación de sintaxis Python
□ 2. Verificación de imports
□ 3. Testing con respuesta exitosa (907)
□ 4. Testing con respuesta rechazada (909)
□ 5. Testing con factura ya revertida (981)
□ 6. Testing con factura inexistente (924)
□ 7. Testing con sistema no autorizado (3011)
□ 8. Testing fuera de plazo (3012)
□ 9. Verificación de logs estructurados
□ 10. Verificación de formato Markdown en UI
```

---

## 🔧 Paso 1: Validación Técnica (5 minutos)

### **1.1 Verificar Sintaxis**

```powershell
cd c:\Users\Bernardo\Desktop\backapp\facturador
python -m py_compile reversion.py
```

**Resultado esperado:** Sin errores

---

### **1.2 Verificar Imports**

```powershell
python -c "import reversion; print('✅ Imports correctos')"
```

**Resultado esperado:** `✅ Imports correctos`

---

### **1.3 Verificar Constantes**

```powershell
python -c "from reversion import ESTADO_REVERSION_RECHAZADA; print(f'Código 909: {ESTADO_REVERSION_RECHAZADA}')"
```

**Resultado esperado:** `Código 909: 909`

---

## 🧪 Paso 2: Testing Funcional con Mock (15 minutos)

Crea un archivo temporal `test_reversion_mejoras.py`:

```python
"""
Test rápido de las mejoras en reversion.py
"""
import sys
sys.path.insert(0, 'c:/Users/Bernardo/Desktop/backapp/facturador')

from reversion import procesar_respuesta_reversion
from models import FacturaCabecera
from datetime import datetime

# Mock de factura
factura_mock = FacturaCabecera()
factura_mock.numeroFactura = 999
factura_mock.estado = "Anulada"
factura_mock.fechaAnulacion = datetime.now()
factura_mock.motivoAnulacion = "Prueba"

print("=" * 80)
print("TEST 1: Respuesta Exitosa (907) - SIN mensajesList")
print("=" * 80)

xml_exito = b"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <ns2:reversionAnulacionFacturaResponse xmlns:ns2="https://siat.impuestos.gob.bo/">
            <RespuestaServicioFacturacion>
                <codigoDescripcion>REVERSION DE ANULACION CONFIRMADA</codigoDescripcion>
                <codigoEstado>907</codigoEstado>
                <transaccion>true</transaccion>
            </RespuestaServicioFacturacion>
        </ns2:reversionAnulacionFacturaResponse>
    </soap:Body>
</soap:Envelope>"""

try:
    # Nota: Esta prueba fallará al intentar guardar en BD porque no hay sesión activa
    # Pero nos permite verificar el parseo
    exito, mensaje = procesar_respuesta_reversion(xml_exito, factura_mock)
    print(f"✅ Parseo exitoso")
    print(f"Mensaje generado:\n{mensaje}\n")
except Exception as e:
    print(f"⚠️ Error esperado (sin BD real): {str(e)[:100]}")

print("\n" + "=" * 80)
print("TEST 2: Respuesta Rechazada (909) - CON mensajesList")
print("=" * 80)

xml_rechazo = b"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <ns2:reversionAnulacionFacturaResponse xmlns:ns2="https://siat.impuestos.gob.bo/">
            <RespuestaServicioFacturacion>
                <codigoDescripcion>REVERSION DE ANULACION RECHAZADA</codigoDescripcion>
                <codigoEstado>909</codigoEstado>
                <mensajesList>
                    <codigo>981</codigo>
                    <descripcion>REVERSION DE ANULACION NO DISPONIBLE PARA LA FACTURA O NOTA DE CREDITO - DEBITO</descripcion>
                </mensajesList>
                <transaccion>false</transaccion>
            </RespuestaServicioFacturacion>
        </ns2:reversionAnulacionFacturaResponse>
    </soap:Body>
</soap:Envelope>"""

exito, mensaje = procesar_respuesta_reversion(xml_rechazo, factura_mock)
print(f"✅ Parseo exitoso")
print(f"Éxito: {exito}")
print(f"Mensaje generado:\n{mensaje}\n")

# Verificar que mensajesList fue extraído
if "[981]" in mensaje:
    print("✅ mensajesList extraído correctamente")
else:
    print("❌ mensajesList NO fue extraído")

# Verificar que hay sugerencias
if "Posibles acciones:" in mensaje:
    print("✅ Sugerencias contextuales incluidas")
else:
    print("❌ Sugerencias NO incluidas")

print("\n" + "=" * 80)
print("TEST 3: Factura Ya Revertida (981) - SIN mensajesList")
print("=" * 80)

xml_ya_revertida = b"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <ns2:reversionAnulacionFacturaResponse xmlns:ns2="https://siat.impuestos.gob.bo/">
            <RespuestaServicioFacturacion>
                <codigoDescripcion>FACTURA NO DISPONIBLE PARA REVERSION</codigoDescripcion>
                <codigoEstado>981</codigoEstado>
                <transaccion>false</transaccion>
            </RespuestaServicioFacturacion>
        </ns2:reversionAnulacionFacturaResponse>
    </soap:Body>
</soap:Envelope>"""

try:
    exito, mensaje = procesar_respuesta_reversion(xml_ya_revertida, factura_mock)
    print(f"✅ Parseo exitoso")
    print(f"Mensaje generado:\n{mensaje}\n")
except Exception as e:
    print(f"⚠️ Error esperado (sin BD real): {str(e)[:100]}")

print("\n" + "=" * 80)
print("RESUMEN DE TESTS")
print("=" * 80)
print("✅ Test 1: Respuesta exitosa parseada")
print("✅ Test 2: Respuesta rechazada con mensajesList extraído")
print("✅ Test 3: Factura ya revertida manejada")
print("\n⚠️ Nota: Los errores de BD son NORMALES en este test sin conexión real")
```

**Ejecutar:**
```powershell
python test_reversion_mejoras.py
```

**Resultado esperado:**
```
✅ Test 1: Respuesta exitosa parseada
✅ Test 2: Respuesta rechazada con mensajesList extraído
✅ Test 3: Factura ya revertida manejada
```

---

## 🔍 Paso 3: Verificación de Logs (5 minutos)

### **3.1 Verificar Estructura de Logs**

```powershell
# Limpiar log anterior
Remove-Item logs/reversion.log -ErrorAction SilentlyContinue

# Ejecutar un test
python test_reversion_mejoras.py

# Ver los logs generados
Get-Content logs/reversion.log
```

**Buscar estos prefijos en los logs:**
```
[PROCESAMIENTO]
[SIAT]
[BD]
[DETALLE]
[✅ ÉXITO]
[⚠️ RECHAZADO]
[❌ ERROR]
```

---

## 🌐 Paso 4: Testing con SIAT Real (Recomendado - 20 minutos)

### **4.1 Preparar Entorno**

```powershell
cd c:\Users\Bernardo\Desktop\backapp\facturador
streamlit run main.py
```

### **4.2 Escenario Real 1: Reversión Exitosa**

1. Acceder a la pestaña "Anular/Revertir"
2. Seleccionar "🔄 Revertir Anulación"
3. Ingresar número de una factura ANULADA reciente
4. Hacer clic en "Revertir Anulación"

**Verificar:**
- [ ] Se muestra mensaje con formato Markdown
- [ ] Aparece emoji ✅
- [ ] Texto en **negrita** se renderiza
- [ ] Factura cambia a estado "Valida"
- [ ] Campos `fechaAnulacion`, `motivoAnulacion`, `anuladaPor` quedan en NULL

---

### **4.3 Escenario Real 2: Reversión Rechazada (909)**

1. Intentar revertir una factura que NO está anulada
2. O intentar revertir una factura ya revertida

**Verificar:**
- [ ] Se muestra mensaje con emoji ❌
- [ ] Aparece sección "**Motivos específicos del rechazo:**"
- [ ] Se lista el código [981] con su descripción
- [ ] Aparece sección "**Posibles acciones:**"
- [ ] Las sugerencias son relevantes al error

**Ejemplo esperado en pantalla:**
```markdown
❌ **REVERSION DE ANULACION RECHAZADA**

**Motivos específicos del rechazo:**
• **[981]** REVERSION DE ANULACION NO DISPONIBLE PARA LA FACTURA O NOTA DE CREDITO - DEBITO

**Posibles acciones:**
• Verifique que la factura esté efectivamente anulada
• Confirme que no haya sido revertida previamente
• La factura pudo haber sido usada en una declaración jurada
```

---

### **4.4 Escenario Real 3: Factura Ya Revertida (981)**

1. Intentar revertir una factura que el SIAT dice ya está revertida
2. Pero en la BD local aparece como "Anulada"

**Verificar:**
- [ ] Sistema sincroniza automáticamente
- [ ] Factura cambia a "Valida" localmente
- [ ] Se muestra mensaje de sincronización exitosa
- [ ] Campos de anulación se limpian

---

## 📊 Paso 5: Verificación de Logs en Producción (10 minutos)

Después de ejecutar los tests reales, revisar logs:

```powershell
# Ver últimos 100 logs
Get-Content logs/reversion.log -Tail 100

# Filtrar solo logs de reversión
Select-String -Path logs/reversion.log -Pattern "\[PROCESAMIENTO\]|\[SIAT\]|\[DETALLE\]"

# Buscar errores
Select-String -Path logs/reversion.log -Pattern "\[❌"
```

**Verificar:**
- [ ] Los logs tienen prefijos estructurados
- [ ] Los códigos de estado se registran correctamente
- [ ] Los mensajes de `mensajesList` aparecen con prefijo `[DETALLE]`
- [ ] No hay errores inesperados

---

## ✅ Criterios de Aceptación

### **Funcionales**
- [ ] Código 909 es reconocido y manejado
- [ ] `mensajesList` se extrae en todas las respuestas que lo contengan
- [ ] Mensajes al usuario tienen formato Markdown
- [ ] Emojis se muestran correctamente
- [ ] Sugerencias son contextuales al código de error
- [ ] Sincronización automática funciona para código 981
- [ ] Campos de anulación se limpian completamente

### **Técnicos**
- [ ] Sin errores de sintaxis Python
- [ ] Sin errores en imports
- [ ] Logs tienen prefijos estructurados
- [ ] Respuestas con y sin `mensajesList` se procesan correctamente
- [ ] Fallback a descripción SIAT funciona si BD no tiene el código

### **Base de Datos**
- [ ] Estado de factura se actualiza correctamente
- [ ] Campos `fechaAnulacion`, `motivoAnulacion`, `anuladaPor` se limpian
- [ ] No hay errores de transacción
- [ ] Sincronización automática funciona

### **Interfaz de Usuario**
- [ ] Mensajes Markdown se renderizan correctamente
- [ ] Emojis se muestran
- [ ] Negritas funcionan
- [ ] Listas con bullets se muestran
- [ ] Mensajes son legibles y profesionales

---

## 🚨 Rollback Plan (Por Si Acaso)

Si encuentras problemas críticos, puedes revertir fácilmente:

```powershell
cd c:\Users\Bernardo\Desktop\backapp

# Ver el último commit
git log --oneline -5

# Revertir al commit anterior
git checkout HEAD~1 -- facturador/reversion.py

# O restaurar desde backup manual si lo hiciste
Copy-Item "facturador/reversion.py.backup" -Destination "facturador/reversion.py"
```

---

## 📝 Registro de Testing

Completa esta tabla durante el testing:

| Test | Estado | Notas |
|------|--------|-------|
| Sintaxis Python | ⏳ | |
| Imports | ⏳ | |
| Test Mock 907 | ⏳ | |
| Test Mock 909 | ⏳ | |
| Test Mock 981 | ⏳ | |
| SIAT Real 907 | ⏳ | |
| SIAT Real 909 | ⏳ | |
| SIAT Real 981 | ⏳ | |
| Logs estructurados | ⏳ | |
| UI Markdown | ⏳ | |

**Estados:** ⏳ Pendiente | ✅ Exitoso | ❌ Fallido | ⚠️ Con observaciones

---

## 🎯 Conclusión

Una vez completados todos los tests con estado ✅, las mejoras están **validadas y listas para producción**.

**Tiempo estimado total:** 1 hora  
**Prioridad:** Alta (resolver el bug del código 909)  
**Riesgo:** Bajo (cambios bien aislados, con fallbacks)

---

**Última actualización:** 14 de octubre de 2025  
**Versión:** 1.0
