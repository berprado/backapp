"""
Módulo para la pestaña de diagnóstico avanzado.
"""
import streamlit as st
from datetime import datetime
from logger_config import get_logger

logger = get_logger()

def render():
    """Renderiza la pestaña de diagnóstico avanzado."""
    st.header("🔧 Diagnóstico Avanzado de Comunicación")
    logger.info("Usuario accedió a la pestaña 'Diagnóstico'")
    
    st.markdown("""
    Esta pestaña utiliza un **servicio mejorado** que combina todas las verificaciones existentes
    del sistema para proporcionar un diagnóstico completo del estado de comunicación con el SIN.
    
    **Nota**: Este diagnóstico **NO reemplaza** las funcionalidades existentes, sino que las **mejora**.
    """)
    
    # Importar el nuevo servicio de manera segura
    try:
        from communication_manager import communication_manager
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🔍 Ejecutar Diagnóstico Completo", type="primary"):
                logger.info("Ejecutando diagnóstico completo de comunicación")
                communication_manager.mostrar_diagnostico_completo()
        
        with col2:
            st.info("**Fuentes de Verificación:**\n"
                   "• soap_services.py\n"
                   "• business_logic.py\n"
                   "• Análisis combinado")
        
        # Mostrar último resultado si existe
        estado_persistente = communication_manager.obtener_estado_persistente()
        ultimo_resultado = estado_persistente.get('ultimo_resultado_completo')
        
        if ultimo_resultado:
            st.subheader("📊 Último Diagnóstico")
            with st.expander("Ver detalles del último diagnóstico"):
                st.json(ultimo_resultado)
                
                # Mostrar tiempo transcurrido
                try:
                    timestamp = datetime.fromisoformat(ultimo_resultado['timestamp'])
                    tiempo_transcurrido = datetime.now() - timestamp
                    st.caption(f"Ejecutado hace: {tiempo_transcurrido}")
                    logger.info(f"Último diagnóstico ejecutado hace: {tiempo_transcurrido}")
                except:
                    st.caption("Tiempo de ejecución: No disponible")
                    logger.warning("No se pudo calcular el tiempo del último diagnóstico")
        
        # Información sobre compatibilidad
        _render_compatibility_info()
        
    except ImportError as e:
        st.error("❌ Error al cargar el servicio de diagnóstico avanzado")
        st.code(f"Error: {e}")
        st.info("💡 El sistema continúa funcionando normalmente con las verificaciones existentes.")
        logger.error(f"Error al importar communication_manager: {e}")

def _render_compatibility_info():
    """Renderiza la información sobre compatibilidad."""
    with st.expander("ℹ️ Información sobre Compatibilidad"):
        st.markdown("""
        ### 🛡️ Garantías de Compatibilidad
        
        Este diagnóstico avanzado:
        
        ✅ **NO modifica** las funciones existentes en `soap_services.py`  
        ✅ **NO modifica** las funciones existentes en `business_logic.py`  
        ✅ **NO cambia** imports existentes en otros módulos  
        ✅ **NO interfiere** con el funcionamiento normal del sistema  
        ✅ **SOLO agrega** funcionalidades adicionales opcionales  
        
        ### 🔧 Cómo Funciona
        
        1. **Usa las funciones ORIGINALES** como base
        2. **Combina** los resultados de múltiples fuentes
        3. **Analiza** patrones y proporciona recomendaciones
        4. **Registra** histórico para análisis de tendencias
        
        ### 📈 Beneficios Adicionales
        
        - **Diagnóstico más completo** que las verificaciones individuales
        - **Recomendaciones inteligentes** basadas en múltiples fuentes
        - **Histórico de verificaciones** para análisis de patrones
        - **Interfaz mejorada** con detalles visuales
        """)
