# 📊 Análisis: Columnas de Estado en `factura_cabecera`

**Fecha:** 16 de octubre de 2025  
**Contexto:** Investigación del error 981 en reversión de factura #777  
**Autor:** Sistema de Facturación Electrónica

---

## 🔍 Problema Detectado

### Estado Actual de Factura #777

| Columna | Valor Actual | ¿Correcto? |
|---------|--------------|------------|
| `estado` | "Anulada" | ✅ |
| `estadoValidacion` | "VALIDA" | ❌ Inconsistente |
| `resultadoValidacion` | "VALIDADA" | ❌ Inconsistente |
| `codigoRecepcion` | "5004a486-aa5c-11f0-97cf-33a893393f4f" | ✅ |

### Secuencia de Eventos (según logs)

```
02:49:47 → Factura generada (numeroFactura: 777)
02:49:51 → SIAT responde: codigoEstado=908 (VALIDADA)
02:50:17 → BD actualizada: estado='VALIDA'
02:51:31 → BD actualizada: estado='ANULADA'  ← Anulación
03:08:46 → BD actualizada: estado='VALIDA'   ← Intento de reversión
```

---

## 📋 Columnas de Estado: Propósito y Uso

### 1. `estado` (VARCHAR(20))

**Propósito:** Ciclo de vida completo de la factura  
**Valores posibles:**
- `"Activa"` - Recién creada, aún no validada por SIAT
- `"Valida"` - Confirmada por SIAT, activa y vigente
- `"Anulada"` - Anulada mediante servicio SIAT
- `"Revertida"` - No se usa (debería volver a "Valida")

**Quién la actualiza:**
- ✅ Proceso de emisión (`facturacion_tab.py`)
- ✅ Proceso de verificación (`estado_factura.py`)
- ✅ Proceso de anulación (`anulacion.py`)
- ✅ Proceso de reversión (`reversion.py`)

**Es la columna PRINCIPAL** para determinar el estado actual de la factura.

---

### 2. `estadoValidacion` (VARCHAR(50))

**Propósito:** Resultado de la validación técnica del SIAT  
**Valores posibles:**
- `"VALIDADA"` - SIAT aceptó la factura técnicamente
- `"OBSERVADA"` - SIAT la aceptó con advertencias
- `"RECHAZADA"` - SIAT rechazó la factura
- `"PENDIENTE"` - Aún no validada por SIAT

**Quién la actualiza:**
- ✅ Proceso de emisión (al recibir respuesta del SIAT)
- ❌ **NO debería cambiar** después de la primera validación

**Problema:** Esta columna NO refleja anulaciones/reversiones, solo validación técnica inicial.

---

### 3. `resultadoValidacion` (VARCHAR(100))

**Propósito:** Código de estado del SIAT (referencia técnica)  
**Valores típicos:**
- `"908 - VALIDADA"` - Validación exitosa
- `"905 - ANULADA"` - Anulación confirmada
- `"907 - REVERSION CONFIRMADA"` - Reversión exitosa

**Quién la actualiza:**
- ✅ Proceso de emisión
- ❓ **Proceso de anulación (debería pero no lo hace)**
- ❓ **Proceso de reversión (debería pero no lo hace)**

**Problema:** No se está actualizando en operaciones posteriores a la emisión.

---

## 🐛 Inconsistencias Detectadas

### Caso de Factura #777

```sql
-- Estado actual en BD:
estado = "Anulada"                    ← ✅ Correcto
estadoValidacion = "VALIDA"           ← ❌ Debería ser "ANULADA" 
resultadoValidacion = "VALIDADA"      ← ❌ Debería ser "905 - ANULADA"
codigoRecepcion = "5004a486-..."      ← ✅ Correcto
```

**Consecuencia:** 
- El campo `estado` dice "Anulada"
- Pero `estadoValidacion` y `resultadoValidacion` dicen "Válida"
- **Esto confunde los procesos de verificación y reversión**

---

## 📝 Análisis de Archivos que Actualizan Estado

### 1. `estado_factura.py` - Función `actualizar_estado_factura_db()`

