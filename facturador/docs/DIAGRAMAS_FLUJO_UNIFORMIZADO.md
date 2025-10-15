# 🔄 Diagramas de Flujo: Anulación y Reversión Uniformizados

## 📊 Flujo Unificado (Ambos Módulos)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INICIO: Usuario solicita operación               │
│                    (Anulación o Reversión de factura)               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1. OBTENER FACTURA DESDE BD                                        │
│     • obtener_cuf_por_numero_factura(numero_factura)                │
│     • Validar que existe                                            │
│     • Log: [BD] Factura encontrada. Estado: X                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                        ¿Factura existe?
                                  │
                    ┌─────────────┴─────────────┐
                    NO                          SÍ
                    │                           │
                    ▼                           ▼
        ❌ Error:                   ┌─────────────────────────┐
        "No se encontró             │  2. VALIDACIONES        │
        la factura"                 │     DE ESTADO           │
                                    └─────────────────────────┘
                                                │
                        ┌───────────────────────┼───────────────────────┐
                        │                       │                       │
                        ▼                       ▼                       ▼
            ¿Ya anulada?          ¿Ya revertida?           ¿Estado válido?
                        │                       │                       │
                    ┌───┴──┐                ┌───┴──┐                ┌───┴──┐
                    SÍ     NO               SÍ     NO               SÍ     NO
                    │      │                │      │                │      │
                    ▼      │                ▼      │                │      ▼
          ⚠️ Rechazo:     │      ⚠️ Rechazo:     │                │   ❌ Error
          "Ya anulada"    │      "Ya revertida"  │                │
                          │                       │                │
                          └───────────────────────┴────────────────┘
                                                  │
                                                  ▼
                                    ┌─────────────────────────┐
                                    │  3. VALIDACIÓN DE PLAZO │
                                    │     (Hasta día 9 del    │
                                    │      mes siguiente)     │
                                    └─────────────────────────┘
                                                  │
                                    ¿Dentro del plazo?
                                                  │
                                    ┌─────────────┴─────────────┐
                                    NO                          SÍ
                                    │                           │
                                    ▼                           ▼
                          ⏰ Rechazo:              ┌─────────────────────────┐
                          "Fuera de plazo"        │  4. OBTENER CUFD        │
                                                  │     • obtener_cufd()    │
                                                  │     • Log: [CUFD] OK    │
                                                  └─────────────────────────┘
                                                              │
                                                              ▼
                                                  ┌─────────────────────────┐
                                                  │  5. OBTENER MOTIVO      │
                                                  │     (Solo anulación)    │
                                                  │     • codigo_motivo     │
                                                  │     • Log: [MOTIVO] OK  │
                                                  └─────────────────────────┘
                                                              │
                                                              ▼
                                                  ┌─────────────────────────────────────┐
                                                  │  6. ENVIAR AL SIAT                  │
                                                  │     • get_siat_client()             │
                                                  │     • client.construir_solicitud()  │
                                                  │     • client.enviar_solicitud()     │
                                                  │     • Log: [SIAT] Enviando...       │
                                                  └─────────────────────────────────────┘
                                                              │
                                                              ▼
                                                    ¿Envío exitoso?
                                                              │
                                                  ┌───────────┴───────────┐
                                                  NO                      SÍ
                                                  │                       │
                                                  ▼                       ▼
                                        ❌ Error HTTP:       ┌─────────────────────────────────────┐
                                        "Error al enviar"   │  7. PROCESAR RESPUESTA XML          │
                                                            │     • Parsear XML                   │
                                                            │     • Extraer codigoEstado          │
                                                            │     • Extraer codigoDescripcion     │
                                                            │     • Extraer mensajesList          │
                                                            │     • Log: [PROCESAMIENTO] ...      │
                                                            └─────────────────────────────────────┘
                                                                            │
                                                                            ▼
                                                            ┌─────────────────────────────────────┐
                                                            │  8. OBTENER DESCRIPCIÓN             │
                                                            │     ESTRATEGIA: BD PRIMERO          │
                                                            │     • obtener_mensaje_por_codigo()  │
                                                            │     • Fallback: descripcion_siat    │
                                                            │     • limpiar_emojis_descripcion()  │
                                                            └─────────────────────────────────────┘
                                                                            │
                                                                            ▼
                                                            ┌─────────────────────────────────────┐
                                                            │  9. PREVENIR DetachedInstance       │
                                                            │     numero_factura = factura.num... │
                                                            └─────────────────────────────────────┘
                                                                            │
                                                                            ▼
                                                                  ¿Código de estado?
                                                                            │
        ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────┴─────────┬─────────────┬─────────────┐
        │             │             │             │             │                   │             │             │
        ▼             ▼             ▼             ▼             ▼                   ▼             ▼             ▼
      905/907       906/909        924          936/981        970                3011          3012      Desconocido
   (Confirmada)   (Rechazada)  (No existe)  (Ya anulada/    (Fuera de         (Sistema     (Solicitud      (Genérico)
                                             revertida)       plazo)          no autor.)     f. plazo)
        │             │             │             │             │                   │             │             │
        ▼             ▼             ▼             ▼             ▼                   ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ 10. ACTUALIZAR│ │ Construir    │ │ Construir    │ │ Construir    │ │ Construir    │ │ Construir    │ │ Construir    │
