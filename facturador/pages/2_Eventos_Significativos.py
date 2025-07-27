# pages/2_Eventos_Significativos.py

import streamlit as st
from datetime import datetime
from soap_services import verificar_comunicacion
from data_access import get_eventos_parametricos, obtener_cufd_vigente, obtener_evento_abierto, insertar_evento_local

st.set_page_config(page_title="Eventos Significativos", layout="centered")

st.title("📌 Registro de Eventos Significativos Planificados")

# Verificar conexión al SIN
mensaje, estado, _ = verificar_comunicacion()

if not estado:
    st.error("❌ No se puede registrar eventos anticipados mientras el sistema está desconectado del SIN.")
    st.stop()

# Cargar eventos permitidos para registrar en línea
eventos = get_eventos_parametricos()
eventos_permitidos = {
    e["codigoClasificador"]: e["descripcion"]
    for e in eventos if e["codigoClasificador"] in ("3", "4")
}

st.success("✅ Conexión activa con el SIN. Puedes registrar eventos planificados.")

# Verificar si ya hay evento abierto
evento_abierto = obtener_evento_abierto()
if evento_abierto:
    st.warning(f"⚠️ Ya existe un evento abierto con ID #{evento_abierto['id']}. No se puede registrar uno nuevo.")
    st.stop()

# Formulario para registrar evento anticipado
with st.form("form_evento_planificado"):
    tipo_evento = st.selectbox("Selecciona el tipo de evento planificado", options=list(eventos_permitidos.keys()), format_func=lambda x: f"{x} - {eventos_permitidos[x]}")
    descripcion = st.text_area("Descripción del evento", value=eventos_permitidos.get(tipo_evento, ""))
    submit = st.form_submit_button("📝 Registrar Evento Significativo")

    if submit:
        cufd = obtener_cufd_vigente()
        if not cufd:
            st.error("⚠️ No se pudo obtener CUFD vigente para registrar el evento.")
        else:
            ahora = datetime.now()
            insertar_evento_local(
                codigo_evento=tipo_evento,
                descripcion=descripcion,
                fecha_inicio=ahora,
                cufd=cufd
            )
            st.success(f"✅ Evento registrado exitosamente como anticipado. ({tipo_evento})")
