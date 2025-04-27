"""
Script para probar el funcionamiento del nuevo sistema de manejo de estado.
Ejecutar este archivo con Streamlit para verificar que los módulos de gestión
de estado y caché funcionan correctamente.

Para ejecutar: streamlit run utils/test_state_manager.py
"""
import os
import sys
import streamlit as st

# Agregar la ruta del directorio padre al path de Python si no está ya
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Importar los módulos de gestión de estado
from utils.state_manager import (
    initialize_app_state, get_state, set_state, get_decimal_state,
    reset_states, is_offline_mode, get_active_event, save_form_data
)
from utils.cache_manager import invalidate_cache, check_cache_expiration

# Configurar página
st.set_page_config(
    page_title="Prueba de State Manager",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧪 Prueba de State Manager")
st.write("Esta herramienta te permite probar el sistema de gestión de estado centralizado.")

# Inicializar estados si no se ha hecho antes
initialize_app_state()

# Crear una estructura de pestañas para organizar las pruebas
tab1, tab2, tab3 = st.tabs(["📊 Estados actuales", "🔄 Pruebas de reinicio", "💾 Pruebas de caché"])

with tab1:
    st.header("📊 Estados actuales")
    
    # Mostrar todos los estados actuales
    st.subheader("Session State completo")
    st.json({k: v for k, v in st.session_state.items() if not k.startswith("_")})
    
    # Probar algunas funciones básicas
    st.subheader("Pruebas de funciones básicas")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("#### Lectura y escritura de estados")
        test_key = st.text_input("Clave a probar:", "test_value")
        test_value = st.text_input("Valor a establecer:", "Valor de prueba")
        
        if st.button("Establecer valor"):
            set_state(test_key, test_value)
            st.success(f"Valor establecido: {test_key} = {test_value}")
        
        current_value = get_state(test_key, "No existe")
        st.write(f"Valor actual de '{test_key}': **{current_value}**")
    
    with col2:
        st.write("#### Valores numéricos (Decimal)")
        decimal_key = st.text_input("Clave decimal:", "monto_prueba")
        decimal_value = st.number_input("Valor decimal:", value=123.45, step=10.0)
        
        if st.button("Establecer decimal"):
            set_state(decimal_key, decimal_value)
            st.success(f"Valor decimal establecido: {decimal_key} = {decimal_value}")
        
        current_decimal = get_decimal_state(decimal_key, 0.0)
        st.write(f"Valor decimal de '{decimal_key}': **{current_decimal}** (tipo: {type(current_decimal).__name__})")

with tab2:
    st.header("🔄 Pruebas de reinicio")
    
    st.write("Prueba las funciones de reinicio de estados según diferentes modos.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Reiniciar estados de factura"):
            reset_states('factura')
            st.success("Estados de factura reiniciados")
        
        if st.button("Reiniciar estados de formulario"):
            reset_states('formulario')
            st.success("Estados de formulario reiniciados")
        
        if st.button("Reiniciar todos los estados"):
            reset_states('all')
            st.success("Todos los estados reiniciados")
    
    with col2:
        # Probar estados de modo offline
        st.write("#### Modo Offline")
        
        if st.checkbox("Activar modo offline", value=is_offline_mode()):
            set_state('modo_offline', True)
            # Simular un evento activo
            if not get_active_event():
                set_state('evento_activo', {
                    'id': 1,
                    'codigo_evento': '5',
                    'descripcion': 'Evento de prueba',
                    'fecha_inicio': '2025-04-26T12:00:00',
                    'fecha_fin': None,
                    'cufd': 'CUFD-DE-PRUEBA-12345'
                })
        else:
            set_state('modo_offline', False)
            set_state('evento_activo', None)
        
        # Mostrar estado actual
        if is_offline_mode():
            st.warning("⚠️ Sistema en modo OFFLINE")
            evento = get_active_event()
            if evento:
                st.info(f"Evento activo: {evento['descripcion']}")
        else:
            st.success("✅ Sistema en modo ONLINE")

with tab3:
    st.header("💾 Pruebas de caché")
    
    st.write("Prueba las funciones de gestión de caché.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cache_type = st.selectbox(
            "Tipo de caché a invalidar:",
            options=[None, "facturas", "comandas", "parametricos", "all"],
            format_func=lambda x: "Todos" if x is None or x == "all" else x.capitalize()
        )
        
        if st.button("Invalidar caché"):
            try:
                invalidated = invalidate_cache(cache_type)
                st.success(f"Caché invalidado: {', '.join(invalidated) if invalidated else 'ninguno'}")
            except Exception as e:
                st.error(f"Error al invalidar caché: {str(e)}")
    
    with col2:
        st.write("#### Verificación de expiración")
        cache_file = st.text_input("Ruta del archivo de caché:", value="cache/comandas_cache.json")
        max_age = st.slider("Edad máxima (horas):", min_value=1, max_value=72, value=24)
        
        if st.button("Verificar expiración"):
            try:
                is_expired = check_cache_expiration(cache_file, max_age)
                if is_expired:
                    st.warning(f"⚠️ El caché ha expirado o no existe: {cache_file}")
                else:
                    st.success(f"✅ El caché sigue siendo válido: {cache_file}")
            except Exception as e:
                st.error(f"Error al verificar expiración: {str(e)}")

# Agregar un pie de página
st.markdown("---")
st.caption("Esta herramienta es parte del sistema de manejo de estado centralizado para la aplicación de facturación.")