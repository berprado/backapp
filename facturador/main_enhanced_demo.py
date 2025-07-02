"""
DEMOSTRACIÓN: Cómo podría mejorarse main.py manteniendo compatibilidad total.

Este archivo es SOLO una demostración de cómo se podría implementar una versión
mejorada de main.py usando el nuevo communication_manager, SIN modificar el
archivo main.py actual.

IMPORTANTE: Este archivo NO reemplaza main.py. Es solo una demostración opcional.
"""

import streamlit as st
from datetime import datetime
import os
import sys

# Asegurar que estamos importando desde el directorio correcto 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports del sistema (IGUALES que en main.py)
from database import get_eventos_parametricos, get_cufd_vigente, obtener_evento_abierto, insertar_evento_local
from ui_copy import main as online_main
from contingencia_auto import finalizar_evento_si_conectado

# NUEVO: Import opcional del servicio mejorado
try:
    from communication_manager import communication_manager, EstadoComunicacion, TipoContingencia
    ENHANCED_SERVICE_AVAILABLE = True
except ImportError:
    # Fallback a la función original si no está disponible
    from soap_services import verificar_comunicacion
    ENHANCED_SERVICE_AVAILABLE = False

from logger_config import get_logger

logger = get_logger()

st.set_page_config(
    page_title="BACKINVOICE",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# Sistema de facturación con contingencia automática"
    }
)

def main_enhanced():
    """
    Versión MEJORADA de main() que usa el nuevo servicio cuando está disponible,
    pero mantiene TOTAL compatibilidad con la implementación original.
    """
    st.title("🧠 Sistema de Facturación BACKINVOICE")
    
    # PASO 1: Intentar finalizar eventos pendientes (IGUAL que original)
    if _intentar_finalizar_eventos_pendientes():
        st.success("✅ Se finalizó el evento pendiente y se procesaron las facturas.")
    
    # PASO 2: Verificar comunicación (MEJORADO si está disponible, ORIGINAL si no)
    if ENHANCED_SERVICE_AVAILABLE:
        _verificar_comunicacion_mejorada()
    else:
        _verificar_comunicacion_original()

def _intentar_finalizar_eventos_pendientes() -> bool:
    """
    Intenta finalizar eventos pendientes - IGUAL que en main.py original.
    """
    try:
        resultado = finalizar_evento_si_conectado()
        logger.info(f"Resultado finalización eventos: {resultado}")
        return bool(resultado)
    except Exception as e:
        logger.error(f"Error al finalizar eventos pendientes: {e}")
        st.warning("⚠️ No se pudieron procesar eventos pendientes.")
        return False

def _verificar_comunicacion_original():
    """
    Verificación ORIGINAL usando soap_services.verificar_comunicacion()
    EXACTAMENTE igual que en main.py original.
    """
    st.info("🔄 Usando verificación estándar...")
    
    # Código IDÉNTICO al main.py original
    mensaje, conectado, tipo_deducido = verificar_comunicacion()

    if conectado:
        st.success("✅ Conexión establecida con el SIN.")
        online_main()
    else:
        st.error("❌ No se pudo conectar al SIN. Se activará la contingencia.")
        
        # Paso 2: Verificar si ya hay un evento abierto
        evento_existente = obtener_evento_abierto()
        
        if evento_existente:
            st.info("[✅] Ya existe un evento abierto. Continúa en modo offline.")
        else:
            st.warning("[⚠️] No hay evento abierto. Creando evento de contingencia...")
            
            # Obtener eventos paramétricos
            eventos = get_eventos_parametricos()
            if eventos:
                # Selecciona el evento tipo 1 (Corte de Internet) por defecto (comparando como string)
                evento_tipo_1 = next((e for e in eventos if str(e["codigoClasificador"]).strip() == "1"), None)
                if evento_tipo_1:
                    cufd = get_cufd_vigente()
                    if cufd:
                        fecha_inicio = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        insertar_evento_local(
                            codigo_evento=evento_tipo_1["codigoClasificador"],
                            descripcion=evento_tipo_1["descripcion"],
                            fecha_inicio=fecha_inicio,
                            cufd=cufd
                        )
                        st.success("✅ Evento de contingencia registrado correctamente.")
                    else:
                        st.error("No se encontró un CUFD vigente para registrar el evento.")
                else:
                    st.error("No se encontró el evento tipo 1 en la parametrización.")

