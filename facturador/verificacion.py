import streamlit as st
import pandas as pd
from estado_factura import verificar_estado_factura  # Importamos la función de verificación
import time

# Función cacheada para verificar el estado de la factura
@st.cache_data(ttl=600)
def verificar_estado_factura_cache(numero_factura):
    return verificar_estado_factura(numero_factura)

def main():
    st.header("Verificar Factura")
    
    # Crear un placeholder para mensajes
    message_placeholder = st.empty()
    
    # Entrada para el número de factura
    numero_factura = st.text_input("Ingrese el número de la factura:")
    
    # Validación en tiempo real del número de factura
    if not numero_factura.isdigit() and numero_factura:
        st.warning("El número de factura debe contener solo dígitos.")
    else:
        # Verificar si el usuario presiona el botón
        if st.button("Verificar Factura"):
            message_placeholder.empty()  # Limpiar mensajes previos
            
            if not numero_factura:
                message_placeholder.warning("Por favor, ingrese un número de factura.")
            else:
                # Mostrar un spinner mientras se procesa la verificación
                with st.spinner("Verificando la factura, por favor espere..."):
                    time.sleep(1)  # Simulamos una pequeña espera
                    exito, mensaje = verificar_estado_factura_cache(numero_factura)
                    
                    # Mostrar el resultado con indicadores visuales
                    if exito:
                        if "VALIDA" in mensaje:
                            message_placeholder.success(f"✅ {mensaje}")
                        elif "ANULADA" in mensaje:
                            message_placeholder.warning(f"⚠️ {mensaje}")
                        elif "RECHAZADA" in mensaje:
                            message_placeholder.error(f"❌ {mensaje}")
                        else:
                            message_placeholder.info(mensaje)
                    else:
                        # Si la factura no existe, mostrar un mensaje claro
                        if "No se encontró la factura" in mensaje:
                            message_placeholder.error(f"❌ {mensaje}")
                        else:
                            message_placeholder.error(f"❌ Error al verificar la factura: {mensaje}")
                    
                    # Agregar la factura al historial
                    if "historial_facturas" not in st.session_state:
                        st.session_state.historial_facturas = []

                    st.session_state.historial_facturas.append({
                        "Número de Factura": numero_factura,
                        "Estado": mensaje
                    })
    
    # Mostrar el historial de verificaciones
    if "historial_facturas" in st.session_state and st.session_state.historial_facturas:
        st.subheader("Historial de Verificaciones")
        st.dataframe(pd.DataFrame(st.session_state.historial_facturas))
    
    # Opción para descargar el historial en CSV
    if "historial_facturas" in st.session_state and st.session_state.historial_facturas:
        st.download_button(
            label="Descargar Historial en CSV",
            data=pd.DataFrame(st.session_state.historial_facturas).to_csv(index=False).encode('utf-8'),
            file_name="historial_verificaciones.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
