# app.py
import streamlit as st
from soap_services import verificar_comunicacion

st.set_page_config(page_title="Sistema de Contingencia SIAT", layout="centered")

st.title("🛰️ Sistema de Contingencia SIAT")
st.markdown("Verifica el estado de conexión y accede a las opciones de contingencia.")

# Verificar comunicación
if st.button("🔄 Verificar conexión con el SIN"):
    mensaje, estado, _ = verificar_comunicacion()
    if estado:
        st.success(f"✅ Conexión establecida: {mensaje}")
    else:
        st.error(f"❌ Sin conexión: {mensaje}")
