# 🏗️ Diagrama de Arquitectura - Sistema de Gestión de Estado

## 📐 Arquitectura de la Solución

```mermaid
graph TB
    subgraph "ANTES - Problemático"
        A1[Variables Globales]
        A2[remote_time = None]
        A3[local_time = None]
        A4[time_difference = None]
        A5[❌ Se pierden en recarga]
        
        A1 --> A2
        A1 --> A3
        A1 --> A4
        A2 --> A5
        A3 --> A5
        A4 --> A5
    end
    
    subgraph "DESPUÉS - Solución Fase 1"
        B1[st.session_state.sync_state]
        B2[remote_time: datetime]
        B3[local_time: datetime]
        B4[time_difference: timedelta]
        B5[ultima_sincronizacion: datetime]
        B6[estado_comunicacion: str]
        B7[✅ Persiste durante sesión]
        
        B1 --> B2
        B1 --> B3
        B1 --> B4
        B1 --> B5
        B1 --> B6
        B2 --> B7
        B3 --> B7
        B4 --> B7
        B5 --> B7
        B6 --> B7
    end
    
    style A1 fill:#ff6b6b
    style A5 fill:#ff6b6b
    style B1 fill:#51cf66
    style B7 fill:#51cf66
```

---

## 🔄 Flujo de Datos

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Función de Sync
    participant I as inicializar_estado_sync()
    participant G as obtener_estado_sync()
    participant S as actualizar_estado_sync()
    participant SS as st.session_state
    participant BD as Base de Datos

    U->>F: Solicita sincronización
    F->>I: Primera vez en sesión
    I->>SS: Crear sync_state{}
    I->>BD: Consultar última_sincronizacion
    BD-->>I: Retorna datos (si existen)
    I->>SS: Cargar datos desde BD
    
    F->>G: Leer estado actual
    G->>I: Asegurar inicialización
    G->>SS: Obtener valor
    SS-->>G: Retornar valor
    G-->>F: Valor obtenido
    
    F->>F: Realizar sincronización SOAP
    F->>S: Actualizar remote_time
    S->>SS: Guardar en session_state
    
    F->>S: Actualizar ultima_sincronizacion
    S->>SS: Guardar en session_state
    S->>BD: Persistir en tabla
    BD-->>S: Confirmación
    S-->>F: Estado actualizado
    
    F-->>U: Mostrar resultado
```

---

## 🔐 Patrón de Encapsulación

```mermaid
graph LR
    subgraph "API Pública"
        A[obtener_estado_sync]
        B[actualizar_estado_sync]
        C[obtener_diferencia_horaria_formateada]
    end
    
    subgraph "Capa de Lógica"
        D[inicializar_estado_sincronizacion]
    end
    
    subgraph "Almacenamiento"
        E[st.session_state.sync_state]
        F[(Base de Datos)]
    end
    
    A --> D
    B --> D
    D --> E
    B --> F
    D -.->|Carga inicial| F
    
    style A fill:#4dabf7
    style B fill:#4dabf7
    style C fill:#4dabf7
    style D fill:#ffd43b
    style E fill:#51cf66
    style F fill:#51cf66
```

---

## 📊 Flujo de Sincronización Bidireccional

```mermaid
graph TD
    A[Primera Carga de Página] --> B{¿Existe sync_state?}
    B -->|NO| C[Crear sync_state vacío]
    B -->|SÍ| D[Usar existente]
    
    C --> E{¿Datos en BD?}
    E -->|SÍ| F[Cargar ultima_sincronizacion]
    E -->|NO| G[Continuar con valores None]
    
    F --> H[Estado Listo]
    G --> H
    D --> H
    
    H --> I[Usuario Sincroniza]
    I --> J[Obtener hora SIAT]
    J --> K[Calcular diferencia]
    K --> L[actualizar_estado_sync]
    
    L --> M[Guardar en session_state]
    L --> N[Guardar en BD]
    
    M --> O[Usuario Navega]
    O --> P[Vuelve a Sincronizar]
    P --> Q{¿sync_state existe?}
    Q -->|SÍ| R[✅ Datos Disponibles]
    Q -->|NO| A
    
    style B fill:#ffd43b
    style E fill:#ffd43b
    style Q fill:#ffd43b
    style R fill:#51cf66
    style M fill:#51cf66
    style N fill:#51cf66
