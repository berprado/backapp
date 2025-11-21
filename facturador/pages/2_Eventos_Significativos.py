import streamlit as st
from datetime import datetime, date

from data_access import (
    get_eventos_parametricos,
    obtener_evento_activo_actual,
    registrar_evento_local_normativo,
    obtener_cufd_vigente,
)
from contingencia_auto import finalizar_evento_si_conectado
from facturador.communication_manager import communication_manager
from facturador.logger_config import get_logger, timed_call

logger = get_logger("ui")

MANUAL_EVENT_CODES = {"3", "4", "5", "6", "7"}
PLAN_EVENT_CODES = {"3", "4"}
NON_OPERATIONAL_CODES = {"5", "6", "7"}

st.set_page_config(page_title="Eventos Significativos", layout="centered")
st.title("Gestion de Eventos Significativos")
logger.info("[EVENTOS] Pantalla de gestion de eventos iniciada")

st.session_state.setdefault("evento_cafc", {})

resultado_completo = timed_call(
    logger,
    "[EVENTOS] Verificacion de comunicacion completa",
    communication_manager.verificar_comunicacion_completa
)
principal = resultado_completo.get("verificacion_principal", {})
conectado = principal.get("conectado", False)
mensaje = principal.get("mensaje", "Estado de comunicacion no disponible.")

if conectado:
    st.success("Conexion establecida con el SIN")
    logger.info("[EVENTOS] Comunicacion con SIN activa")
else:
    st.warning("El sistema no tiene comunicacion con el SIN. Solo podra cerrar eventos cuando se restablezca la conexion.")
    logger.warning("[EVENTOS] SIN sin conexion: %s", mensaje)

evento_abierto = timed_call(logger, "[EVENTOS] Consulta de evento activo", obtener_evento_activo_actual)
logger.debug("[EVENTOS] Evento activo: %s", evento_abierto)


if evento_abierto:
    evento_id = evento_abierto.get("id")
    codigo_evento = str(evento_abierto.get("codigo_evento"))
    descripcion = evento_abierto.get("descripcion", "Sin descripcion")
    fecha_inicio = evento_abierto.get("fecha_inicio")

    st.info(f"Evento abierto: ID #{evento_id} - Codigo {codigo_evento} - Inicio {fecha_inicio}")

    cafc_guardado = st.session_state["evento_cafc"].get(evento_id, "").strip()

    if codigo_evento in NON_OPERATIONAL_CODES:
        if cafc_guardado:
            st.success(f"CAFC configurado: {cafc_guardado}")
        else:
            st.warning("Configura el CAFC desde la barra lateral antes de emitir facturas durante este evento.")
    elif codigo_evento in PLAN_EVENT_CODES:
        st.warning("Verifique que las facturas offline generadas durante el evento planificado se hayan sincronizado antes del cierre.")

    with st.form("form_cierre_evento"):
        confirmacion = True
        if codigo_evento in MANUAL_EVENT_CODES:
            confirmacion = st.checkbox(
                "Confirmo que todas las facturas emitidas durante el evento fueron transcritas o validadas.",
                value=False,
                key=f"confirmacion_{evento_id}"
            )
        cerrar_evento = st.form_submit_button("Finalizar evento y enviarlo al SIN")

    if cerrar_evento:
        logger.info("[EVENTOS] Solicitud de cierre manual para evento %s", evento_id)

        if codigo_evento in MANUAL_EVENT_CODES and not confirmacion:
            st.error("Debe confirmar la transcripcion o validacion de facturas antes de cerrar el evento.")
        else:
            cafc_para_cierre = None
            if codigo_evento in NON_OPERATIONAL_CODES:
                cafc_para_cierre = cafc_guardado or None

            exito_cierre, detalle_cierre = timed_call(
                logger,
                f"[EVENTOS] Finalizacion evento {evento_id}",
                finalizar_evento_si_conectado,
                cierre_manual=(codigo_evento in MANUAL_EVENT_CODES),
                cafc_manual=cafc_para_cierre,
                confirmacion_manual=confirmacion
            )

            if exito_cierre:
                st.success(detalle_cierre)
                logger.info("[EVENTOS] Evento %s finalizado: %s", evento_id, detalle_cierre)
                st.rerun()
            else:
                st.error(detalle_cierre)
                logger.error("[EVENTOS] Cierre evento %s rechazado: %s", evento_id, detalle_cierre)
