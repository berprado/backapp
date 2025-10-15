# 🔍 Guía de Diagnóstico: Error HTTP 500 en Anulación

## 📋 Descripción del Problema

**Error recibido:**
```
❌ Error al comunicarse con el SIAT:
Error HTTP 500 durante anulación: 500 Server Error: 
for url: https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta
```

**Interpretación:**
- ✅ La comunicación con el servidor SIAT **sí se está estableciendo**
- ❌ El servidor SIAT **rechaza la solicitud** con un error interno (500)
- Esto **NO es un problema de red**, sino de **validación de datos** en el servidor

---

## 🔧 Correcciones Aplicadas (v2.0.1)

### 1. **Manejo de codificación de errores** ✅

**Problema:** Los mensajes de error con emojis se convertían a bytes y causaban problemas de visualización.

**Solución aplicada en `anulacion.py`:**
```python
if not exito:
    # Decodificar el mensaje de error si viene en bytes
    mensaje_error = respuesta.decode('utf-8') if isinstance(respuesta, bytes) else str(respuesta)
    logger.error(f"[SIAT ERROR] Fallo al enviar solicitud: {mensaje_error}")
    return False, f"❌ **Error al comunicarse con el SIAT:**\n\n{mensaje_error}"
```

### 2. **Mejora en el parsing de errores HTTP** ✅

**Problema:** Los errores HTTP 500 no extraían información útil del cuerpo de la respuesta.

**Solución aplicada en `siat_service_client.py`:**
```python
except requests.exceptions.HTTPError as http_err:
    status_code = response.status_code if 'response' in locals() else 'N/A'
    error_msg = f"Error HTTP {status_code} durante {operacion}"
    
    # Intentar extraer mensaje de error del cuerpo de la respuesta XML
    if 'response' in locals() and response.content:
        try:
            tree = ET.fromstring(response.content)
            fault_string = tree.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault/faultstring')
            
            if fault_string is not None and fault_string.text:
                error_msg += f": {fault_string.text}"
        except Exception as parse_err:
            logger.debug(f"[SIAT Client] No se pudo parsear error XML: {parse_err}")
```

### 3. **Validación de parámetros antes de enviar** ✅

**Problema:** No se validaban los parámetros antes de construir el XML.

**Solución aplicada en `anulacion.py`:**
```python
# Validación de parámetros críticos
if not cuf or len(cuf) == 0:
    logger.error("[VALIDACION] CUF vacio o None")
    return False, "CUF no válido: está vacío"

if not codigo_motivo or int(codigo_motivo) <= 0:
    logger.error(f"[VALIDACION] Codigo de motivo invalido: {codigo_motivo}")
    return False, f"Código de motivo no válido: {codigo_motivo}"
```

### 4. **Logging detallado para debugging** ✅

**Solución aplicada en `siat_service_client.py`:**
```python
# Log completo del XML para debugging (solo en modo DEBUG)
if logger.level <= 10:  # DEBUG level
    logger.debug(f"[SIAT Client] XML completo de anulacion:\n{xml_bytes.decode('utf-8')}")
```

---

## 🔍 Causas Comunes del Error HTTP 500

### 1. **CUFD o CUIS Expirado** (CAUSA MÁS PROBABLE)

**Síntomas:**
- Error 500 sin mensaje descriptivo
- Funcionaba antes pero dejó de funcionar
- Afecta a todas las operaciones (anulación, reversión, verificación)

**Solución:**
```sql
-- Verificar CUFD vigente
SELECT codigo, fechaVigencia, vigente 
FROM cufd 
WHERE vigente = 1 
ORDER BY fechaVigencia DESC 
LIMIT 1;

-- Verificar CUIS vigente
SELECT codigo, fechaVigencia, vigente 
FROM cuis 
WHERE vigente = 1 
ORDER BY fechaVigencia DESC 
LIMIT 1;
```

**Si están expirados:**
1. Ir a la pestaña de "Sincronización" en Streamlit
2. Solicitar nuevo CUFD
3. Solicitar nuevo CUIS si es necesario
4. Reintentar la operación

---

### 2. **CUF Inválido o No Existe en el SIAT**

**Síntomas:**
- Error 500 específico para una factura
- Otras facturas se pueden anular correctamente

**Solución:**
```python
# Verificar estado de la factura antes de anular
from estado_factura import verificar_estado_factura

numero_factura = "12345"
resultado = verificar_estado_factura(numero_factura)
print(resultado)
```

**Posibles resultados:**
- Si retorna código **908 (Validada)**: La factura existe y puede ser anulada
- Si retorna código **924 (No existe)**: La factura nunca fue enviada al SIAT
- Cualquier otro código: Ver sección de códigos más abajo

---

### 3. **Código de Motivo Inválido**

**Síntomas:**
- Error 500 al intentar anular
- El motivo seleccionado no está en la paramétrica

