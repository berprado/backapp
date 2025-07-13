# facturador/main.py

import streamlit as st
from datetime import datetime
import os
import sys
# Asegurar que estamos importando desde el directorio correcto 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Importar explícitamente desde el archivo database.py local del directorio facturador
from database import get_eventos_parametricos, get_cufd_vigente, obtener_evento_abierto, insertar_evento_local
from ui_copy import main as online_main
from contingencia_auto import finalizar_evento_si_conectado
from significant_events import register_significant_event, get_significant_events, close_significant_event
# NUEVO: Importar el communication_manager para diagnóstico avanzado
from communication_manager import communication_manager, EstadoComunicacion, TipoContingencia
from logger_config import get_logger

# Fallback a la función original por compatibilidad
#from soap_services import verificar_comunicacion

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
        online_main(is_online=conectado, connectivity_info=resultado_completo)
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

        # Mostrar información de eventos activos (centralizado)
        if evento:
            with st.form("form_factura_offline"):
                st.subheader("📋 Ingresar factura offline")
                numero_factura = st.text_input("Número de Factura")
                nombre = st.text_input("Nombre o Razón Social")
                documento = st.text_input("Número de Documento")
                monto = st.number_input("Monto Total", min_value=0.0, format="%.2f")
                submit = st.form_submit_button("💾 Guardar como XML")

                if submit:
                    # Estructura del XML
                    now = datetime.now()
                    timestamp = now.strftime("%Y%m%d_%H%M%S")
                    nombre_archivo = f"offline_{evento['id']}_{timestamp}.xml"
                    ruta_archivo = os.path.join("offline", nombre_archivo)

                    # Asegurar existencia de carpeta
                    os.makedirs("offline", exist_ok=True)

                    contenido_xml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<facturaOffline>\n<idEvento>{evento['id']}</idEvento>\n<fecha>{now.strftime('%Y-%m-%d %H:%M:%S')}</fecha>\n<numeroFactura>{numero_factura}</numeroFactura>\n<nombre>{nombre}</nombre>\n<documento>{documento}</documento>\n<monto>{monto:.2f}</monto>\n</facturaOffline>\n"""

                    with open(ruta_archivo, "w", encoding="utf-8") as f:
                        f.write(contenido_xml)

                    st.success(f"✅ Factura guardada como {nombre_archivo}")

            # Botón para finalizar contingencia y volver a modo online
            st.markdown("---")
            if st.button("🟢 Finalizar contingencia y volver a modo online"):
                now = datetime.now()
                fecha_fin = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                exito, mensaje = close_significant_event(event_id=evento['id'], end_time=fecha_fin)
                if exito:
                    st.success("✅ Contingencia finalizada correctamente. Puedes volver a facturar en línea.")
                    st.experimental_rerun()
                else:
                    st.error(f"❌ Error al finalizar contingencia: {mensaje}")
        else:
            st.error("❌ No se encontró evento significativo activo para asociar la factura.")

if __name__ == "__main__":
    main()
