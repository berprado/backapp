"""
Punto de entrada principal integrado para el sistema de facturación v1.0.
Combina todas las funcionalidades implementadas.
"""
import sys
import os
from pathlib import Path

# Agregar el directorio padre al path para importaciones
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import asyncio
from datetime import datetime

from config.rf_settings import settings, validate_settings_on_startup
from utils.rf_logger import log_info, log_error, log_warning
from core.rf_connection_detector import detect_mode, get_cached_mode, ConnectionMode
from core.rf_business_logic import rf_business, OperationResult
from data.rf_models import crear_factura_prueba
from ui.rf_components import RFComponents

def configure_page():
    """Configura la página principal."""
    st.set_page_config(
        page_title="Sistema de Facturación Digital v1.0",
        page_icon="🧾",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def main():
    """Función principal integrada."""
    configure_page()
    
    try:
        # 0. Validar configuración al inicio
        if not validate_settings_on_startup():
            log_error("Error crítico en la configuración del sistema al inicio")
            st.error("❌ Error crítico en la configuración del sistema")
            st.info("💡 Revisa el archivo .env y los recursos necesarios")
            st.stop()
        
        log_info("Sistema integrado iniciado correctamente")
        
        # 1. Header principal con información del sistema
        render_header()
        
        # 2. Sidebar con estado y navegación
        render_sidebar()
        
        # 3. Contenido principal según la página seleccionada
        page = st.session_state.get('current_page', 'facturacion')
        
        if page == 'facturacion':
            render_facturacion_page()
        elif page == 'dashboard':
            render_dashboard_page()
        elif page == 'configuracion':
            render_configuracion_page()
        elif page == 'testing':
            render_testing_page()
        
    except Exception as e:
        log_error("Error crítico del sistema integrado", exception=e)
        st.error(f"❌ Error crítico del sistema: {str(e)}")
        
        # Mostrar información técnica en desarrollo
        if settings.siat['codigo_ambiente'] == 2:
            with st.expander("🔍 Información Técnica (Solo en Desarrollo)"):
                st.code(str(e))
                import traceback
                st.code(traceback.format_exc())

def render_header():
    """Renderiza el header principal."""
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        st.title("🧾 Sistema de Facturación Digital v1.0")
        st.caption("Sistema modular con Streamlit 1.46.0")
    
    with col2:
        # Mostrar modo de conexión actual
        cached_mode = get_cached_mode()
        if cached_mode:
            mode, details = cached_mode
            mode_icon = "🟢" if mode == ConnectionMode.ONLINE else "🟡"
            mode_color = "green" if mode == ConnectionMode.ONLINE else "orange"
            
            st.markdown(f"### {mode_icon} Modo: {mode.value}")
            
            # Botón para cambiar modo manualmente
            if st.button("🔄 Detectar Conexión"):
                with st.spinner("Detectando conexión..."):
                    try:
                        new_mode, new_details = asyncio.run(detect_mode(force_check=True))
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.warning("🔍 Detectando modo...")
    
    with col3:
        # Estado operativo
        st.html('<div style="text-align: center; background: #28a745; color: white; padding: 8px; border-radius: 8px; margin-top: 20px;"><strong>✅ OPERATIVO</strong></div>')

def render_sidebar():
    """Renderiza el sidebar con navegación y estado."""
    with st.sidebar:
        st.header("🧭 Navegación")
        
        # Menú de navegación usando st.radio
        page = st.radio(
            "Seleccionar página:",
            options=['facturacion', 'dashboard', 'configuracion', 'testing'],
            format_func=lambda x: {
                'facturacion': '📝 Nueva Factura',
                'dashboard': '📊 Dashboard',
                'configuracion': '⚙️ Configuración',
                'testing': '🧪 Testing'
            }[x],
            key='current_page'
        )
        
        st.divider()
        
        # Estado de conexión
        try:
            # Verificar conexión rápidamente usando la función existente
            mode = get_cached_mode()  # Usar el cache existente
            
            # Si no hay cache, verificar
            if mode is None:
                mode = asyncio.run(detect_mode())
            
            details = {
                'mode': mode,
                'message': f"Modo actual: {mode.value}"
            }
            
            RFComponents.connection_indicator(mode, details)
        except Exception as e:
            st.warning(f"No se pudo verificar el estado de conexión: {str(e)}")
            # Mostrar indicador offline por defecto
            RFComponents.connection_indicator(ConnectionMode.OFFLINE)
        
        st.divider()
        
        # Información del sistema
        st.subheader("📋 Información")
        st.write("**Versión:** 1.0.0")
        st.write("**Streamlit:** 1.46.0")
        st.write("**Estado:** Operativo")
        
        # Información del emisor
        st.subheader("🏢 Emisor")
        st.write(f"**NIT:** {settings.siat['nit']:,}")
        st.write(f"**Sucursal:** {settings.siat['codigo_sucursal']}")
        st.write(f"**Punto Venta:** {settings.siat['codigo_punto_venta']}")
        
        # Ambiente
        ambiente = "🟢 Producción" if settings.siat['codigo_ambiente'] == 1 else "🧪 Pruebas"
        st.write(f"**Ambiente:** {ambiente}")

def render_facturacion_page():
    """Renderiza la página principal de facturación."""
    st.header("📝 Nueva Factura")
    
    # 1. Formulario del cliente
    cliente_data = RFComponents.cliente_form()
    
    if cliente_data:
        st.divider()
        
        # 2. Formulario de detalles
        detalles = RFComponents.detalle_factura_form()
        
        if detalles:
            st.divider()
            
            # 3. Vista previa
            RFComponents.mostrar_resumen_factura(1, cliente_data, detalles)
            
            st.divider()
            
            # 4. Botones de acción
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                if st.button("💾 Crear y Procesar Factura", type="primary", use_container_width=True):
                    process_new_invoice(cliente_data, detalles)
            
            with col2:
                if st.button("🗑️ Limpiar Formulario", use_container_width=True):
                    # Los datos del formulario se limpiarán en la próxima recarga
                    st.rerun()
            
            with col3:
                if st.button("👁️ Solo Vista Previa", use_container_width=True):
                    st.info("Vista previa mostrada arriba ☝️")

def process_new_invoice(cliente_data, detalles):
    """Procesa una nueva factura."""
    with st.spinner("Procesando factura..."):
        try:
            # 1. Crear factura
            result, factura, message = asyncio.run(
                rf_business.crear_factura(cliente_data, detalles)
            )
            
            if result == OperationResult.SUCCESS and factura:
                # 2. Procesar factura
                process_result, process_message, process_details = asyncio.run(
                    rf_business.procesar_factura(factura)
                )
                
                # 3. Mostrar resultado
                steps = [
                    {
                        "step": "Procesamiento de Factura",
                        "status": "completed" if process_result == OperationResult.SUCCESS else "error",
                        "message": process_message,
                        "details": process_details
                    }
                ]
                RFComponents.progreso_procesamiento(steps)
                
                if process_result == OperationResult.SUCCESS:
                    # Limpiar formulario después del éxito - se hace con st.rerun()
                    pass
                    
                    # Mostrar datos de la factura procesada
                    with st.expander("📄 Factura Procesada - Detalles Completos"):
                        st.json(factura.to_dict())
                    
                    # Botón para crear otra factura
                    if st.button("📝 Crear Nueva Factura"):
                        st.rerun()
            else:
                st.error(f"❌ Error al crear factura: {message}")
                
        except Exception as e:
            log_error("Error al procesar nueva factura", exception=e)
            st.error(f"❌ Error inesperado: {str(e)}")

def render_dashboard_page():
    """Renderiza la página del dashboard."""
    st.header("📊 Dashboard de Facturación")
    
    # Estadísticas principales
    estadisticas_ejemplo = {
        "facturas_emitidas": 0,
        "facturas_online": 0,
        "facturas_offline": 0,
        "total_facturado": "0.00",
        "ultimo_procesamiento": "N/A"
    }
    RFComponents.mostrar_estadisticas(estadisticas_ejemplo)
    
    st.divider()
    
    # Información adicional
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔄 Acciones Rápidas")
        
        if st.button("🌐 Verificar Conexión SIAT", use_container_width=True):
            with st.spinner("Verificando conexión..."):
                try:
                    mode, details = asyncio.run(detect_mode(force_check=True))
                    
                    mode_icon = "🟢" if mode == ConnectionMode.ONLINE else "🟡"
                    st.success(f"{mode_icon} Estado: {mode.value}")
                    
                    with st.expander("🔍 Detalles de Conectividad"):
                        st.json(details)
                        
                except Exception as e:
                    st.error(f"Error en verificación: {str(e)}")
        
        if st.button("🧪 Crear Factura de Prueba", use_container_width=True):
            try:
                factura_prueba = crear_factura_prueba()
                st.success("✅ Factura de prueba creada")
                
                with st.expander("📄 Ver Factura de Prueba"):
                    st.json(factura_prueba.to_dict())
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        st.subheader("📈 Estado del Sistema")
        
        # Métricas del sistema
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.metric("Uptime", "100%", delta="Estable")
            st.metric("Logs Hoy", "45", delta="12")
        
        with col_m2:
            st.metric("Memoria", "156 MB", delta="-5 MB")
            st.metric("CPU", "12%", delta="Normal")

def render_configuracion_page():
    """Renderiza la página de configuración."""
    st.header("⚙️ Configuración del Sistema")
    
    # Configuración actual
    with st.expander("📋 Configuración Actual", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🏢 Emisor")
            st.write(f"**NIT:** {settings.siat['nit']:,}")
            st.write(f"**Sucursal:** {settings.siat['codigo_sucursal']}")
            st.write(f"**Punto Venta:** {settings.siat['codigo_punto_venta']}")
        
        with col2:
            st.subheader("🌐 SIAT")
            st.write(f"**CUIS:** {settings.siat['cuis'][:12]}...")
            ambiente = "Producción" if settings.siat['codigo_ambiente'] == 1 else "Pruebas"
            st.write(f"**Ambiente:** {ambiente}")
        
        with col3:
            st.subheader("📁 Archivos")
            cert_status = "✅" if settings.paths['certificate_file'].exists() else "❌"
            st.write(f"**Certificado:** {cert_status}")
            key_status = "✅" if settings.paths['private_key_file'].exists() else "❌"
            st.write(f"**Clave Privada:** {key_status}")
    
    st.divider()
    
    # Acciones de configuración
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Validaciones")
        
        if st.button("🧪 Validar Configuración Completa", use_container_width=True):
            with st.spinner("Validando configuración..."):
                resultado = settings.validate_configuration()
                
                if resultado['valid']:
                    st.success("✅ Configuración válida")
                else:
                    st.error("❌ Errores encontrados:")
                    for error in resultado['errors']:
                        st.write(f"  • {error}")
                
                if resultado['warnings']:
                    st.warning("⚠️ Advertencias:")
                    for warning in resultado['warnings']:
                        st.write(f"  • {warning}")
    
    with col2:
        st.subheader("🔄 Modo de Conexión")
        
        # Forzar modo manualmente
        modo_forzado = st.selectbox(
            "Forzar modo de conexión:",
            options=[None, ConnectionMode.ONLINE, ConnectionMode.OFFLINE],
            format_func=lambda x: "Automático" if x is None else x.value,
            help="Fuerza un modo específico ignorando la detección automática"
        )
        
        if st.button("💾 Aplicar Modo Forzado", use_container_width=True):
            if modo_forzado:
                from core.rf_connection_detector import force_mode
                force_mode(modo_forzado, "Forzado por usuario desde configuración")
                st.success(f"✅ Modo forzado a: {modo_forzado.value}")
                st.rerun()
            else:
                st.info("ℹ️ Selecciona un modo para forzar")

def render_testing_page():
    """Renderiza la página de testing y diagnósticos."""
    st.header("🧪 Testing y Diagnósticos")
    
    # Tests básicos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Tests Básicos")
        
        if st.button("🧪 Probar Modelos de Datos", use_container_width=True):
            with st.spinner("Probando modelos..."):
                try:
                    factura_prueba = crear_factura_prueba()
                    st.success("✅ Modelos funcionando correctamente")
                    
                    with st.expander("📄 Datos de Prueba"):
                        st.json(factura_prueba.to_dict())
                        
                except Exception as e:
                    st.error(f"❌ Error en modelos: {str(e)}")
        
        if st.button("📝 Probar Logger", use_container_width=True):
            log_info("Test de logging desde la interfaz de testing")
            log_warning("Test de warning desde la interfaz")
            log_error("Test de error desde la interfaz")
            st.success("✅ Logs generados. Revisa los archivos de log.")
    
    with col2:
        st.subheader("🌐 Tests de Conectividad")
        
        if st.button("🌐 Test Completo de Conexión", use_container_width=True):
            with st.spinner("Ejecutando test completo..."):
                try:
                    mode, details = asyncio.run(detect_mode(force_check=True))
                    
                    st.success(f"✅ Test completado")
                    
                    # Mostrar resultados detallados
                    col_r1, col_r2 = st.columns(2)
                    
                    with col_r1:
                        mode_icon = "🟢" if mode == ConnectionMode.ONLINE else "🟡"
                        st.metric("Modo Detectado", f"{mode_icon} {mode.value}")
                        
                        if details.get("average_response_time_ms"):
                            st.metric("Tiempo Promedio", f"{details['average_response_time_ms']:.0f} ms")
                    
                    with col_r2:
                        siat_info = details.get("siat_services", {})
                        if siat_info:
                            st.metric("Servicios SIAT", f"{siat_info.get('connected', 0)}/{siat_info.get('total', 0)}")
                            st.metric("Tasa de Éxito", f"{siat_info.get('success_rate', 0)*100:.1f}%")
                    
                    with st.expander("🔍 Detalles Técnicos Completos"):
                        st.json(details)
                        
                except Exception as e:
                    st.error(f"❌ Error en test: {str(e)}")

if __name__ == "__main__":
    main()
