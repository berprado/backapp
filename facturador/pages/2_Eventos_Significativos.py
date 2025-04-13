# pages/2_Eventos_Significativos.py

import streamlit as st
from datetime import datetime
from soap_services import verificar_comunicacion, consulta_eventos_significativos
from database import (
    get_eventos_parametricos,
    get_cufd_vigente,
    obtener_evento_abierto,
    insertar_evento_local
)
from logger_config import get_eventos_logger  # Importación corregida - eliminado el prefijo facturador

# Configurar logger para eventos significativos
logger = get_eventos_logger()

st.set_page_config(page_title="Eventos Significativos", layout="wide")
st.title("📌 Gestión de Eventos Significativos")

# 🔍 Verificar conexión
mensaje, estado, _ = verificar_comunicacion()
if not estado:
    logger.warning("Intento de acceder a la gestión de eventos sin conexión al SIN")
    st.error("❌ No se puede operar mientras el sistema está desconectado del SIN.")
    st.stop()
else:
    logger.info("Acceso a gestión de eventos con conexión activa al SIN")
    st.success("✅ Conexión activa con el SIN.")

# 🗂️ Pestañas
tabs = st.tabs(["📝 Registrar Evento Planificado", "📋 Consultar Eventos Registrados"])

# ======================================
# 📝 TAB 1 - Registro anticipado
# ======================================
with tabs[0]:
    st.subheader("📝 Registro de evento planificado (códigos 3 y 4)")
    
    # Validar si hay evento activo
    evento_abierto = obtener_evento_abierto()
    if evento_abierto:
        logger.warning(f"Intento de registro con evento abierto existente ID={evento_abierto['id']}")
        st.warning(f"⚠️ Ya existe un evento abierto con ID #{evento_abierto['id']}. No se puede registrar uno nuevo.")
    else:
        eventos = get_eventos_parametricos()
        logger.debug(f"Obtenidos {len(eventos)} eventos paramétricos desde BD")
        eventos_permitidos = {
            e["codigoClasificador"]: e["descripcion"]
            for e in eventos if e["codigoClasificador"] in ("3", "4")
        }

        with st.form("form_evento_planificado"):
            tipo_evento = st.selectbox(
                "Selecciona el tipo de evento planificado",
                options=list(eventos_permitidos.keys()),
                format_func=lambda x: f"{x} - {eventos_permitidos[x]}"
            )
            descripcion = st.text_area("Descripción del evento", value=eventos_permitidos.get(tipo_evento, ""))
            submit = st.form_submit_button("📝 Registrar Evento")

            if submit:
                logger.info(f"Intento de registro de evento planificado tipo={tipo_evento}")
                cufd = get_cufd_vigente()
                if not cufd:
                    logger.error("No se pudo obtener CUFD vigente para registro de evento planificado")
                    st.error("⚠️ No se pudo obtener CUFD vigente.")
                else:
                    ahora = datetime.now()
                    insertar_evento_local(
                        codigo_evento=tipo_evento,
                        descripcion=descripcion,
                        fecha_inicio=ahora,
                        cufd=cufd
                    )
                    logger.info(f"Evento planificado registrado exitosamente: tipo={tipo_evento}, inicio={ahora}")
                    st.success(f"✅ Evento registrado exitosamente. Tipo {tipo_evento}")

# ======================================
# 📋 TAB 2 - Consulta de eventos
# ======================================
with tabs[1]:
    st.subheader("📋 Consultar eventos registrados en el SIN")

    # Selección de fecha y hora
    col1, col2 = st.columns([2, 1])
    with col1:
        fecha_consulta = st.date_input("📅 Fecha del evento", value=datetime.today())
    with col2:
        hora_consulta = st.time_input("🕓 Hora del evento (opcional)", value=datetime.strptime("01:00:00", "%H:%M:%S").time())

    if st.button("🔍 Consultar eventos registrados"):
        # Construir fecha en formato ISO extendido
        fecha_evento_str = f"{fecha_consulta}T{hora_consulta.strftime('%H:%M:%S')}.000"
        logger.info(f"Consultando eventos para fecha: {fecha_evento_str}")

        eventos = consulta_eventos_significativos(fecha_evento=fecha_evento_str)

        if not eventos:
            logger.info(f"No se encontraron eventos para la fecha {fecha_evento_str}")
            st.info("ℹ️ No hay eventos registrados para esa fecha u hora, o no se pudo obtener la información.")
        else:
            logger.info(f"Se encontraron {len(eventos)} eventos para la fecha {fecha_evento_str}")
            st.success(f"✅ Se encontraron {len(eventos)} evento(s) registrados.")
            for e in eventos:
                # Verificar que todos los campos esperados existan en la respuesta
                codigo_recepcion = e.get("codigoRecepcionEventoSignificativo", "No disponible")
                codigo_evento = e.get("codigoEvento", "No disponible")
                descripcion = e.get("descripcion", "No disponible")
                fecha_inicio = e.get("fechaInicioEvento", "No disponible")
                fecha_fin = e.get("fechaFinEvento", "En curso")
                cufd = e.get("cufd", "No disponible")
                
                # Mostrar información formateada al usuario
                st.markdown(f"""
                ---
                🆔 **Código Recepción:** `{codigo_recepcion}`  
                🧩 **Tipo de Evento:** `{codigo_evento}`  
                📄 **Descripción:** {descripcion}  
                🗓️ **Inicio:** {fecha_inicio}  
                🕓 **Fin:** {fecha_fin if fecha_fin else '⏳ En curso'}
                🔑 **CUFD:** `{cufd}`
                """)
                logger.debug(f"Evento mostrado: código={codigo_evento}, recepción={codigo_recepcion}")
