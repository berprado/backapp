import os
import streamlit as st

# Directorio donde se encuentran los archivos de sincronización
sync_dir = '.'

# Lista todos los archivos en el directorio
files = os.listdir(sync_dir)

# Filtra solo los archivos de sincronización (ajusta esto según tus necesidades)
sync_files = [file for file in files if file.endswith('.py')]

# Crea un selector en la interfaz de Streamlit para seleccionar el archivo de sincronización
selected_file = st.selectbox('Selecciona un archivo de sincronización', sync_files)

# Cuando se presiona el botón, ejecuta el archivo de sincronización seleccionado
if st.button('Ejecutar archivo de sincronización'):
    exec(open(os.path.join(sync_dir, selected_file)).read())