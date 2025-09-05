import streamlit as st
import os
import sys
import pandas as pd

# Agregar ruta del directorio padre al path de Python
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Importar el sistema centralizado de verificación
from facturador.communication_manager import communication_manager
from logger_config import get_logger

# Obtener logger para este módulo
logger = get_logger()

def mostrar_estado_servicios(resultado_verificacion):
    """
    Muestra el estado de los servicios usando los resultados del communication_manager.
    
    Args:
        resultado_verificacion (dict): Resultado de la verificación centralizada
    """
    results = []
    
    # Agregar verificación principal
    principal = resultado_verificacion.get("verificacion_principal", {})
    if principal:
        tiempo_respuesta = principal.get("response_time", "N/A")
        
        # Formatear el tiempo de respuesta con colores
        if tiempo_respuesta != "N/A" and tiempo_respuesta != "Error":
            try:
                tiempo_num = float(tiempo_respuesta.replace('s', ''))
                if tiempo_num < 1.0:
                    tiempo_formateado = f"🟢 {tiempo_respuesta}"  # Verde para respuestas rápidas
                elif tiempo_num < 3.0:
                    tiempo_formateado = f"🟡 {tiempo_respuesta}"  # Amarillo para respuestas normales
                else:
                    tiempo_formateado = f"🔴 {tiempo_respuesta}"  # Rojo para respuestas lentas
            except:
                tiempo_formateado = tiempo_respuesta
        else:
            tiempo_formateado = tiempo_respuesta
        
        results.append({
            "Servicio": "🔍 Verificación Principal",
            "Estado": "✅ Operativo" if principal.get("conectado") else "❌ Con problemas", 
            "Mensaje": principal.get("mensaje", "Sin mensaje"),
            "Fuente": principal.get("fuente", "Sistema general"),
            "Tiempo": tiempo_formateado
        })
    
    # Agregar verificaciones por servicio
    servicios = resultado_verificacion.get("verificaciones_servicios", {})
    service_names = {
        "FacturacionCodigos": "📋 Facturación Códigos",
        "FacturacionOperaciones": "⚙️ Facturación Operaciones", 
        "FacturacionSincronizacion": "🔄 Facturación Sincronización",
        "DocumentosAjuste": "📄 Documentos de Ajuste",
        "FacturaCompraVenta": "💰 Facturación Compra-Venta"
    }
    
    for servicio, detalle in servicios.items():
        nombre_amigable = service_names.get(servicio, servicio)
        tiempo_respuesta = detalle.get("response_time", "N/A")
        
        # Formatear el tiempo de respuesta con colores
        if tiempo_respuesta != "N/A" and tiempo_respuesta != "Error":
            try:
                tiempo_num = float(tiempo_respuesta.replace('s', ''))
                if tiempo_num < 1.0:
                    tiempo_formateado = f"🟢 {tiempo_respuesta}"  # Verde para respuestas rápidas
                elif tiempo_num < 3.0:
                    tiempo_formateado = f"🟡 {tiempo_respuesta}"  # Amarillo para respuestas normales
                else:
                    tiempo_formateado = f"🔴 {tiempo_respuesta}"  # Rojo para respuestas lentas
            except:
                tiempo_formateado = tiempo_respuesta
        else:
            tiempo_formateado = tiempo_respuesta
        
        results.append({
            "Servicio": nombre_amigable,
            "Estado": "✅ Operativo" if detalle.get("conectado") else "❌ Con problemas",
            "Mensaje": detalle.get("mensaje", "Sin mensaje"),
            "Fuente": detalle.get("fuente", "Sistema específico"),
            "Tiempo": tiempo_formateado
        })
    
    # Mostrar tabla si hay resultados
    if results:
        # Mostrar estadísticas de rendimiento
        st.subheader("📊 Estadísticas de Rendimiento")
        
        # Extraer tiempos para estadísticas
        tiempos_validos = []
        for row in results:
            tiempo_str = row["Tiempo"]
            if "🟢" in tiempo_str or "🟡" in tiempo_str or "🔴" in tiempo_str:
                try:
                    tiempo_limpio = tiempo_str.split()[-1].replace('s', '')
                    tiempos_validos.append(float(tiempo_limpio))
                except:
                    continue
        
        if tiempos_validos:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("⚡ Tiempo Promedio", f"{sum(tiempos_validos)/len(tiempos_validos):.3f}s")
            with col2:
                st.metric("🚀 Más Rápido", f"{min(tiempos_validos):.3f}s")
            with col3:
                st.metric("🐌 Más Lento", f"{max(tiempos_validos):.3f}s")
            with col4:
                st.metric("📊 Servicios OK", f"{sum(1 for r in results if '✅' in r['Estado'])}/{len(results)}")
        
        st.subheader("🔍 Detalle por Servicio")
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Determinar estado general
        todos_operativos = all(row["Estado"] == "✅ Operativo" for row in results)
        
        if todos_operativos:
            st.success("✅ Todos los servicios están operativos")
        else:
            servicios_con_problemas = [
                row["Servicio"] for row in results 
                if row["Estado"] != "✅ Operativo"
            ]
            st.error(f"⚠️ Hay problemas con: {', '.join(servicios_con_problemas)}")
            
            # Mostrar recomendación de contingencia
            recomendacion = resultado_verificacion.get("recomendacion", "")
            if recomendacion:
                st.warning(f"💡 **Recomendación del Sistema:** {recomendacion}")
            
            st.info("""
            **Sugerencia:** Si los problemas persisten, considere activar el modo de contingencia.
            El sistema puede detectar automáticamente el tipo de contingencia apropiado.
            """)
    else:
        st.warning("No se obtuvieron resultados de la verificación")

