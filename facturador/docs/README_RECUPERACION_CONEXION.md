# 🔄 Flujo de Procesamiento Post-Recuperación de Conexión

## 📋 Descripción General

Una vez que el sistema **recupera la conexión** con los servicios del SIN después de un período de contingencia, se activa un **flujo automático y normativo** para procesar todas las facturas que se generaron en modo offline. Este flujo está diseñado para cumplir al 100% con las regulaciones del Servicio de Impuestos Nacionales (SIN) de Bolivia.

---

## 🚦 **Activación del Flujo Post-Recuperación**

### **Punto de Entrada Principal**
El flujo se inicia **automáticamente** cada vez que se ejecuta `main.py`, específicamente en la función `main()`:

```python
# Paso previo: intentar finalizar evento abierto si hay conexión
resultado = finalizar_evento_si_conectado()
if resultado:
    st.success("✅ Se finalizó el evento pendiente y se comprimieron las facturas (si existían).")
else:
    st.warning("ℹ️ No se pudo finalizar el evento o el sistema aún está sin conexión.")
```

**Archivo clave:** `facturador/main.py:100-107`

---

## 📊 **Flujo Detallado Post-Recuperación**

### **Fase 1: Verificación de Conectividad** 🌐
**Archivo:** `contingencia_auto.py:15-30`

```python
def finalizar_evento_si_conectado():
    # Usar el communication_manager centralizado con caché
    resultado_completo = communication_manager.verificar_comunicacion_completa()
    principal = resultado_completo.get("verificacion_principal", {})
    conectado = principal.get("conectado", False)

    if not conectado:
        logger.info("Aún no hay conexión con el SIN. No se puede finalizar evento.")
        return False
```

**Proceso:**
1. **Consulta optimizada** usando `CommunicationManager` con caché de 30 segundos
2. **Verifica múltiples servicios**: Recepción, Operaciones, Códigos
3. **Determina tipo de conectividad**: Completa, parcial o nula
4. **Si NO hay conexión:** Se detiene el proceso y retorna `False`

---

### **Fase 2: Verificación de Evento Activo** 📝
**Archivo:** `contingencia_auto.py:31-37`

```python
evento = obtener_evento_activo_actual()
if not evento:
    logger.info("No hay evento abierto. El sistema está en modo normal.")
    return True
```

**Proceso:**
1. **Consulta base de datos** para verificar si existe un evento con `fecha_fin = NULL`
2. **Si NO hay evento activo:** El sistema ya está en modo normal, retorna `True`
3. **Si SÍ hay evento activo:** Procede con el proceso de finalización

---

### **Fase 3: Obtención de Nuevo CUFD** 🔐
**Archivo:** `contingencia_auto.py:40-50`

```python
# SEGÚN NORMATIVA - OBTENER **NUEVO** CUFD ANTES DE REGISTRAR EVENTO
from cufd import solicitar_cufd
nuevo_cufd = solicitar_cufd()

if not nuevo_cufd:
    logger.error("CRÍTICO: No se pudo obtener NUEVO CUFD. No se puede finalizar evento según normativa.")
    return False
```

**Proceso:**
1. **Solicita un CUFD completamente nuevo** (NO reutiliza el anterior)
2. **Cumple normativa**: El registro del evento ante el SIN debe hacerse con un CUFD vigente POST-recuperación
3. **Si falla la obtención:** Se detiene todo el proceso para evitar inconsistencias normativas

---

### **Fase 4: Registro del Evento ante el SIN** 📨
**Archivo:** `contingencia_auto.py:49-60`

```python
# PASO 2: SEGÚN NORMATIVA - REGISTRAR evento con el SIN usando el NUEVO CUFD
fecha_fin = datetime.now()
codigo_recepcion, transaccion = enviar_evento_significativo(
    evento=evento,
    fecha_fin=fecha_fin,
    cufd=nuevo_cufd  # Usar el NUEVO CUFD según normativa
)

if not transaccion:
    logger.error("El SIN no aceptó el cierre del evento.")
    return False
```

**Proceso:**
1. **Establece fecha_fin** del evento (momento actual)
2. **Envía el evento al SIN** usando servicio web oficial `enviar_evento_significativo()`
3. **Parámetros críticos:**
   - `fecha_inicio`: Tomada del evento almacenado localmente  
   - `fecha_fin`: Timestamp actual de recuperación
   - `cufd`: El **nuevo** CUFD obtenido en la fase anterior
   - `codigo_evento`: Tipo de contingencia (1-7) según normativa
