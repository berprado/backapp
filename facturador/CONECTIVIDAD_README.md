# 🌐 Sistema de Gestión de Conectividad

## Descripción General

Este sistema proporciona una gestión centralizada de la conectividad con los servicios del SIN (Servicio de Impuestos Nacionales), permitiendo al sistema de facturación trabajar tanto en modo online como offline de manera transparente.

## 📁 Archivos Involucrados

### `api_clients.py` - Cliente Centralizado
**Propósito**: Módulo central para gestionar todas las conexiones a servicios externos.

**Funciones principales**:
- `get_soap_client()`: Devuelve cliente SOAP singleton
- `reset_soap_client()`: Reinicia la conexión
- `is_soap_client_available()`: Verifica disponibilidad
- `get_connectivity_info()`: Información detallada del estado

### `ui_copy.py` - Interfaz Principal
**Mejoras implementadas**:
- **Banner de estado**: Muestra si está online/offline
- **Botón de reconexión**: Permite intentar reconectar manualmente
- **Información detallada**: Expandir para ver detalles técnicos

### Pestañas Actualizadas
- **`validar_nit_tab.py`**: Bloquea función si no hay conectividad
- **`cuis_tab.py`**: Advierte sobre funciones limitadas en offline

## 🚀 Características del Sistema

### ✅ Modo Online
- ✅ Todas las funciones disponibles
- ✅ Validación de NIT en tiempo real
- ✅ Solicitud de CUIS/CUFD
- ✅ Envío de facturas al SIN

### ⚠️ Modo Offline  
- ✅ Consulta de datos locales (clientes, facturas)
- ✅ Generación de facturas (se almacenan localmente)
- ❌ Validación de NIT
- ❌ Solicitud de nuevos códigos
- ❌ Envío inmediato al SIN

## 🔄 Gestión de Reconexión

### Reconexión Automática
El sistema verifica automáticamente la conectividad cada vez que se solicita el cliente.

### Reconexión Manual
Los usuarios pueden usar el botón "🔄 Reconectar" en la interfaz principal.

### Recuperación Post-Contingencia
Cuando se recupera la conectividad:
1. El sistema detecta automáticamente la reconexión
2. Las facturas offline se pueden enviar en lotes
3. Los códigos vigentes se pueden renovar

## 💡 Indicadores Visuales

### Estados de Conectividad
- 🟢 **Verde**: Conectado completamente
- 🟡 **Amarillo**: Internet disponible, SIN no accesible  
- 🔴 **Rojo**: Sin conexión a internet

### Mensajes para el Usuario
- **Modo Online**: "🌐 CONECTADO - Servicios del SIN disponibles"
- **Modo Offline**: "🌐 MODO OFFLINE - Sin conexión con los servicios del SIN"

## 🛠️ Implementación Técnica

### Patrón Singleton
```python
# El cliente se inicializa solo una vez
client = get_soap_client()
if client:
    # Usar cliente para servicios SOAP
    response = client.service.verificarNit(...)
```

### Verificación de Estado
```python
# Verificar antes de usar funciones que requieren conectividad
if is_soap_client_available():
    # Función online disponible
    validar_nit(numero)
else:
    # Mostrar mensaje de modo offline
    st.warning("Función no disponible offline")
```

### Información Detallada
```python
# Obtener estado completo del sistema
info = get_connectivity_info()
# info contiene: connected, client_available, status, status_message, last_check
```

## 🔧 Mantenimiento

### Agregar Nueva Función que Requiere Conectividad
1. Importar: `from api_clients import is_soap_client_available`
2. Verificar: `if not is_soap_client_available(): return`
3. Mostrar mensaje apropiado al usuario

### Debugging
- Los logs se registran automáticamente en `logger_config.py`
- Usar `get_connectivity_info()` para diagnóstico detallado
- El estado se muestra en el expandir "Detalles de conectividad"

## 🎯 Beneficios

### Para Usuarios
- **Transparencia**: Siempre saben en qué modo están trabajando
- **Control**: Pueden intentar reconectar cuando quieran
- **Continuidad**: El trabajo no se interrumpe por problemas de red

### Para Desarrolladores  
- **Separación clara**: UI no maneja detalles de conectividad
- **Código centralizado**: Un solo punto para gestionar clientes SOAP
- **Fácil mantenimiento**: Agregar nuevas funciones es simple

### Para el Sistema
- **Rendimiento**: Conexiones reutilizadas (singleton)
- **Confiabilidad**: Manejo robusto de errores de red
- **Escalabilidad**: Fácil agregar nuevos tipos de clientes

---

## 📋 Checklist de Implementación

- ✅ Cliente SOAP centralizado (`api_clients.py`)
- ✅ Indicador visual en UI principal
- ✅ Botón de reconexión manual
- ✅ Información detallada expandible
- ✅ Pestañas actualizadas para modo offline
- ✅ Logging y manejo de errores
- ✅ Documentación completa

**Estado**: ✅ **IMPLEMENTACIÓN COMPLETA**
