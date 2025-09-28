# facturador/main.py

import streamlit as st
import os
import sys
import logging

# Asegura que el path raíz del proyecto esté en sys.path para que Python encuentre el paquete facturador
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

# 🔧 CONFIGURACIÓN PARA REDUCIR OUTPUT VERBOSO EN TERMINAL
# Suprimir logs DEBUG de librerías externas que generan ruido
logging.getLogger('fontTools').setLevel(logging.WARNING)
logging.getLogger('fontTools.ttLib').setLevel(logging.WARNING)
logging.getLogger('fontTools.subset').setLevel(logging.WARNING)
logging.getLogger('fontTools.ttLib.ttFont').setLevel(logging.WARNING)
logging.getLogger('fontTools.subset.timer').setLevel(logging.WARNING)

# También suprimir otros posibles logs verbosos
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

from data_access import (
    obtener_cufd_vigente, 
    registrar_evento_local_normativo,
    obtener_evento_activo_actual,
    obtener_evento_por_id
)
from ui_copy import render_full_ui
from contingencia_auto import finalizar_evento_si_conectado
# NOTA: significant_events.py será deprecado en favor del nuevo sistema normativo
# from significant_events import register_significant_event, get_significant_events, close_significant_event
# NUEVO: Importar el communication_manager para diagnóstico avanzado
from communication_manager import communication_manager, EstadoComunicacion, TipoContingencia
# NOTA: El contingency_manager será simplificado en favor del sistema normativo integrado
# from contingency_manager import handle_offline_mode, get_contingency_manager
from logger_config import get_logger

# IMPORTACIONES CLAVE PARA EL SISTEMA DE IMPRESIÓN
from print_manager import start_printer_worker

# IMPORTACIONES PARA LA RECONEXIÓN
from api_clients import reset_soap_client

# -----------------------------------------------------------------
# INICIAR EL SERVICIO DE IMPRESIÓN EN SEGUNDO PLANO
start_printer_worker()
# -----------------------------------------------------------------

logger = get_logger()

def handle_reconexion():
    """
    Función callback para manejar la reconexión desde la UI.
    Esta función centraliza toda la lógica de reconexión.
    """
    with st.spinner("Intentando reconectar..."):
        # Reiniciar el cliente SOAP
        client = reset_soap_client()
        
        # Verificar el estado después del reinicio
        resultado_reconexion = communication_manager.verificar_comunicacion_completa()
        principal = resultado_reconexion["verificacion_principal"]
        conectado = principal["conectado"] if principal else False
        
        if conectado:
            st.success("✅ Reconexión exitosa - Servicios del SIN disponibles")
            logger.info("Reconexión exitosa - refresca automáticamente")
        else:
            st.error("❌ No se pudo reconectar - Servicios del SIN no disponibles")
            logger.warning("Intento de reconexión falló")
        
        st.rerun()  # Refrescar la página para mostrar el nuevo estado

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

def notificar_reconexion_si_aplica():
    """
    Verifica si la conexión y los servicios del SIN han vuelto y notifica al usuario,
    pero NO cambia automáticamente el modo de operación.
    
    Versión mejorada que utiliza el communication_manager para diagnóstico más detallado.
    """
    # Usar el nuevo communication_manager para diagnóstico avanzado
    resultado_completo = communication_manager.verificar_comunicacion_completa()
    principal = resultado_completo["verificacion_principal"]
    conectado = principal["conectado"] if principal else False
    servicios = resultado_completo.get("verificaciones_servicios", {})
    
    if conectado:
        servicios_ok = sum(1 for s in servicios.values() if s.get("conectado", False))
        total_servicios = len(servicios)
        st.info(f"🟢 ¡Conexión restablecida! ({servicios_ok}/{total_servicios} servicios disponibles). Puedes finalizar la contingencia cuando termines la factura en curso.")
    else:
        st.warning("🔴 El sistema sigue en modo contingencia. Esperando reconexión...")

