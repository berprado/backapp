# main.py
import streamlit as st 
from ui_copy import main  # Asegúrate de que esto esté importando correctamente desde ui.py

st.set_page_config(page_title="BACKINVOICE", page_icon="💎", layout="wide", initial_sidebar_state="auto", menu_items={
    'Get Help': 'https://www.extremelycoolapp.com/help',
    'Report a bug': "https://www.extremelycoolapp.com/bug",
    'About': "# This is a header. This is an *extremely* cool app!"
})

if __name__ == "__main__":
    main()