**Código actual:**
```python
def actualizar_estado_factura_db(numero_factura: int, nuevo_estado: str):
    """
    Actualiza el estado de una factura en la base de datos.
    """
    session = SessionLocal()
    try:
        factura = session.query(FacturaCabecera).filter_by(
            numeroFactura=numero_factura
        ).first()
        
        if factura:
            # SOLO actualiza la columna 'estado'
            factura.estado = nuevo_estado
            session.commit()
            logger.info(f"[BD] ✅ Factura #{numero_factura} actualizada a estado '{nuevo_estado}'")
```

**Problema:** ❌ NO actualiza `estadoValidacion` ni `resultadoValidacion`

---

### 2. `anulacion.py` - Función `procesar_respuesta_anulacion()`

**Código relevante:**
```python
# Cuando la anulación es exitosa (código 905):
factura.estado = "Anulada"
factura.fechaAnulacion = datetime.now()
factura.anuladoPor = "ADMIN"
factura.motivoAnulacion = descripcion_motivo

# ❌ FALTA: NO actualiza estadoValidacion ni resultadoValidacion
session.commit()
```

**Problema:** Solo actualiza `estado`, no las otras columnas.

---

### 3. `reversion.py` - Función `procesar_respuesta_reversion()`

**Código relevante:**
```python
# Cuando la reversión es exitosa (código 907):
factura.estado = "Valida"
factura.fechaAnulacion = None
factura.anuladoPor = None
factura.motivoAnulacion = None

# ❌ FALTA: NO actualiza estadoValidacion ni resultadoValidacion
session.commit()
```

**Problema:** Solo actualiza `estado`, no las otras columnas.

---

## ✅ Solución Propuesta

### Opción 1: Actualizar Todas las Columnas Consistentemente

**En `anulacion.py` - al confirmar anulación:**
```python
if codigo_estado == ESTADO_ANULACION_CONFIRMADA:  # 905
    factura.estado = "Anulada"
    factura.estadoValidacion = "ANULADA"              # ← NUEVO
    factura.resultadoValidacion = "905 - ANULADA"    # ← NUEVO
    factura.fechaAnulacion = datetime.now()
    factura.anuladoPor = "ADMIN"
    factura.motivoAnulacion = descripcion_motivo
    session.commit()
```

**En `reversion.py` - al confirmar reversión:**
```python
if codigo_estado == ESTADO_REVERSION_CONFIRMADA:  # 907
    factura.estado = "Valida"
    factura.estadoValidacion = "VALIDADA"                    # ← NUEVO
    factura.resultadoValidacion = "907 - REVERSION OK"       # ← NUEVO
    factura.fechaAnulacion = None
    factura.anuladoPor = None
    factura.motivoAnulacion = None
    session.commit()
```

---

### Opción 2: Usar Solo `estado` (Simplificar)

Si `estadoValidacion` y `resultadoValidacion` solo se usan para la validación inicial:

1. **Renombrar las columnas** para evitar confusión:
   - `estadoValidacion` → `estadoValidacionInicial`
   - `resultadoValidacion` → `codigoEstadoInicial`

2. **Documentar claramente** que NO reflejan el ciclo de vida completo

3. **Usar solo `estado`** como fuente de verdad:
   ```python
   # En verificaciones y validaciones:
   if factura.estado == "Anulada":
       # Es anulada
   elif factura.estado == "Valida":
       # Es válida
   ```

---

## 🔴 Caso Específico: Factura #777

### ¿Por qué el SIAT rechaza la reversión?

**Respuesta del SIAT:**
```xml
<codigo>981</codigo>
<descripcion>REVERSION DE ANULACION NO DISPONIBLE PARA LA FACTURA</descripcion>
```

**Hipótesis más probable:**

Mirando los logs:
```
02:51:31 → Estado actualizado a 'ANULADA'
03:08:46 → Estado actualizado a 'VALIDA'  ← ¿Reversión exitosa?
```

El log dice que se actualizó a `VALIDA` a las `03:08:46`. Esto sugiere dos escenarios:

