import os
import sys
import logging
import traceback
import streamlit as st
sys.path.append(os.path.dirname(__file__))
from sync import sincronizarActividades
from sync import sincronizarListaActividadesDocumentoSector
from sync import sincronizarListaLeyendasFactura
from sync import sincronizarListaMensajesServicios
from sync import sincronizarListaProductosServicios
from sync import sincronizarParametricaEventosSignificativos
from sync import sincronizarParametricaTipoDocumentoIdentidad
from sync import sincronizarParametricaTipoDocumentoSector
from sync import sincronizarParametricaTipoHabitacion
from sync import sincronizarParametricaTipoMetodoPago
from sync import sincronizarParametricaTipoMoneda
from sync import sincronizarParametricaTipoPuntoVenta
from sync import sincronizarParametricaTiposFactura
from sync import sincronizarParametricaUnidadMedida
from sync import sincronizarParametricaTipoEmision
from sync import sincronizarParametricaPaisOrigen
from sync import sincronizarParametricaMotivoAnulacion
# Agregar el directorio actual al PYTHONPATH

# Configurar el logging
log_file_path = 'sincronizaciones.txt'
if not os.path.exists(log_file_path):
    open(log_file_path, 'a').close()

logging.basicConfig(
    filename=log_file_path,
    filemode='a',  # Agregar a los logs existentes
    level=logging.DEBUG,  # Nivel de detalle
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Directorio donde se encuentran los archivos de sincronización
sync_dir = 'sync'


st.set_page_config(page_title="Sincronizar", page_icon=":arrows_counterclockwise:", layout="wide")

st.markdown("# Sincronizar Datos")
st.sidebar.header("Sincronizar")
# Lista de tuplas (nombre de archivo, función de sincronización)
sync_functions = [
    ('sincronizarActividades.py', sincronizarActividades.sincronizar),
    ('sincronizarListaActividadesDocumentoSector.py', sincronizarListaActividadesDocumentoSector.sincronizar_documento_sector),
    ('sincronizarListaLeyendasFactura.py', sincronizarListaLeyendasFactura.sincronizar_lista_leyendas_factura),
    ('sincronizarListaMensajesServicios.py', sincronizarListaMensajesServicios.sincronizar_lista_mensajes_servicios),
    ('sincronizarListaProductosServicios.py', sincronizarListaProductosServicios.sincronizar_lista_productos_servicios),    
    ('sincronizarParametricaEventosSignificativos.py', sincronizarParametricaEventosSignificativos.sincronizar_parametrica_eventos_significativos),
    ('sincronizarParametricaTipoDocumentoIdentidad.py', sincronizarParametricaTipoDocumentoIdentidad.sincronizar_parametrica_tipo_documento_identidad),
    ('sincronizarParametricaTipoDocumentoSector.py', sincronizarParametricaTipoDocumentoSector.sincronizar_parametrica_tipo_documento_sector),
    ('sincronizarParametricaTipoHabitacion.py', sincronizarParametricaTipoHabitacion.sincronizar_parametrica_tipo_habitacion),
    ('sincronizarParametricaTipoMetodoPago.py', sincronizarParametricaTipoMetodoPago.sincronizar_parametrica_tipo_metodo_pago),
    ('sincronizarParametricaTipoMoneda.py', sincronizarParametricaTipoMoneda.sincronizar_parametrica_tipo_moneda),
    ('sincronizarParametricaTipoPuntoVenta.py', sincronizarParametricaTipoPuntoVenta.sincronizar_parametrica_tipo_punto_venta),
    ('sincronizarParametricaTiposFactura.py', sincronizarParametricaTiposFactura.sincronizar_parametrica_tipos_factura),
    ('sincronizarParametricaUnidadMedida.py', sincronizarParametricaUnidadMedida.sincronizar_parametrica_unidad_medida),
    ('sincronizarParametricaTipoEmision.py', sincronizarParametricaTipoEmision.sincronizar_parametrica_tipo_emision),
    ('sincronizarParametricaPaisOrigen.py', sincronizarParametricaPaisOrigen.sincronizar_parametrica_pais_origen),
    ('sincronizarParametricaMotivoAnulacion.py', sincronizarParametricaMotivoAnulacion.sincronizar_parametrica_motivo_anulacion)
]

# Interfaz de Streamlit


# Columna para los botones
col1, col2 = st.columns(2)

# Función para ejecutar sincronización y registrar logs
def ejecutar_sincronizacion(func, file_name):
    try:
        logging.info(f'Iniciando sincronización para {file_name}')
        func()
        logging.info(f'Sincronización completada para {file_name}')
    except Exception as e:
        logging.error(f'Error al sincronizar {file_name}: {e}')
        logging.error(traceback.format_exc())
        st.error(f'Error al sincronizar {file_name}: {e}')

# Botón para ejecutar todas las sincronizaciones con st.spinner
if col1.button('Sincronizar Todo (Spinner)'):
    for file, sync_function in sync_functions:
        file_name = file.replace('sincronizar', '').replace('.py', '')
        with st.spinner(f"Sincronizando {file_name}..."):
            ejecutar_sincronizacion(sync_function, file_name)
        if file_name == 'Actividades':
            st.success(f" :heavy_check_mark: Las {file_name} se han sincronizado correctamente.")
        else:
            st.success(f" :heavy_check_mark: Los valores de :blue[ {file_name} ] se han sincronizado correctamente.")

# Botón para ejecutar todas las sincronizaciones con st.status
if col2.button('Sincronizar Todo (Status)'):
    for file, sync_function in sync_functions:
        with st.status(f":shark: {file}..."):
            ejecutar_sincronizacion(sync_function, file)
    st.status(f" :heavy_check_mark: {file} sincronizado correctamente.:sunglasses:")

# Lista de sincronizaciones individuales
st.markdown('---')
st.header('Sincronizaciones Individuales')
selected_files = st.multiselect('Selecciona los Servicios a sincronizar', [file for file, _ in sync_functions])

# Botón para ejecutar las sincronizaciones seleccionadas
if st.button('Ejecutar Sincronizaciones Seleccionadas'):
    for selected_file in selected_files:
        for file, sync_function in sync_functions:
            if file == selected_file:
                file_name = file.replace('sincronizar', '').replace('.py', '')
        with st.spinner(f"Sincronizando {file_name}..."):
            ejecutar_sincronizacion(sync_function, file_name)
        if file_name == 'Actividades':
            st.success(f" :heavy_check_mark: Los valores de las {file_name} se han sincronizado correctamente.")
        else:
            st.success(f" :heavy_check_mark: Los valores de :blue[ {file_name} ] se han sincronizado correctamente.")