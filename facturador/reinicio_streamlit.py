#!/usr/bin/env python3
"""
Script de reinicio limpio para Streamlit
"""
import streamlit as st
import time

def limpiar_session_state():
    """Limpia el session_state completamente"""
    # Establecer una bandera en session_state para indicar que debe limpiarse
    st.session_state['_limpiar_todo'] = True
    
    # Mostrar mensaje y recargar
    st.success("✅ Session State será limpiado. La página se recargará automáticamente.")
    time.sleep(0.5)  # Pequeña pausa para que el usuario vea el mensaje
    st.rerun()

if __name__ == "__main__":
    st.title("🔄 Reinicio de Estado de Impresión")
    st.write("Este script limpia completamente el estado de impresión.")
    
    # Comprobar si hay una bandera de limpieza y procesarla
    if '_limpiar_todo' in st.session_state and st.session_state['_limpiar_todo']:
        # Eliminar todas las claves excepto la propia bandera
        keys = [k for k in st.session_state.keys() if k != '_limpiar_todo']
        for key in keys:
            if key in st.session_state:
                del st.session_state[key]
                
        # Eliminar la bandera al final
        del st.session_state['_limpiar_todo']
        st.success("✅ Session State ha sido limpiado correctamente.")
    
    if st.button("🧹 Limpiar Session State"):
        limpiar_session_state()
