# 📋 FLUJO DE FACTURACIÓN ELECTRÓNICA OFFLINE - SISTEMA NORMATIVO

Este documento describe detalladamente el flujo implementado para la emisión de facturas cuando el sistema **NO tiene conectividad** con el Servicio de Impuestos Nacionales (SIAT), conforme a la normativa boliviana.

---

## 🔄 **FLUJO COMPLETO OFFLINE**

### **1. DETECCIÓN DE CONTINGENCIA**

**Archivos participantes:** `main.py`, `communication_manager.py`, `soap_services.py`

#### **1.1 Verificación de Conectividad (main.py:110-125)**
```python
resultado_completo = communication_manager.verificar_comunicacion_completa()
principal = resultado_completo["verificacion_principal"]
conectado = principal["conectado"] if principal else False
```

#### **1.2 Detección de Errores Normativos (soap_services.py:53-72)**
El sistema detecta automáticamente los siguientes estados que activan contingencia según normativa:
- `HTTP 400/404/500/502/503` - Servicios SIN inaccesibles
- `Timeout` - Tiempo de espera agotado  
- `ConnectionError` - Corte de Internet
- `Código -1` - Error específico normativo
- `Java Null Point Exception` - Error Java

**Función:** `verificar_comunicacion()` clasifica automáticamente el tipo de contingencia (códigos 1-7).

---

### **2. REGISTRO AUTOMÁTICO DEL EVENTO SIGNIFICATIVO**

**Archivos participantes:** `main.py`, `data_access.py`

#### **2.1 Verificación de Evento Activo (main.py:165-168)**
```python
evento_activo = obtener_evento_activo_actual()
if evento_activo:
    # Usar evento existente
else:
    # Crear nuevo evento
```

#### **2.2 Registro Normativo del Evento (main.py:170-185)**
```python
evento_data = {
    'codigoClasificador': tipo_deducido,  # Tipo deducido (1-7)
    'descripcion': f"Contingencia por falta de comunicación - {datetime.now()}"
}
evento_activo = registrar_evento_local_normativo(evento_data)
```

**Función:** `registrar_evento_local_normativo()` en `data_access.py:787-825` garantiza que solo exista **1 evento activo** simultáneamente conforme a normativa.

---

### **3. ACTIVACIÓN DE INTERFAZ OFFLINE**

**Archivos participantes:** `main.py`, `ui_copy.py`, `facturacion_tab.py`

#### **3.1 Carga de UI Offline (main.py:203-210)**
```python
render_full_ui(
    is_online=False, 
    connectivity_info=resultado_completo, 
    evento_activo=evento_activo,
    reconectar_callback=handle_reconexion
)
```

#### **3.2 Configuración del Entorno Offline (ui_copy.py)**
- Desactiva servicios online
- Activa modo contingencia en todas las pestañas
- Pasa el `evento_activo` a la pestaña de facturación

---

### **4. GENERACIÓN DE FACTURAS OFFLINE**

**Archivos participantes:** `tabs/facturacion_tab.py`, `data_access.py`, `invoice_xml_generator.py`

#### **4.1 Preparación de Datos (facturacion_tab.py:290-310)**
- Recopila datos del cliente (nombre, NIT/CI)
- Selecciona comandas y calcula totales
- Obtiene método de pago e información adicional

#### **4.2 Obtención del CUFD del Evento (facturacion_tab.py:340-344)**
```python
cufd_evento = evento_activo.get('cufd')
if not cufd_evento:
    show_message('error', "Error: El evento no tiene un CUFD válido")
    return
```

**CRÍTICO:** Se usa el CUFD que estaba vigente **ANTES del corte**, almacenado en el evento. Función `obtener_cufd_de_evento_activo()` en `data_access.py:164-178`.

#### **4.3 Manejo de Código de Excepción NIT (facturacion_tab.py:345-346)**
```python
codigo_excepcion = 1 if tipo_documento_seleccionado['codigoClasificador'] == '5' else None
```

**NORMATIVA:** Si el tipo de documento es NIT (código 5), **obligatorio** enviar código de excepción = 1.

#### **4.4 Generación del CUF (facturacion_tab.py:350-358)**
```python
cuf = generate_cuf(
    nit=NIT,
    fecha_emision=fecha_emision,
    sucursal=CODIGO_SUCURSAL,
    modalidad=CODIGO_MODALIDAD,
    tipoEmision=2,  # CRÍTICO: Código 2 = Contingencia offline
    # ... otros parámetros
)
```

**Archivo:** `generate_cuf.py` genera el Código Único de Facturación con `tipoEmision=2` indicando **facturación offline**.

---

### **5. CREACIÓN DEL XML FISCAL**

**Archivos participantes:** `invoice_xml_generator.py`, `facturacion_tab.py`

#### **5.1 Generación del XML (facturacion_tab.py:360-375)**
```python
xml_content = generate_xml_invoice(
    fecha_emision=fecha_emision,
    cuf=cuf,
    cufd=cufd_evento,  # CUFD del evento pre-corte
    codigoExcepcion=codigo_excepcion,
    # ... datos de cabecera y detalle
)
```

**Función:** `generate_xml_invoice()` en `invoice_xml_generator.py` crea el XML con estructura normativa incluyendo:
- Cabecera con información fiscal
- Detalles de productos/servicios  
- Leyenda aleatoria de base de datos
- Código de excepción cuando aplica

