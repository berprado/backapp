# Dependencias internas de [facturador/communication_manager.py](facturador/communication_manager.py)

## Visión general
El gestor centraliza diagnósticos de conectividad con el SIN y provee resultados cacheados para el resto de la aplicación. No reemplaza flujos existentes; reutiliza servicios actuales y los enriquece con métricas y clasificación normativa.

## Módulos propios utilizados

1. **[facturador/soap_services.py](facturador/soap_services.py)**  
   - Funciones: `verificar_comunicacion`.  
   - Rol: ejecutar la verificación principal contra los servicios base del SIN.

2. **[facturador/business_logic.py](facturador/business_logic.py)**  
   - Funciones: `verificar_comunicacion`.  
   - Rol: realizar verificaciones específicas por servicio (códigos, operaciones, sincronización).

3. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: `get_logger`.  
   - Rol: registrar diagnósticos, errores y métricas de tiempos.

## Conclusión
`communication_manager.py` actúa como capa de orquestación sobre servicios ya existentes (`soap_services`, `business_logic`), añadiendo caché y clasificación `EstadoComunicacion`/`TipoContingencia`. Dado su rol transversal, cualquier refactor debe preservar las firmas y mensajes usados por `main.py` y módulos de contingencia.
