# pages/2_📤_Finalizar_y_Enviar_Evento.py
import streamlit as st
from datetime import datetime
from database import (
    get_cufd_vigente,
    obtener_evento_abierto,
    actualizar_evento_final
)
from soap_services import verificar_comunicacion, enviar_evento_significativo

st.title("📤 Finalizar y Enviar Evento Significativo")

# 1. Verificar reconexión
mensaje, estado, _ = verificar_comunicacion()

if not estado:
    st.warning("⚠️ El sistema aún no está conectado al SIN.")
    st.stop()
else:
    st.success("✅ Conexión restablecida. Puedes cerrar y reportar el evento.")

# 2. Obtener evento abierto
evento = obtener_evento_abierto()
if not evento:
    st.info("No hay eventos locales pendientes por enviar.")
    st.stop()

# 3. Mostrar datos actuales
st.markdown("### Evento detectado previamente:")
st.write(f"🆔 ID: {evento['id']}")
st.write(f"📆 Fecha Inicio: {evento['fecha_inicio']}")
st.write(f"📝 Motivo: {evento['descripcion']}")

# 4. Confirmar envío
if st.button("📨 Enviar evento al SIN"):
    fecha_fin = datetime.now()
    cufd_actual = get_cufd_vigente()

    # Enviar al SIN
    codigo_recepcion, transaccion = enviar_evento_significativo(
        evento=evento,
        fecha_fin=fecha_fin,
        cufd=cufd_actual
    )

    if transaccion:
        actualizar_evento_final(
            evento_id=evento['id'],
            fecha_fin=fecha_fin,
            codigo_recepcion=codigo_recepcion
        )
        st.success(f"✅ Evento registrado con éxito en el SIN.")
        st.code(f"Código de recepción: {codigo_recepcion}")
    else:
        st.error("❌ No se pudo registrar el evento ante el SIN. Intenta nuevamente más tarde.")
