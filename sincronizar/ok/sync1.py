
import streamlit as st
import sincronizarActividades
import sincronizarListaActividadesDocumentoSector
import sincronizarListaLeyendasFactura
import sincronizarListaMensajesServicios
import sincronizarParametricaEventosSignificativos
import sincronizarParametricaTipoDocumentoIdentidad
import sincronizarParametricaTipoDocumentoSector
import sincronizarParametricaTipoHabitacion
import sincronizarParametricaTipoMetodoPago
import sincronizarParametricaTipoMoneda
import sincronizarParametricaTipoPuntoVenta
import sincronizarParametricaTiposFactura
import sincronizarParametricaUnidadMedida
import sincronizarParametricaTipoEmision
import sincronizarParametricaPaisOrigen
import sincronizarParametricaMotivoAnulacion


# Directorio donde se encuentran los archivos de sincronización
sync_dir = '.'

# Lista de tuplas (nombre de archivo, función de sincronización)
sync_functions = [
    ('sincronizarActividades.py', sincronizarActividades.sincronizar, ),
    ('sincronizarListaActividadesDocumentoSector.py', sincronizarListaActividadesDocumentoSector.sincronizar_documento_sector),
    ('sincronizarListaLeyendasFactura.py', sincronizarListaLeyendasFactura.sincronizar_lista_leyendas_factura),
    ('sincronizarListaMensajesServicios.py', sincronizarListaMensajesServicios.sincronizar_lista_mensajes_servicios),
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
st.title('Sincronización de Datos')

# Columna para los botones
col1, col2, col3 = st.columns(3)

# Botón para ejecutar todas las sincronizaciones con st.progress
with col1:
   st.header("A cat")
   st.image("https://static.streamlit.io/examples/cat.jpg")

# Botón para ejecutar todas las sincronizaciones con st.spinner
if col2.button('Sincronizar Todo (Spinner)'):
    for file, sync_function in sync_functions:
        file_name = file.replace('sincronizar', '').replace('.py', '')
        with st.spinner(f"Actualizando {file_name}..."):
            sync_function()
        if file_name == 'Actividades':
            st.write(f" :heavy_check_mark: Las {file_name} se han sincronizado correctamente.")
        else:
            st.write(f" :heavy_check_mark: Los valores de la :blue[ {file_name} ]se han sincronizado correctamente.")

# Botón para ejecutar todas las sincronizaciones con st.status
if col3.button('Sincronizar Todo (Status)'):
    for file, sync_function in sync_functions:
        with st.status(f":sunglasses: {file}..."):
            sync_function()
    st.status(f" :heavy_check_mark: {file} sincronizado correctamente.:sunglasses:")
# Lista de sincronizaciones individuales
st.markdown('---')
st.header('Sincronizaciones Individuales')
selected_files = st.multiselect('Selecciona los archivos de sincronización', [file for file, _ in sync_functions])

# Botón para ejecutar las sincronizaciones seleccionadas
if st.button('Ejecutar Sincronizaciones Seleccionadas'):
    for selected_file in selected_files:
        for file, sync_function in sync_functions:
            if file == selected_file:
                file_name = file.replace('sincronizar', '').replace('.py', '')
        with st.spinner(f"Actualizando {file_name}..."):
            sync_function()
        if file_name == 'Actividades':
            st.write(f" :heavy_check_mark: Las {file_name} se han sincronizado correctamente.")
        else:
            st.write(f" :heavy_check_mark: Los valores de :blue[ {file_name} ] se han sincronizado correctamente.")