```

---

## 🧩 Componentes del Sistema

```mermaid
graph TB
    subgraph "Funciones Accessor"
        F1[inicializar_estado_sincronizacion]
        F2[obtener_estado_sync]
        F3[actualizar_estado_sync]
        F4[obtener_diferencia_horaria_formateada]
    end
    
    subgraph "Estado Centralizado"
        S1[sync_state.remote_time]
        S2[sync_state.local_time]
        S3[sync_state.time_difference]
        S4[sync_state.ultima_sincronizacion]
        S5[sync_state.estado_comunicacion]
    end
    
    subgraph "Funciones Consumidoras (Fase 2)"
        C1[sincronizar_fecha_hora]
        C2[mostrar_informacion_sincronizacion]
        C3[main]
    end
    
    F1 --> S1
    F1 --> S2
    F1 --> S3
    F1 --> S4
    F1 --> S5
    
    F2 --> S1
    F2 --> S2
    F2 --> S3
    F2 --> S4
    F2 --> S5
    
    F3 --> S1
    F3 --> S2
    F3 --> S3
    F3 --> S4
    F3 --> S5
    
    F4 --> S3
    
    C1 -.->|Fase 2| F2
    C1 -.->|Fase 2| F3
    C2 -.->|Fase 2| F2
    C2 -.->|Fase 2| F4
    C3 -.->|Fase 2| F2
    
    style F1 fill:#4dabf7
    style F2 fill:#4dabf7
    style F3 fill:#4dabf7
    style F4 fill:#4dabf7
    style S1 fill:#51cf66
    style S2 fill:#51cf66
    style S3 fill:#51cf66
    style S4 fill:#51cf66
    style S5 fill:#51cf66
    style C1 fill:#ffd43b
    style C2 fill:#ffd43b
    style C3 fill:#ffd43b
```

---

## 📝 Comparación de Acceso a Datos

### **ANTES (Variables Globales)**

```python
# ❌ Acceso directo - Volátil
global remote_time, local_time, time_difference

# Leer
if remote_time is not None:
    print(remote_time)

# Escribir
remote_time = datetime.now()
```

### **DESPUÉS (Session State con Accessors)**

```python
# ✅ Acceso encapsulado - Persistente

# Leer (con inicialización automática)
remote_time = obtener_estado_sync('remote_time')
if remote_time is not None:
    print(remote_time)

# Escribir (con sincronización BD opcional)
actualizar_estado_sync('remote_time', datetime.now(), guardar_bd=False)
actualizar_estado_sync('ultima_sincronizacion', datetime.now(pytz.utc))  # Guarda en BD
```

---

## 🔍 Vista de Debugging

```mermaid
graph LR
    A[Inspector de Streamlit] --> B[st.session_state]
    B --> C[sync_state]
    C --> D[remote_time]
    C --> E[local_time]
    C --> F[time_difference]
    C --> G[ultima_sincronizacion]
    C --> H[estado_comunicacion]
    
    I[Logs] --> J[logger.debug]
    J --> K["Estado sync actualizado: remote_time = ..."]
    J --> L["Estado sync guardado en BD"]
    
    style C fill:#51cf66
    style D fill:#e9ecef
    style E fill:#e9ecef
    style F fill:#e9ecef
    style G fill:#e9ecef
    style H fill:#e9ecef
```

Para inspeccionar el estado en tiempo real:

```python
# En cualquier parte del código Streamlit
import streamlit as st

# Mostrar todo el estado de sincronización
st.write(st.session_state.sync_state)

# O individualmente
st.write(f"Remote time: {st.session_state.sync_state.get('remote_time')}")
```

---

## 🎯 Beneficios Arquitectónicos

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Acoplamiento** | Alto (global mutable) | Bajo (encapsulado) |
| **Testabilidad** | Difícil | Fácil (mock session_state) |
| **Debugging** | 3 lugares diferentes | 1 único lugar |
| **Consistencia** | ⚠️ Requiere sincronización manual | ✅ Automática |
| **Escalabilidad** | ❌ Agregar campos = modificar código | ✅ Solo agregar en inicialización |

---

## 🚀 Escalabilidad Futura

Agregar nuevos campos es trivial:

```python
def inicializar_estado_sincronizacion():
    if 'sync_state' not in st.session_state:
        st.session_state.sync_state = {
            # ... campos existentes ...
            
            # ✅ FÁCIL: Solo agregar aquí
            'sincronizaciones_fallidas': 0,
            'ultimo_error': None,
            'historial_diferencias': []
        }
```

No requiere cambios en las funciones accessor ni en el resto del código.

---

**Autor:** GitHub Copilot  
**Fecha:** 9 de octubre de 2025  
**Versión:** 1.0
