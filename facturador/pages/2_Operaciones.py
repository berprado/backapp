import os
import sys
import pandas as pd
import streamlit as st
import time
from datetime import datetime, timedelta

# Agregar ruta del directorio padre al path de Python
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Importar módulos necesarios para contingencias
from facturador.contingency_manager import get_contingency_manager, ContingencyStatus, SignificantEventType
from facturador.batch_sender import BatchSender
from facturador.significant_events import register_significant_event, get_significant_events, query_siat_significant_events
from facturador.models import FacturaCabecera
from database import SessionLocal
from facturador.logger_config import get_logger  # Cambiar esta importación

# Configurar loggers
logger = get_logger()
contingency_logger = get_logger('contingency')

# Función para formatear fechas consistentemente
def format_datetime(dt):
    if dt:
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except:
                return dt
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    return "N/A"

def main():
    st.title("Operaciones de Contingencia y Emisión Masiva")
    
    # Obtener el gestor de contingencias
    contingency_manager = get_contingency_manager()
    
    # Crear tabs para las diferentes funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs(["Estado del Sistema", "Gestión de Contingencia", "Envío Masivo", "Eventos Significativos"])
    
    # Tab 1: Estado del Sistema
    with tab1:
        st.header("Estado del Sistema")
        
        # Mostrar el estado actual de la conexión
        status = contingency_manager.get_status()
        
        col1, col2 = st.columns(2)
        with col1:
            status_color = {
                "normal": "🟢",
                "monitoring": "🟡",
                "contingency": "🔴",
                "recovering": "🟠"
            }
            
            st.subheader(f"{status_color.get(status['status'], '⚪')} Estado Actual: {status['status'].upper()}")
            
            if status['last_check_time']:
                st.write(f"Última verificación: {format_datetime(status['last_check_time'])}")
            
            if status['contingency_start_time']:
                st.write(f"Inicio de contingencia: {format_datetime(status['contingency_start_time'])}")
            
            if status['status'] == 'contingency':
                tiempo_contingencia = datetime.now() - datetime.fromisoformat(status['contingency_start_time'])
                horas, minutos = divmod(tiempo_contingencia.seconds // 60, 60)
                st.info(f"⏱️ Tiempo en contingencia: {tiempo_contingencia.days} días, {horas} horas, {minutos} minutos")
            
            if status['event_type']:
                st.write(f"Tipo de evento: {status['event_type']} - {status['event_description']}")
        
        with col2:
            # Mostrar estadísticas de facturas en contingencia
            session = SessionLocal()
            try:
                facturas_contingencia = session.query(FacturaCabecera).filter(
                    FacturaCabecera.estadoFirma == "CONTINGENCIA"
                ).count()
                
                st.metric(
                    label="Facturas pendientes en contingencia", 
                    value=facturas_contingencia,
                    delta=None
                )
                
                # Últimos 5 eventos significativos
                st.subheader("Últimos eventos:")
                events = get_significant_events(5)
                
                if events:
                    for event in events[:3]:
                        st.info(f"{format_datetime(event['fecha_registro'])}: {event['descripcion']}")
                else:
                    st.write("No hay eventos registrados")
                
            finally:
                session.close()
        
        # Sección de verificación de conexión
        st.subheader("Verificar conexión con servicios SIAT")
        
        if st.button("Verificar conexión ahora", key="check_connection"):
            with st.spinner("Verificando conexión con los servicios..."):
                all_ok, problem_services = contingency_manager.check_connection()
                
                if all_ok:
                    st.success("✅ Todos los servicios están operativos")
                else:
                    st.error(f"⚠️ Problemas de conexión con: {', '.join(problem_services)}")
    
    # Tab 2: Gestión de Contingencia
    with tab2:
        st.header("Gestión de Contingencia")
        
        # Obtener estado actual
        status = contingency_manager.get_status()
        
        # Mostrar estado actual
        if status['status'] == 'contingency':
            st.warning("🔴 Sistema actualmente en modo contingencia")
            st.info(f"""
            **Información de la contingencia actual:**
            - Inicio: {format_datetime(status['contingency_start_time'])}
            - Evento: {status['event_description']}
            """)
            
            # Opción para desactivar manualmente
            if st.button("Desactivar modo contingencia", type="primary"):
                with st.spinner("Desactivando modo contingencia..."):
                    success = contingency_manager.deactivate_contingency()
                    if success:
                        st.success("✅ Modo contingencia desactivado correctamente")
                        st.info("El sistema enviará las facturas pendientes automáticamente")
                        st.rerun()
                    else:
                        st.error("Error al desactivar el modo contingencia. Consulte los logs para más detalles.")
        else:
            # Opciones para activar manualmente
            st.info("Sistema en modo normal (sin contingencia)")
            
            with st.expander("Activar contingencia manualmente"):
                # Obtener tipos de eventos disponibles
                event_types = contingency_manager.get_available_event_types()
                
                # Crear opciones para el selectbox
                event_options = {f"{e['codigo']} - {e['descripcion']}": e['codigo'] for e in event_types}
                
                # Mostrar selectbox con eventos
                selected_event = st.selectbox(
                    "Seleccione el tipo de evento:",
                    options=list(event_options.keys()),
                    key="event_type"
                )
                
                # Descripción personalizada
                description = st.text_area(
                    "Descripción del evento:",
                    placeholder="Ingrese una descripción detallada del evento",
                    key="event_description"
                )
                
                # Botón para activar
                if st.button("Activar modo contingencia", type="primary", key="activate_contingency"):
                    if not selected_event or not description:
                        st.error("Debe seleccionar un tipo de evento y proporcionar una descripción.")
                    else:
                        with st.spinner("Activando modo contingencia..."):
                            # Obtener código del evento seleccionado
                            event_code = event_options[selected_event]
                            
                            # Activar contingencia
                            success = contingency_manager.activate_contingency(
                                event_type=event_code,
                                description=description
                            )
                            
                            if success:
                                st.success("✅ Modo contingencia activado correctamente")
                                st.info("""
                                **Instrucciones para operar en contingencia:**
                                1. Las facturas se emitirán en modo offline
                                2. Los datos se almacenarán localmente
                                3. Una vez restablecida la conexión, se enviarán automáticamente
                                """)
                                st.rerun()
                            else:
                                st.error("Error al activar el modo contingencia. Consulte los logs para más detalles.")
        
        # Información sobre el modo contingencia
        with st.expander("¿Qué es el modo contingencia?"):
            st.markdown("""
            El **modo contingencia** permite seguir emitiendo facturas cuando hay problemas de conexión con el servicio SIAT.
            
            ### Causas comunes
            - Fallas en la conexión a internet
            - Indisponibilidad de servicios SIAT
            - Problemas técnicos con el servidor
            
            ### Funcionamiento
            1. Las facturas se emiten offline con el último CUFD válido
            2. Se almacenan localmente en formato XML
            3. Una vez restablecida la conexión, se registra el evento significativo
            4. Se envían las facturas pendientes en lotes
            
            ### Consideraciones importantes
            - El CUFD se extiende hasta 72 horas en contingencia
            - Es obligatorio registrar el evento significativo al finalizar
            - Máximo 500 facturas por lote de envío
            """)
        
        # Monitor de conexión
        with st.expander("Monitor de conexión"):
            st.write("Estado del monitor automático de conexión:")
            
            # Asegurarse de que monitor_active sea un booleano
            monitoring_thread = contingency_manager.monitoring_thread
            monitor_active = False  # Valor predeterminado seguro
            
            if monitoring_thread is not None:
                monitor_active = monitoring_thread.is_alive()
            
            st.write(f"Monitor activo: {'✅ Sí' if monitor_active else '❌ No'}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Iniciar monitoreo", disabled=monitor_active):
                    contingency_manager.start_monitoring()
                    st.success("✅ Monitoreo iniciado")
                    time.sleep(1)
                    st.rerun()
            
            with col2:
                if st.button("Detener monitoreo", disabled=not monitor_active):
                    contingency_manager.stop_monitoring()
                    st.success("✅ Monitoreo detenido")
                    time.sleep(1)
                    st.rerun()
    
    # Tab 3: Envío Masivo
    with tab3:
        st.header("Envío Masivo de Facturas")
        
        # Información del estado actual
        session = SessionLocal()
        try:
            # Contar facturas pendientes de envío
            facturas_pendientes = session.query(FacturaCabecera).filter(
                FacturaCabecera.estadoFirma == "CONTINGENCIA"
            ).all()
            
            total_pendientes = len(facturas_pendientes)
            
            # Mostrar información
            st.metric(
                label="Facturas pendientes de envío", 
                value=total_pendientes,
                delta=None
            )
            
            if total_pendientes > 0:
                # Agrupar por fecha para mostrar estadísticas
                facturas_por_fecha = {}
                for factura in facturas_pendientes:
                    fecha = factura.fechaEmision.strftime("%Y-%m-%d")
                    if fecha not in facturas_por_fecha:
                        facturas_por_fecha[fecha] = 0
                    facturas_por_fecha[fecha] += 1
                
                # Mostrar gráfico de facturas pendientes por fecha
                df = pd.DataFrame({
                    'Fecha': list(facturas_por_fecha.keys()),
                    'Facturas': list(facturas_por_fecha.values())
                })
                
                st.bar_chart(df.set_index('Fecha'))
                
                # Botón para enviar todas las facturas pendientes
                if st.button("Enviar todas las facturas pendientes", type="primary"):
                    with st.spinner("Enviando facturas pendientes..."):
                        # Crear y ejecutar el enviador de lotes
                        batch_sender = BatchSender()
                        results = batch_sender.send_all_pending_invoices()
                        
                        # Mostrar resultados
                        if results["success"]:
                            st.success(f"✅ {results['message']}")
                            st.balloons()
                            
                            if "batches_results" in results:
                                # Mostrar detalles de cada lote
                                with st.expander("Ver detalles por lote"):
                                    for batch_result in results["batches_results"]:
                                        status = "✅ Éxito" if batch_result["success"] else "❌ Error"
                                        st.write(f"**Lote {batch_result['batch_number']}:** {status} - {batch_result.get('message', '')} ({batch_result['invoices']} facturas)")
                        else:
                            st.error(f"❌ {results['message']}")
            else:
                st.info("No hay facturas pendientes de envío")
                
                # Opción para verificar factura específica
                with st.expander("Verificar factura específica"):
                    numero_factura = st.text_input("Número de factura:", key="check_invoice")
                    if st.button("Verificar estado", key="check_invoice_button"):
                        with st.spinner("Verificando estado de la factura..."):
                            # Buscar la factura
                            factura = session.query(FacturaCabecera).filter(
                                FacturaCabecera.numeroFactura == numero_factura
                            ).first()
                            
                            if factura:
                                st.write(f"**Factura #{factura.numeroFactura}**")
                                st.write(f"Estado: {factura.estado}")
                                st.write(f"Estado de validación: {factura.estadoValidacion}")
                                st.write(f"Resultado de validación: {factura.resultadoValidacion or 'No validada'}")
                                st.write(f"Fecha de emisión: {format_datetime(factura.fechaEmision)}")
                                st.write(f"Monto total: {float(factura.montoTotal):.2f} Bs.")
                            else:
                                st.warning(f"No se encontró la factura #{numero_factura}")
        finally:
            session.close()
    
    # Tab 4: Eventos Significativos
    with tab4:
        st.header("Eventos Significativos")
        
        # Tabs para eventos locales y del SIAT
        event_tab1, event_tab2, event_tab3 = st.tabs(["Eventos registrados", "Consultar SIAT", "Registrar evento"])
        
        # Tab de eventos registrados localmente
        with event_tab1:
            st.subheader("Eventos registrados en el sistema")
            
            # Obtener eventos
            events = get_significant_events(50)
            
            if events:
                # Convertir a DataFrame para mostrar en tabla
                events_data = []
                for event in events:
                    events_data.append({
                        "Código": event['codigo'],
                        "Descripción": event['descripcion'],
                        "Inicio": format_datetime(event['fecha_inicio']),
                        "Fin": format_datetime(event['fecha_fin']),
                        "Registro": format_datetime(event['fecha_registro'])
                    })
                
                df = pd.DataFrame(events_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No se encontraron eventos registrados")
        
        # Tab de consulta al SIAT
        with event_tab2:
            st.subheader("Consultar eventos registrados en SIAT")
            
            if st.button("Consultar eventos en SIAT"):
                with st.spinner("Consultando eventos en el SIAT..."):
                    success, data = query_siat_significant_events()
                    
                    if success:
                        if data:
                            # Convertir a DataFrame para mostrar en tabla
                            siat_events_data = []
                            for event in data:
                                siat_events_data.append({
                                    "Código": event['codigoEvento'],
                                    "Descripción": event['descripcionEvento'],
                                    "Inicio": format_datetime(event['fechaInicio']),
                                    "Fin": format_datetime(event['fechaFin']),
                                    "CUFD": event['cufdEvento'][:15] + "..."
                                })
                            
                            df = pd.DataFrame(siat_events_data)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        else:
                            st.info("No se encontraron eventos registrados en el SIAT")
                    else:
                        st.error(f"❌ Error al consultar eventos: {data}")
        
        # Tab de registro manual de eventos
        with event_tab3:
            st.subheader("Registrar evento significativo")
            
            # Obtener tipos de eventos disponibles
            event_types = contingency_manager.get_available_event_types()
            
            # Crear opciones para el selectbox
            event_options = {f"{e['codigo']} - {e['descripcion']}": e['codigo'] for e in event_types}
            
            # Formulario para registro de evento
            with st.form("register_event_form"):
                # Seleccionar tipo de evento
                selected_event = st.selectbox(
                    "Tipo de evento:",
                    options=list(event_options.keys()),
                    key="register_event_type"
                )
                
                # Descripción
                description = st.text_area(
                    "Descripción:",
                    placeholder="Ingrese una descripción detallada del evento",
                    key="register_event_description"
                )
                
                # Fechas
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input(
                        "Fecha de inicio:",
                        value=datetime.now().date(),
                        key="start_date"
                    )
                    start_time = st.time_input(
                        "Hora de inicio:",
                        value=datetime.now().time(),
                        key="start_time"
                    )
                
                with col2:
                    end_date = st.date_input(
                        "Fecha de fin:",
                        value=datetime.now().date(),
                        key="end_date"
                    )
                    end_time = st.time_input(
                        "Hora de fin:",
                        value=datetime.now().time(),
                        key="end_time"
                    )
                
                # CUFD
                cufd = st.text_input(
                    "CUFD utilizado durante el evento:",
                    help="Deje en blanco para usar el CUFD actual",
                    key="event_cufd"
                )
                
                # Botón de envío
                submit_button = st.form_submit_button("Registrar evento")
            
            # Procesar el formulario al enviar
            if submit_button:
                if not description:
                    st.warning("Por favor, ingrese una descripción para el evento")
                else:
                    # Crear fechas completas
                    start_datetime = datetime.combine(start_date, start_time)
                    end_datetime = datetime.combine(end_date, end_time)
                    
                    # Validar fechas
                    if end_datetime <= start_datetime:
                        st.error("La fecha de fin debe ser posterior a la fecha de inicio")
                    else:
                        # Formatear fechas para el servicio
                        start_str = start_datetime.strftime("%Y-%m-%dT%H:%M:%S.000")
                        end_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S.000")
                        
                        # Obtener código del evento seleccionado
                        event_code = event_options[selected_event]
                        
                        with st.spinner("Registrando evento..."):
                            success, message = register_significant_event(
                                event_code=event_code,
                                description=description,
                                start_time=start_str,
                                end_time=end_str,
                                cufd=cufd if cufd else None
                            )
                            
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")

# Ejecutar la aplicación si se ejecuta directamente
if __name__ == "__main__":
    main()