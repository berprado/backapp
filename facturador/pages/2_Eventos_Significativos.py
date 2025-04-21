# pages/2_Eventos_Significativos.py

import streamlit as st
import os
import sys
from datetime import datetime
from soap_services import verificar_comunicacion, consulta_eventos_significativos
from database import (
    get_eventos_parametricos,
    get_cufd_vigente,
    obtener_evento_abierto,
    insertar_evento_local,
    obtener_facturas_por_evento
)
from logger_config import get_eventos_logger

# Añadir el directorio padre al path para poder importar funciones
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from contingencia_auto import finalizar_evento_manual

# Configurar logger para eventos significativos
logger = get_eventos_logger()

st.set_page_config(page_title="Eventos Significativos", layout="wide")
st.title("📌 Gestión de Eventos Significativos")

# Banner de estado del sistema
evento_abierto = obtener_evento_abierto()
if evento_abierto:
    st.warning(f"""
    ⚠️ **MODO CONTINGENCIA ACTIVO** ⚠️
    
    • **Tipo de evento:** {evento_abierto['codigo_evento']} - {evento_abierto['descripcion']}
    • **Inicio:** {evento_abierto['fecha_inicio'].strftime('%d/%m/%Y %H:%M:%S')}
    • **Estado:** Las facturas se están emitiendo en modo OFFLINE
    
    Para finalizar este evento y sincronizar las facturas pendientes, 
    vaya a la pestaña "⚠️ Eventos Activos".
    """)
    # Guardar en session_state para uso posterior
    st.session_state['modo_offline'] = True
    st.session_state['evento_activo'] = evento_abierto
else:
    # 🔍 Verificar conexión
    mensaje, estado, _ = verificar_comunicacion()
    if not estado:
        st.error("❌ No hay conexión con el SIN. El sistema detectará automáticamente el estado.")
        # Guardar en session_state
        st.session_state['modo_offline'] = True
    else:
        st.success("✅ Conexión activa con el SIN.")
        # Guardar en session_state
        st.session_state['modo_offline'] = False

# 🗂️ Pestañas
tabs = st.tabs(["📝 Registrar Evento", "📋 Consultar Eventos", "⚠️ Eventos Activos"])

# ======================================
# 📝 TAB 1 - Registro de eventos
# ======================================
with tabs[0]:
    st.subheader("📝 Registro de eventos significativos")
    
    # Validar si hay evento activo
    if evento_abierto:
        st.info(f"""
        ℹ️ Ya existe un evento activo (#{evento_abierto['id']}).
        No se puede registrar uno nuevo hasta finalizar el actual.
        """)
    else:
        eventos = get_eventos_parametricos()
        
        # Obtener todos los tipos de eventos
        eventos_dict = {e["codigoClasificador"]: e["descripcion"] for e in eventos}

        # Agrupar eventos por tipo
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Eventos de Contingencia")
            tipo_evento_contingencia = st.selectbox(
                "Tipo de evento de contingencia",
                options=["1", "2", "5", "6", "7"],
                format_func=lambda x: f"{x} - {eventos_dict.get(x, 'Desconocido')}"
            )
            
        with col2:
            st.subheader("Eventos Planificados")
            tipo_evento_planificado = st.selectbox(
                "Tipo de evento planificado",
                options=["3", "4"],
                format_func=lambda x: f"{x} - {eventos_dict.get(x, 'Desconocido')}"
            )
            
        # Selector de tipo de evento a registrar
        tipo_registro = st.radio(
            "¿Qué tipo de evento desea registrar?",
            options=["Contingencia", "Planificado"],
            horizontal=True
        )
        
        if tipo_registro == "Contingencia":
            tipo_evento = tipo_evento_contingencia
        else:
            tipo_evento = tipo_evento_planificado
            
        descripcion_predeterminada = eventos_dict.get(tipo_evento, "")
        
        with st.form("form_evento"):
            descripcion = st.text_area(
                "Descripción del evento", 
                value=descripcion_predeterminada,
                help="Puede personalizar la descripción o dejar la predeterminada"
            )
            
            submit = st.form_submit_button("📝 Registrar Evento")

            if submit:
                logger.info(f"Intento de registro de evento tipo={tipo_evento}")
                cufd = get_cufd_vigente()
                if not cufd:
                    logger.error("No se pudo obtener CUFD vigente para registro de evento")
                    st.error("⚠️ No se pudo obtener CUFD vigente.")
                else:
                    ahora = datetime.now()
                    insertar_evento_local(
                        codigo_evento=tipo_evento,
                        descripcion=descripcion,
                        fecha_inicio=ahora,
                        cufd=cufd
                    )
                    logger.info(f"Evento registrado exitosamente: tipo={tipo_evento}, inicio={ahora}")
                    st.success(f"✅ Evento registrado exitosamente. Tipo {tipo_evento}")
                    
                    # Mostrar mensaje específico para eventos de contingencia
                    if tipo_evento in ["1", "2", "5", "6", "7"]:
                        st.warning("""
                        ⚠️ Se ha activado el modo CONTINGENCIA.
                        
                        A partir de este momento, las facturas se emitirán en modo OFFLINE
                        hasta que se finalice manualmente este evento.
                        """)
                        
                    # Recargar la página para mostrar el banner de modo contingencia
                    st.rerun()

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
        # Verificar si hay conexión antes de hacer la consulta
        mensaje, estado, _ = verificar_comunicacion()
        if not estado:
            st.error("❌ No hay conexión con el SIN. No se puede realizar la consulta en este momento.")
        else:
            # Construir fecha en formato ISO extendido
            fecha_evento_str = f"{fecha_consulta}T{hora_consulta.strftime('%H:%M:%S')}.000"
            logger.info(f"Consultando eventos para fecha: {fecha_evento_str}")

            with st.spinner("Consultando eventos..."):
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