**Solución:**
```sql
-- Verificar motivos disponibles
SELECT codigoClasificador, descripcion 
FROM sincronizar_parametrica_motivo_anulacion
WHERE vigente = 1
ORDER BY codigoClasificador;
```

**Motivos más comunes:**
1. Emitido con error
2. Devolución de mercancía
3. Duplicado
4. Otro (especificar)

---

### 4. **Factura Incluida en Declaración Jurada**

**Síntomas:**
- Error 500 para facturas antiguas
- Facturas recientes funcionan bien

**Explicación:**
Una vez que una factura es incluida en una **Declaración Jurada** mensual al SIN, **no puede ser anulada**.

**Solución:**
- Verificar la fecha de la factura
- Si es de un mes anterior al actual y ya pasó el plazo de declaración (día 15 del mes siguiente), **no se puede anular**
- Alternativa: Emitir una **Nota de Crédito-Débito** (funcionalidad futura)

---

### 5. **Problema Temporal del Servidor SIAT**

**Síntomas:**
- Error 500 para todas las operaciones
- Comenzó súbitamente sin cambios en el sistema
- Afecta también verificación y reversión

**Solución:**
```python
# Verificar conectividad con el SIAT
from communication_manager import communication_manager

resultado = communication_manager.verificar_comunicacion_completa(force_check=True)
print(f"Estado principal: {resultado['verificacion_principal']['conectado']}")
print(f"Servicios disponibles: {resultado['servicios_disponibles']}")
```

**Si todos los servicios fallan con 500:**
- El problema es del servidor SIAT
- Esperar y reintentar más tarde (15-30 minutos)
- Revisar anuncios oficiales del SIN

---

## 🧪 Procedimiento de Diagnóstico Paso a Paso

### **Paso 1: Activar logs detallados**

```python
# En facturador/logger_config.py, cambiar nivel a DEBUG temporalmente
import logging

def get_logger():
    logger = logging.getLogger('facturacion')
    logger.setLevel(logging.DEBUG)  # Cambiar de INFO a DEBUG
    # ... resto del código
```

### **Paso 2: Revisar logs de la última anulación**

```bash
# En PowerShell
cd C:\Users\Bernardo\Desktop\backapp\facturador\logs
tail -n 100 app.log | Select-String "anulacion|SIAT Client"
```

**Buscar estos indicadores:**
```
[VALIDACION] CUF: ... (longitud: 64)  # Debe ser 64 caracteres
[VALIDACION] Codigo motivo: 1         # Debe ser un número válido
[SIAT Client] Construyendo solicitud anulacion...
[SIAT Client] XML completo de anulacion: ...  # Solo si DEBUG está activo
[SIAT Client] [HTTP ERROR] Error HTTP 500 durante anulación
```

### **Paso 3: Verificar datos de la factura**

```sql
-- Verificar estructura completa de la factura
SELECT 
    numeroFactura,
    cuf,
    estado,
    fechaEmision,
    LENGTH(cuf) as longitud_cuf,
    fechaAnulacion,
    motivoAnulacion
FROM factura_cabecera
WHERE numeroFactura = <NUMERO_FACTURA>;
```

**Validaciones críticas:**
- ✅ `LENGTH(cuf)` debe ser exactamente **64**
- ✅ `estado` debe ser **'Valida'** (no 'Anulada', no 'Revertida')
- ✅ `fechaEmision` debe ser menor a 30 días

### **Paso 4: Verificar CUFD/CUIS**

```sql
-- Verificar vigencia de códigos
SELECT 'CUFD' as tipo, codigo, fechaVigencia, 
       CASE WHEN fechaVigencia > NOW() THEN 'VIGENTE' ELSE 'EXPIRADO' END as estado
FROM cufd 
WHERE vigente = 1
UNION ALL
SELECT 'CUIS' as tipo, codigo, fechaVigencia,
       CASE WHEN fechaVigencia > NOW() THEN 'VIGENTE' ELSE 'EXPIRADO' END as estado
FROM cuis 
WHERE vigente = 1;
```

**Si alguno está expirado:**
```python
# Solicitar nuevo CUFD desde Streamlit o Python
from cufd import solicitar_cufd
resultado = solicitar_cufd()
print(resultado)
```

### **Paso 5: Probar con verificación de estado primero**

```python
# Antes de intentar anular, verificar que la factura existe en el SIAT
from estado_factura import verificar_estado_factura

numero_factura = "12345"
exito, resultado = verificar_estado_factura(numero_factura)

if exito and "908" in resultado:  # Código 908 = Validada
    print("✅ Factura existe en SIAT y puede ser anulada")
    # Ahora sí intentar anular
else:
    print(f"❌ Problema con la factura: {resultado}")
```

### **Paso 6: Capturar XML enviado (DEBUG)**

Si los logs muestran el XML completo (modo DEBUG), copiarlo y verificar:

