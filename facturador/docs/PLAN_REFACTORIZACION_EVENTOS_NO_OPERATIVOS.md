# Plan de Refactorizacion: Eventos Significativos No Operativos (Codigos 5, 6, 7)

## 1. Antecedentes
- Los eventos 1 y 2 se registran automaticamente segun la clasificacion de `soap_services.verificar_comunicacion()` y se cierran con `finalizar_evento_si_conectado()` (`facturador/main.py:122`, `facturador/contingencia_auto.py:13`).
- Los eventos planificados 3 y 4 se gestionan manualmente desde `facturador/pages/2_Eventos_Significativos.py`, reutilizando `registrar_evento_local_normativo()` (`facturador/data_access.py:197`).
- El fallback actual asigna codigo 5 cuando ocurre un error inesperado durante la verificacion (`facturador/soap_services.py:71`, `facturador/soap_services.py:77`). Esta conducta no esta alineada con la normativa, que exige que los eventos 5-7 solo se registren cuando el sistema esta realmente fuera de servicio.

## 2. Objetivos
1. Eliminar el uso del codigo 5 como fallback automatico y reemplazarlo por un estado "no clasificado" que obligue a una seleccion manual.
2. Permitir el registro manual (y posterior cierre) de eventos 5, 6 y 7 reutilizando la infraestructura existente de eventos significativos.
3. Mantener un flujo uniforme de cierre y empaquetado para todos los codigos una vez que el sistema se recupere.

## 3. Consideraciones normativas clave
- Eventos 5, 6 y 7 implican que el sistema no estuvo accesible; la fecha de inicio se determina retrospectivamente cuando el sistema vuelve (`facturador/docs/DOCUMENTACION_EVENTOS_Y_PAQUETES.md:23`).
- La documentacion oficial requiere que estos eventos se registren ante el SIN con el codigo correcto y que el paquete de facturas manuales use el mismo codigo (`facturador/docs/DOCUMENTACION_EVENTOS_Y_PAQUETES.md:49`).

## 4. Plan tecnico
### 4.1 Diagnostico y clasificacion
- **Eliminar fallback automatico:**
  - Ajustar `facturador/soap_services.py` para que, en lugar de devolver "5" en el bloque `except Exception`, retorne `None` como `tipo_deducido` y un mensaje que indique que se requiere clasificacion manual.
  - Actualizar `communication_manager.verificar_comunicacion_completa()` para propagar `None` y etiquetar el estado como "requiere intervencion" (`facturador/communication_manager.py:197`).
- **UI de clasificacion manual:**
  - En `facturador/main.py`, cuando `tipo_contingencia` sea `None` pero el estado sea offline, mostrar un `selectbox` con opciones (5, 6, 7) y guardar la seleccion en `st.session_state` antes de llamar a `registrar_evento_local_normativo()`.
  - Anadir validaciones para evitar continuar al modo offline sin que el usuario elija una causa.

### 4.2 Refactor de `2_Eventos_Significativos.py`
- Dividir la vista en dos secciones claramente diferenciadas:
  1. **Eventos planificados (codigos 3 y 4)**: mantener el formulario actual.
  2. **Eventos no operativos (codigos 5, 6, 7)**:
     - Permitir registrar manualmente un evento cuando el usuario dispone de fechas de inicio/fin (por ejemplo, al retomar operaciones tras el incidente).
     - Reutilizar `registrar_evento_local_normativo()` pasando un `codigo_evento` de la lista `["5", "6", "7"]` y forzando la carga del CUFD que estaba vigente antes de la falla (el usuario debera proporcionarlo). En caso de duda, admitir ingreso manual del CUFD o seleccionar uno historico.
     - Anadir mensajes de ayuda con la descripcion normativa de cada codigo (`facturador/docs/DOCUMENTACION_EVENTOS_Y_PAQUETES.md:23`).

### 4.3 Registro post-incidente
- Crear un helper en `facturador/data_access.py` para registrar eventos con fecha de inicio personalizada (opcional) que utilice la misma validacion de "un evento abierto".
- Anadir en la nueva seccion de la UI la posibilidad de ingresar fechas de inicio/fin manuales para documentar con fidelidad la duracion real del evento (por defecto usar `datetime.now()` para fecha_fin y `st.date_input` para fecha_inicio).

### 4.4 Ajustes en empaquetado y cierre
- Asegurarse de que el pipeline de cierre reenvie el codigo correcto:
  - `facturador/contingency_packager.py:409` debe tomar `codigo_evento` desde `obtener_evento_activo_actual()` en lugar de usar `1` de forma fija.
  - Verificar que `BatchSender.process_and_validate_batch()` recupere el `codigo_evento` del evento cerrado (`facturador/batch_sender.py:268`).

### 4.5 Coordinacion con flujo automatico
- En `facturador/main.py`, reutilizar el mismo bloque de registro para los eventos manuales 5-7 de modo que el cierre siga pasando por `finalizar_evento_si_conectado()`.
- Documentar en `docs/README_OFFLINE.md` que los eventos 5-7 requieren cargar la informacion retrospectivamente y que no existe flujo automatico para ellos.

## 5. Validacion
1. Simular contingencia para codigos 1 y 2 y comprobar que el flujo automatico no se ve afectado.
2. Ejecutar el nuevo flujo manual para codigos 5, 6 y 7:
   - Registrar un evento manual.
   - Emitir facturas fuera de linea o registrar facturas manuales.
   - Cerrar el evento con `finalizar_evento_si_conectado()`.
   - Verificar que el paquete se registre con el codigo correcto en la base de datos y en la respuesta del SIN.
3. Revisar logs (`facturador/logger_config.py`) para comprobar que se registran las causas seleccionadas.

## 6. Riesgos y mitigaciones
- **Clasificacion manual erronea:** mitigar mostrando descripciones normativas y confirmaciones adicionales.
- **CUFD incorrecto para eventos retroactivos:** proporcionar instrucciones para validar el CUFD vigente en la fecha de inicio y permitir editarlo antes de registrar.
- **Dependencia en la interaccion de usuario:** documentar el procedimiento operativo para el personal encargado cuando se restablezca el sistema.

## 7. Entregables
- Refactor de `facturador/pages/2_Eventos_Significativos.py` con las dos secciones.
- Actualizacion de `facturador/soap_services.py`, `facturador/communication_manager.py` y `facturador/main.py` para la nueva clasificacion.
- Ajustes en empaquetado/cierre (`facturador/contingency_packager.py`, `facturador/batch_sender.py`).
- Actualizacion de documentacion en `docs/README_OFFLINE.md` y `docs/DOCUMENTACION_EVENTOS_Y_PAQUETES.md` con las instrucciones para eventos 5, 6, 7.