# ======================================
# ⚠️ TAB 3 - Gestión de Eventos Activos
# ======================================
with tabs[2]:
    st.subheader("⚠️ Gestión de eventos activos")
    
    # Refrescar el estado del evento activo
    evento_abierto = obtener_evento_abierto()
    
    if not evento_abierto:
        st.info("No hay eventos de contingencia activos en este momento.")
    else:
        # Mostrar detalles del evento activo
        st.write("### Detalles del Evento Activo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **ID del evento:** {evento_abierto['id']}  
            **Tipo de evento:** {evento_abierto['codigo_evento']}  
            **Descripción:** {evento_abierto['descripcion']}  
            **CUFD asociado:** `{evento_abierto['cufd'][:10]}...`
            """)
            
        with col2:
            st.markdown(f"""
            **Fecha de inicio:** {evento_abierto['fecha_inicio'].strftime('%d/%m/%Y %H:%M:%S')}  
            **Duración:** {(datetime.now() - evento_abierto['fecha_inicio']).total_seconds() / 3600:.2f} horas  
            """)
        
        # Obtener facturas emitidas durante este evento
        facturas_evento = obtener_facturas_por_evento(evento_abierto['id'])
        
        st.write("### Facturas Emitidas en Contingencia")
        if not facturas_evento:
            st.info("No se han emitido facturas durante este evento de contingencia.")
        else:
            st.success(f"Se han emitido {len(facturas_evento)} facturas durante este evento.")
            
            # Mostrar tabla resumida de facturas
            st.write("#### Resumen de facturas")
            tabla_data = []
            for f in facturas_evento:
                tabla_data.append({
                    "Nº Factura": f.get("numeroFactura", "N/A"),
                    "Cliente": f.get("nombreRazonSocial", "Sin nombre"),
                    "Monto": f"{float(f.get('montoTotal', 0)):.2f} Bs",
                    "Fecha": f.get("fechaEmision").strftime("%d/%m/%Y %H:%M") if f.get("fechaEmision") else "N/A",
                })
            
            # Mostrar la tabla si hay datos
            if tabla_data:
                st.dataframe(tabla_data, use_container_width=True)
        
        # Sección para finalizar el evento
        st.write("### Finalizar Evento")
        
        # Verificar conexión con el SIN
        mensaje, estado, _ = verificar_comunicacion()
        if not estado:
            st.error(f"""
            ❌ No hay conexión con el SIN. No es posible finalizar el evento en este momento.
            
            Error: {mensaje}
            
            Intente nuevamente cuando se restablezca la conexión.
            """)
        else:
            st.success("✅ Hay conexión con el SIN. Es posible finalizar el evento.")
            
            if st.button("🔄 Finalizar evento y sincronizar facturas", type="primary"):
                with st.spinner("Finalizando evento..."):
                    resultado = finalizar_evento_manual(evento_abierto['id'])
                
                if resultado['exito']:
                    st.success(f"""
                    ✅ Evento finalizado exitosamente.
                    
                    - Código de recepción: {resultado['codigo_recepcion']}
                    - Facturas comprimidas: {resultado['facturas_comprimidas']}
                    """)
                    
                    # Si hay facturas comprimidas y una ruta de ZIP
                    if resultado['facturas_comprimidas'] > 0 and resultado['ruta_zip']:
                        # Aquí se podría añadir un botón para descargar el ZIP si fuera necesario
                        st.info(f"""
                        Las facturas han sido comprimidas en: {resultado['ruta_zip']}
                        """)
                    
                    # Recargar la página después de 3 segundos
                    st.rerun()
                else:
                    st.error(f"""
                    ❌ Error al finalizar el evento:
                    
                    {resultado['mensaje']}
                    """)
