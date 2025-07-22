# facturador/main.py

import streamlit as st
from datetime import datetime
import os
import sys
# Asegurar que estamos importando desde el directorio correcto 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Importar explícitamente desde el archivo database.py local del directorio facturador
from database import get_eventos_parametricos, get_cufd_vigente, obtener_evento_abierto, insertar_evento_local
from ui_copy import render_full_ui
from contingencia_auto import finalizar_evento_si_conectado
from significant_events import register_significant_event, get_significant_events, close_significant_event
# NUEVO: Importar el communication_manager para diagnóstico avanzado
from communication_manager import communication_manager, EstadoComunicacion, TipoContingencia
from logger_config import get_logger

# IMPORTACIONES CLAVE PARA EL SISTEMA DE IMPRESIÓN
from print_manager import start_printer_worker

# IMPORTACIONES PARA LA RECONEXIÓN
from api_clients import reset_soap_client

# -----------------------------------------------------------------
# INICIAR EL SERVICIO DE IMPRESIÓN EN SEGUNDO PLANO
start_printer_worker()
# -----------------------------------------------------------------

# Fallback a la función original por compatibilidad
#from soap_services import verificar_comunicacion

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

def registrar_evento_significativo_automatico(tipo_evento, descripcion, cufd):
    """
    Registra un evento significativo automáticamente usando la función centralizada.
    """
    now = datetime.now()
    fecha_inicio = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    fecha_fin = None  # El evento se cierra manualmente por el usuario

    exito, mensaje = register_significant_event(
        event_code=int(tipo_evento),
        description=descripcion,
        start_time=fecha_inicio,
        end_time=fecha_fin,
        cufd=cufd
    )
    return exito, mensaje

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
    # Paso previo: intentar finalizar evento abierto si hay conexión
    resultado = finalizar_evento_si_conectado()
    if resultado:
        st.success("✅ Se finalizó el evento pendiente y se comprimieron las facturas (si existían).")
    else:
        st.warning("ℹ️ No se pudo finalizar el evento o el sistema aún está sin conexión.")
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

        # Paso 2: Verificar si ya hay un evento abierto
        eventos_activos = get_significant_events(limit=5, only_open=True)
        if eventos_activos:
            st.info("ℹ️ Ya existe un evento registrado en modo contingencia.")
            evento = eventos_activos[0]
        else:
            # Paso 3: Registrar evento automáticamente con información mejorada
            st.warning("⚠️ Registrando evento significativo automáticamente...")

            # Obtener CUFD vigente
            cufd = get_cufd_vigente()
            if not cufd:
                st.error("❌ No se pudo obtener CUFD vigente para registrar el evento.")
                evento = None
            else:
                eventos_parametricos = get_eventos_parametricos()
                tipos = {e["codigoClasificador"]: e["descripcion"] for e in eventos_parametricos}
                
                # Usar tipo_contingencia del communication_manager si está disponible
                tipo_evento = tipo_deducido if tipo_deducido in tipos else "5"
                
                # Obtener información más detallada del communication_manager
                try:
                    nombre_contingencia = TipoContingencia(tipo_evento).name
                    detalle_adicional = resultado_completo.get("recomendacion", "")
                    descripcion = f"{tipos.get(tipo_evento, 'Evento automático')}: {nombre_contingencia} - {detalle_adicional}"
                except:
                    descripcion = tipos.get(tipo_evento, "Evento no identificado automáticamente")

                exito, mensaje = registrar_evento_significativo_automatico(tipo_evento, descripcion, cufd)
                if exito:
                    st.success(f"✅ Evento registrado: {descripcion}")
                    eventos_activos = get_significant_events(limit=5, only_open=True)
                    evento = eventos_activos[0] if eventos_activos else None
                else:
                    st.error(f"❌ Error al registrar evento: {mensaje}")
                    evento = None

        # Paso 4: Cargar la interfaz offline
        st.warning("🛠️ Activando modo offline de facturación...")

        # Si tenemos un evento, llamamos a la UI completa en modo offline
        if evento:
            render_full_ui(
                is_online=False, 
                connectivity_info=resultado_completo, 
                evento_activo=evento,
                reconectar_callback=handle_reconexion
            )
        else:
            st.error("❌ Error crítico: No se pudo obtener o registrar un evento de contingencia. La facturación está deshabilitada.")

if __name__ == "__main__":
    main()
