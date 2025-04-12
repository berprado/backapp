# pages/1_📝_Registrar_Evento_Inicio.py

import streamlit as st
from datetime import datetime
from database import (
    get_eventos_parametricos,
    get_cufd_vigente,
    insertar_evento_local
)
from soap_services import verificar_comunicacion

st.set_page_config(page_title="Registrar Evento", layout="centered")
st.title("📝 Registrar Evento Significativo (Inicio)")

# Obtener comunicación y tipo deducido
mensaje, conectado, tipo_deducido = verificar_comunicacion()

# Obtener lista de eventos paramétricos desde BD
tipos = get_eventos_parametricos()
opciones = {t["descripcion"]: t["codigoClasificador"] for t in tipos}
inverso = {v: k for k, v in opciones.items()}

# Solo eventos 3 y 4 están permitidos con conexión activa
TIPOS_PERMITIDOS_EN_LINEA = ['3', '4']

# Selección guiada por modo automático
if not conectado:
    st.warning(f"⚠️ El sistema está sin conexión: {mensaje}")
    st.info("Modo automático activado para registrar evento local.")

    # Intentar preseleccionar tipo sugerido
    if tipo_deducido and tipo_deducido in inverso:
        seleccion = st.selectbox(
            "Motivo sugerido por el sistema:",
            options=list(opciones.keys()),
            index=list(opciones.values()).index(tipo_deducido)
        )
        st.caption(f"💡 Sugerencia automática basada en el error detectado.")
    else:
        seleccion = st.selectbox("Selecciona el motivo del evento:", list(opciones.keys()))

elif conectado:
    st.success("✅ El sistema está en línea.")
    # Filtrar solo eventos permitidos en línea
    opciones_filtradas = {k: v for k, v in opciones.items() if v in TIPOS_PERMITIDOS_EN_LINEA}
    if not opciones_filtradas:
        st.info("No hay eventos configurados que puedan registrarse en línea.")
        st.stop()

    seleccion = st.selectbox("Selecciona el motivo del evento (anticipado):", list(opciones_filtradas.keys()))
else:
    st.error("Error desconocido al verificar la conexión.")
    st.stop()

# Obtener CUFD vigente desde BD
cufd = get_cufd_vigente()
if not cufd:
    st.error("❌ No se pudo obtener el CUFD vigente.")
    st.stop()

# Descripción del evento (manual)
descripcion = st.text_area("📝 Descripción adicional del evento")

if st.button("💾 Registrar evento local"):
    fecha_inicio = datetime.now()

    insertar_evento_local(
        codigo_evento=opciones[seleccion],
        descripcion=descripcion if descripcion else seleccion,
        fecha_inicio=fecha_inicio,
        cufd=cufd
    )

    st.success("✅ Evento registrado localmente con éxito.")
    st.caption("Cuando se restablezca la conexión, podrás finalizar y reportar este evento al SIN desde la página 📤.")
