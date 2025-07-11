"""
Componentes de UI reutilizables para el sistema de facturación.
Aprovecha las nuevas funcionalidades de Streamlit 1.46.0.
"""
import streamlit as st
from typing import Optional, Dict, Any, List, Callable
from datetime import date, datetime
from decimal import Decimal

from data.rf_models import Cliente, DetalleFactura, TipoDocumento, CodigoExcepcion
from core.rf_connection_detector import ConnectionMode
from utils.rf_logger import log_info

class RFComponents:
    """Componentes reutilizables para la interfaz de usuario."""
    
    @staticmethod
    def status_badge(status: str, mode: ConnectionMode = None) -> None:
        """
        Muestra un badge de estado usando las nuevas funcionalidades de Streamlit 1.46.0.
        
        Args:
            status: Estado a mostrar
            mode: Modo de conexión (opcional)
        """
        if mode == ConnectionMode.ONLINE:
            color = "success"
            icon = "🟢"
        elif mode == ConnectionMode.OFFLINE:
            color = "warning" 
            icon = "🟡"
        else:
            color = "secondary"
            icon = "⚪"
        
        # Usar st.html para badges personalizados (nuevo en v1.46.0)
        badge_html = f"""
        <span style="
            background: {RFComponents._get_badge_color(color)}; 
            color: white; 
            padding: 4px 12px; 
            border-radius: 16px; 
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
        ">
            {icon} {status}
        </span>
        """
        st.html(badge_html)
    
    @staticmethod
    def _get_badge_color(color_type: str) -> str:
        """Obtiene el color hex para badges."""
        colors = {
            "success": "#28a745",
            "warning": "#ffc107", 
            "error": "#dc3545",
            "info": "#17a2b8",
            "secondary": "#6c757d"
        }
        return colors.get(color_type, "#6c757d")
    
    @staticmethod
    def connection_indicator(mode: ConnectionMode, details: Optional[Dict] = None) -> None:
        """
        Indicador de conexión mejorado.
        
        Args:
            mode: Modo de conexión actual
            details: Detalles adicionales de la conexión
        """
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if mode == ConnectionMode.ONLINE:
                st.success("🟢 Conexión Online")
            elif mode == ConnectionMode.OFFLINE:
                st.warning("🟡 Modo Offline")
            else:
                st.error("❌ Estado Desconocido")
        
        with col2:
            if details:
                siat_info = details.get("siat_services", {})
                if siat_info:
                    success_rate = siat_info.get("success_rate", 0) * 100
                    st.metric("Servicios SIAT", f"{success_rate:.0f}%")
                
                if "average_response_time_ms" in details:
                    st.metric("Latencia", f"{details['average_response_time_ms']:.0f} ms")
        
        with col3:
            if st.button("🔄", help="Actualizar estado de conexión"):
                st.rerun()
    
    @staticmethod
    def cliente_form(key_prefix: str = "cliente") -> Optional[Cliente]:
        """
        Formulario para captura de datos de cliente.
        
        Args:
            key_prefix: Prefijo para las keys de los widgets
            
        Returns:
            Cliente creado o None si hay errores
        """
        st.subheader("👤 Información del Cliente")
        
        with st.form(f"{key_prefix}_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Usar nuevo parámetro de icono en text_input (v1.45.0+)
                nit = st.text_input(
                    "NIT/CI:", 
                    key=f"{key_prefix}_nit",
                    help="Número de identificación del cliente"
                )
                
                tipo_doc = st.selectbox(
                    "Tipo de Documento:",
                    options=[doc.value for doc in TipoDocumento],
                    format_func=lambda x: {
                        1: "CI - Cédula de Identidad",
                        2: "CEX - Cédula de Extranjero", 
                        3: "PAS - Pasaporte",
                        4: "OD - Otro Documento",
                        5: "NIT - Número de Identificación Tributaria"
                    }.get(x, str(x)),
                    key=f"{key_prefix}_tipo_doc"
                )
            
            with col2:
                razon_social = st.text_input(
                    "Razón Social/Nombre:",
                    key=f"{key_prefix}_razon_social",
                    help="Nombre completo o razón social"
                )
                
                codigo_excepcion = st.selectbox(
                    "Código de Excepción:",
                    options=[exc.value for exc in CodigoExcepcion],
                    format_func=lambda x: {
                        0: "Sin excepción",
                        1: "NIT inválido/no verificable"
                    }.get(x, str(x)),
                    key=f"{key_prefix}_excepcion"
                )
            
            # Datos opcionales
            email = st.text_input(
                "Email (opcional):",
                key=f"{key_prefix}_email"
            )
            
            telefono = st.text_input(
                "Teléfono (opcional):",
                key=f"{key_prefix}_telefono"
            )
            
            submitted = st.form_submit_button("✅ Validar Cliente")
            
            if submitted:
                try:
                    cliente = Cliente(
                        nit=nit,
                        razon_social=razon_social,
                        tipo_documento=TipoDocumento(tipo_doc),
                        codigo_excepcion=CodigoExcepcion(codigo_excepcion),
                        email=email if email else None,
                        telefono=telefono if telefono else None
                    )
                    
                    st.success("✅ Cliente validado correctamente")
                    log_info("Cliente validado en formulario", extra_data={
                        "nit": cliente.nit,
                        "razon_social": cliente.razon_social
                    })
                    return cliente
                    
                except ValueError as e:
                    st.error(f"❌ Error en datos del cliente: {str(e)}")
                    return None
        
        return None
    
    @staticmethod
    def detalle_factura_form(key_prefix: str = "detalle") -> Optional[DetalleFactura]:
        """
        Formulario para agregar detalles de factura.
        
        Args:
            key_prefix: Prefijo para las keys de los widgets
            
        Returns:
            DetalleFactura creado o None si hay errores
        """
        st.subheader("📦 Detalle de Factura")
        
        with st.form(f"{key_prefix}_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                codigo_producto = st.text_input(
                    "Código de Producto:",
                    key=f"{key_prefix}_codigo"
                )
                
                descripcion = st.text_area(
                    "Descripción:",
                    key=f"{key_prefix}_descripcion",
                    height=100
                )
            
            with col2:
                cantidad = st.number_input(
                    "Cantidad:",
                    min_value=0.01,
                    value=1.0,
                    step=0.01,
                    key=f"{key_prefix}_cantidad"
                )
                
                precio_unitario = st.number_input(
                    "Precio Unitario (Bs):",
                    min_value=0.01,
                    value=1.0,
                    step=0.01,
                    key=f"{key_prefix}_precio"
                )
                
                descuento = st.number_input(
                    "Descuento (Bs):",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    key=f"{key_prefix}_descuento"
                )
            
            submitted = st.form_submit_button("➕ Agregar Detalle")
            
            if submitted:
                try:
                    detalle = DetalleFactura(
                        codigo_producto=codigo_producto,
                        descripcion=descripcion,
                        cantidad=Decimal(str(cantidad)),
                        precio_unitario=Decimal(str(precio_unitario)),
                        descuento=Decimal(str(descuento))
                    )
                    
                    st.success(f"✅ Detalle agregado: {detalle.descripcion} - {detalle.subtotal_redondeado} Bs")
                    return detalle
                    
                except ValueError as e:
                    st.error(f"❌ Error en detalle: {str(e)}")
                    return None
        
        return None
    
    @staticmethod
    def mostrar_resumen_factura(numero: int, cliente: Cliente, detalles: List[DetalleFactura], 
                               descuento_adicional: Decimal = Decimal('0')) -> None:
        """
        Muestra un resumen visual de la factura.
        
        Args:
            numero: Número de factura
            cliente: Cliente de la factura
            detalles: Lista de detalles
            descuento_adicional: Descuento adicional aplicado
        """
        st.subheader("📄 Resumen de Factura")
        
        # Información básica
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Número de Factura", f"F{numero:06d}")
            st.metric("Cliente", cliente.razon_social)
            st.metric("NIT", cliente.nit)
        
        with col2:
            st.metric("Fecha", date.today().strftime("%d/%m/%Y"))
            st.metric("Items", len(detalles))
        
        # Detalles en tabla mejorada (usar nuevas funcionalidades de dataframe v1.46.0)
        if detalles:
            st.subheader("📋 Detalles")
            
            # Preparar datos para la tabla
            tabla_datos = []
            for i, detalle in enumerate(detalles, 1):
                tabla_datos.append({
                    "Item": i,
                    "Código": detalle.codigo_producto,
                    "Descripción": detalle.descripcion,
                    "Cantidad": float(detalle.cantidad),
                    "Precio Unit.": f"{detalle.precio_unitario:.2f}",
                    "Descuento": f"{detalle.descuento:.2f}",
                    "Subtotal": f"{detalle.subtotal_redondeado:.2f}"
                })
            
            # Mostrar tabla con mejor configuración (v1.46.0)
            st.dataframe(
                tabla_datos,
                use_container_width=True,
                hide_index=True
            )
        
        # Cálculos totales
        if detalles:
            subtotal = sum(d.subtotal_redondeado for d in detalles)
            descuento_total = sum(d.descuento for d in detalles) + descuento_adicional
            total = subtotal - descuento_adicional
            
            # Mostrar totales
            st.subheader("💰 Totales")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Subtotal", f"{subtotal:.2f} Bs")
            with col2:
                st.metric("Descuento Total", f"{descuento_total:.2f} Bs")
            with col3:
                st.metric("**TOTAL**", f"**{total:.2f} Bs**")
    
    @staticmethod
    def progreso_procesamiento(steps: List[Dict[str, Any]]) -> None:
        """
        Muestra el progreso del procesamiento de factura.
        
        Args:
            steps: Lista de pasos del procesamiento
        """
        st.subheader("⚡ Progreso del Procesamiento")
        
        for i, step in enumerate(steps, 1):
            col1, col2, col3 = st.columns([1, 4, 1])
            
            with col1:
                if step.get("success", False):
                    st.success("✅")
                else:
                    st.error("❌")
            
            with col2:
                step_name = step.get("step", f"Paso {i}")
                st.write(f"**{step_name.replace('_', ' ').title()}**")
                
                if "error" in step:
                    st.error(f"Error: {step['error']}")
                elif "timestamp" in step:
                    timestamp = step["timestamp"]
                    st.caption(f"Completado: {timestamp}")
            
            with col3:
                if "timestamp" in step:
                    try:
                        ts = datetime.fromisoformat(step["timestamp"])
                        st.caption(ts.strftime("%H:%M:%S"))
                    except:
                        pass
    
    @staticmethod
    def selector_modo_manual() -> Optional[ConnectionMode]:
        """
        Permite seleccionar manualmente el modo de conexión.
        
        Returns:
            Modo seleccionado o None
        """
        st.subheader("🔧 Selector de Modo Manual")
        
        col1, col2 = st.columns(2)
        
        with col1:
            modo_seleccionado = st.radio(
                "Seleccionar modo:",
                options=["auto", "online", "offline"],
                format_func=lambda x: {
                    "auto": "🔄 Automático",
                    "online": "🟢 Forzar Online", 
                    "offline": "🟡 Forzar Offline"
                }.get(x, x),
                horizontal=True
            )
        
        with col2:
            if modo_seleccionado != "auto":
                if st.button("🔧 Aplicar Modo Manual"):
                    if modo_seleccionado == "online":
                        return ConnectionMode.ONLINE
                    else:
                        return ConnectionMode.OFFLINE
        
        return None
    
    @staticmethod
    def mostrar_estadisticas(estadisticas: Dict[str, Any]) -> None:
        """
        Muestra estadísticas del sistema.
        
        Args:
            estadisticas: Diccionario con estadísticas
        """
        st.subheader("📊 Estadísticas del Sistema")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            modo_actual = estadisticas.get("modo_actual", "No detectado")
            st.metric("Modo Actual", modo_actual)
        
        with col2:
            pendientes = estadisticas.get("facturas_offline_pendientes", 0)
            st.metric("Facturas Offline", pendientes)
        
        with col3:
            # Mostrar timestamp de última actualización
            timestamp = estadisticas.get("timestamp", "")
            if timestamp:
                try:
                    ts = datetime.fromisoformat(timestamp)
                    st.metric("Última Act.", ts.strftime("%H:%M:%S"))
                except:
                    pass

# Instancia global de componentes
rf_components = RFComponents()
