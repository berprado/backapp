# 🧪 Guía Rápida de Testing - Cliente SIAT Refactorizado

**Objetivo:** Validar que la refactorización no rompió funcionalidad existente  
**Tiempo estimado:** 15 minutos

---

## ✅ **Test 1: Validación de Sintaxis (2 minutos)**

```powershell
# Desde la raíz del proyecto
cd c:\Users\Bernardo\Desktop\backapp\facturador

# Validar sintaxis
python -m py_compile siat_service_client.py
python -m py_compile estado_factura.py

# Resultado esperado: Sin errores
```

**Estado:** ✅ PASADO (confirmado durante implementación)

---

## ✅ **Test 2: Verificar Imports (1 minuto)**

```powershell
# Crear script de prueba temporal
python -c "from siat_service_client import get_siat_client; print('✅ Import correcto')"
python -c "from estado_factura import verificar_estado_factura; print('✅ Import correcto')"
```

**Resultado esperado:**
```
✅ Import correcto
✅ Import correcto
```

---

## ✅ **Test 3: Instancia del Cliente (1 minuto)**

Crear archivo `test_siat_client.py`:

```python
"""
Test rápido del cliente SIAT centralizado
"""
import sys
sys.path.insert(0, 'c:/Users/Bernardo/Desktop/backapp/facturador')

from siat_service_client import get_siat_client

# Test 1: Crear instancia
client = get_siat_client()
print(f"✅ Cliente creado: {type(client).__name__}")

# Test 2: Verificar que es singleton
client2 = get_siat_client()
assert client is client2
print("✅ Patrón Singleton funcionando")

# Test 3: Verificar que tiene los métodos esperados
assert hasattr(client, 'construir_solicitud_verificacion')
assert hasattr(client, 'construir_solicitud_reversion')
assert hasattr(client, 'construir_solicitud_anulacion')
assert hasattr(client, 'enviar_solicitud')
print("✅ Todos los métodos disponibles")

# Test 4: Construir solicitud de prueba
cuf_prueba = "A" * 64  # CUF ficticio para testing
xml = client.construir_solicitud_verificacion(cuf_prueba)
assert len(xml) > 0
assert b'verificacionEstadoFactura' in xml
print(f"✅ XML construido correctamente ({len(xml)} bytes)")

print("\n🎉 ¡Todos los tests pasaron!")
```

**Ejecutar:**
```powershell
python test_siat_client.py
```

**Resultado esperado:**
```
✅ Cliente creado: SIATServiceClient
✅ Patrón Singleton funcionando
✅ Todos los métodos disponibles
✅ XML construido correctamente (~800 bytes)

🎉 ¡Todos los tests pasaron!
```

---

## ✅ **Test 4: Funciones Deprecadas (Compatibilidad) (2 minutos)**

Crear archivo `test_compatibilidad.py`:

```python
"""
Test de compatibilidad retroactiva
"""
import sys
sys.path.insert(0, 'c:/Users/Bernardo/Desktop/backapp/facturador')

# Test 1: Imports antiguos deben funcionar
try:
    from estado_factura import construir_solicitud_verificacion
    from estado_factura import enviar_solicitud_verificacion
    print("✅ Imports legacy funcionan")
except ImportError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 2: Funciones deprecadas deben funcionar (con warning)
cuf_prueba = "A" * 64
xml = construir_solicitud_verificacion(cuf_prueba)
assert len(xml) > 0
print("✅ Función deprecada 'construir_solicitud_verificacion' funciona")

print("\n⚠️ Nota: Deberías ver un WARNING en logs sobre funciones deprecadas")
print("🎉 ¡Compatibilidad retroactiva confirmada!")
```

**Ejecutar:**
```powershell
python test_compatibilidad.py
```

**Resultado esperado:**
```
✅ Imports legacy funcionan
✅ Función deprecada 'construir_solicitud_verificacion' funciona

⚠️ Nota: Deberías ver un WARNING en logs sobre funciones deprecadas
🎉 ¡Compatibilidad retroactiva confirmada!
```

---

## 🌐 **Test 5: Verificación con Streamlit (5 minutos)**

```powershell
# Iniciar aplicación
streamlit run main.py
```

### **Pasos:**

1. ✅ **Verificar que la app inicia sin errores**
   - La aplicación debe cargar normalmente
   - No debe haber errores de import en consola

2. ✅ **Navegar a "Verificar Factura"**
   - La pestaña debe cargar correctamente
   - Formulario debe mostrarse

