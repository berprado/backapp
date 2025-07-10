#!/usr/bin/env python3
"""
Script de reinicio limpio para Streamlit
"""
import streamlit as st

def limpiar_session_state():
    """Limpia el session_state completamente"""
    keys_to_remove = [
        'impresion_en_progreso',
        'impresion_finalizada', 
        'print_status',
        'debug_impresion',
        'ultimo_numero_factura',
        'ultima_impresion_timestamp'
    ]
    
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
            
    st.session_state.clear()
    st.rerun()

if __name__ == "__main__":
    st.title("🔄 Reinicio de Estado de Impresión")
    st.write("Este script limpia completamente el estado de impresión.")
    
    if st.button("🧹 Limpiar Session State"):
        limpiar_session_state()
        st.success("✅ Session State limpiado. La página se recargará automáticamente.")