│ BD:           │ │ mensaje de   │ │ mensaje de   │ │ mensaje de   │ │ mensaje de   │ │ mensaje de   │ │ mensaje de   │
│ • estado      │ │ error con    │ │ advertencia  │ │ advertencia  │ │ advertencia  │ │ error        │ │ error        │
│ • fecha       │ │ Markdown     │ │ con Markdown │ │ con Markdown │ │ con Markdown │ │ crítico      │ │ genérico     │
│ • motivo      │ │              │ │              │ │              │ │              │ │              │ │              │
│               │ │              │ │              │ │              │ │              │ │              │ │              │
│ session.add() │ │              │ │              │ │              │ │              │ │              │ │              │
│ session.commit│ │              │ │              │ │              │ │              │ │              │ │              │
│               │ │              │ │              │ │              │ │              │ │              │ │              │
│ Log: [BD] OK  │ │              │ │              │ │              │ │              │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        │             │             │             │             │                   │             │             │
        ▼             ▼             ▼             ▼             ▼                   ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  11. CONSTRUIR MENSAJE MARKDOWN PARA EL USUARIO                                                                 │
│      • Título con emoji apropiado (✅, ❌, ⚠️, ⏰, 🔴, ❓)                                                      │
│      • Descripción limpia (sin emojis duplicados)                                                               │
│      • Detalles de la factura (número, fecha, motivo)                                                           │
│      • Mensajes adicionales del SIAT si existen                                                                 │
│      • Referencias normativas cuando aplica                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                              │
                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  12. RETORNAR (éxito: bool, mensaje: str)                                                                       │
│      • Log: [EXITO] o [ERROR] según el caso                                                                     │
│      • Mensaje formateado para Streamlit (st.success/error/warning)                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                              │
                                                              ▼
                                                         ┌─────────┐
                                                         │   FIN   │
                                                         └─────────┘
```

---

## 🔑 Diferencias Específicas

### Anulación vs Reversión

| Paso | Anulación | Reversión |
|------|-----------|-----------|
| **Paso 5** | ✅ Requiere motivo | ❌ No requiere motivo |
| **Validación estado inicial** | `Valida` | `Anulada` |
| **Operación SIAT** | `anulacionFactura` | `reversionAnulacionFactura` |
| **Código éxito** | 905 | 907 |
| **Código rechazo** | 906 | 909 |
| **Código ya procesada** | 936 (ya anulada) | 981 (ya revertida) |
| **Estado final (éxito)** | `Anulada` | `Valida` |
| **Campo actualizado** | `fechaAnulacion`, `motivoAnulacion` | `fechaValidacion` |

---

## 📋 Códigos de Estado Comunes

```
┌──────────────┬─────────────────────────────────────┬──────────────────┐
│ Código       │ Descripción                         │ Ambos módulos    │
├──────────────┼─────────────────────────────────────┼──────────────────┤
│ 905 / 907    │ Confirmada (Anulación / Reversión)  │ ✅ Sí            │
│ 906 / 909    │ Rechazada (Anulación / Reversión)   │ ✅ Sí            │
│ 924          │ Factura no existe en BD SIN         │ ✅ Sí            │
│ 936 / 981    │ Ya procesada (Anulada / Revertida)  │ ✅ Sí            │
│ 970          │ Fuera de plazo                      │ ✅ Sí            │
│ 3011         │ Sistema no autorizado               │ ✅ Sí            │
│ 3012         │ Solicitud fuera de plazo            │ ✅ Sí            │
└──────────────┴─────────────────────────────────────┴──────────────────┘
```

---

## 🔄 Flujo de Datos

```
Usuario (Streamlit UI)
       │
       │ (numero_factura, descripcion_motivo)
       ▼
