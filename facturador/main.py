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

NON_OPERATIONAL_EVENT_CODES = {"5", "6", "7"}

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
        
        # ✅ CORRECCIÓN: Marcar flag para forzar verificación en el próximo render
        st.session_state['_force_comm_check'] = True
        
        # Verificar el estado después del reinicio con verificación forzada
        resultado_reconexion = communication_manager.verificar_comunicacion_completa(force_check=True)
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

    # ⚠️ CAMBIO CRÍTICO: Solo verificar si se fuerza manualmente o si el caché expiró
    # El caché de 30 segundos ya está implementado en communication_manager
    force_check = st.session_state.get('_force_comm_check', False)
    if force_check:
        st.session_state['_force_comm_check'] = False  # Resetear flag
        logger.info("Verificación de comunicación forzada por el usuario")
    
    # Paso 1: Verificar conexión utilizando el sistema mejorado con caché
    resultado_completo = communication_manager.verificar_comunicacion_completa(force_check=force_check)
    principal = resultado_completo["verificacion_principal"]
    conectado = principal["conectado"] if principal else False
    mensaje = principal["mensaje"] if principal else "Error desconocido"
    tipo_deducido = principal.get("tipo_contingencia") if principal else None

    st.session_state.setdefault("evento_cafc", {})
    evento_activo = obtener_evento_activo_actual()

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

        if evento_activo and str(evento_activo.get("codigo_evento")) in NON_OPERATIONAL_EVENT_CODES:
            st.divider()
            st.subheader("CAFC para eventos no operativos")
            evento_id = evento_activo.get("id")
            cafc_actual = st.session_state["evento_cafc"].get(evento_id, "")
            nuevo_cafc = st.text_input("CAFC vigente para facturas manuales", value=cafc_actual, key=f"cafc_sidebar_{evento_id}")
            st.session_state["evento_cafc"][evento_id] = nuevo_cafc.strip()

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
            evento_activo=evento_activo,
            reconectar_callback=handle_reconexion
        )
    else:
        st.error("SIN no disponible. Se activara la contingencia.")

        # Notificar si la reconexion es posible (no cambia el modo automaticamente)
        notificar_reconexion_si_aplica()

        automatic_codes = {"1", "2"}
        evento_activo = obtener_evento_activo_actual()

        if evento_activo:
            st.info(f"Evento activo detectado: {evento_activo.get('descripcion', 'Sin descripcion')}")
            logger.info(f"Usando evento activo existente con ID: {evento_activo.get('id')}")
        elif tipo_deducido in automatic_codes:
            st.warning("Registrando evento significativo segun diagnostico automatico...")
            try:
                cufd_actual = obtener_cufd_vigente()
                if not cufd_actual:
                    st.error("No se pudo obtener CUFD vigente para el evento.")
                    logger.error("No se pudo obtener CUFD vigente para crear evento")
                else:
                    evento_id = registrar_evento_local_normativo(
                        codigo_evento=tipo_deducido,
                        cufd=cufd_actual
                    )
                    if evento_id:
                        evento_activo = obtener_evento_por_id(evento_id)
                        st.success(f"Evento registrado automaticamente: {evento_activo.get('descripcion') if evento_activo else 'Evento creado'}")
                        logger.info(f"Evento de contingencia creado automaticamente (codigo {tipo_deducido}) con ID: {evento_id}")
                        st.rerun()
                    else:
                        st.error("No se pudo registrar el evento automaticamente.")
                        logger.error("registrar_evento_local_normativo() fallo")
            except Exception as exc:
                st.error(f"Error al registrar evento automatico: {exc}")
                logger.exception("Error en registrar_evento_local_normativo()")
        else:
            st.warning("No existe evento activo y el diagnostico no permite registro automatico. Registra un evento manual (codigos 3-7) desde la pantalla de Eventos Significativos.")
            logger.warning("Sin evento activo y tipo de contingencia manual. Se requiere registro manual.")

        # Paso 4: Cargar la interfaz offline solo si existe evento
        st.warning("Activando modo offline de facturacion...")

        if evento_activo:
            render_full_ui(
                is_online=False,
                connectivity_info=resultado_completo,
                evento_activo=evento_activo,
                reconectar_callback=handle_reconexion
            )
        else:
            st.error("No se detecto evento de contingencia activo. La facturacion permanece deshabilitada hasta registrarlo.")
if __name__ == "__main__":
    main()
