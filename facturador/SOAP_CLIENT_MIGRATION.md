# Migración de Cliente SOAP Centralizado

## Resumen

Se ha refactorizado la inicialización del cliente SOAP desde `ui_copy.py` hacia un nuevo módulo centralizado `api_clients.py` para mejorar la separación de responsabilidades y la mantenibilidad del código.

## Cambios Realizados

### 1. Nuevo Módulo: `api_clients.py`
- **Función principal**: `get_soap_client()` - Devuelve un cliente SOAP singleton
- **Funciones auxiliares**: 
  - `reset_soap_client()` - Reinicia el cliente después de contingencias
  - `is_soap_client_available()` - Verifica disponibilidad del cliente
- **Características**:
  - Patrón Singleton para evitar múltiples conexiones
  - Verificación automática de conectividad
  - Manejo de errores robusto
  - Logging completo de eventos

### 2. Archivos Actualizados

#### `ui_copy.py`
- ❌ **Removido**: Lógica de creación del cliente SOAP
- ✅ **Mejorado**: Enfoque únicamente en la presentación

#### `verifica_stream.py`
- ✅ **Actualizado**: Usa `get_soap_client()` en lugar de crear cliente local
- ✅ **Mejorado**: Mejor manejo de casos sin conectividad

#### `validators.py`
- ✅ **Actualizado**: `verificar_nit()` usa el cliente centralizado
- ❌ **Removido**: Función `crear_cliente_soap()` obsoleta

#### `client_manager.py`
- ✅ **Actualizado**: Importa y usa `get_soap_client()`

#### `data_access.py`
- ✅ **Actualizado**: `solicitar_cuis()` usa el cliente centralizado

### 3. Beneficios de la Refactorización

1. **Separación de Responsabilidades**
   - UI: Solo se encarga de la presentación
   - Lógica de negocio: Usa servicios especializados
   - Acceso a datos: Centralizado en módulos específicos

2. **Mejor Manejo de Conectividad**
   - Verificación automática antes de crear conexiones
   - Modo offline transparente
   - Reconexión automática tras contingencias

3. **Mantenibilidad**
   - Un solo punto de configuración para clientes SOAP
   - Fácil debugging y logging
   - Reutilización de código

4. **Rendimiento**
   - Patrón Singleton evita múltiples conexiones
   - Inicialización perezosa (lazy loading)

## Uso del Nuevo Cliente

### Ejemplo Básico
```python
from api_clients import get_soap_client

def mi_funcion_que_usa_soap():
    client = get_soap_client()
    if client is None:
        return False, "Sin conexión con el servicio del SIN"
    
    # Usar el cliente normalmente
    response = client.service.verificarNit(...)
    return True, response
```

### Verificar Disponibilidad
```python
from api_clients import is_soap_client_available

if is_soap_client_available():
    # Proceder con operaciones que requieren SOAP
    pass
else:
    # Manejar modo offline
    pass
```

### Reconectar Después de Contingencia
```python
from api_clients import reset_soap_client

# Después de resolver una contingencia
client = reset_soap_client()
if client:
    # Cliente reconectado exitosamente
    pass
```

## Archivos que Aún Necesitan Actualización

Los siguientes archivos aún contienen referencias a clientes SOAP locales y deberían actualizarse cuando sea necesario:

1. `significant_events.py`
2. `pages/3_Puntos_de_Venta.py` 
3. `pages/1_Sincronizar.py`
4. `cufd.py`
5. `business_logic.py`
6. `batch_sender.py`

## Pruebas Recomendadas

1. **Funcionalidad de Validación de NIT**
   - Verificar que la pestaña "Validar NIT" funciona correctamente
   - Probar tanto en modo online como offline

2. **Gestión de CUIS**
   - Verificar que la solicitud de CUIS funciona
   - Comprobar manejo de errores

3. **Modo Offline**
   - Desconectar internet y verificar que el sistema maneja gracefully el modo offline
   - Verificar que las funciones devuelven mensajes apropiados

## Notas de Migración

- **Compatibilidad**: La interfaz pública se mantiene igual (las funciones que recibían `client` como parámetro opcional siguen funcionando)
- **Logging**: Todos los eventos de conexión se registran en los logs
- **Variables de Entorno**: Se requieren las mismas variables que antes (`API_KEY`, `WSDL_URL_CODIGOS`, etc.)
