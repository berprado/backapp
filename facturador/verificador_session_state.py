#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificador de integridad del session_state
"""
import streamlit as st
import os
import sys
import threading
import glob
import time
from typing import Dict, Any, List
from datetime import datetime

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verificar_estructura_session_state() -> Dict[str, Any]:
    """
    Verifica la estructura e integridad del session_state

    Returns:
        dict: Reporte de verificación
    """
    reporte = {
        'timestamp': datetime.now().isoformat(),
        'claves_encontradas': [],
        'claves_faltantes': [],
        'tipos_incorrectos': [],
        'datos_corruptos': [],
        'estructura_valida': True,
        'recomendaciones': []
    }
    
    # Claves esperadas y sus tipos
    claves_obligatorias = {
        'factura_validada': bool,
        'impresion_en_progreso': bool,
        'impresion_finalizada': bool,
        'print_status': (str, type(None)),
        'print_status_info': (dict, type(None)),
        'printer_worker_status': (str, type(None)),
        'printer_worker_last_heartbeat': (float, type(None)),
        'ultimo_trabajo_impresion': (dict, type(None)),
        'auto_print_last_id': (str, type(None)),
    }

    claves_opcionales = {
        'factura_a_procesar': object,
        'datos_impresion': dict,
        'cuf': (str, type(None)),
        'ultima_factura': (str, int, type(None)),
        'processed_comandas': (list, set, type(None)),
    }
    
    print("🔍 VERIFICACIÓN DE SESSION_STATE")
    print("=" * 50)
    
    # Verificar claves existentes
    for clave in st.session_state.keys():
        reporte['claves_encontradas'].append(clave)
        valor = st.session_state[clave]
        # Mostrar cada clave encontrada con un ícono de verificación
        print(f"✅ {clave}: {type(valor).__name__} = {valor}")
    
    print(f"\n📋 Total de claves en session_state: {len(st.session_state.keys())}")
    
    # Verificar claves esperadas
    print("\n🎯 VERIFICACIÓN DE CLAVES CRÍTICAS")
    print("-" * 30)
    
    for clave, tipo_esperado in claves_obligatorias.items():
        if clave in st.session_state:
            valor = st.session_state[clave]
            if isinstance(tipo_esperado, tuple):
                tipo_correcto = any(isinstance(valor, t) for t in tipo_esperado)
            else:
                tipo_correcto = isinstance(valor, tipo_esperado)

            if tipo_correcto:
                print(f"OK {clave}: tipo {type(valor).__name__}")
            else:
                print(f"ERROR {clave}: Tipo incorrecto. Esperado {tipo_esperado}, encontrado {type(valor)}")
                reporte['tipos_incorrectos'].append({
                    'clave': clave,
                    'tipo_esperado': str(tipo_esperado),
                    'tipo_encontrado': type(valor).__name__,
                    'valor': str(valor)
                })
                reporte['estructura_valida'] = False
        else:
            print(f"FALTA {clave}: NO ENCONTRADA")
            reporte['claves_faltantes'].append(clave)
            reporte['estructura_valida'] = False

    for clave, tipo_esperado in claves_opcionales.items():
        if clave in st.session_state:
            valor = st.session_state[clave]
            if tipo_esperado is object:
                continue
            if isinstance(tipo_esperado, tuple):
                tipo_correcto = any(isinstance(valor, t) for t in tipo_esperado)
            else:
                tipo_correcto = isinstance(valor, tipo_esperado)

            if tipo_correcto:
                print(f"OK {clave}: tipo {type(valor).__name__}")
            else:
                print(f"WARN {clave}: Tipo inesperado. Esperado {tipo_esperado}, encontrado {type(valor)}")
                reporte['tipos_incorrectos'].append({
                    'clave': clave,
                    'tipo_esperado': str(tipo_esperado),
                    'tipo_encontrado': type(valor).__name__,
                    'valor': str(valor)
                })
                reporte['recomendaciones'].append(f"Revisar la clave opcional {clave}, tipo inesperado.")
        else:
            print(f"INFO {clave}: No presente (opcional)")

    # Verificación específica de datos_impresion
    if 'datos_impresion' in st.session_state:
        print("\n🧾 VERIFICACIÓN DE DATOS_IMPRESION")
        print("-" * 35)
        
        datos = st.session_state['datos_impresion']
        campos_esperados = [
            'subtotal', 'descuento_adicional', 'monto_giftcard',
            'lineas_productos', 'nombre_cliente', 'fecha_emision_str',
            'seleccion_metodo_pago', 'codigo_clasificador_metodo_pago',
            'seleccion_tipo_documento', 'codigo_clasificador_documento',
            'numero_documento', 'complemento', 'email', 'telefono'
        ]
        
        if isinstance(datos, dict):
            for campo in campos_esperados:
                if campo in datos:
                        print(f"✅ {campo}: {type(datos[campo]).__name__}")
                else:
                        print(f"⚠️ {campo}: FALTANTE")
                    
            # Verificar lineas_productos si existe
            if 'lineas_productos' in datos and datos['lineas_productos']:
                print(f"📦 Productos: {len(datos['lineas_productos'])} elementos")
                if datos['lineas_productos']:
                    primer_producto = datos['lineas_productos'][0]
                    campos_producto = ['codigo', 'nombre', 'precio', 'cantidad', 'sub_total']
                    for campo in campos_producto:
                        estado = "✅" if campo in primer_producto else "❌"
                        print(f"  {estado} {campo}")
        else:
            print("❌ datos_impresion no es un diccionario")
            reporte['datos_corruptos'].append('datos_impresion')
            reporte['estructura_valida'] = False
    
    # Verificación de estados de impresión
    print("\n🖨️ VERIFICACIÓN DE ESTADOS DE IMPRESIÓN")
    print("-" * 40)
    
    estados_impresion = {
        'factura_validada': st.session_state.get('factura_validada', False),
        'impresion_en_progreso': st.session_state.get('impresion_en_progreso', False),
        'impresion_finalizada': st.session_state.get('impresion_finalizada', False)
    }
    
    for estado, valor in estados_impresion.items():
        icono = "✅" if valor else "❌"
        print(f"{icono} {estado}: {valor}")
    
    # Lógica de estados
    if estados_impresion['factura_validada']:
        print("🎯 FACTURA VALIDADA - Sistema listo para imprimir")
        if estados_impresion['impresion_en_progreso']:
            print("🔄 IMPRESIÓN EN PROGRESO - Bloqueando nuevas impresiones")
        elif estados_impresion['impresion_finalizada']:
            print("✅ IMPRESIÓN FINALIZADA - Proceso completado")
        else:
            print("⏳ ESPERANDO ACCIÓN - Lista para iniciar impresión")
    else:
        print("🚫 FACTURA NO VALIDADA - Impresión no disponible")
    
    # Generar recomendaciones
    if reporte['claves_faltantes']:
        reporte['recomendaciones'].append("Inicializar claves faltantes usando initialize_print_state()")
    
    if reporte['tipos_incorrectos']:
        reporte['recomendaciones'].append("Corregir tipos de datos incorrectos")
    
    if reporte['datos_corruptos']:
        reporte['recomendaciones'].append("Reinicializar datos corruptos usando reiniciar_estados()")
    
    # Resumen final
    print("\n" + "=" * 50)
    if reporte['estructura_valida']:
        print("🎉 ESTRUCTURA VÁLIDA - Session state correctamente configurado")
    else:
        print("⚠️ PROBLEMAS DETECTADOS - Revisar recomendaciones")
        for rec in reporte['recomendaciones']:
            print(f"💡 {rec}")
    
    return reporte

def mostrar_debug_session_state(prefix_key="debug"):
    """
    Muestra información de debug del session_state en la interfaz
    """
    st.subheader("🔍 Debug del Session State")
    
    reporte = verificar_estructura_session_state()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Estados Críticos:**")
        estados = {
            'factura_validada': st.session_state.get('factura_validada', 'NO DEFINIDO'),
            'impresion_en_progreso': st.session_state.get('impresion_en_progreso', 'NO DEFINIDO'),
            'impresion_finalizada': st.session_state.get('impresion_finalizada', 'NO DEFINIDO'),
            'print_status': st.session_state.get('print_status', 'NO DEFINIDO')
        }
        
        for key, value in estados.items():
            if value == 'NO DEFINIDO':
                st.warning(f"⚠️ {key}: {value}")
            elif isinstance(value, bool) and value:
                st.success(f"✅ {key}: {value}")
            else:
                st.info(f"ℹ️ {key}: {value}")
    
    with col2:
        st.write("**Datos de Facturación:**")
        datos = st.session_state.get('datos_impresion', {})
        if datos:
            st.success(f"✅ datos_impresion: {len(datos)} campos")
            
            campos_importantes = ['nombre_cliente', 'subtotal', 'lineas_productos']
            for campo in campos_importantes:
                if campo in datos:
                    if campo == 'lineas_productos':
                        st.write(f"  - {campo}: {len(datos[campo])} productos")
                    else:
                        st.write(f"  - {campo}: {datos[campo]}")
                else:
                    st.warning(f"⚠️ {campo}: FALTANTE")
        else:
            st.warning("⚠️ datos_impresion: Vacío")
        
        # Mostrar CUF y número de factura
        cuf = st.session_state.get('cuf', 'NO DEFINIDO')
        ultima_factura = st.session_state.get('ultima_factura', 'NO DEFINIDO')
        
        st.write(f"**CUF**: {cuf}")
        st.write(f"**Última Factura**: {ultima_factura}")
    
    # Mostrar recomendaciones si hay problemas
    if not reporte['estructura_valida']:
        st.error("⚠️ Problemas detectados en session_state")
        for rec in reporte['recomendaciones']:
                st.warning(f"💡 {rec}")
    else:
        st.success("✅ Session state en estado óptimo")
    
    # Opción para limpiar estados
    if st.button("🧹 Limpiar Session State", key=f"{prefix_key}_limpiar_session_state_debug"):
        from print_manager import reiniciar_estados
        reiniciar_estados()
        st.success("✅ Session state limpiado")
        st.rerun()

def diagnosticar_estado_fantasma(prefix_key="tab"):
    """
    Diagnostica si hay un proceso fantasma bloqueando la impresión
    """
    st.subheader("👻 Diagnóstico de Proceso Fantasma")
    
    # Verificar el estado actual
    impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)
    impresion_finalizada = st.session_state.get('impresion_finalizada', False)
    print_status = st.session_state.get('print_status', 'No definido')
    status_info = st.session_state.get('print_status_info') or {}
    ultima_factura = st.session_state.get('ultima_factura', 'No definida')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Estado Actual:**")
        st.write(f"- impresion_en_progreso: `{impresion_en_progreso}`")
        st.write(f"- impresion_finalizada: `{impresion_finalizada}`")
        st.write(f"- print_status: `{print_status}`")
        if status_info:
            st.write(f"- status_code: `{status_info.get('code', 'N/D')}` ({status_info.get('severity', 'N/D')})")
            if status_info.get('message') and status_info.get('message') != print_status:
                st.caption(f"Mensaje estructurado: {status_info.get('message')}")
        st.write(f"- ultima_factura: `{ultima_factura}`")
    
    with col2:
        st.write("**Diagnóstico:**")
        if impresion_en_progreso and not impresion_finalizada:
            st.error("🚨 PROCESO FANTASMA DETECTADO")
            st.write("Hay un proceso marcado como 'en progreso' que nunca finalizó")
            
            # Mostrar tiempo transcurrido si hay timestamp
            timestamp_inicio = st.session_state.get('timestamp_impresion_inicio')
            if timestamp_inicio:
                tiempo_transcurrido = datetime.now() - datetime.fromisoformat(timestamp_inicio)
                st.write(f"⏱️ Tiempo transcurrido: {tiempo_transcurrido}")
            
        elif impresion_en_progreso and impresion_finalizada:
            st.warning("⚠️ ESTADO INCONSISTENTE")
            st.write("Proceso marcado como en progreso Y finalizado")
        elif not impresion_en_progreso and impresion_finalizada:
            st.info("ℹ️ IMPRESIÓN ANTERIOR COMPLETADA")
            st.write("Listo para nueva impresión")
        else:
            st.success("✅ Estado normal")
    
    # Verificar archivos relacionados con la última factura
    if ultima_factura and ultima_factura != 'No definida':
        st.write("**Verificación de Archivos:**")
        
        # Buscar archivos HTML
        html_pattern = f"debug/*{ultima_factura}*.html"
        html_files = glob.glob(html_pattern)
        
        # Buscar archivos PDF  
        pdf_pattern = f"pdfs/*{ultima_factura}*.pdf"
        pdf_files = glob.glob(pdf_pattern)
        
        # Buscar archivos de señal
        signal_pattern = f"debug/*{ultima_factura}*.signal"
        signal_files = glob.glob(signal_pattern)
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            if html_files:
                st.success(f"✅ HTML: {len(html_files)}")
                for f in html_files[-2:]:  # Últimos 2
                    st.text(f"  {os.path.basename(f)}")
            else:
                st.error("❌ No hay archivos HTML")
        
        with col4:
            if pdf_files:
                st.success(f"✅ PDF: {len(pdf_files)}")
                for f in pdf_files[-2:]:  # Últimos 2
                    st.text(f"  {os.path.basename(f)}")
            else:
                st.error("❌ No hay archivos PDF")
        
        with col5:
            if signal_files:
                st.success(f"✅ Señales: {len(signal_files)}")
                for f in signal_files[-2:]:  # Últimos 2
                    st.text(f"  {os.path.basename(f)}")
            else:
                st.warning("⚠️ No hay archivos de señal")
    
    # Botones de acción
    st.write("**Acciones de Diagnóstico:**")
    col6, col7, col8 = st.columns(3)
    
    with col6:
        if st.button("🛠️ Forzar Limpieza de Estado", key=f"{prefix_key}_forzar_limpieza_estado_fantasma"):
            # Limpiar con timestamp
            st.session_state['impresion_en_progreso'] = False
            st.session_state['impresion_finalizada'] = False
            st.session_state['print_status'] = f"🧹 Estado limpiado manualmente a las {datetime.now().strftime('%H:%M:%S')}"
            
            # Remover timestamps si existen
            if 'timestamp_impresion_inicio' in st.session_state:
                del st.session_state['timestamp_impresion_inicio']
            
            st.success("✅ Estado limpiado forzosamente")
            st.rerun()
    
    with col7:
        if st.button("🧵 Verificar Hilos", key=f"{prefix_key}_verificar_hilos_fantasma"):
            # Mostrar información de hilos
            hilos_activos = threading.active_count()
            hilos = threading.enumerate()
            
            st.write(f"**Hilos activos:** {hilos_activos}")
            for hilo in hilos:
                # Muestra cada hilo con un indicador verde si está vivo o rojo si está muerto
                estado = "🟢" if hilo.is_alive() else "🔴"
                st.text(f"{estado} {hilo.name} (daemon: {hilo.daemon})")
    
    with col8:
        if st.button("📜 Ver Logs Recientes", key=f"{prefix_key}_ver_logs_fantasma"):
            # Mostrar logs recientes
            try:
                log_file = "logs/printer_20250703.log"
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        st.text_area("Últimos logs:", 
                                   "".join(lines[-10:]), 
                                   height=200,
                                   key=f"{prefix_key}_logs_recientes_fantasma")
                else:
                    st.warning("❌ No se encontró el archivo de logs")
            except Exception as e:
                st.error(f"Error leyendo logs: {e}")

def verificar_hilos_activos(prefix_key="verificar_hilos"):
    """
    Verifica hilos de Python activos y detecta hilos de impresión colgados
    """
    st.subheader("🧵 Verificación de Hilos Activos")
    
    hilos = threading.enumerate()
    total_hilos = len(hilos)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total de hilos activos", total_hilos)
        
        # Categorizar hilos
        hilos_impresion = [h for h in hilos if 'print' in h.name.lower()]
        hilos_daemon = [h for h in hilos if h.daemon]
        hilos_normales = [h for h in hilos if h not in hilos_impresion and not h.daemon]
        
        st.write("**Categorización:**")
        st.write(f"- 🟢 Normales: {len(hilos_normales)}")
        st.write(f"- 🖨️ Impresión: {len(hilos_impresion)}")
        st.write(f"- 👻 Daemon: {len(hilos_daemon)}")
    
    with col2:
        st.write("**Diagnóstico:**")
        if len(hilos_impresion) > 0:
            st.error(f"🚨 {len(hilos_impresion)} hilo(s) de impresión detectado(s)")
            st.write("Esto puede indicar un proceso de impresión que no terminó")
        elif total_hilos > 5:
            st.warning(f"⚠️ Muchos hilos activos ({total_hilos})")
        else:
            st.success("✅ Estado normal de hilos")

def verificar_archivos_senal(prefix_key="verificar_archivos"):
    """
    Verifica archivos de señalización que podrían estar causando problemas
    """
    st.subheader("📁 Verificación de Archivos de Señal")
    
    # Buscar archivos de señal
    signal_files = glob.glob("debug/*.signal")
    
    if signal_files:
        st.warning(f"⚠️ {len(signal_files)} archivo(s) de señal encontrado(s)")
        
        for archivo in signal_files:
            nombre = os.path.basename(archivo)
            st.write(f"- {nombre}")
        
        if st.button("🧹 Limpiar Archivos de Señal", key=f"{prefix_key}_limpiar_archivos_senal"):
            eliminados = 0
            for archivo in signal_files:
                try:
                    os.remove(archivo)
                    eliminados += 1
                except Exception as e:
                    st.error(f"Error eliminando {archivo}: {e}")
            
            if eliminados > 0:
                st.success(f"✅ {eliminados} archivo(s) eliminado(s)")
                st.rerun()
    else:
        st.success("✅ No hay archivos de señal pendientes")

def verificar_recargas_streamlit(prefix_key="verificar_recargas"):
    """
    Verifica si hay problemas con recargas de Streamlit
    """
    st.subheader("🔄 Verificación de Recargas de Streamlit")
    
    # Contador de sesión para detectar recargas
    if 'session_counter' not in st.session_state:
        st.session_state['session_counter'] = 0
        st.session_state['primera_carga'] = datetime.now().isoformat()
    
    st.session_state['session_counter'] += 1
    st.session_state['ultima_recarga'] = datetime.now().isoformat()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Contador de sesión", st.session_state['session_counter'])
        
        primera_carga = datetime.fromisoformat(st.session_state['primera_carga'])
        st.write(f"**Primera carga:** {primera_carga.strftime('%H:%M:%S')}")
        
        if st.session_state['session_counter'] > 1:
            # Mostrar la hora de la última recarga
            ultima_recarga = datetime.fromisoformat(st.session_state['ultima_recarga'])
            st.write(f"**Última recarga:** {ultima_recarga.strftime('%H:%M:%S')}")

            # Calcular y mostrar el tiempo total de la sesión
            tiempo_sesion = ultima_recarga - primera_carga
            st.write(f"**Tiempo de sesión:** {tiempo_sesion}")
    
    with col2:
        st.write("**Diagnóstico de Persistencia:**")
        
        # Verificar si estados críticos persisten entre recargas
        if st.session_state['session_counter'] > 1:
            impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)

            if impresion_en_progreso:
                st.error("🚨 PROBLEMA DETECTADO")
                st.write("El estado 'impresion_en_progreso' persiste entre recargas")
                st.write("Esto indica que el estado no se limpia correctamente")
            else:
                st.success("✅ Estado se limpia correctamente")
        else:
            st.info("ℹ️ Primera carga de la sesión")
    
    # Botón para simular recarga
    if st.button("🔄 Simular Recarga", key=f"{prefix_key}_simular_recarga_streamlit"):
        st.rerun()
    
    # Información adicional
    st.write("**Información de la Sesión:**")
    st.write(f"- ID de sesión: `{id(st.session_state)}`")
    st.write(f"- Claves en session_state: {len(st.session_state.keys())}")

def ejecutar_diagnostico_completo(prefix_key="tab"):
    """
    Ejecuta todos los verificadores en una interfaz organizada

    Args:
        prefix_key: Prefijo para las claves de los elementos UI para evitar duplicados
    """
    st.title("🔍 Diagnóstico Completo del Sistema de Impresión")
    st.write("Este panel ejecuta todos los verificadores para encontrar la causa del bloqueo de impresión.")
    
    # Menú de tabs para organizar los verificadores
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👻 Estado Fantasma",
        "🧵 Hilos",
        "📁 Archivos Señal",
        "🔄 Recargas",
        "📊 Resumen"
    ])
    
    with tab1:
        diagnosticar_estado_fantasma(prefix_key)
    
    with tab2:
        verificar_hilos_activos(prefix_key)
    
    with tab3:
        verificar_archivos_senal(prefix_key)
    
    with tab4:
        verificar_recargas_streamlit(prefix_key)
    
    with tab5:
        mostrar_resumen_diagnostico(prefix_key)

def mostrar_resumen_diagnostico(prefix_key="resumen"):
    """
    Muestra un resumen de todos los diagnósticos
    """
    # Encabezado del resumen con ícono
    st.subheader("📊 Resumen del Diagnóstico")

    impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)
    impresion_finalizada = st.session_state.get('impresion_finalizada', False)
    worker_status = st.session_state.get('printer_worker_status', 'desconocido')
    worker_heartbeat = st.session_state.get('printer_worker_last_heartbeat')
    ultimo_trabajo = st.session_state.get('ultimo_trabajo_impresion')

    hilos_total = threading.active_count()
    hilos_impresion = [h for h in threading.enumerate() if 'print' in h.name.lower()]
    signal_files = glob.glob('debug/*.signal')
    session_counter = st.session_state.get('session_counter', 1)

    nivel_alerta = 'normal'
    mensaje_estado = 'Sistema de impresion sin alertas'

    col1, col2 = st.columns(2)
    problemas_detectados = []
    status_info = st.session_state.get('print_status_info') or {}
    status_severity = (status_info.get('severity') or '').lower()
    if status_severity == 'error':
        problemas_detectados.append('🚨 Estado de impresión en error')
        nivel_alerta = 'error'
        mensaje_estado = 'Estado de impresion con error'
    elif status_severity == 'warning':
        problemas_detectados.append('⚠️ Estado de impresión con advertencia')
        if nivel_alerta != 'error':
            nivel_alerta = 'warning'
            mensaje_estado = 'Estado de impresion con advertencia'

    if impresion_en_progreso and not impresion_finalizada:
        # Hay un proceso de impresión en curso
        problemas_detectados.append('🚨 Proceso de impresión en curso')
        if ultimo_trabajo and ultimo_trabajo.get('timestamp'):
            try:
                inicio = datetime.fromisoformat(ultimo_trabajo['timestamp']).timestamp()
                # Si lleva más de 180 segundos, se considera bloqueado
                if time.time() - inicio > 180:
                    problemas_detectados.append('🚨 Proceso de impresión bloqueado (>180s)')
            except Exception:
                pass

    if worker_status not in ('running', 'desconocido'):
        problemas_detectados.append(f'⚠️ Worker en estado {worker_status}')

    if worker_heartbeat:
        delay = time.time() - worker_heartbeat
        if delay > 120:
            problemas_detectados.append('🚨 Sin señal del worker (>120s)')
        elif delay > 60:
            problemas_detectados.append('⚠️ Señal del worker antigua (>60s)')

    if len(hilos_impresion) > 1:
        problemas_detectados.append(f'⚠️ {len(hilos_impresion)} hilos de impresión activos')

    if len(signal_files) > 5:
        problemas_detectados.append(f'⚠️ {len(signal_files)} archivos de señal acumulados')

    if session_counter > 1 and impresion_en_progreso:
        problemas_detectados.append('⚠️ Estado de impresión persiste entre recargas')

    with col1:
        st.write('**Estado General:**')
        if problemas_detectados:
            # Mostrar cada problema detectado
            st.error('🚨 Problemas detectados:')
            for problema in problemas_detectados:
                st.write(f'  - {problema}')
        else:
            st.success('✅ No se detectaron problemas obvios')

    with col2:
        st.write('**Métricas del Sistema:**')
        st.metric('Hilos activos', hilos_total)
        st.metric('Hilos de impresión', len(hilos_impresion))
        st.metric('Archivos de senal', len(signal_files))
        st.metric('Recargas de sesion', session_counter)
        st.metric('Estado impresion', status_info.get('code', 'N/D'))
        st.metric('Nivel alerta', nivel_alerta.upper())
        if mensaje_estado:
            st.caption(f'Resumen estado: {mensaje_estado}')
        if status_info.get('message'):
            st.caption('Mensaje estado: {}'.format(status_info.get('message')))
        st.metric('Estado worker', worker_status)
        if worker_heartbeat:
            try:
                last_seen = datetime.fromtimestamp(worker_heartbeat).strftime('%H:%M:%S')
            except Exception:
                last_seen = 'N/D'
            st.metric('Último heartbeat', last_seen)
        else:
            st.metric('Último heartbeat', 'Sin datos')
        if ultimo_trabajo:
            st.metric('Último trabajo', ultimo_trabajo.get('numero_factura', 'N/D'))

    st.write('**Recomendaciones:**')

    if impresion_en_progreso and not impresion_finalizada:
        st.error('🚨 **ACCIÓN PRINCIPAL:** Usar "Forzar Limpieza de Estado" en la pestaña "Estado Fantasma"')

    if worker_status == 'stopped':
        st.error('🚨 **ACCIÓN PRIORITARIA:** Reiniciar el servicio de impresión.')
    elif worker_status not in ('running', 'desconocido'):
        st.warning('⚠️ **REVISIÓN:** Verificar logs del servicio de impresión.')

    if len(hilos_impresion) > 1:
        st.warning('⚠️ **ACCIÓN SECUNDARIA:** Reiniciar la aplicación Streamlit')

    if len(signal_files) > 5:
        st.info('ℹ️ **ACCIÓN OPCIONAL:** Limpiar archivos de señal en la pestaña "Archivos Señal"')

    if not problemas_detectados:
        st.success(f'Estado optimo: {mensaje_estado}')
