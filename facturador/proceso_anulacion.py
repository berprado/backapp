import streamlit as st
import pandas as pd
from data_access import obtener_motivos_anulacion  # Obtener los motivos de anulación
from anulacion import anular_factura, obtener_codigo_motivo  # Función de anulación y código motivo
import time

def main():
    st.header("Anular Factura")
    
    # Placeholder para mensajes
    message_placeholder = st.empty()
    
    # Entrada para el número de factura
    numero_factura_anular = st.text_input("Ingrese el número de la factura a anular:")

    # Obtener las opciones de motivos desde la base de datos
    opciones_motivos = obtener_motivos_anulacion()
    
    # Verificar si hay motivos de anulación disponibles
    if opciones_motivos:
        # El usuario selecciona el motivo de anulación
        descripcion_motivo = st.selectbox("Seleccione el motivo de la anulación", opciones_motivos)
    else:
        st.error("No se encontraron motivos de anulación disponibles.")
        return

    # Botón para iniciar la anulación de la factura
    if st.button("Anular Factura"):
        message_placeholder.empty()  # Limpiar mensajes previos
        
        # Validación de los campos requeridos
        if not numero_factura_anular or not descripcion_motivo:
            message_placeholder.warning("Por favor, ingrese todos los datos requeridos.")
        else:
            # Obtener el código de motivo a partir de la descripción
            codigo_motivo = obtener_codigo_motivo(descripcion_motivo)
            
            if not codigo_motivo:
                message_placeholder.error("No se pudo obtener el código del motivo de anulación.")
                return

            # Mostrar spinner mientras se realiza la anulación
            with st.spinner("Anulando factura, por favor espere..."):
                time.sleep(1)  # Simulación de tiempo de espera
                exito, mensaje = anular_factura(numero_factura_anular, descripcion_motivo)
                
                # Manejar la respuesta con indicadores visuales
                if exito:
                    message_placeholder.success(f"✅ {mensaje}")
                    
                    # Almacenar en el historial de facturas anuladas
                    if "historial_anulaciones" not in st.session_state:
                        st.session_state.historial_anulaciones = []

                    st.session_state.historial_anulaciones.append({
                        "Número de Factura": numero_factura_anular,
                        "Motivo": descripcion_motivo,
                        "Resultado": mensaje
                    })
                else:
                    message_placeholder.error(f"❌ {mensaje}")
    
    # Mostrar historial de facturas anuladas
    if "historial_anulaciones" in st.session_state and st.session_state.historial_anulaciones:
        st.subheader("Historial de Facturas Anuladas")
        st.dataframe(pd.DataFrame(st.session_state.historial_anulaciones))
    
    # Opción para descargar el historial en CSV
    if "historial_anulaciones" in st.session_state and st.session_state.historial_anulaciones:
        st.download_button(
            label="Descargar Historial en CSV",
            data=pd.DataFrame(st.session_state.historial_anulaciones).to_csv(index=False).encode('utf-8'),
            file_name="historial_anulaciones.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
