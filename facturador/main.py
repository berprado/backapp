# main.py
import streamlit as st
import os
import sys
from contingency_manager import check_connectivity, handle_offline_mode
from ui_copy import main as online_main
from offline_billing import offline_main  # Importar la interfaz de facturación offline

st.set_page_config(page_title="BACKINVOICE", page_icon="💎", layout="wide", initial_sidebar_state="auto", menu_items={
    'Get Help': 'https://www.extremelycoolapp.com/help',
    'Report a bug': "https://www.extremelycoolapp.com/bug",
    'About': "# This is a header. This is an *extremely* cool app!"
})

def main():
    try:
        # Verificar conectividad y comunicación con el servidor remoto
        is_connected, server_accessible = check_connectivity()

        if is_connected and server_accessible:
            print("Conexión establecida. Operando en modo online.")
            online_main()
        else:
            print("No hay conexión a internet o el servidor no está accesible. Operando en modo offline.")
            handle_offline_mode()
            st.warning("Modo offline activado. Las facturas se emitirán en contingencia.")
            offline_main()  # Cargar la interfaz de facturación offline
    except Exception as e:
        print(f"Error al iniciar el sistema: {e}")
        st.error("Error crítico al iniciar el sistema. Operando en modo offline.")
        handle_offline_mode()
        offline_main()

if __name__ == "__main__":
    main()