def _verificar_comunicacion_mejorada():
    """
    Verificación MEJORADA usando el nuevo communication_manager.
    MANTIENE toda la funcionalidad original pero con mejoras adicionales.
    """
    st.info("🔄 Usando verificación mejorada con diagnóstico completo...")
    
    with st.spinner("Verificando comunicación con el SIN..."):
        # Usar el servicio mejorado que internamente usa las funciones originales
        resultado_completo = communication_manager.verificar_comunicacion_completa()
    
    # Extraer información para compatibilidad con main.py original
    principal = resultado_completo["verificacion_principal"]
    conectado = principal["conectado"] if principal else False
    mensaje = principal["mensaje"] if principal else "Error desconocido"
    
    # Mostrar información adicional en sidebar
    with st.sidebar:
        estado = resultado_completo["estado_general"]
        if estado == EstadoComunicacion.ONLINE.value:
            st.success("🟢 **SISTEMA ONLINE**")
        else:
            st.error("🔴 **SISTEMA OFFLINE**")
        
        st.caption(f"📊 {resultado_completo['recomendacion']}")
        
        # Mostrar detalles de servicios
        with st.expander("🔧 Detalles de Servicios"):
            servicios = resultado_completo["verificaciones_servicios"]
            for nombre, detalle in servicios.items():
                if detalle["conectado"]:
                    st.success(f"✅ {nombre}")
                else:
                    st.error(f"❌ {nombre}")
    
    # MISMA lógica que main.py original para compatibilidad
    if conectado:
        st.success("✅ Conexión establecida con el SIN.")
        
        # Información adicional sobre el diagnóstico
        with st.expander("📊 Ver Diagnóstico Completo"):
            servicios_ok = sum(1 for s in resultado_completo["verificaciones_servicios"].values() if s["conectado"])
            total_servicios = len(resultado_completo["verificaciones_servicios"])
            st.metric("Servicios Funcionando", f"{servicios_ok}/{total_servicios}")
            
            if servicios_ok < total_servicios:
                st.warning(f"⚠️ Algunos servicios presentan problemas. El sistema funcionará con limitaciones.")
        
        online_main()
    else:
        st.error("❌ No se pudo conectar al SIN. Se activará la contingencia.")
        
        # Mostrar tipo de contingencia recomendado
        tipo_contingencia = principal.get("tipo_contingencia") if principal else None
        if tipo_contingencia:
            try:
                nombre_contingencia = TipoContingencia(tipo_contingencia).name
                st.info(f"🔧 **Tipo de contingencia recomendado**: {nombre_contingencia}")
            except:
                st.info(f"🔧 **Código de contingencia**: {tipo_contingencia}")
        
        # MISMA lógica que main.py original
        evento_existente = obtener_evento_abierto()
        
        if evento_existente:
            st.info("[✅] Ya existe un evento abierto. Continúa en modo offline.")
        else:
            st.warning("[⚠️] No hay evento abierto. Creando evento de contingencia...")
            
            # Obtener eventos paramétricos
            eventos = get_eventos_parametricos()
            if eventos:
                # Selecciona el evento tipo 1 (Corte de Internet) por defecto (comparando como string)
                evento_tipo_1 = next((e for e in eventos if str(e["codigoClasificador"]).strip() == "1"), None)
                if evento_tipo_1:
                    cufd = get_cufd_vigente()
                    if cufd:
                        fecha_inicio = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        insertar_evento_local(
                            codigo_evento=evento_tipo_1["codigoClasificador"],
                            descripcion=evento_tipo_1["descripcion"],
                            fecha_inicio=fecha_inicio,
                            cufd=cufd
                        )
                        st.success("✅ Evento de contingencia registrado correctamente.")
                    else:
                        st.error("No se encontró un CUFD vigente para registrar el evento.")
                else:
                    st.error("No se encontró el evento tipo 1 en la parametrización.")

def mostrar_comparacion_servicios():
    """
    Función de demostración que muestra las diferencias entre 
    el servicio original y el mejorado.
    """
    st.header("🔬 Comparación de Servicios de Comunicación")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📟 Servicio Original")
        st.code("""
# soap_services.py
mensaje, conectado, tipo = verificar_comunicacion()

# Características:
✅ Verificación básica
✅ Timeout 6 segundos  
✅ Clasificación de errores
❌ Solo un endpoint
❌ Sin histórico
❌ Sin análisis combinado
        """)
        
        if st.button("🧪 Probar Verificación Original"):
            try:
                from soap_services import verificar_comunicacion
                with st.spinner("Ejecutando verificación original..."):
                    resultado = verificar_comunicacion()
                st.json({
                    "mensaje": resultado[0],
                    "conectado": resultado[1], 
                    "tipo": resultado[2]
                })
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        st.subheader("🚀 Servicio Mejorado")
        st.code("""
# communication_manager.py  
resultado = manager.verificar_comunicacion_completa()

# Características:
✅ Verificación múltiple
✅ Todos los endpoints
✅ Análisis combinado
✅ Histórico de verificaciones
✅ Recomendaciones inteligentes
✅ Compatible con original
        """)
        
        if st.button("🧪 Probar Verificación Mejorada") and ENHANCED_SERVICE_AVAILABLE:
            with st.spinner("Ejecutando verificación mejorada..."):
                resultado = communication_manager.verificar_comunicacion_completa()
            st.json(resultado)

if __name__ == "__main__":
    # Mostrar selector de modo
    st.sidebar.header("🔧 Modo de Demostración")
    modo = st.sidebar.selectbox(
        "Seleccionar modo:",
        ["🚀 Mejorado (si disponible)", "📟 Original", "🔬 Comparación"]
    )
    
    if modo == "🔬 Comparación":
        mostrar_comparacion_servicios()
    elif modo == "📟 Original":
        st.info("🔄 Forzando uso del servicio original...")
        _verificar_comunicacion_original()
    else:
        main_enhanced()
