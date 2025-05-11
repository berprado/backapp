# facturador/main.py

import streamlit as st
from datetime import datetime
from soap_services import verificar_comunicacion
from database import get_eventos_parametricos, get_cufd_vigente, obtener_evento_abierto, insertar_evento_local
from ui_copy import main as online_main
from contingencia_auto import finalizar_evento_si_conectado
from logger_config import get_eventos_logger
import os

# Configurar logger para eventos significativos
logger = get_eventos_logger()

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

# Importar el nuevo sistema de gestión de estado (al inicio, después de las importaciones existentes)
try:
    from utils.state_manager import initialize_app_state, get_state, set_state
    from utils.cache_manager import invalidate_cache
    USE_NEW_STATE_MANAGER = True
    logger.info("Usando nuevo sistema de gestión de estado en main.py")
except ImportError as e:
    USE_NEW_STATE_MANAGER = False
    logger.warning(f"No se pudo importar el nuevo sistema de gestión de estado en main.py: {e}")
    logger.info("Usando sistema de gestión de estado original en main.py")


def main():
    logger.info("Iniciando sistema de facturación")
    
    # Inicializar todos los estados al inicio usando el nuevo sistema si está disponible
    if USE_NEW_STATE_MANAGER:
        initialize_app_state()
        logger.info("Estados inicializados con el nuevo sistema")
    
    # Paso previo: solo verificar conexión, sin finalizar eventos automáticamente
    logger.info("Verificando estado de conectividad")
    resultado = finalizar_evento_si_conectado()
    
    # Verificar si hay evento activo
    evento_activo = obtener_evento_abierto()
    if evento_activo:
        logger.info(f"Evento activo detectado: #{evento_activo['id']}, tipo={evento_activo['codigo_evento']}")
        st.warning(f"""
        ⚠️ **MODO CONTINGENCIA ACTIVO** ⚠️

        • **Tipo de evento:** {evento_activo['codigo_evento']} - {evento_activo['descripcion']}
        • **Inicio:** {evento_activo['fecha_inicio'].strftime('%d/%m/%Y %H:%M:%S')}
        • **Estado:** Las facturas se están emitiendo en modo OFFLINE
        """)
        # Guardar en session_state para uso posterior - usar el nuevo sistema si está disponible
        if USE_NEW_STATE_MANAGER:
            set_state('modo_offline', True)
            set_state('evento_activo', evento_activo)
            set_state('evento_contingencia', evento_activo)
        else:
            st.session_state['modo_offline'] = True
            st.session_state['evento_activo'] = evento_activo

        # *** Llamar SIEMPRE a la UI offline si hay evento activo ***
        offline_main()
        return  # Importante para evitar que siga el flujo y se duplique la UI

    # Si no hay evento activo, verificar conexión
    logger.info("Verificando conexión con el SIN")
    mensaje, conectado, tipo_deducido = verificar_comunicacion()

    if conectado:
        logger.info("Conexión establecida con el SIN - iniciando modo online")
        st.success("✅ Conexión establecida con el SIN.")
        # Guardar en session_state - usar el nuevo sistema si está disponible
        if USE_NEW_STATE_MANAGER:
            set_state('modo_offline', False)
            set_state('evento_activo', None)
            set_state('evento_contingencia', None)
        else:
            st.session_state['modo_offline'] = False
        online_main()
    else:
        logger.warning(f"No se pudo conectar al SIN: {mensaje}. Tipo deducido: {tipo_deducido}")
        st.error("❌ No se pudo conectar al SIN. Se activará la contingencia.")
        # Guardar en session_state - usar el nuevo sistema si está disponible
        if USE_NEW_STATE_MANAGER:
            set_state('modo_offline', True)
        else:
            st.session_state['modo_offline'] = True

        # Paso 2: Verificar si ya hay un evento abierto
        evento_existente = obtener_evento_abierto()
        if evento_existente:
            logger.info(f"Se encontró un evento activo existente (ID: {evento_existente['id']})")
            st.info("ℹ️ Ya existe un evento registrado en modo contingencia.")
            # Guardar en session_state - usar el nuevo sistema si está disponible
            if USE_NEW_STATE_MANAGER:
                set_state('evento_activo', evento_existente)
                set_state('evento_contingencia', evento_existente)
            else:
                st.session_state['evento_activo'] = evento_existente

            # *** Llamar SIEMPRE a la UI offline si hay evento activo ***
            offline_main()
            return

        # Paso 3: Registrar evento automáticamente
        logger.info("Registrando evento significativo automáticamente")
        st.warning("⚠️ Registrando evento significativo automáticamente...")

        # Obtener CUFD vigente
        cufd = get_cufd_vigente()
        if not cufd:
            logger.error("No se pudo obtener el CUFD vigente para registrar el evento")
            st.error("❌ No se pudo obtener CUFD vigente para registrar el evento.")
        else:
            eventos_parametricos = get_eventos_parametricos()
            tipos = {e["codigoClasificador"]: e["descripcion"] for e in eventos_parametricos}
            tipo_evento = tipo_deducido if tipo_deducido in tipos else "5"
            descripcion = tipos.get(tipo_evento, "Evento no identificado automáticamente")
            
            logger.info(f"Registrando evento automático: tipo={tipo_evento}, descripción={descripcion}")
            
            ahora = datetime.now()
            insertar_evento_local(
                codigo_evento=tipo_evento,
                descripcion=descripcion,
                fecha_inicio=ahora,
                cufd=cufd
            )
            
            logger.info(f"Evento registrado exitosamente: tipo={tipo_evento}, inicio={ahora}")
            st.success(f"✅ Evento registrado localmente: {descripcion}")

            # Obtener el evento recién creado
            evento_activo = obtener_evento_abierto()
            # Guardar en session_state - usar el nuevo sistema si está disponible
            if evento_activo:
                if USE_NEW_STATE_MANAGER:
                    set_state('evento_activo', evento_activo)
                    set_state('evento_contingencia', evento_activo)
                else:
                    st.session_state['evento_activo'] = evento_activo

                # *** Llamar SIEMPRE a la UI offline si hay evento activo ***
                offline_main()
                return

    # Si llega aquí, no hay conexión ni evento, mostrar error
    st.error("❌ No se pudo activar el modo offline ni registrar un evento de contingencia.")

def offline_main():
    """
    Versión de la interfaz principal para modo offline/contingencia.
    Esta función maneja la facturación cuando estamos en modo contingencia.
    """
    # Intentar recuperar el evento de contingencia desde session_state primero
    evento = st.session_state.get('evento_contingencia')
    if not evento:
        # Si no está en session_state, intentar obtenerlo de la base de datos
        evento = obtener_evento_abierto()
        if evento:
            st.session_state['evento_contingencia'] = evento

    if evento:
        logger.info(f"Mostrando formulario para facturación offline asociada al evento #{evento['id']}")
        from ui_copy import main as ui_main
        ui_main(tipo_emision=2, evento_contingencia=evento)
    else:
        logger.error("No se encontró evento significativo activo para asociar la factura")
        st.error("❌ No se encontró evento significativo activo para asociar la factura.")

if __name__ == "__main__":
    main()