def main():
    # NOTA: La gestión automática de contingencias ahora se maneja en el flujo principal
    # en lugar de usar un hilo separado para mayor simplicidad y control normativo
    
    # Paso previo: intentar finalizar evento abierto si hay conexión
    exito_cierre, detalle_cierre = finalizar_evento_si_conectado()
    if exito_cierre:
        st.success(f"✅ {detalle_cierre}")
    else:
        st.warning(f"ℹ️ {detalle_cierre}")
    st.title("🧠 Inicializando Sistema de Facturación...")

    # Paso 1: Verificar conexión utilizando el sistema mejorado
    resultado_completo = communication_manager.verificar_comunicacion_completa()
    principal = resultado_completo["verificacion_principal"]
    conectado = principal["conectado"] if principal else False
    mensaje = principal["mensaje"] if principal else "Error desconocido"
    tipo_deducido = principal.get("tipo_contingencia", "5")
    
    # Mostrar información en sidebar
    with st.sidebar:
        estado = resultado_completo["estado_general"]
        if estado == EstadoComunicacion.ONLINE.value:
            st.success("🟢 **SISTEMA ONLINE**")
        else:
            st.error("🔴 **SISTEMA OFFLINE**")
        
        st.caption(f"📊 {resultado_completo['recomendacion']}")
        
        # Mostrar detalles de servicios
        with st.expander("🔧 Detalles de Servicios"):
            servicios = resultado_completo.get("verificaciones_servicios", {})
            for nombre, detalle in servicios.items():
                if detalle.get("conectado", False):
                    st.success(f"✅ {nombre}")
                else:
                    st.error(f"❌ {nombre}")

    if conectado:
        st.success("✅ Conexión establecida con el SIN.")
        
        # Información adicional sobre el diagnóstico
        with st.expander("📊 Ver Diagnóstico Completo"):
            servicios_ok = sum(1 for s in resultado_completo.get("verificaciones_servicios", {}).values() if s.get("conectado", False))
            total_servicios = len(resultado_completo.get("verificaciones_servicios", {}))
            st.metric("Servicios Funcionando", f"{servicios_ok}/{total_servicios}")
            
            if servicios_ok < total_servicios:
                st.warning(f"⚠️ Algunos servicios presentan problemas. El sistema funcionará con limitaciones.")
        
        # Pasar el estado de conectividad y la información completa a la interfaz online
        # para evitar verificaciones redundantes
        render_full_ui(
            is_online=conectado, 
            connectivity_info=resultado_completo, 
            reconectar_callback=handle_reconexion
        )
    else:
        st.error("❌ No se pudo conectar al SIN. Se activará la contingencia.")

        # Notificar si la reconexión es posible (no cambia el modo automáticamente)
        notificar_reconexion_si_aplica()

        # Paso 2: Verificar si ya hay un evento activo usando las funciones normativas
        evento_activo = obtener_evento_activo_actual()
        
        if evento_activo:
            st.info(f"ℹ️ Ya existe un evento registrado en modo contingencia: {evento_activo.get('descripcion', 'Sin descripción')}")
            logger.info(f"Usando evento activo existente con ID: {evento_activo.get('id')}")
        else:
            # Paso 3: Registrar nuevo evento usando la función normativa
            st.warning("⚠️ Registrando evento significativo según normativa...")
            
            try:
                # Obtener CUFD vigente antes del evento según normativa
                cufd_actual = obtener_cufd_vigente()
                if not cufd_actual:
                    st.error("❌ Error: No se pudo obtener CUFD vigente para el evento.")
                    logger.error("No se pudo obtener CUFD vigente para crear evento")
                    evento_activo = None
                else:
                    # Usar la función mejorada con descripción oficial del SIN
                    evento_id = registrar_evento_local_normativo(
                        codigo_evento=tipo_deducido,  # Tipo deducido de la verificación (1-7)
                        # descripcion ya no es necesaria - se obtiene de la tabla parametrizada
                        cufd=cufd_actual  # CUFD vigente pre-corte
                    )
                    
                    if evento_id:
                        # Obtener el evento completo para pasarlo a la UI
                        evento_activo = obtener_evento_por_id(evento_id)
                        st.success(f"✅ Evento registrado normativo: {evento_activo.get('descripcion') if evento_activo else 'Evento creado'}")
                        logger.info(f"Evento de contingencia creado con ID: {evento_id} según normativa")
                    else:
                        st.error("❌ Error: No se pudo registrar el evento según normativa.")
                        logger.error("registrar_evento_local_normativo() falló")
                        evento_activo = None
                        
            except Exception as e:
                st.error(f"❌ Error al registrar evento normativo: {str(e)}")
                logger.exception("Error en registrar_evento_local_normativo()")
                evento_activo = None

        # Paso 4: Cargar la interfaz offline
        st.warning("🛠️ Activando modo offline de facturación...")

        # Si tenemos un evento, llamamos a la UI completa en modo offline
        if evento_activo:
            render_full_ui(
                is_online=False, 
                connectivity_info=resultado_completo, 
                evento_activo=evento_activo,
                reconectar_callback=handle_reconexion
            )
        else:
            st.error("❌ Error crítico: No se pudo obtener o registrar un evento de contingencia. La facturación está deshabilitada.")

if __name__ == "__main__":
    main()
