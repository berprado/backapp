# Plan Refactorizacion Cierre Manual de Eventos 3-7

## Parte 1: Registro manual de eventos 5, 6, 7
1. **Actualizar UI** (`facturador/pages/2_Eventos_Significativos.py`)
   - Dividir el layout en dos secciones: *Eventos planificados (3-4)* y *Eventos no operativos (5-7)*.
   - Reutilizar el filtro de eventos parametricos para incluir codigos `["5","6","7"]` en la nueva seccion.
   - Permitir capturar fecha/hora de inicio y, opcionalmente, fecha de fin (por defecto `None`).
   - Solicitar el CUFD vigente previo a la falla: usar `obtener_cufd_vigente()` y, si no coincide con la fecha indicada, habilitar input manual.
   - Registrar usando `registrar_evento_local_normativo()` y mostrar confirmacion con descripcion oficial (`get_eventos_parametricos()`).

2. **Soporte en capa de datos** (`facturador/data_access.py`)
   - Anadir helper opcional `registrar_evento_no_operativo(codigo_evento, fecha_inicio, cufd)` que delegue en `registrar_evento_local_normativo` permitiendo fecha personalizada (o extender la funcion existente para aceptar `fecha_inicio` opcional).
   - Asegurar que solo exista un evento abierto (validacion actual ya lo hace).

3. **Documentacion**
   - Actualizar `docs/DOCUMENTACION_EVENTOS_Y_PAQUETES.md` con instrucciones para registrar manualmente eventos 5-7.
   - Anadir guia operativa en `docs/README_OFFLINE.md` sobre uso del formulario y captura de CUFD.

## Parte 2: Cierre manual para eventos 3-7
1. **Evitar cierre automatico**
   - Modificar `facturador/main.py` para que, tras recuperar la conexion, solo invoque `finalizar_evento_si_conectado()` si el evento activo tiene codigo 1 o 2 (consultar `evento_activo['codigo_evento']`).
   - Actualizar `contingencia_auto.finalizar_evento_si_conectado()` para verificar el codigo del evento activo: si pertenece a {"3","4","5","6","7"}, retornar sin cerrar y registrar en logs que se requiere cierre manual.

2. **Flujo de cierre manual desde UI**
   - Mantener el boton "?? Finalizar evento y enviarlo al SIN" en `2_Eventos_Significativos.py` pero hacerlo visible para cualquier evento activo.
   - Al presionarlo: llamar a `finalizar_evento_si_conectado()`. Esta funcion debe aceptar un flag `forzar_cierre_manual` o reconocer que se trata de un cierre manual y proceder aunque la conexion ya este disponible.
   - Si no hay conexion y el usuario intenta cerrar, mostrar advertencia. Si hay conexion: enviar al SIN y luego disparar empaquetado si aplica.
   - Incluir un checkbox de confirmacion que obligue a declarar que las facturas manuales ya fueron transcritas al sistema antes de cerrar (aplica a codigos 5-7).

3. **Paquetes y facturas manuales y CAFC**
   - Ajustar `contingency_packager.py` y `batch_sender.py` para tomar `codigo_evento` dinamico (esto ya se detallo en `PLAN_REFACTORIZACION_EVENTOS_NO_OPERATIVOS.md`).
   - Incorporar en la UI una nota que recuerde solicitar un nuevo CUFD antes de enviar paquetes y que las facturas manuales se transcriben con el CUFD vigente al inicio del evento.
   - Para eventos 5, 6 y 7 validar que el CAFC sea obligatorio al consumir `recepcionPaqueteFactura`; si proviene de documentos preimpresos debe capturarse o seleccionarse en la UI y persistirse junto con el evento (para eventos 1-4 el CAFC permanece en 0).

4. **Logs y feedback**
   - Anadir mensajes claros en logs (`logger.info`) y en la UI indicando que eventos 3-7 solo se cerraran manualmente.

5. **Pruebas**
   - Escenario A: Evento 3 planificado -> generar facturas offline -> recuperar conexion -> sistema no cierra automaticamente -> usuario confirma transcripcion y presiona cerrar -> paquete enviado con codigo 3.
   - Escenario B: Evento 5 (no operativo) -> registrar manualmente fechas -> no permitir cierre automatico -> cerrar manualmente tras cargar facturas -> validar que el codigo enviado al SIN sea 5.
   - Verificar que eventos 1 y 2 mantienen el cierre automatico y que el boton manual tambien funciona como alternativa si es necesario.

## Consideraciones normativas y operativas obligatorias
- **CUFD segun escenario:**
  - Si el sistema sigue operativo (eventos 3-4) la emision offline usa el CUFD vigente antes del corte y se debe solicitar un CUFD nuevo antes de registrar el evento y antes de enviar paquetes para evitar caducidad del CUFD.
  - Si el sistema estuvo inoperativo (eventos 5-7) las facturas manuales se transcriben usando el CUFD vigente al ingresar en contingencia y tambien se debe obtener un nuevo CUFD antes del registro del evento y antes del envio de paquetes.
- **Transcripcion y cierre:** Mantener un registro de facturas sin codigo de respuesta y, una vez restablecido el servicio, consultar `verificacionEstadoFactura` para evitar duplicidades o anular las que ya esten registradas.
- **Codigo de excepcion para NIT:** Toda factura emitida fuera de linea con tipo de documento NIT debe enviar `codigoExcepcion = 1`; por defecto el valor es 0 y solo se cambia a 1 en estos casos.
- **Documentacion de eventos 5-7:** Registrar manualmente fecha de inicio (minuto exacto), fecha de fin, codigo de evento, CUFD asociado al evento y descripcion. El CUFD usado en la transcripcion debe coincidir con el registrado en el evento.
- **Paquetes por contingencia:**
  1. Transcribir facturas manuales a XML con `tipoEmision = 2`, firmarlas (modalidad electronica), validarlas contra XSD y almacenarlas individualmente.
  2. Formar paquetes de hasta 500 facturas, comprimir en Gzip, calcular hash SHA-256, obtener nuevo CUFD para el envio, consumir `recepcionPaqueteFactura` usando `codigoRecepcionEvento`, CAFC y CUFD del envio, y luego validar con `validacionRecepcionPaqueteFactura` (estados 901, 904, 908).
- **Buenas practicas adicionales:**
  - Solicitar CAFC correspondientes en ambiente piloto.
  - Los codigos especiales 99001, 99002 y 99003 tambien deben enviarse con tipo de documento NIT y `codigoExcepcion = 1`.
  - Validar que los valores de documentos (CI, NIT) sean numericos.
  - Recordar que el tipo de emision "CONTINGENCIA" del catalogo es de uso exclusivo del SIN; el sistema debe usar `tipoEmision = 2` para fuera de linea.

## Documentacion a actualizar
- `docs/PLAN_REFACTORIZACION_EVENTOS_NO_OPERATIVOS.md` con las decisiones finales y referencias cruzadas.
- `docs/DOCUMENTACION_EVENTOS_Y_PAQUETES.md` y `docs/README_OFFLINE.md` con las obligaciones sobre CUFD, codigo de excepcion y flujo de paquetes.
- Incluir en la documentacion (segun corresponda) la obligatoriedad del CAFC distinto de 0 para eventos 5-7 cuando se invoque `recepcionPaqueteFactura` y mantenerlo en 0 para eventos 1-4.
- `docs/README_RECUPERACION_CONEXION.md` para agregar la verificacion de facturas sin respuesta y el checklist previo al envio de paquetes.