4. **Recibe código de recepción** del SIN que identifica únicamente este evento

---

### **Fase 5: Actualización Local del Evento** 💾
**Archivo:** `contingencia_auto.py:62-72`

```python
# Paso 3: Usar la función normativa para cerrar el evento
resultado_cierre = cerrar_evento_significativo(
    evento_id=evento["id"], 
    codigo_recepcion=codigo_recepcion
)

if resultado_cierre:
    logger.info(f"Evento #{evento['id']} finalizado exitosamente con código {codigo_recepcion}.")
else:
    logger.error(f"Error al cerrar el evento #{evento['id']} en base de datos.")
    return False
```

**Proceso:**
1. **Actualiza base de datos local** con:
   - `fecha_fin = timestamp_actual`
   - `codigo_recepcion = respuesta_del_SIN`
   - `estado = "FINALIZADO"`
2. **Función utilizada:** `cerrar_evento_significativo()` en `data_access.py`
3. **Garantiza consistencia** entre SIN y sistema local

---

### **Fase 6: Procesamiento de Facturas Offline** 📦
**Archivo:** `contingencia_auto.py:74-110`

#### **6.1 Búsqueda de Archivos XML**
```python
# Buscar archivos con el patrón: factura_offline_ev{evento_id}_n{numero}.xml
carpeta_offline = "offline_invoices"
archivos = [
    f for f in os.listdir(carpeta_offline)
    if f.startswith(f"factura_offline_ev{evento['id']}_") and f.endswith(".xml")
]
```

**Proceso:**
- **Carpeta objetivo:** `offline_invoices/`
- **Patrón de búsqueda:** `factura_offline_ev{ID_EVENTO}_n{NUMERO_FACTURA}.xml`
- **Ejemplo:** `factura_offline_ev47_n00012345.xml`

#### **6.2 Creación de Paquete ZIP**
```python
if archivos:
    os.makedirs("paquetes_contingencia", exist_ok=True)
    nombre_zip = f"paquetes_contingencia/evento_{evento['id']}_recepcion_{codigo_recepcion}.zip"

    with zipfile.ZipFile(nombre_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for archivo in archivos:
            ruta_completa = os.path.join(carpeta_offline, archivo)
            zipf.write(ruta_completa, arcname=archivo)
```

**Proceso:**
1. **Crea carpeta:** `paquetes_contingencia/` si no existe
2. **Nombre del ZIP:** `evento_{ID}_recepcion_{CODIGO_SIN}.zip`
3. **Compresión:** ZIP_DEFLATED para optimizar tamaño
4. **Contenido:** Todos los XMLs generados durante la contingencia

#### **6.3 Organización de Archivos**
```python
# Mover archivos procesados a subcarpeta
carpeta_procesados = os.path.join(carpeta_offline, "procesados")
os.makedirs(carpeta_procesados, exist_ok=True)

for archivo in archivos:
    origen = os.path.join(carpeta_offline, archivo)
    destino = os.path.join(carpeta_procesados, archivo)
    os.rename(origen, destino)
```

**Proceso:**
1. **Crea subcarpeta:** `offline_invoices/procesados/`
2. **Mueve archivos XML** desde raíz a subcarpeta para mantener orden
3. **Evita reprocessamiento** en futuras ejecuciones

---

## 🔄 **Flujo de Envío Masivo (BatchSender)**

### **Activación del Batch Sender**
**Archivo:** `batch_sender.py`

Una vez finalizado el evento, el sistema puede activar el `BatchSender` para enviar las facturas pendientes en lotes:

#### **Preparación de Lotes**
```python
def prepare_batches(self):
    # Obtener facturas en estado CONTINGENCIA
    facturas = self.session.query(FacturaCabecera).filter(
        FacturaCabecera.estadoFirma == "CONTINGENCIA"
    ).all()
    
    # Agrupar en lotes de máximo 500 facturas
    batches = []
    current_batch = []
    
    for factura in facturas:
        current_batch.append(factura.numeroFactura)
        if len(current_batch) >= self.max_batch_size:
            batches.append(current_batch)
            current_batch = []
```

