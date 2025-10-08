# Evaluacion de reemplazo de `1_Sincronizar.py`

## Contexto
Se analizo el modulo actual `facturador/pages/1_Sincronizar.py` y la propuesta `facturador/docs/mejoras/Propuesta_Sincronizar.py` para determinar la viabilidad de sustituir el primero por el segundo.

## Cambios relevantes detectados
- Centralizacion del logging: la propuesta elimina la configuracion manual de handlers y utiliza la infraestructura de `logger_config`, ahora a traves del logger dedicado `get_sincronizacion_logger`, integrando los mensajes en la infraestructura de logging rotativo definida para la aplicacion.
- Helper `registrar_y_mostrar`: se introduce una funcion que publica mensajes simultaneamente en Streamlit y en el log, reduciendo codigo repetido y homogeneizando la comunicacion.
- Ajustes de mensajeria: las llamadas directas a `st.success`, `st.warning`, `st.error` y `st.info` se reemplazan por `registrar_y_mostrar`, y se agrega un log informativo al finalizar cada sincronizacion individual.

## Pros de adoptar la propuesta
- Consistencia con la configuracion central de logs (formato comun, rotacion por fecha, codificacion UTF-8 garantizada).
- Menor duplicacion de codigo y menos riesgo de olvidar registrar eventos en el log cuando se modifica la interfaz.
- Log de resultados por servicio aprovechando el logger `facturador.sincronizacion`, lo que facilita trazabilidad dedicada sin perder integracion con la plataforma de logging.
- La infraestructura de `RotatingFileHandler` evita el crecimiento indefinido del archivo `sincronizacion_detallada.log` que usaba la version actual.

## Contras y riesgos identificados
- (Mitigado) Orden de importaciones: se movio la configuracion de `sys.path` antes del uso del logger y se usa `facturador.logger_config`.
- (Mitigado) Cambio de destino del log: se cre� el logger dedicado `facturador.sincronizacion`, conservando un archivo rotado especifico para este proceso.
- (Mitigado) Fallback de severidad: `registrar_y_mostrar` preserva el nivel del mensaje incluso cuando la capa de UI no esta disponible.
- Dependencia fuerte de `logger_config`: el import ejecuta `setup_application_loggers()` (crea multiples handlers y vacia `logging.getLogger().handlers`). Aunque esta es la estrategia corporativa, vale revisar que no interfiera con otras inicializaciones cuando Streamlit recarga el modulo.

## Recomendaciones
1. Realizar una ejecucion de prueba de las sincronizaciones (total e individuales) y revisar `logs/sincronizacion_*.log` para validar el flujo de mensajes y el comportamiento del logger bajo carga.
2. Confirmar que la inicializacion de loggers al recargar Streamlit no afecte otros modulos con configuraciones adicionales.

## Trabajo realizado
- Se reemplazo `facturador/pages/1_Sincronizar.py` con la version propuesta ajustada, moviendo la configuracion de `sys.path` antes de los imports y utilizando el logger `facturador.sincronizacion`.
- Se agrego el logger dedicado de sincronizacion en `facturador/logger_config.py`, garantizando rotacion diaria y preservando un archivo especifico para este proceso (`logs/sincronizacion_YYYYMMDD.log`).
- El helper `registrar_y_mostrar` ahora conserva la severidad del mensaje aun cuando Streamlit no este disponible, evitando degradacion a `info`.
- Se normalizan las claves compuestas y se cachean registros nuevos durante la sesion de sincronizacion para descartar duplicados enviados por el servicio cuando `autoflush` esta deshabilitado, evitando errores `IntegrityError`.