```xml
<?xml version='1.0' encoding='utf-8'?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <anulacionFactura>
      <SolicitudServicioAnulacionFactura>
        <codigoAmbiente>2</codigoAmbiente>
        <codigoDocumentoSector>1</codigoDocumentoSector>
        <!-- ... resto de campos ... -->
        <cuf>DEBE_SER_64_CARACTERES_EXACTOS</cuf>
        <codigoMotivoAnulacion>1</codigoMotivoAnulacion>
      </SolicitudServicioAnulacionFactura>
    </anulacionFactura>
  </soapenv:Body>
</soapenv:Envelope>
```

**Verificar:**
- Todos los campos obligatorios presentes
- `<cuf>` tiene 64 caracteres exactos
- `<codigoMotivoAnulacion>` es un número válido (1-10)
- `<cufd>` y `<cuis>` no están vacíos

---

## 📊 Códigos de Respuesta del SIAT

| Código | Descripción | Acción |
|--------|-------------|--------|
| **905** | Anulación confirmada | ✅ Éxito |
| **906** | Anulación rechazada | ⚠️ Ver mensajes adicionales |
| **924** | Factura no existe en BD del SIN | ❌ CUF inválido o factura no enviada |
| **936** | Factura ya anulada | ⚠️ Operación duplicada |
| **970** | Fuera de plazo | ⏰ Más de 9 días desde emisión |
| **3011** | Sistema no autorizado | 🔴 Problema de credenciales |
| **3012** | Solicitud fuera de plazo | ⏰ Alternativa al 970 |

---

## 🚀 Siguiente Paso Recomendado

**Ejecuta este script de diagnóstico completo:**

```python
# Script: diagnostico_anulacion.py
from anulacion import anular_factura
from estado_factura import verificar_estado_factura
from data_access import obtener_cuf_por_numero_factura
from database import SessionLocal
from models import Cufd, Cuis

def diagnostico_completo(numero_factura, motivo):
    print("="*60)
    print(f"🔍 DIAGNÓSTICO DE ANULACIÓN - Factura #{numero_factura}")
    print("="*60)
    
    # 1. Verificar factura en BD local
    print("\n1️⃣ Verificando factura en BD local...")
    cuf, factura = obtener_cuf_por_numero_factura(numero_factura)
    if factura:
        print(f"   ✅ Factura encontrada")
        print(f"   - CUF: {cuf[:20]}...")
        print(f"   - Estado: {factura.estado}")
        print(f"   - Fecha emisión: {factura.fechaEmision}")
        print(f"   - Longitud CUF: {len(cuf)} caracteres")
    else:
        print(f"   ❌ Factura no encontrada")
        return
    
    # 2. Verificar CUFD/CUIS
    print("\n2️⃣ Verificando CUFD y CUIS...")
    session = SessionLocal()
    try:
        cufd = session.query(Cufd).filter_by(vigente=1).first()
        cuis = session.query(Cuis).filter_by(vigente=1).first()
        
        if cufd:
            print(f"   ✅ CUFD vigente: {cufd.codigo[:20]}...")
            print(f"   - Válido hasta: {cufd.fechaVigencia}")
        else:
            print(f"   ❌ No hay CUFD vigente")
        
        if cuis:
            print(f"   ✅ CUIS vigente: {cuis.codigo[:20]}...")
        else:
            print(f"   ❌ No hay CUIS vigente")
    finally:
        session.close()
    
    # 3. Verificar estado en SIAT
    print("\n3️⃣ Verificando estado en SIAT...")
    exito, resultado = verificar_estado_factura(numero_factura)
    if exito:
        print(f"   ✅ Respuesta SIAT: {resultado}")
    else:
        print(f"   ⚠️ Error al verificar: {resultado}")
    
    # 4. Intentar anulación
    print("\n4️⃣ Intentando anulación...")
    exito, mensaje = anular_factura(numero_factura, motivo)
    
    print("\n" + "="*60)
    if exito:
        print("✅ ANULACIÓN EXITOSA")
    else:
        print("❌ ANULACIÓN FALLIDA")
    print("="*60)
    print(mensaje)
    print("="*60)

# Uso:
if __name__ == "__main__":
    diagnostico_completo("12345", "Emitido con error")
```

---

## 📞 Checklist de Soporte

Si después de todos los pasos anteriores el problema persiste:

- [ ] ¿El error HTTP 500 ocurre con **todas** las facturas o solo con una específica?
- [ ] ¿Cuándo ocurrió por primera vez? ¿Funcionaba antes?
- [ ] ¿El CUFD y CUIS están vigentes? (verificado en BD)
- [ ] ¿La verificación de estado funciona correctamente?
- [ ] ¿Los logs muestran el XML completo? (activar DEBUG)
- [ ] ¿El CUF tiene exactamente 64 caracteres?
- [ ] ¿El código de motivo es válido? (1-10)
- [ ] ¿La factura tiene menos de 30 días de emisión?
- [ ] ¿Otros servicios SIAT funcionan? (verificación, cufd)

---

**Versión:** 1.0.0  
**Fecha:** 15 de octubre de 2025  
**Estado:** 🔧 Correcciones aplicadas - Listo para testing