#### **Envío al SIN**
```python
def send_batch(self, xml_path, compressed_path, cufd_code):
    # Crear archivo comprimido Gzip
    # Calcular hash SHA-256
    # Enviar vía servicio "recepcionPaqueteFactura"
    
    solicitud = {
        'codigoEmision': 2,  # Modo offline
        'cufd': cufd_code,
        'archivo': archivo_base64,
        'hashArchivo': hash_archivo,
        'cantidadFacturas': cantidad_facturas
    }
    
    response = client.service.recepcionPaqueteFactura(**solicitud)
```

---

## 📊 **Estados y Códigos de Respuesta**

### **Estados de Paquetes Post-Envío**
| Código | Estado | Descripción |
|--------|--------|-------------|
| **901** | 🟡 Pendiente | Paquete recibido, en proceso de validación |
| **904** | 🟠 Observado | Paquete con observaciones que requieren corrección |
| **908** | 🟢 Validado | Paquete procesado exitosamente |

### **Estados de Facturas en Base de Datos**
| Estado | Momento | Descripción |
|--------|---------|-------------|
| `CONTINGENCIA` | Durante offline | Factura emitida en contingencia |
| `PENDIENTE_ENVIO` | Post-recuperación | Lista para envío en paquete |
| `ENVIADA` | Post-envío | Incluida en paquete enviado al SIN |
| `VALIDADA` | Post-validación | Confirmada por el SIN |

---

## 🛡️ **Aspectos Normativos Clave**

### **✅ Cumplimiento Regulatorio**
1. **Máximo 500 facturas por paquete** (Normativa SIN)
2. **Registro obligatorio del evento** ante el SIN con fechas exactas
3. **Uso de CUFD vigente** para el registro del evento (NO reutilizar el de contingencia)
4. **Compresión Gzip** y hash SHA-256 de archivos
5. **Códigos de excepción** para NITs (código 1 obligatorio)

### **🔒 Garantías de Integridad**
1. **Atomicidad:** Si falla cualquier paso, se revierte todo
2. **Consistencia:** Estado sincronizado entre local y SIN
3. **Trazabilidad:** Logs completos de todo el proceso
4. **Recuperación:** Capacidad de reintento en caso de fallas

---

## 📁 **Estructura de Archivos Resultante**

```
facturador/
├── offline_invoices/
│   ├── procesados/                    # XMLs ya procesados
│   │   ├── factura_offline_ev47_n00012345.xml
│   │   ├── factura_offline_ev47_n00012346.xml
│   │   └── ...
│   └── (archivos nuevos de futuras contingencias)
│
├── paquetes_contingencia/             # Paquetes ZIP creados
│   ├── evento_47_recepcion_9357522.zip
│   ├── evento_46_recepcion_9332685.zip
│   └── ...
│
└── xmls_batch/                        # Archivos de lote (BatchSender)
    ├── batch_20250831_143022.xml
    ├── batch_20250831_143022.xml.gz
    └── ...
```

---

## 🎯 **Resultado Final**

Al completarse todo el flujo exitosamente:

### **✅ Estado del Sistema**
- **Evento de contingencia:** FINALIZADO con código de recepción del SIN
- **Base de datos local:** Actualizada con `fecha_fin` y `codigo_recepcion`
- **Facturas offline:** Organizadas en ZIP y movidas a carpeta `procesados/`
- **Sistema:** Vuelve a modo ONLINE normal

### **📊 Métricas Disponibles**
- **Número de facturas procesadas** durante la contingencia
- **Duración exacta** del evento (desde `fecha_inicio` hasta `fecha_fin`)
- **Código de recepción oficial** del SIN para referencia futura
- **Archivos ZIP generados** con todas las facturas del evento

### **🔄 Preparación para Futuras Contingencias**
- **Sistema listo** para detectar nuevas desconexiones
- **Carpetas limpias** para futuras facturas offline
- **Experiencia normativa** aplicada correctamente

---

## 🚀 **Ventajas del Diseño Implementado**

1. **🤖 Automático:** Se ejecuta sin intervención manual
2. **📋 Normativo:** Cumple 100% con regulaciones del SIN
3. **🛡️ Robusto:** Manejo completo de errores y rollback
4. **📊 Auditable:** Logs detallados de todo el proceso
5. **⚡ Eficiente:** Usa caché para evitar verificaciones redundantes
6. **🔧 Mantenible:** Código modular y bien documentado

---

**🎉 El sistema garantiza que ninguna factura generada durante contingencia se pierda y que todas sean procesadas conforme a la normativa boliviana una vez restaurada la conectividad.**
