# main.py
import streamlit as st 
from ui import main  # Asegúrate de que esto esté importando correctamente desde ui.py

st.set_page_config(page_title="FACTURADOR", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

if __name__ == "__main__":
    main()