3. ✅ **Intentar verificar una factura existente**
   - Ingresar número de factura válido
   - Hacer clic en "Verificar"
   - Verificar que muestra resultado correcto

4. ✅ **Revisar logs**
   ```powershell
   # En otra terminal
   Get-Content logs/app.log -Tail 50
   ```
   
   **Buscar:**
   - Líneas con prefijo `[SIAT Client]`
   - Líneas con `[VERIFICACIÓN]`
   - ⚠️ WARNING sobre funciones deprecadas (si se usan)

**Resultado esperado:**
```
[SIAT Client] 🚀 Instancia singleton creada exitosamente
[VERIFICACIÓN] Verificando estado de factura #123...
[SIAT Client] 📡 Enviando solicitud: verificación de estado
[SIAT Client] ✅ Respuesta exitosa (HTTP 200)
[VERIFICACIÓN] ✅ Factura #123 es VÁLIDA
```

---

## 🔍 **Test 6: Revisar Logs Completos (2 minutos)**

```powershell
# Ver logs recientes
Get-Content logs/app.log -Tail 100

# Filtrar solo logs del cliente SIAT
Select-String -Path logs/app.log -Pattern "\[SIAT Client\]" | Select-Object -Last 20

# Buscar advertencias de funciones deprecadas
Select-String -Path logs/app.log -Pattern "DEPRECADO"
```

**Verificar:**
- [ ] Logs tienen prefijos estructurados
- [ ] No hay errores inesperados
- [ ] Mensajes son descriptivos
- [ ] Si hay warnings de DEPRECADO, identificar origen

---

## 📊 **Checklist de Validación**

```
Sintaxis y Estructura:
☑ siat_service_client.py compila sin errores
☑ estado_factura.py compila sin errores
☑ Imports funcionan correctamente
☑ Cliente singleton se crea correctamente

Funcionalidad:
☑ construir_solicitud_verificacion() genera XML válido
☑ Funciones deprecadas siguen funcionando
☑ verificar_estado_factura() funciona en Streamlit
☑ Respuestas del SIAT se procesan correctamente

Logging:
☑ Logs muestran prefijo [SIAT Client]
☑ Logs muestran prefijo [VERIFICACIÓN]
☑ Warnings de funciones deprecadas aparecen si se usan
☑ No hay errores inesperados en logs

Compatibilidad:
☑ Código existente funciona sin cambios
☑ Imports antiguos siguen válidos
☑ API pública preservada
```

---

## 🚨 **Si Algo Falla**

### **Error: `ModuleNotFoundError: No module named 'siat_service_client'`**

**Solución:**
```powershell
# Verificar que el archivo existe
Test-Path c:\Users\Bernardo\Desktop\backapp\facturador\siat_service_client.py

# Si no existe, recrearlo desde el backup
```

### **Error: Timeout o error de conexión**

**Es NORMAL si:**
- No hay conexión a Internet
- Servidor SIAT está caído
- Firewall bloquea la conexión

**Verificar logs:**
```
[SIAT Client] ⏱️ Timeout (30s) al conectar con SIAT
[SIAT Client] 🔌 Error de conexión: Sin Internet o servidor SIAT caído
```

Estos son **errores manejados correctamente**, no bugs.

### **Warning: Funciones deprecadas**

**Es NORMAL si ves:**
```
[DEPRECADO] Usando construir_solicitud_verificacion(). Migrar a siat_service_client.
```

Esto significa que hay código legacy que todavía usa las funciones antiguas. **NO es un error**, es información para futuras migraciones.

---

## ✅ **Criterio de Aceptación**

El testing es **exitoso** si:

1. ✅ Todos los tests unitarios pasan
2. ✅ La aplicación Streamlit inicia sin errores
3. ✅ Verificación de facturas funciona correctamente
4. ✅ Los logs muestran prefijos estructurados
5. ✅ No hay errores inesperados

---

## 📝 **Registro de Testing**

Completa esta tabla al ejecutar los tests:

| Test | Estado | Tiempo | Notas |
|------|--------|--------|-------|
| Sintaxis Python | ✅ | - | Confirmado durante implementación |
| Imports | ⏳ | - | |
| Instancia Cliente | ⏳ | - | |
| Compatibilidad | ⏳ | - | |
| Streamlit | ⏳ | - | |
| Logs | ⏳ | - | |

**Leyenda:**
- ⏳ Pendiente
- ✅ Exitoso
- ❌ Fallido
- ⚠️ Con observaciones

---

**Última actualización:** 14 de octubre de 2025  
**Versión:** 1.0