#### **5.2 Almacenamiento del XML (facturacion_tab.py:410-415)**
```python
evento_id = evento_activo.get('id')
filename = f"offline_invoices/factura_offline_ev{evento_id}_n{numero_factura}.xml"

with open(filename, 'w', encoding='utf-8') as f:
    f.write(xml_content)
```

**PATRÓN NORMATIVO:** `factura_offline_ev{ID_EVENTO}_n{NUMERO}.xml` permite identificar facturas por evento para procesamiento posterior.

---

### **6. REGISTRO EN BASE DE DATOS LOCAL**

**Archivos participantes:** `facturacion_tab.py`, `data_access.py`

#### **6.1 Guardado de Cabecera (facturacion_tab.py:417-425)**
```python
factura_cabecera_data.update({
    'tipoEmision': "2",  # Offline
    'estado': "PENDIENTE_ENVIO", 
    'codigoEvento': evento_activo.get('id'),  # Vinculación con evento
    'cuf': cuf,
    'cufd': cufd_evento
})
guardar_factura_cabecera(factura_cabecera_data)
```

#### **6.2 Guardado de Detalles (facturacion_tab.py:426-430)**
```python
for detalle in factura_detalles_data:
    detalle['numero_factura'] = numero_factura
    guardar_factura_detalle(detalle)
```

**Funciones:** `guardar_factura_cabecera()` y `guardar_factura_detalle()` en `data_access.py` almacenan toda la información fiscal localmente.

---

### **7. INCREMENTO DE NUMERACIÓN**

**Archivos participantes:** `facturacion_tab.py`, `data_access.py`

```python
incrementar_numero_factura()
```

**Función:** `incrementar_numero_factura()` en `data_access.py:253-270` mantiene secuencia numérica consistente entre facturas online y offline.

---

### **8. GENERACIÓN E IMPRESIÓN**

**Archivos participantes:** `facturacion_tab.py`, `invoice_templates.py`, `print_manager.py`

#### **8.1 Creación del HTML (facturacion_tab.py:435-440)**
```python
html_content = generate_html_invoice(factura_procesada)
qr_code = generate_qr_code(cuf, numero_factura)
```

#### **8.2 Envío a Cola de Impresión**
```python
solicitar_impresion(factura_procesada)
```

**Hilo independiente:** `print_manager.py` maneja la impresión térmica en segundo plano sin bloquear la interfaz.

---

## 🔄 **FINALIZACIÓN AUTOMÁTICA DE CONTINGENCIA**

**Archivos participantes:** `contingencia_auto.py`, `main.py`, `data_access.py`

### **9. DETECCIÓN DE RECONEXIÓN (main.py:95-101)**
```python
resultado = finalizar_evento_si_conectado()
if resultado:
    st.success("✅ Evento finalizado y facturas comprimidas")
```

### **10. SECUENCIA NORMATIVA DE CIERRE (contingencia_auto.py:30-60)**

#### **10.1 Obtención de NUEVO CUFD (CRÍTICO)**
```python
nuevo_cufd = solicitar_cufd()  # NUEVO CUFD, no reutilizar anterior
```

#### **10.2 Registro del Evento con SIN**
```python
codigo_recepcion, transaccion = enviar_evento_significativo(
    evento=evento,
    fecha_fin=datetime.now(),
    cufd=nuevo_cufd  # Usar NUEVO CUFD
)
```

#### **10.3 Cierre en Base de Datos Local**
```python
cerrar_evento_significativo(
    evento_id=evento["id"], 
    codigo_recepcion=codigo_recepcion
)
```

**Función:** `cerrar_evento_significativo()` en `data_access.py:849-867` actualiza el evento con código de recepción del SIN.

### **11. COMPRESIÓN DE PAQUETES (contingencia_auto.py:70-95)**
```python
archivos = [f for f in os.listdir("offline_invoices") 
            if f.startswith(f"factura_offline_ev{evento['id']}_")]

nombre_zip = f"paquetes_contingencia/evento_{evento['id']}_recepcion_{codigo_recepcion}.zip"
```

**Resultado:** Todas las facturas del evento se comprimen en un ZIP con nombre normativo para envío posterior al SIN.

---

## 📊 **ARCHIVOS Y FUNCIONES CLAVE**

| Archivo | Funciones Principales | Propósito |
|---------|----------------------|-----------|
| **main.py** | `main()` | Orquestación y detección inicial |
| **communication_manager.py** | `verificar_comunicacion_completa()` | Diagnóstico de conectividad |
| **soap_services.py** | `verificar_comunicacion()` | Detección de errores normativos |
| **data_access.py** | `registrar_evento_local_normativo()` | Gestión de eventos normativos |
| **facturacion_tab.py** | `_handle_offline_submission()` | Procesamiento facturas offline |
| **invoice_xml_generator.py** | `generate_xml_invoice()` | Creación XML fiscal |
| **contingencia_auto.py** | `finalizar_evento_si_conectado()` | Cierre normativo de contingencia |

---

## ✅ **CUMPLIMIENTO NORMATIVO**

- ✅ **Solo 1 evento activo** por vez
- ✅ **CUFD pre-corte** en todas las facturas offline  
- ✅ **Código excepción = 1** para documentos NIT
- ✅ **tipoEmision = 2** para facturas offline
- ✅ **Nuevo CUFD antes de registrar evento** al finalizar
- ✅ **Registro dentro de 48 horas** posterior a contingencia
- ✅ **Compresión en paquetes** con nombres normativos

**🎯 RESULTADO:** Sistema 100% conforme a normativa boliviana SIN para facturación offline.