else:
    st.info("No hay eventos abiertos actualmente.")
    logger.info("[EVENTOS] Sin evento activo, mostrar formularios de registro")

    eventos_parametricos = {
        e["codigoClasificador"]: e["descripcion"]
        for e in timed_call(logger, "[EVENTOS] Obtener eventos parametricos", get_eventos_parametricos)
    }
    eventos_planificados = {k: v for k, v in eventos_parametricos.items() if k in PLAN_EVENT_CODES}
    eventos_no_operativos = {k: v for k, v in eventos_parametricos.items() if k in NON_OPERATIONAL_CODES}

    st.subheader("Eventos planificados (codigos 3 y 4)")
    with st.form("form_evento_planificado"):
        tipo_evento_plan = st.selectbox(
            "Seleccione el tipo de evento planificado",
            options=list(eventos_planificados.keys()),
            format_func=lambda x: f"{x} - {eventos_planificados[x]}"
        )
        fecha_plan = st.date_input("Fecha de inicio", value=date.today())
        hora_plan = st.time_input("Hora de inicio", value=datetime.now().time())
        cufd_plan = st.text_input(
            "CUFD vigente antes del evento",
            value=obtener_cufd_vigente() or "",
            help="Use el CUFD que estaba vigente al iniciar la contingencia."
        )
        registrar_plan = st.form_submit_button("Registrar evento planificado")

    if registrar_plan:
        logger.info("[EVENTOS] Registro de evento planificado solicitado para codigo %s", tipo_evento_plan)
        if not cufd_plan.strip():
            st.error("Debe proporcionar el CUFD vigente para el evento planificado.")
        else:
            try:
                evento_id = timed_call(
                    logger,
                    f"[EVENTOS] Registro evento planificado {tipo_evento_plan}",
                    registrar_evento_local_normativo,
                    codigo_evento=tipo_evento_plan,
                    cufd=cufd_plan.strip(),
                    fecha_inicio=datetime.combine(fecha_plan, hora_plan)
                )
                if evento_id:
                    logger.info("[EVENTOS] Evento planificado %s registrado con ID %s", tipo_evento_plan, evento_id)
                    st.success(f"Evento {tipo_evento_plan} registrado correctamente.")
                    st.rerun()
                else:
                    st.error("No se pudo registrar el evento planificado. Consulte los registros.")
            except Exception as exc:
                logger.error("[EVENTOS] Error registrando evento planificado: %s", exc)
                st.error(f"Error al registrar evento planificado: {exc}")

    st.subheader("Eventos no operativos (codigos 5, 6 y 7)")
    with st.form("form_evento_no_operativo"):
        tipo_evento_manual = st.selectbox(
            "Seleccione el tipo de evento no operativo",
            options=list(eventos_no_operativos.keys()),
            format_func=lambda x: f"{x} - {eventos_no_operativos[x]}"
        )
        fecha_manual = st.date_input("Fecha de inicio del evento", value=date.today(), key="fecha_manual")
        hora_manual = st.time_input("Hora de inicio del evento", value=datetime.now().time(), key="hora_manual")
        cufd_manual = st.text_input(
            "CUFD vigente al inicio de la contingencia",
            value=obtener_cufd_vigente() or "",
            help="Use el CUFD que estaba vigente cuando ocurrio la falla."
        )
        registrar_manual = st.form_submit_button("Registrar evento no operativo")

    if registrar_manual:
        logger.info("[EVENTOS] Registro de evento no operativo solicitado para codigo %s", tipo_evento_manual)
        if not cufd_manual.strip():
            st.error("Debe proporcionar el CUFD vigente para registrar el evento.")
        else:
            try:
                evento_id = timed_call(
                    logger,
                    f"[EVENTOS] Registro evento no operativo {tipo_evento_manual}",
                    registrar_evento_local_normativo,
                    codigo_evento=tipo_evento_manual,
                    cufd=cufd_manual.strip(),
                    fecha_inicio=datetime.combine(fecha_manual, hora_manual)
                )
                if evento_id:
                    logger.info("[EVENTOS] Evento no operativo %s registrado con ID %s", tipo_evento_manual, evento_id)
                    st.success("Evento no operativo registrado correctamente. Configure el CAFC en la barra lateral antes de emitir facturas manuales.")
                    st.rerun()
                else:
                    st.error("No se pudo registrar el evento no operativo. Consulte los registros.")
            except Exception as exc:
                logger.error("[EVENTOS] Error registrando evento no operativo: %s", exc)
                st.error(f"Error al registrar evento no operativo: {exc}")
