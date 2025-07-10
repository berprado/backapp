"""
Punto de entrada principal del sistema de facturación refactorizado.
Detecta automáticamente el modo (online/offline) y carga la UI correspondiente.
"""
import sys
import os
from pathlib import Path

# Agregar el directorio padre al path para importaciones
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from config.rf_settings import settings, validate_settings_on_startup

def main():
    """
    Función principal que orquesta todo el sistema.
    """
    # Configuración de la página
    st.set_page_config(
        page_title="Sistema de Facturación Digital Refactorizado v1.0",
        page_icon="🧾",
        layout="wide",
        initial_sidebar_state="auto"
    )
    
    try:
        # 0. Validar configuración al inicio
        if not validate_settings_on_startup():
            st.error("❌ Error crítico en la configuración del sistema")
            st.info("💡 Revisa el archivo .env y los recursos necesarios")
            st.stop()
        
        # 1. Mostrar información del sistema
        st.title("🧾 Sistema de Facturación Digital Refactorizado")
        st.subheader("v1.0 - En Desarrollo")
        
        # 2. Mostrar estado de configuración
        with st.expander("📋 Estado del Sistema", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Ambiente", "Pruebas" if settings.siat['codigo_ambiente'] == 2 else "Producción")
                st.metric("NIT", f"{settings.siat['nit']:,}")
            
            with col2:
                st.metric("Sucursal", settings.siat['codigo_sucursal'])
                st.metric("Punto Venta", settings.siat['codigo_punto_venta'])
            
            with col3:
                st.metric("CUIS", settings.siat['cuis'][:8] + "..." if settings.siat['cuis'] else "No configurado")
                
        # 3. Información sobre módulos disponibles
        st.subheader("🏗️ Estado de Desarrollo")
        
        modulos_estado = {
            "🔧 Configuración": "✅ Completado",
            "📁 Estructura de Archivos": "✅ Completado",
            "📊 Modelos de Datos": "🔄 Próximo",
            "🌐 Detector de Conexión": "🔄 Próximo",
            "💼 Lógica de Negocio": "🔄 Próximo",
            "🖥️ Interfaz de Usuario": "🔄 Próximo",
            "📡 Servicios SIAT": "🔄 Próximo",
            "📦 Gestión Offline": "🔄 Próximo"
        }
        
        for modulo, estado in modulos_estado.items():
            st.write(f"{modulo}: {estado}")
        
        # 4. Próximos pasos
        st.subheader("🚀 Próximos Pasos")
        st.markdown("""
        1. **Modelos de Datos (rf_models.py)** - Estructuras de datos con validaciones del SIN
        2. **Logger Centralizado (rf_logger.py)** - Sistema de logging unificado
        3. **Detector de Conexión (rf_connection_detector.py)** - Detección automática online/offline
        4. **Servicios de Facturación** - Implementación para modos online y offline
        5. **Interfaz de Usuario Unificada** - UI que se adapta al modo detectado
        """)
        
        # 5. Testing de configuración
        if st.button("🧪 Probar Configuración"):
            with st.spinner("Validando configuración..."):
                resultado = settings.validate_configuration()
                
                if resultado['valid']:
                    st.success("✅ Configuración válida")
                else:
                    st.error("❌ Errores en configuración:")
                    for error in resultado['errors']:
                        st.write(f"  - {error}")
                
                if resultado['warnings']:
                    st.warning("⚠️ Advertencias:")
                    for warning in resultado['warnings']:
                        st.write(f"  - {warning}")
        
        # 6. Información de desarrollo
        with st.sidebar:
            st.header("📋 Info de Desarrollo")
            st.write("**Versión:** 1.0.0")
            st.write("**Estado:** En Desarrollo")
            st.write("**Fecha:** Enero 2025")
            
            st.subheader("📁 Estructura Creada")
            estructura = [
                "📁 core/ - Lógica de negocio",
                "📁 services/ - Servicios externos",
                "📁 ui/ - Interfaz de usuario",
                "📁 data/ - Acceso a datos",
                "📁 utils/ - Utilidades",
                "📁 config/ - Configuración",
                "📁 operations/ - Operaciones específicas",
                "📁 resources/ - Recursos (XSD, certificados)",
                "📁 storage/ - Almacenamiento temporal",
                "📁 logs/ - Logs del sistema"
            ]
            
            for item in estructura:
                st.write(item)
        
    except Exception as e:
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