def main():
    st.title("🔍 Verificador de Comunicación con SIAT")
    
    st.write("""
    Esta herramienta utiliza el **sistema centralizado de verificación** para diagnosticar 
    la comunicación con los servicios de facturación del SIAT de manera optimizada.
    """)
    
    # Información del sistema
    st.info("""
    ℹ️ **Sistema Optimizado**: Esta página utiliza caché inteligente de 30 segundos 
    para evitar sobrecargar los servicios del SIAT con consultas repetitivas.
    """)
    
    # Botones de acción principales
    st.subheader("🎯 Opciones de Verificación")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        verificar_normal = st.button(
            "🔧 Verificación Estándar", 
            help="Usa caché si está disponible (recomendado)",
            use_container_width=True
        )
    
    with col2:
        verificar_forzado = st.button(
            "🔄 Verificación Forzada", 
            help="Ignora caché y ejecuta verificación nueva",
            use_container_width=True
        )
    
    with col3:
        diagnostico_completo = st.button(
            "🩺 Diagnóstico Completo", 
            help="Muestra interfaz avanzada de diagnóstico",
            use_container_width=True
        )
    
    # Mostrar estado de caché
    with st.expander("📊 Información del Sistema de Caché"):
        st.write("""
        - **Tiempo de vida del caché**: 30 segundos
        - **Última verificación**: Se muestra en los resultados
        - **Estado del sistema**: Centralizado y optimizado
        """)
    
    # Procesar acciones de los botones
    if verificar_normal:
        st.subheader("📋 Resultados de Verificación Estándar")
        
        with st.spinner("🔍 Verificando comunicación (usando caché si está disponible)..."):
            try:
                resultado = communication_manager.verificar_comunicacion_completa(force_check=False)
                mostrar_estado_servicios(resultado)
                
                # Mostrar timestamp
                timestamp = resultado.get("timestamp", "No disponible")
                st.caption(f"⏰ Última verificación: {timestamp}")
                
            except Exception as e:
                st.error(f"❌ Error durante la verificación: {str(e)}")
                logger.error(f"Error en verificación estándar: {e}")
    
    elif verificar_forzado:
        st.subheader("🔄 Resultados de Verificación Forzada")
        
        with st.spinner("🚀 Ejecutando verificación completa (ignorando caché)..."):
            try:
                resultado = communication_manager.verificar_comunicacion_completa(force_check=True)
                mostrar_estado_servicios(resultado)
                
                # Mostrar timestamp
                timestamp = resultado.get("timestamp", "No disponible")
                st.success(f"✅ Verificación forzada completada: {timestamp}")
                
            except Exception as e:
                st.error(f"❌ Error durante la verificación forzada: {str(e)}")
                logger.error(f"Error en verificación forzada: {e}")
    
    elif diagnostico_completo:
        st.subheader("🩺 Diagnóstico Completo del Sistema")
        
        try:
            # Mostrar la interfaz completa de diagnóstico del communication_manager
            communication_manager.mostrar_diagnostico_completo()
            
        except Exception as e:
            st.error(f"❌ Error en diagnóstico completo: {str(e)}")
            logger.error(f"Error en diagnóstico completo: {e}")
    
    # Sección de ayuda
    with st.expander("❓ Ayuda y Guía de Uso"):
        st.markdown("""
        ### 🎯 ¿Cuándo usar cada opción?
        
        - **🔧 Verificación Estándar**: Para uso normal. Es rápida y eficiente.
        - **🔄 Verificación Forzada**: Cuando necesites datos en tiempo real o si sospechas cambios recientes.
        - **🩺 Diagnóstico Completo**: Para análisis detallado, historial y troubleshooting avanzado.
        
        ### 📊 Estados de los Servicios
        
        - **✅ Operativo**: El servicio responde correctamente
        - **❌ Con problemas**: Hay errores de comunicación o respuesta
        - **⚠️ No configurado**: El servicio no está configurado en el sistema
        
        ### ⏱️ Interpretación de Tiempos de Respuesta
        
        - **� < 1.0s**: Excelente - Respuesta muy rápida
        - **🟡 1.0-3.0s**: Normal - Tiempo de respuesta aceptable  
        - **🔴 > 3.0s**: Lento - Puede indicar problemas de conectividad
        - **Error**: El servicio no respondió o falló la conexión
        
        ### �🚨 Recomendaciones de Contingencia
        
        El sistema puede sugerir automáticamente el tipo de contingencia apropiado 
        basándose en el patrón de errores detectados.
        """)
        
        # Agregar información técnica adicional
        with st.expander("🔧 Información Técnica"):
            st.markdown("""
            ### 📈 Métricas de Rendimiento
            
            - **Caché TTL**: 30 segundos para optimizar rendimiento
            - **Timeout**: 10 segundos por servicio
            - **Servicios monitoreados**: 4 servicios principales del SIAT
            - **Historial**: Se mantienen los últimos 50 registros
            
            ### 🔍 Servicios Verificados
            
            1. **Verificación Principal**: Usando `soap_services.py`
            2. **Facturación Códigos**: Sincronización de catálogos
            3. **Facturación Operaciones**: CUFD, CUIS y operaciones
            4. **Facturación Sincronización**: Sincronización de tiempo
            """)
                # Footer con información del sistema
    st.markdown("---")
    st.caption("""
    🔗 **Sistema Centralizado**: Esta página utiliza el `CommunicationManager` 
    para verificaciones optimizadas y consistentes en toda la aplicación.
    """)

if __name__ == "__main__":
    main()
