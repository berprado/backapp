🧠 Prompt: Generar sistema de registro de eventos significativos en contingencia (SIAT Bolivia)

Instrucción al LLM/agente:

Actúa como un desarrollador experto en normativa tributaria boliviana y consumo de servicios web. Tu objetivo es generar un módulo funcional en Python con Streamlit que permita registrar eventos significativos, conforme a la normativa del SIAT (Servicio de Impuestos Nacionales - Bolivia), incluyendo:
🎯 Objetivo del sistema

Construir un módulo con interfaz web que permita:

    Registrar eventos significativos anticipadamente si el sistema está en línea (tipos 3 y 4).

    Registrar eventos automáticamente si se detecta falla de comunicación con el SIN.

    Guardar el evento en base de datos MySQL con todos los campos necesarios.

    Utilizar SOAP para el consumo posterior del servicio registroEventoSignificativo.

🔑 Reglas y condiciones que debe respetar el sistema

    Tipos de eventos permitidos en línea:

        3 Ingreso a zonas sin internet por despliegue de puntos de venta

        4 Venta en lugares sin internet

    Eventos que requieren desconexión para registrarse:

        Tipos 1, 2, 5, 6, 7 (detectar vía verificarComunicacion())

    Lógica inteligente de inferencia:

        El sistema debe sugerir el tipo de evento si detecta:

            HTTP 500 → tipo 2

            Timeout o fallo de DNS → tipo 1

            Error inesperado → tipo 5

    Datos obligatorios a registrar:

        codigo_evento: código desde la tabla sincronizarparametricaeventossignificativos

        descripcion: ingresada por el usuario o sugerida

        fecha_inicio: timestamp automático

        fecha_fin: igual a inicio (se actualizará después)

        cufd: obtenido desde la tabla cufd donde vigente = 1

    Tabla destino: eventos_significativos_registrados, con esta estructura:

    (id, codigo_evento, descripcion, fecha_inicio, fecha_fin, cufd, codigo_recepcion, fecha_registro)

📌 Detalles técnicos del sistema

    Interfaz web con Streamlit

    Backend en Python 3.9+

    Base de datos MySQL

    Variables del sistema cargadas desde .env

    Consumo de servicios SOAP con requests

    Verificación de conexión con el servicio verificarComunicacion (SOAP)

📥 Entradas necesarias para el LLM

    Acceso a las siguientes funciones o que pueda generarlas:

        verificar_comunicacion() -> Tuple[str, bool, Optional[str]]

        get_eventos_parametricos() -> List[Dict]

        get_cufd_vigente() -> str

        insertar_evento_local(...)

✅ Salida esperada

    Un archivo Streamlit Registrar_Evento_Inicio.py con:

        Verificación de conectividad automática

        Inferencia del tipo de evento si hay error

        Formulario de descripción

        Registro del evento local con validación

🧪 Ejemplo de comportamiento esperado

🔄 Detecta que no hay conexión → deduce que es tipo 2
📝 Usuario confirma descripción
💾 Se guarda evento con fecha y CUFD actual
✅ Mensaje: "Evento registrado localmente. Cuando se recupere la conexión, será enviado al SIN"


🧠 Prompt: Generar módulo para finalizar y enviar eventos significativos al SIN (SIAT Bolivia)

Instrucción al LLM/agente:

Actúa como un desarrollador especializado en facturación electrónica en Bolivia. Genera un módulo en Python + Streamlit que permita finalizar un evento significativo previamente registrado (modo contingencia) y enviarlo al SIN mediante el servicio registroEventoSignificativo vía SOAP.
🎯 Objetivo funcional

El sistema debe:

    Detectar si la conexión con el SIN ha sido restablecida.

    Obtener el último evento significativo registrado en base de datos que aún no ha sido enviado (estado: pendiente).

    Completar el evento con la fecha/hora actual (fecha_fin).

    Obtener el CUFD vigente desde la tabla cufd.

    Enviar la información al SIN usando el servicio SOAP.

    Si el resultado de la transacción es exitoso, actualizar la tabla local con:

        fecha_fin

        codigo_recepcion devuelto por el SIN

        fecha_registro (auto)

📥 Datos esperados en base de datos

Tabla: eventos_significativos_registrados
El evento pendiente cumple con:

WHERE fecha_inicio = fecha_fin AND codigo_recepcion IS NULL

Campos necesarios para el envío:

    codigo_evento

    descripcion

    fecha_inicio

    cufd usado durante el evento

También debe obtenerse desde entorno/configuración:

    CUIS, NIT, CODIGO_SISTEMA, CODIGO_SUCURSAL, CODIGO_PUNTO_VENTA, CODIGO_AMBIENTE

🔧 SOAP: Servicio a consumir

registroEventoSignificativo con cuerpo:

<SolicitudEventoSignificativo>
  <codigoAmbiente>2</codigoAmbiente>
  <codigoMotivoEvento>1</codigoMotivoEvento>
  <codigoPuntoVenta>0</codigoPuntoVenta>
  <codigoSistema>XXXX</codigoSistema>
  <codigoSucursal>0</codigoSucursal>
  <cufd>CUFD_VIGENTE</cufd>
  <cufdEvento>CUFD_DEL_EVENTO</cufdEvento>
  <cuis>CUIS</cuis>
  <descripcion>Descripción</descripcion>
  <fechaHoraFinEvento>2025-04-11T10:11:12</fechaHoraFinEvento>
  <fechaHoraInicioEvento>2025-04-11T08:30:00</fechaHoraInicioEvento>
  <nit>123456789</nit>
</SolicitudEventoSignificativo>

✅ Validaciones que debe incluir

    Si no hay conexión, no permitir envío.

    Si no hay evento pendiente, mostrar mensaje informativo.

    Si el SIN responde con error, no guardar nada, solo mostrar mensaje.

    Si transaccion = true, guardar codigo_recepcion en la fila del evento.

📦 Funcionalidades requeridas

    Verificación de conexión con verificar_comunicacion()

    Recuperación de evento pendiente con obtener_evento_abierto()

    Envío al SIN con enviar_evento_significativo(evento, fecha_fin, cufd)

    Actualización con actualizar_evento_final(...)

✅ Resultado esperado en UI (Streamlit)

✅ Conexión al SIN restablecida
📝 Evento detectado: ID #12 – “Falla de internet”
📤 Enviando...

✅ Evento registrado con éxito ante el SIN
📦 Código de recepción: 9876543

📁 Salida solicitada

Un archivo Streamlit pages/2_📤_Finalizar_y_Enviar_Evento.py con:

    Verificación de conectividad

    Detección y visualización del evento pendiente

    Envío del evento con validación de respuesta

    Actualización de la base de datos

    Mensajes amigables al usuario


