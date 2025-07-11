"""
Interfaz de usuario principal unificada para el sistema de facturación.
Se adapta automáticamente al modo de conexión detectado.
"""
import streamlit as st
import asyncio
from typing import Optional, List
from datetime import date
from decimal import Decimal

from data.rf_models import Factura, Cliente, DetalleFactura, TipoEmision, crear_factura_prueba
from core.rf_business_logic import procesar_factura, OperationResult, get_estadisticas, get_cola_offline
from core.rf_connection_detector import detect_mode, get_cached_mode, ConnectionMode, force_mode
from ui.rf_components import rf_components
from utils.rf_logger import log_info, log_error, log_warning
from config.rf_settings import settings

class RFMainUI:
    """Interfaz principal unificada del sistema de facturación."""
    
    def __init__(self):
        """Inicializa la interfaz principal."""
        self.reset_session_state()
    
    def reset_session_state(self):
        """Inicializa o resetea el estado de la sesión."""
        if 'current_cliente' not in st.session_state:
            st.session_state.current_cliente = None
        if 'current_detalles' not in st.session_state:
            st.session_state.current_detalles = []
        if 'numero_factura' not in st.session_state:
            st.session_state.numero_factura = 1
        if 'processing_result' not in st.session_state:
            st.session_state.processing_result = None
    
    def render_main_interface(self):
        """Renderiza la interfaz principal adaptativa."""
        # Configurar página
        st.set_page_config(
            page_title="Facturación Digital - Sistema Unificado",
            page_icon="🧾",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Título principal
        st.title("🧾 Sistema de Facturación Digital Unificado")
        
        # Detección de conexión y modo
        self._render_connection_status()
        
        # Navegación principal usando st.navigation (nuevo en v1.46.0)
        self._render_navigation()
    
    def _render_connection_status(self):
        """Renderiza el estado de conexión en tiempo real."""
        st.subheader("🌐 Estado de Conexión")
        
        cached_mode = get_cached_mode()
        if cached_mode:
            mode, details = cached_mode
            rf_components.connection_indicator(mode, details)
            
            # Selector manual de modo
            manual_mode = rf_components.selector_modo_manual()
            if manual_mode:
                force_mode(manual_mode, "Forzado manualmente por el usuario")
                st.success(f"✅ Modo cambiado a: {manual_mode.value}")
                st.rerun()
        else:
            st.info("🔍 Detectando modo de conexión...")
            
            if st.button("🔄 Detectar Conexión"):
                with st.spinner("Detectando modo..."):
                    try:
                        mode, details = asyncio.run(detect_mode(force_check=True))
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error en detección: {str(e)}")
    
    def _render_navigation(self):
        """Renderiza la navegación principal."""
        # Crear pestañas para la navegación
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📝 Nueva Factura",
            "📊 Estadísticas", 
            "📦 Cola Offline",
            "🧪 Pruebas",
            "⚙️ Configuración"
        ])
        
        with tab1:
            self._render_nueva_factura()
        
        with tab2:
            self._render_estadisticas()
        
        with tab3:
            self._render_cola_offline()
        
        with tab4:
            self._render_pruebas()
        
        with tab5:
            self._render_configuracion()
    
    def _render_nueva_factura(self):
        """Renderiza la interfaz para crear una nueva factura."""
        st.header("📝 Nueva Factura")
        
        # Mostrar modo actual
        cached_mode = get_cached_mode()
        if cached_mode:
            mode, _ = cached_mode
            rf_components.status_badge(f"Modo: {mode.value}", mode)
        
        st.markdown("---")
        
        # Paso 1: Información del cliente
        if st.session_state.current_cliente is None:
            cliente = rf_components.cliente_form("nueva_factura_cliente")
            if cliente:
                st.session_state.current_cliente = cliente
                st.rerun()
        else:
            # Mostrar cliente actual
            st.success(f"✅ Cliente: {st.session_state.current_cliente.razon_social} (NIT: {st.session_state.current_cliente.nit})")
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🔄 Cambiar Cliente"):
                    st.session_state.current_cliente = None
                    st.rerun()
        
        # Paso 2: Detalles de la factura
        if st.session_state.current_cliente:
            st.markdown("---")
            
            # Agregar detalles
            detalle = rf_components.detalle_factura_form("nueva_factura_detalle")
            if detalle:
                st.session_state.current_detalles.append(detalle)
                st.rerun()
            
            # Mostrar detalles actuales
            if st.session_state.current_detalles:
                st.subheader("📋 Detalles Agregados")
                
                # Mostrar tabla de detalles
                for i, det in enumerate(st.session_state.current_detalles):
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                    
                    with col1:
                        st.write(f"**{det.descripcion}**")
                        st.caption(f"Código: {det.codigo_producto}")
                    
                    with col2:
                        st.metric("Cantidad", f"{det.cantidad}")
                    
                    with col3:
                        st.metric("Precio Unit.", f"{det.precio_unitario:.2f} Bs")
                    
                    with col4:
                        st.metric("Subtotal", f"{det.subtotal_redondeado:.2f} Bs")
                    
                    with col5:
                        if st.button("🗑️", key=f"delete_detail_{i}", help="Eliminar detalle"):
                            st.session_state.current_detalles.pop(i)
                            st.rerun()
                    
                    st.markdown("---")
                
                # Resumen y procesamiento
                self._render_factura_resumen_y_procesamiento()
    
    def _render_factura_resumen_y_procesamiento(self):
        """Renderiza el resumen de la factura y opciones de procesamiento."""
        # Calcular totales
        subtotal = sum(d.subtotal_redondeado for d in st.session_state.current_detalles)
        
        # Descuento adicional
        descuento_adicional = st.number_input(
            "Descuento Adicional (Bs):",
            min_value=0.0,
            max_value=float(subtotal),
            value=0.0,
            step=0.01
        )
        
        total = subtotal - Decimal(str(descuento_adicional))
        
        # Mostrar resumen
        rf_components.mostrar_resumen_factura(
            st.session_state.numero_factura,
            st.session_state.current_cliente,
            st.session_state.current_detalles,
            Decimal(str(descuento_adicional))
        )
        
        # Botones de acción
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Procesar Factura", type="primary"):
                self._procesar_factura_actual(descuento_adicional)
        
        with col2:
            if st.button("💾 Guardar Borrador"):
                st.info("💾 Funcionalidad en desarrollo")
        
        with col3:
            if st.button("🗑️ Limpiar Todo"):
                self._limpiar_factura_actual()
    
    def _procesar_factura_actual(self, descuento_adicional: float):
        """Procesa la factura actual."""
        try:
            # Crear objeto Factura
            factura = Factura(
                numero_factura=st.session_state.numero_factura,
                fecha_emision=date.today(),
                cliente=st.session_state.current_cliente,
                detalles=st.session_state.current_detalles.copy(),
                descuento_adicional=Decimal(str(descuento_adicional)),
                codigo_sucursal=settings.siat['codigo_sucursal'],
                codigo_punto_venta=settings.siat['codigo_punto_venta'],
                cuis=settings.siat['cuis']
            )
            
            # Procesar la factura
            with st.spinner("⚡ Procesando factura..."):
                result, details = asyncio.run(procesar_factura(factura))
                
                # Guardar resultado en session state
                st.session_state.processing_result = {
                    "result": result,
                    "details": details,
                    "factura": factura
                }
                
                # Mostrar resultado
                self._mostrar_resultado_procesamiento(result, details, factura)
                
                # Si fue exitoso, limpiar para nueva factura
                if result in [OperationResult.SUCCESS, OperationResult.OFFLINE_QUEUED]:
                    st.session_state.numero_factura += 1
                    
        except Exception as e:
            log_error("Error procesando factura en UI", exception=e)
            st.error(f"❌ Error procesando factura: {str(e)}")
    
    def _mostrar_resultado_procesamiento(self, result: OperationResult, details: Dict, factura: Factura):
        """Muestra el resultado del procesamiento."""
        st.markdown("---")
        st.subheader("📋 Resultado del Procesamiento")
        
        # Estado principal
        if result == OperationResult.SUCCESS:
            st.success("🎉 ¡Factura procesada exitosamente!")
            rf_components.status_badge("EXITOSO", ConnectionMode.ONLINE)
        elif result == OperationResult.OFFLINE_QUEUED:
            st.warning("📦 Factura agregada a cola offline")
            rf_components.status_badge("EN COLA", ConnectionMode.OFFLINE)
        else:
            st.error("❌ Error en el procesamiento")
            rf_components.status_badge("ERROR")
        
        # Mostrar progreso detallado
        if "steps" in details:
            rf_components.progreso_procesamiento(details["steps"])
        
        # Información de la factura procesada
        with st.expander("📄 Información de la Factura"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Número:** F{factura.numero_factura:06d}")
                st.write(f"**Estado:** {factura.estado.value}")
                st.write(f"**Tipo Emisión:** {factura.tipo_emision.value}")
                if factura.cuf:
                    st.write(f"**CUF:** {factura.cuf}")
            
            with col2:
                st.write(f"**Cliente:** {factura.cliente.razon_social}")
                st.write(f"**Total:** {factura.monto_total_redondeado:.2f} Bs")
                if factura.codigo_recepcion:
                    st.write(f"**Código Recepción:** {factura.codigo_recepcion}")
        
        # Acciones post-procesamiento
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Ver Detalles JSON"):
                st.json(factura.to_dict())
        
        with col2:
            if st.button("🖨️ Imprimir"):
                st.info("🖨️ Funcionalidad de impresión en desarrollo")
        
        with col3:
            if st.button("🆕 Nueva Factura"):
                self._limpiar_factura_actual()
    
    def _limpiar_factura_actual(self):
        """Limpia la factura actual para empezar una nueva."""
        st.session_state.current_cliente = None
        st.session_state.current_detalles = []
        st.session_state.processing_result = None
        st.rerun()
    
    def _render_estadisticas(self):
        """Renderiza la pantalla de estadísticas."""
        st.header("📊 Estadísticas del Sistema")
        
        # Obtener estadísticas
        estadisticas = get_estadisticas()
        rf_components.mostrar_estadisticas(estadisticas)
        
        # Gráficos y métricas adicionales
        st.markdown("---")
        st.subheader("📈 Métricas Detalladas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Facturas del Día", "0", help="Funcionalidad en desarrollo")
        
        with col2:
            st.metric("Monto Total", "0.00 Bs", help="Funcionalidad en desarrollo")
        
        with col3:
            st.metric("Tiempo Promedio", "0s", help="Funcionalidad en desarrollo")
    
    def _render_cola_offline(self):
        """Renderiza la gestión de la cola offline."""
        st.header("📦 Gestión de Cola Offline")
        
        cola = get_cola_offline()
        
        if not cola:
            st.info("📭 No hay facturas en cola offline")
        else:
            st.warning(f"📦 {len(cola)} facturas pendientes en cola offline")
            
            # Mostrar tabla de facturas en cola
            st.subheader("📋 Facturas Pendientes")
            
            for i, factura_info in enumerate(cola):
                with st.expander(f"Factura {factura_info['numero_factura']} - {factura_info['cliente']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Número:** {factura_info['numero_factura']}")
                        st.write(f"**Cliente:** {factura_info['cliente']}")
                    
                    with col2:
                        st.write(f"**Monto:** {factura_info['monto']} Bs")
                        st.write(f"**Intentos:** {factura_info['attempts']}")
                    
                    with col3:
                        st.write(f"**Timestamp:** {factura_info['timestamp']}")
                        
                        if st.button(f"🔄 Reintentar", key=f"retry_{i}"):
                            st.info("🔄 Funcionalidad de reintento en desarrollo")
            
            # Acciones masivas
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📤 Enviar Todas", type="primary"):
                    st.info("📤 Funcionalidad de envío masivo en desarrollo")
            
            with col2:
                if st.button("🗑️ Limpiar Cola"):
                    st.warning("🗑️ Funcionalidad de limpieza en desarrollo")
    
    def _render_pruebas(self):
        """Renderiza la pantalla de pruebas y testing."""
        st.header("🧪 Pruebas y Testing")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Pruebas Rápidas")
            
            if st.button("🧪 Crear Factura de Prueba"):
                try:
                    factura_prueba = crear_factura_prueba()
                    st.success("✅ Factura de prueba creada")
                    
                    with st.expander("📄 Ver Factura de Prueba"):
                        st.json(factura_prueba.to_dict())
                        
                        if st.button("🚀 Procesar Factura de Prueba"):
                            with st.spinner("Procesando factura de prueba..."):
                                result, details = asyncio.run(procesar_factura(factura_prueba))
                                self._mostrar_resultado_procesamiento(result, details, factura_prueba)
                                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            
            if st.button("🌐 Probar Conexión"):
                with st.spinner("Probando conexión..."):
                    try:
                        mode, details = asyncio.run(detect_mode(force_check=True))
                        st.success(f"✅ Conexión: {mode.value}")
                        
                        with st.expander("🔍 Detalles de Conexión"):
                            st.json(details)
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        with col2:
            st.subheader("📊 Estado del Sistema")
            
            # Información del sistema
            st.write("**Configuración:**")
            st.write(f"- Ambiente: {'Pruebas' if settings.siat['codigo_ambiente'] == 2 else 'Producción'}")
            st.write(f"- NIT: {settings.siat['nit']}")
            st.write(f"- Sucursal: {settings.siat['codigo_sucursal']}")
            st.write(f"- Punto Venta: {settings.siat['codigo_punto_venta']}")
    
    def _render_configuracion(self):
        """Renderiza la pantalla de configuración."""
        st.header("⚙️ Configuración del Sistema")
        
        # Validación de configuración
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Validar Configuración"):
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
        
        with col2:
            if st.button("📋 Ver Configuración"):
                with st.expander("🔍 Configuración Actual"):
                    config_display = {
                        "NIT": settings.siat['nit'],
                        "Ambiente": settings.siat['codigo_ambiente'],
                        "Sucursal": settings.siat['codigo_sucursal'],
                        "Punto Venta": settings.siat['codigo_punto_venta'],
                        "CUIS": settings.siat['cuis'][:10] + "..." if settings.siat['cuis'] else "No configurado"
                    }
                    st.json(config_display)

# Instancia global de la interfaz
rf_main_ui = RFMainUI()

def render_main_interface():
    """Función principal para renderizar la interfaz."""
    rf_main_ui.render_main_interface()
