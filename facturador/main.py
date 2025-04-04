# main.py
import streamlit as st
import os
import sys
from contingency_manager import check_connectivity, handle_offline_mode
from ui_copy import main as online_main

st.set_page_config(page_title="BACKINVOICE", page_icon="💎", layout="wide", initial_sidebar_state="auto", menu_items={
    'Get Help': 'https://www.extremelycoolapp.com/help',
    'Report a bug': "https://www.extremelycoolapp.com/bug",
    'About': "# This is a header. This is an *extremely* cool app!"
})

def main():
    # Verificar conectividad y comunicación con el servidor remoto
    is_connected, server_accessible = check_connectivity()

    if is_connected and server_accessible:
        print("Conexión establecida. Operando en modo online.")
        online_main()
    else:
        print("No hay conexión a internet o el servidor no está accesible. Operando en modo offline.")
        handle_offline_mode()

if __name__ == "__main__":
    main()