**Escenario 1: La reversión YA se hizo exitosamente**
- A las 03:08:46 se **completó** una reversión
- La BD se actualizó a `"Valida"`
- Pero `estadoValidacion` quedó inconsistente como `"VALIDA"` (no `"ANULADA"`)
- **Ahora** estás intentando revertir una factura que **ya está válida**
- El SIAT rechaza porque no está anulada

**Escenario 2: Actualización prematura**
- El código actualizó la BD a `"Valida"` **antes** de que el SIAT confirmara
- Luego el SIAT rechazó
- Quedó en estado inconsistente

### Verificación en SIAT

Para confirmar, necesitamos verificar el estado **real** en el SIAT:

```python
from estado_factura import verificar_estado_factura

resultado = verificar_estado_factura("777", force_check=True)
print(f"Estado en SIAT: {resultado.get('estado_siat')}")
print(f"Código: {resultado.get('codigo_estado_siat')}")
```

**Posibles resultados:**
- `690` = VÁLIDA → La reversión ya se hizo
- `691` = ANULADA → Hay un bug en el proceso de reversión

---

## 📊 Tabla Comparativa: Estado Esperado vs Real

| Operación | `estado` | `estadoValidacion` | `resultadoValidacion` |
|-----------|----------|--------------------|-----------------------|
| **Emisión exitosa** | "Valida" | "VALIDADA" | "908 - VALIDADA" |
| **Anulación (código 905)** | "Anulada" | ❌ "VALIDADA" (no cambia) | ❌ "VALIDADA" (no cambia) |
| **Reversión (código 907)** | "Valida" | ❌ "VALIDADA" (no cambia) | ❌ "VALIDADA" (no cambia) |

| Operación | `estado` | `estadoValidacion` | `resultadoValidacion` |
|-----------|----------|--------------------|-----------------------|
| **Emisión exitosa** | "Valida" | "VALIDADA" | "908 - VALIDADA" |
| **Anulación (código 905)** | "Anulada" | ✅ "ANULADA" | ✅ "905 - ANULADA" |
| **Reversión (código 907)** | "Valida" | ✅ "VALIDADA" | ✅ "907 - REVERSION OK" |

---

## 🎯 Recomendaciones Inmediatas

### 1. Verificar Estado Real en SIAT (URGENTE)

Antes de hacer cualquier corrección, confirmar el estado actual de la factura #777 en el SIAT.

### 2. Corregir `anulacion.py`

Actualizar todas las columnas al confirmar anulación:
```python
factura.estado = "Anulada"
factura.estadoValidacion = "ANULADA"
factura.resultadoValidacion = f"{codigo_estado} - ANULADA"
```

### 3. Corregir `reversion.py`

Actualizar todas las columnas al confirmar reversión:
```python
factura.estado = "Valida"
factura.estadoValidacion = "VALIDADA"
factura.resultadoValidacion = f"{codigo_estado} - REVERSION CONFIRMADA"
```

### 4. Agregar Validación Pre-Reversión Mejorada

En `anular_revertir_tab.py`:
```python
# Verificar TODAS las columnas de estado
if factura.estado != "Anulada":
    st.error("La factura no está anulada según 'estado'")
    return

if factura.estadoValidacion == "VALIDADA" and factura.estado == "Anulada":
    st.warning("⚠️ Inconsistencia detectada en columnas de estado")
    # Verificar en SIAT para confirmar estado real
```

### 5. Script de Corrección de Inconsistencias

Crear un script que detecte y corrija facturas con estados inconsistentes:
```sql
-- Detectar inconsistencias
SELECT numeroFactura, estado, estadoValidacion, resultadoValidacion
FROM factura_cabecera
WHERE estado = 'Anulada' 
  AND estadoValidacion != 'ANULADA';
```

---

## 📚 Conclusiones

1. **Hay 3 columnas de estado** con propósitos diferentes pero confusos
2. **Solo `estado` se actualiza consistentemente** en todo el ciclo de vida
3. **`estadoValidacion` y `resultadoValidacion`** quedan congeladas después de la emisión
4. **Esto causa inconsistencias** que confunden los procesos posteriores
5. **La solución** es actualizar las 3 columnas en cada operación crítica

---

**Siguiente paso:** Verificar el estado real de la factura #777 en el SIAT antes de aplicar correcciones.
