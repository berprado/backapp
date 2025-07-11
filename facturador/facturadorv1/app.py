"""
Punto de entrada para la aplicación de facturación completa.
Sistema unificado que se adapta automáticamente al modo de conexión.
"""
import sys
import os
from pathlib import Path

# Agregar el directorio padre al path para importaciones
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from config.rf_settings import settings, validate_settings_on_startup
from ui.rf_main_ui import render_main_interface
from utils.rf_logger import log_info, log_error

def main():
    """
    Función principal de la aplicación de facturación completa.
    """
    try:
        # Validar configuración al inicio
        if not validate_settings_on_startup():
            log_error("Error crítico en la configuración del sistema al inicio")
            st.error("❌ Error crítico en la configuración del sistema")
            st.info("💡 Revisa el archivo .env y los recursos necesarios")
            st.stop()
        
        log_info("Sistema de facturación completo iniciado correctamente")
        
        # Renderizar la interfaz principal unificada
        render_main_interface()
        
    except Exception as e:
        log_error("Error crítico del sistema de facturación", exception=e)
        st.error(f"❌ Error crítico del sistema: {str(e)}")
        st.info("💡 Verifica los logs para más detalles")
        
        # Mostrar información técnica en desarrollo
        if settings.siat['codigo_ambiente'] == 2:  # Solo en ambiente de pruebas
            with st.expander("🔍 Información Técnica (Solo en Desarrollo)"):
                st.code(str(e))
                import traceback
                st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
