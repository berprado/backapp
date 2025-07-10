"""
Punto de entrada principal del sistema de facturación refactorizado.
Detecta automáticamente el modo (online/offline) y carga la UI correspondiente.
Actualizado para Streamlit 1.46.0 con nuevas funcionalidades.
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
    Actualizada para Streamlit 1.46.0 con nuevas funcionalidades.
    """
    # Configuración de la página con múltiples llamadas permitidas en v1.46.0
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
        
        # 1. Mostrar información del sistema con detección de tema
        st.title("🧾 Sistema de Facturación Digital Refactorizado")
        
        # Nuevo: Detectar tema actual (funcionalidad de v1.46.0)
        try:
            current_theme = st.context.theme if hasattr(st.context, 'theme') else "unknown"
            tema_info = f"🎨 Tema: {current_theme.title()}" if current_theme != "unknown" else ""
        except:
            tema_info = ""
        
        st.subheader(f"v1.0 - Streamlit 1.46.0 {tema_info}")
        
        # Nuevo: Badge para mostrar el estado (funcionalidad nueva)
        col_status, col_version = st.columns([3, 1])
        with col_status:
            st.markdown("### Estado del Sistema")
        with col_version:
            # Usando st.html con mejor soporte para estilos inline
            st.html('<span style="background: #28a745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">✅ OPERATIVO</span>')
        
        # 2. Mostrar estado de configuración mejorado
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
                
                # Nuevo: Información de contexto avanzado (v1.45.0+)
                try:
                    if hasattr(st.context, 'timezone'):
                        st.metric("Zona Horaria", st.context.timezone or "No detectada")
                except:
                    pass
                
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
            st.write("**Streamlit:** 1.46.0")
            st.write("**Estado:** En Desarrollo")
            st.write("**Fecha:** Enero 2025")
            
            # Nuevo: Información de contexto avanzado si está disponible
            try:
                if hasattr(st.context, 'ip_address') and st.context.ip_address:
                    st.write(f"**IP:** {st.context.ip_address}")
                if hasattr(st.context, 'locale') and st.context.locale:
                    st.write(f"**Locale:** {st.context.locale}")
            except:
                pass
            
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