anular_factura() / revertir_anulacion_factura()
       │
       ├──► obtener_cuf_por_numero_factura()  ───► BD Local
       │                                             │
       │                                             ▼
       │                                        (cuf, factura)
       │
       ├──► Validaciones locales
       │     • Estado actual
       │     • Plazo
       │
       ├──► obtener_cufd_vigente()  ───► BD Local
       │                                   │
       │                                   ▼
       │                              (cufd_codigo)
       │
       ├──► obtener_codigo_motivo()  ───► BD Local (solo anulación)
       │                                   │
       │                                   ▼
       │                              (codigo_motivo)
       │
       ├──► enviar_solicitud_anulacion() / enviar_solicitud_reversion()
       │           │
       │           ├──► get_siat_client()
       │           │         │
       │           │         ├──► construir_solicitud_anulacion/reversion()
       │           │         │         │
       │           │         │         ▼
       │           │         │    (xml_solicitud)
       │           │         │
       │           │         └──► enviar_solicitud()  ───► SIAT (Web Service)
       │           │                                         │
       │           │                                         ▼
       │           │                                    (respuesta_xml)
       │           │
       │           └──► (exito, respuesta_xml)
       │
       └──► procesar_respuesta_anulacion() / procesar_respuesta_reversion()
                   │
                   ├──► Parsear XML
                   │
                   ├──► obtener_mensaje_por_codigo()  ───► BD Local
                   │                                          │
                   │                                          ▼
                   │                                    (descripcion_bd)
                   │
                   ├──► limpiar_emojis_descripcion()
                   │         │
                   │         ▼
                   │    (descripcion_limpia)
                   │
                   ├──► Actualizar BD
                   │     • factura.estado
                   │     • factura.fechaAnulacion / fechaValidacion
                   │     • factura.motivoAnulacion (solo anulación)
                   │
                   └──► Construir mensaje Markdown
                             │
                             ▼
                        (éxito, mensaje)
                             │
                             ▼
                   Usuario (Mensaje en UI)
```

---

## 🎨 Componentes Compartidos

```
┌─────────────────────────────────────────────────────────────┐
│              COMPONENTES COMPARTIDOS                        │
│          (Usados por ambos módulos)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. siat_service_client.py                                  │
│     • get_siat_client()                                     │
│     • construir_solicitud_anulacion(cuf, codigo_motivo)     │
│     • construir_solicitud_reversion(cuf)                    │
│     • enviar_solicitud(xml, operacion)                      │
│                                                             │
│  2. data_access.py                                          │
│     • obtener_cuf_por_numero_factura(numero)                │
│     • obtener_mensaje_por_codigo(codigo)                    │
│     • obtener_cufd_vigente()                                │
│                                                             │
│  3. logger_config.py                                        │
│     • get_logger()                                          │
│                                                             │
│  4. database.py                                             │
│     • SessionLocal                                          │
│                                                             │
│  5. models.py                                               │
│     • FacturaCabecera                                       │
│     • SincronizarParametricaMotivoAnulacion                 │
│     • SincronizarListaMensajesServicios                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧩 Funciones Idénticas

```python
# Ambos módulos tienen esta función idéntica:

def limpiar_emojis_descripcion(descripcion):
    """
    Limpia emojis comunes del inicio de una descripción.
    """
    if not descripcion:
        return descripcion
    
    emojis_a_limpiar = ['✅', '❌', '⚠️', 'ℹ️', '🔴', '🟢', '🟡', '⏰', '❓']
    descripcion_limpia = descripcion.strip()
    
    for emoji in emojis_a_limpiar:
        while descripcion_limpia.startswith(emoji):
            descripcion_limpia = descripcion_limpia[len(emoji):].strip()
    
    return descripcion_limpia
```

---

## 📊 Patrones de Diseño Aplicados

### 1. Singleton Pattern
```python
# siat_service_client.py
_siat_client_instance = None

def get_siat_client():
    global _siat_client_instance
    if _siat_client_instance is None:
        _siat_client_instance = SIATServiceClient()
    return _siat_client_instance
```

### 2. Strategy Pattern (BD primero, SIAT fallback)
```python
# Estrategia uniforme en ambos módulos
descripcion_bd = obtener_mensaje_por_codigo(codigo_estado)
descripcion_principal = descripcion_bd if descripcion_bd else codigo_descripcion_siat
```

### 3. Template Method Pattern (flujo uniforme)
```python
# Ambos módulos siguen el mismo template:
# 1. Obtener factura
# 2. Validar estado
# 3. Validar plazo
# 4. Obtener CUFD
# 5. Enviar al SIAT
# 6. Procesar respuesta
```

---

## 🎯 Puntos de Extensibilidad

Si se agregan nuevos servicios SIAT (ej: modificación, duplicado), seguir este patrón:

1. Añadir método en `siat_service_client.py`:
   ```python
   def construir_solicitud_modificacion(self, cuf, datos_modificacion):
       # ...
   ```

2. Crear módulo `modificacion.py` con estructura idéntica:
   ```python
   # Constantes de estado
   ESTADO_MODIFICACION_CONFIRMADA = "XXX"
   
   # Función de limpieza (copiada)
   def limpiar_emojis_descripcion(descripcion):
       # ...
   
   # Función de envío (usa cliente)
   def enviar_solicitud_modificacion(cuf, datos):
       client = get_siat_client()
       # ...
   
   # Función de procesamiento (BD primero)
   def procesar_respuesta_modificacion(respuesta_xml, factura):
       descripcion_bd = obtener_mensaje_por_codigo(codigo_estado)
       # ...
   
   # Función principal (validaciones + envío + procesamiento)
   def modificar_factura(numero_factura, datos_modificacion):
       # ...
   ```

---

**Versión del diagrama:** 1.0.0  
**Fecha:** 15 de octubre de 2025  
**Estado:** ✅ Uniformización completada
