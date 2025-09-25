# 🇧🇴 SISTEMA DE CONTINGENCIA - CUMPLIMIENTO NORMATIVO BOLIVIANO

## 📋 **Normativa de Referencia**
- **Resolución Normativa de Régimen Específico Nº 102500000013**
- **Servicio de Impuestos Nacionales (SIN) - Bolivia**

---

## ✅ **CUMPLIMIENTO NORMATIVO 100% IMPLEMENTADO**

### 🚨 **1. EVENTOS SIGNIFICATIVOS (7 Tipos Codificados)**

| Código | Evento Significativo | Estado |
|--------|---------------------|---------|
| **1** | Corte del servicio de Internet | ✅ Implementado |
| **2** | Inaccesibilidad al Servicio Web SIN | ✅ Implementado |
| **3** | Ingreso a zonas sin Internet (despliegue PV) | ✅ Implementado |
| **4** | Venta en lugares sin Internet | ✅ Implementado |
| **5** | Virus informático o falla de software | ✅ Implementado |
| **6** | Cambio de infraestructura/falla hardware | ✅ Implementado |
| **7** | Corte de suministro de energía eléctrica | ✅ Implementado |

### 🔄 **2. FLUJO DE CONTINGENCIA OBLIGATORIO**

```
📡 DETECCIÓN AUTOMÁTICA DE CONTINGENCIA
    ↓
📝 REGISTRO ÚNICO EN BASE DE DATOS LOCAL 
    ↓  
💾 FACTURACIÓN OFFLINE CON CUFD PRE-CORTE
    ↓
🔄 DETECCIÓN DE RECONEXIÓN
    ↓
🆔 OBTENER **NUEVO** CUFD (CRÍTICO)
    ↓
📤 REGISTRAR EVENTO CON SIN
    ↓
📦 ENVIAR PAQUETES DE FACTURAS
```

### ⚠️ **3. CONDICIONES DE ERROR QUE ACTIVAN CONTINGENCIA**

**✅ TODOS IMPLEMENTADOS:**
- `Timeout` - Tiempo de espera agotado
- `HTTP 500/502/503` - Error servidor SIN
- `HTTP 400/404` - Servicio remoto inaccesible  
- `HTTP 401/403` - Problemas autenticación
- `ConnectionError` - Error de conexión/DNS
- `Código -1` - Error específico mencionado en normativa
- `Java Null Point Exception` - Error Java detectado
- Cualquier excepción no controlada

### 📄 **4. FACTURACIÓN OFFLINE NORMATIVA**

**✅ IMPLEMENTADO CORRECTAMENTE:**
- Solo **1 evento activo** permitido simultáneamente
- Facturas usan **CUFD pre-corte** (del evento)
- **Código de excepción = 1** cuando tipo documento = NIT
- Facturas almacenadas en `offline_invoices/`
- Patrón de nombre: `factura_offline_ev{ID}_n{numero}.xml`

### 🕒 **5. LÍMITES TEMPORALES NORMATIVOS**

**✅ CUMPLE NORMATIVA:**
- **Registro evento**: Máximo 48 horas después de finalizada contingencia
- **Duración CUFD**: Extendida hasta 72 horas durante contingencia
- **Reintento conexión**: Máximo 2 horas antes de verificar nuevamente

### 🔐 **6. SECUENCIA CRÍTICA AL FINALIZAR CONTINGENCIA**

**🎯 IMPLEMENTACIÓN CORRECTA:**
1. **PASO 1**: Obtener **NUEVO CUFD** (función: `solicitar_cufd()`)
2. **PASO 2**: Registrar evento con SIN usando nuevo CUFD
3. **PASO 3**: Comprimir y enviar paquetes XML
4. **PASO 4**: Cerrar evento en base de datos local

---

## 🛡️ **FUNCIONES NORMATIVAS CLAVE**

### **data_access.py**
```python
registrar_evento_local_normativo()    # Cumple regla: 1 evento activo
obtener_evento_activo_actual()        # Obtiene evento abierto actual  
cerrar_evento_significativo()         # Cierra con código SIN
obtener_cufd_de_evento_activo()       # CUFD del evento pre-corte
```

### **contingencia_auto.py**
```python
finalizar_evento_si_conectado()       # Secuencia normativa completa
```

### **soap_services.py** 
```python
verificar_comunicacion()              # Detección completa de errores
enviar_evento_significativo()         # Registro con SIN
```

---

## 📊 **CARACTERÍSTICAS DEL SISTEMA**

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| **Base Legal** | ✅ | Resolución 102500000013 |
| **Eventos Únicos** | ✅ | Solo 1 activo por vez |
| **CUFD Correcto** | ✅ | Pre-corte, extendido 72h |
| **Detección Errores** | ✅ | 8+ tipos según normativa |
| **Código Excepción NIT** | ✅ | Automático cuando aplica |
| **Secuencia Cierre** | ✅ | Nuevo CUFD → Evento → Paquetes |
| **Límites Temporales** | ✅ | 48h evento, 72h CUFD, 2h reintentos |
| **Paquetes ZIP** | ✅ | Con ID evento + código recepción |

---

## 🔄 **PRÓXIMAS MEJORAS RECOMENDADAS**

1. **Sistema de Verificación Post-Contingencia**
   - Verificar estado de facturas sin código respuesta
   - Anulación automática de duplicados

2. **Dashboard de Contingencias**
   - Monitor tiempo real de eventos
   - Historial de contingencias
   - Estadísticas de cumplimiento

3. **Alertas Proactivas**
   - Notificación próximo vencimiento CUFD
   - Alerta eventos próximos a 48h

---

## 🎯 **CONCLUSIÓN**

El sistema **CUMPLE AL 100%** con la normativa boliviana para eventos significativos y contingencia. Todas las reglas, códigos, secuencias y límites temporales están correctamente implementados según la Resolución Normativa del SIN.

**✅ SISTEMA LISTO PARA PRODUCCIÓN EN BOLIVIA** 🇧🇴
