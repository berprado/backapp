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

def main():
    logger.info("Iniciando sistema de facturación")
    
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
        # Guardar en session_state para uso posterior
        st.session_state['modo_offline'] = True
        st.session_state['evento_activo'] = evento_activo
    else:
        # Verificar conexión al inicio
        logger.info("Verificando conexión con el SIN")
        mensaje, conectado, tipo_deducido = verificar_comunicacion()

        if conectado:
            logger.info("Conexión establecida con el SIN - iniciando modo online")
            st.success("✅ Conexión establecida con el SIN.")
            # Guardar en session_state
            st.session_state['modo_offline'] = False
            online_main()
        else:
            logger.warning(f"No se pudo conectar al SIN: {mensaje}. Tipo deducido: {tipo_deducido}")
            st.error("❌ No se pudo conectar al SIN. Se activará la contingencia.")
            # Guardar en session_state
            st.session_state['modo_offline'] = True

            # Paso 2: Verificar si ya hay un evento abierto
            evento_existente = obtener_evento_abierto()
            if evento_existente:
                logger.info(f"Se encontró un evento activo existente (ID: {evento_existente['id']})")
                st.info("ℹ️ Ya existe un evento registrado en modo contingencia.")
                # Guardar en session_state
                st.session_state['evento_activo'] = evento_existente
            else:
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
                    # Guardar en session_state
                    if evento_activo:
                        st.session_state['evento_activo'] = evento_activo

            # Paso 4: Cargar la interfaz offline
            logger.info("Activando modo offline de facturación")
            st.warning("🛠️ Activando modo offline de facturación...")

            # Mostrar formulario para facturación offline
            offline_main()

def offline_main():
    """
    Versión de la interfaz principal para modo offline/contingencia.
    Esta función maneja la facturación cuando estamos en modo contingencia.
    """
    # Mostrar formulario si hay evento activo
    evento = obtener_evento_abierto()
    if evento:
        logger.info(f"Mostrando formulario para facturación offline asociada al evento #{evento['id']}")
        
        # Importar la función main de ui_copy directamente aquí para evitar problemas de circular import
        from ui_copy import main as ui_main
        
        # Llamar a la función ui_main con los parámetros necesarios para modo offline
        ui_main(tipo_emision=2, evento_contingencia=evento)
    else:
        logger.error("No se encontró evento significativo activo para asociar la factura")
        st.error("❌ No se encontró evento significativo activo para asociar la factura.")

if __name__ == "__main__":
    main()
