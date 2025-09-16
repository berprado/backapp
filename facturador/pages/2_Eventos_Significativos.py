import streamlit as st
from datetime import datetime, date

from data_access import (
    get_eventos_parametricos,
    obtener_evento_activo_actual,
    registrar_evento_local_normativo,
    obtener_cufd_vigente
)
from contingencia_auto import finalizar_evento_si_conectado
from facturador.communication_manager import communication_manager


# --- Configuración de la página ---
st.set_page_config(page_title="Eventos Significativos", layout="centered")
st.title("📌 Gestión de Eventos Significativos (Planificados)")


# --- Paso 1: Verificar comunicación con SIN usando el gestor centralizado ---
resultado_completo = communication_manager.verificar_comunicacion_completa()
principal = resultado_completo.get("verificacion_principal", {})
estado = principal.get("conectado", False)
mensaje = principal.get("mensaje", "No se pudo obtener el estado de comunicación.")

if not estado:
    st.warning("⚠️ El sistema no tiene comunicación con el SIN. "
               "Solo puede cerrar un evento si ya se restauró la conexión.")
else:
    st.success("✅ Conectado al SIN")


# --- Paso 2: Validar si existe un evento abierto ---
evento_abierto = obtener_evento_activo_actual()

if evento_abierto:
    st.info(f"📡 Evento abierto: ID #{evento_abierto['id']} "
            f"- Código {evento_abierto['codigo_evento']} "
            f"- Inicio: {evento_abierto['fecha_inicio']}")

    # --- Opción para cerrar evento ---
    if st.button("🛑 Finalizar evento y enviarlo al SIN"):
        resultado = finalizar_evento_si_conectado()
        if resultado:
            st.success("✅ Evento cerrado y enviado al SIN correctamente.")
        else:
            st.error("❌ No se pudo cerrar ni enviar el evento. Verifique logs.")
else:
    st.info("ℹ️ No hay eventos abiertos actualmente.")

    # --- Paso 3: Registrar nuevo evento planificado ---
    eventos = get_eventos_parametricos()
    eventos_permitidos = {
        e["codigoClasificador"]: e["descripcion"]
        for e in eventos if e["codigoClasificador"] in ("3", "4")
    }

    with st.form("form_evento_planificado"):
        tipo_evento = st.selectbox(
            "Selecciona el tipo de evento planificado",
            options=list(eventos_permitidos.keys()),
            format_func=lambda x: f"{x} - {eventos_permitidos[x]}"
        )

        # Permitir que el usuario planifique fecha/hora de inicio (opcional)
        fecha_inicio = st.date_input("Fecha de inicio", value=date.today())
        hora_inicio = st.time_input("Hora de inicio", value=datetime.now().time())
        fecha_inicio_dt = datetime.combine(fecha_inicio, hora_inicio)

        submit = st.form_submit_button("📝 Registrar Evento")

    if submit:
        cufd = obtener_cufd_vigente()
        if not cufd:
            st.error("⚠️ No se pudo obtener un CUFD vigente para registrar el evento.")
        else:
            try:
                registrar_evento_local_normativo(
                    codigo_evento=tipo_evento,
                    cufd=cufd
                )
                st.success(f"✅ Evento registrado exitosamente "
                           f"({tipo_evento} - {eventos_permitidos[tipo_evento]}).")
            except Exception as e:
                st.error(f"❌ Error al registrar evento: {str(e)}")
