"""
Script para probar la integración del nuevo sistema de gestión de estado
con la aplicación de facturación existente.
"""
import streamlit as st
import os
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("integration_test.log")
    ]
)

# Asegurarse de que podemos importar desde la carpeta raíz
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Importar los sistemas de gestión de estado (nuevo y antiguo)
from utils.state_manager import (
    initialize_app_state, get_state, set_state, 
    get_decimal_state, reset_states
)
from utils.cache_manager import invalidate_cache
from utils.state_compat import initialize_print_state, reiniciar_estados

# Configurar la página
st.set_page_config(
    page_title="Prueba de Integración",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Prueba de Integración del Sistema de Gestión de Estado")
st.write("""
Esta herramienta prueba la integración entre el sistema original de 
gestión de estado y el nuevo sistema modular.
""")

# Comprobar que los módulos están correctamente importados
modules_ok = True
try:
    # Probar inicialización de estados
    initialize_app_state()
    st.success("✅ Sistema de gestión de estado inicializado correctamente")
    
    # Probar capa de compatibilidad
    initialize_print_state()
    st.success("✅ Capa de compatibilidad para inicializar estados funciona correctamente")
    
    # Probar gestor de caché
    try:
        invalidate_cache("facturas")
        st.success("✅ Sistema de gestión de caché funciona correctamente")
    except Exception as e:
        st.warning(f"⚠️ El sistema de gestión de caché encontró un problema (posiblemente es normal si es el primer uso): {str(e)}")
except Exception as e:
    modules_ok = False
    st.error(f"❌ Error al importar/inicializar los módulos: {str(e)}")

# Si los módulos están bien, realizar pruebas más detalladas
if modules_ok:
    st.write("---")
    st.subheader("Pruebas de Funcionalidad")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 1. Escribir y leer un valor")
        test_key = st.text_input("Clave:", "test_value")
        test_value = st.text_input("Valor:", "Este es un valor de prueba")
        
        if st.button("Guardar valor"):
            set_state(test_key, test_value)
            st.success(f"✅ Valor guardado: {test_key} = '{test_value}'")
        
        if st.button("Leer valor"):
            value = get_state(test_key, "No existe el valor")
            st.info(f"📖 Valor leído: '{value}'")
    
    with col2:
        st.write("#### 2. Escribir y leer un valor decimal")
        decimal_key = st.text_input("Clave decimal:", "test_decimal")
        decimal_value = st.number_input("Valor decimal:", value=123.45)
        
        if st.button("Guardar decimal"):
            set_state(decimal_key, decimal_value)
            st.success(f"✅ Valor decimal guardado: {decimal_key} = {decimal_value}")
        
        if st.button("Leer decimal"):
            value = get_decimal_state(decimal_key, 0.0)
            st.info(f"📖 Valor decimal leído: {value} (tipo: {type(value).__name__})")
    
    st.write("---")
    st.subheader("Pruebas de Reset de Estados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### Estado Actual")
        
        # Mostrar los valores actuales en session_state
        if st.button("Mostrar estado actual"):
            st.json({k: v for k, v in st.session_state.items() if not k.startswith("_")})
    
    with col2:
        st.write("#### Reiniciar Estados")
        
        reset_mode = st.radio(
            "Modo de reinicio:",
            options=["factura", "formulario", "all"],
            format_func=lambda x: {
                "factura": "Solo datos de factura",
                "formulario": "Solo datos de formulario",
                "all": "Todos los datos"
            }.get(x, x)
        )
        
        if st.button("Reiniciar estados"):
            reset_states(reset_mode)
            st.success(f"✅ Estados reiniciados en modo '{reset_mode}'")
            
            # También probar la capa de compatibilidad
            if reset_mode == "all":
                reiniciar_estados()
                st.success("✅ Capa de compatibilidad para reiniciar estados funciona correctamente")
    
    st.write("---")
    st.subheader("Pruebas de Modo Offline")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### Establecer Modo Offline")
        
        # Activar/desactivar modo offline
        is_offline = st.checkbox("Activar modo offline", value=get_state("modo_offline", False))
        
        if is_offline:
            # Si activamos el modo offline, también creamos un evento simulado
            set_state("modo_offline", True)
            
            # Crear un evento simulado si no existe
            if not get_state("evento_contingencia"):
                evento = {
                    "id": 999,
                    "codigo_evento": "5",
                    "descripcion": "Evento de prueba desde la integración",
                    "fecha_inicio": datetime.now().isoformat(),
                    "fecha_fin": None,
                    "cufd": "CUFD-DE-PRUEBA-12345"
                }
                set_state("evento_contingencia", evento)
                set_state("evento_activo", evento)
                st.success("✅ Evento simulado creado para pruebas")
            
            # Mostrar información del evento
            evento = get_state("evento_contingencia")
            if evento:
                st.info(f"📌 **Evento activo:**\n\n" +
                       f"- ID: {evento['id']}\n" +
                       f"- Código: {evento['codigo_evento']}\n" +
                       f"- Descripción: {evento['descripcion']}")
        else:
            # Si desactivamos el modo offline, limpiamos los eventos
            set_state("modo_offline", False)
            set_state("evento_contingencia", None)
            set_state("evento_activo", None)
    
    with col2:
        st.write("#### Estado de Conexión")
        
        # Mostrar el estado actual de modo offline
        if get_state("modo_offline", False):
            st.warning("⚠️ Sistema en modo OFFLINE")
            st.info("Las facturas se emitirán en modo contingencia")
        else:
            st.success("✅ Sistema en modo ONLINE")
            st.info("Las facturas se emitirán en modo normal")

# Información adicional
st.write("---")
st.caption("Esta herramienta es para probar la integración del nuevo sistema de gestión de estado en la aplicación existente.")
st.caption(f"Fecha y hora de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")