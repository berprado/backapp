import os
import streamlit as st
from invoice_templates import generate_compact_html_invoice  # Función para generar el HTML de la factura
from data_access import fetch_cliente, fetch_random_leyenda  # Funciones de acceso a datos
from database import SessionLocal  # Sesión de base de datos
# Imports at the top of prueba.py
from printer_utils import print_invoice_escpos  # Add this import
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("printer_debug.log"),
        logging.StreamHandler()
    ]
)

# Inicializar el estado de la aplicación para manejar el HTML y el CUF de la factura
if 'html_content' not in st.session_state:
    st.session_state['html_content'] = None
if 'cuf' not in st.session_state:
    st.session_state['cuf'] = None

# Conectar con la base de datos y obtener los datos de la factura
session = SessionLocal()

# Definir los datos de la factura obtenidos dinámicamente desde la base de datos
# Los valores reales deben ser consultados mediante las funciones definidas en `data_access.py`
cliente_data, error_cliente = fetch_cliente("344096024")  # Número de documento de prueba, reemplazar por valor dinámico
if error_cliente:
    st.error(f"Error al obtener los datos del cliente: {error_cliente}")
else:
    nombre_cliente = cliente_data.get("nombre_cliente", "Cliente Desconocido")

# Configurar el resto de los datos basados en la consulta o valores predeterminados
subtotal = float(cliente_data.get("subtotal", 0.0))
descuento_adicional = float(cliente_data.get("descuento_adicional", 0.0))
monto_giftcard = float(cliente_data.get("monto_giftcard", 0.0))
lineas_productos = [
    {"codigo": "001", "nombre": "Producto A", "unidad": "Pieza", "cantidad": 1, "precio_venta": 90.0, "sub_total": 90.0},
    {"codigo": "002", "nombre": "Producto B", "unidad": "Caja", "cantidad": 2, "precio_venta": 50.0, "sub_total": 100.0},
]  # Productos dinámicos basados en la consulta, reemplazar con datos reales
fecha_emision = "2023-09-28"
numero_factura = 248  # Esto debe ser generado o gestionado dinámicamente
nit = os.getenv('NIT') or "344096024"
cuf = None  # Se generará al confirmar la factura

# Generar leyenda desde la base de datos
leyenda = fetch_random_leyenda()
st.write(f"Leyenda utilizada: {leyenda}")

# Interfaz de Streamlit
st.title("Sistema de Facturación con Datos Reales")
col1, col2, col3 = st.columns(3)

# Botón en `col1` para generar la factura y actualizar `html_content` y `cuf`
with col1:
    if st.button("Facturar", key="generar_xml", help="Generar la factura con datos reales", disabled=False):
        try:
            # Generar el CUF de la factura (puede ser generado dinámicamente)
            cuf = "178B43EFDB95D6AC059AFDAA83896B4AFB4516EB05903DEBAD1409E74"  # Valor simulado, reemplazar con CUF real

            # Generar el HTML de la factura usando los datos reales obtenidos
            html_content = generate_compact_html_invoice(
                subtotal, descuento_adicional, monto_giftcard, 
                lineas_productos, nombre_cliente, fecha_emision, numero_factura, nit
            )

            # Actualizar el estado con el HTML y el CUF generado
            st.session_state['html_content'] = html_content
            st.session_state['cuf'] = cuf

            # Mostrar el HTML generado en la UI para inspección
            st.success(f"Factura generada correctamente con datos reales. CUF: {cuf}")
            st.code(html_content, language='html')
        except Exception as e:
            st.error(f"Error al generar la factura con datos reales: {str(e)}")

# **Botón de impresión** en `col2` que se muestra solo si la factura ha sido generada
with col2:
    if st.session_state['html_content'] is not None:
        if st.button("Imprimir Factura", key="imprimir_factura"):
            try:
                # Asegurarse de que todos los parámetros estén disponibles
                if not all([st.session_state['html_content'], 
                          st.session_state['cuf'], 
                          nit, 
                          numero_factura]):
                    raise ValueError("Faltan datos necesarios para la impresión")
                    
                # Intentar imprimir
                print_invoice_escpos(
                    html_content=st.session_state['html_content'],
                    cuf=st.session_state['cuf'],
                    nit=nit,
                    numero_factura=numero_factura
                )
                st.success("✅ Factura impresa correctamente")
                
            except Exception as e:
                logging.error(f"Error durante la impresión: {str(e)}")
                st.error(f"❌ Error al imprimir: {str(e)}")

# Botón de prueba para verificar la visibilidad de `col3`
with col3:
    st.button("Botón de prueba", key="boton_prueba_produccion")

# Cerrar la sesión de la base de datos después de completar el flujo
session.close()
