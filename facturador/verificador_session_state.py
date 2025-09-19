#!/usr/bin/env python
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

# AÃƒÂ±adir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verificar_estructura_session_state() -> Dict[str, Any]:
    """
    Verifica la estructura e integridad del session_state
    
    Returns:
        dict: Reporte de verificaciÃƒÂ³n
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
    claves_esperadas = {
        'factura_validada': bool,
        'impresion_en_progreso': bool,
        'impresion_finalizada': bool,
        'print_status': (str, type(None)),
        'datos_impresion': dict,
        'cuf': (str, type(None)),
        'ultima_factura': (str, int, type(None)),
        'processed_comandas': (list, set, type(None)),
        'printer_worker_status': (str, type(None)),
        'printer_worker_last_heartbeat': (float, type(None)),
        'ultimo_trabajo_impresion': (dict, type(None)),
        'auto_print_enabled': (bool, type(None)),
        'auto_print_last_id': (str, type(None))
    }
    
    print("Ã°Å¸â€Â VERIFICACIÃƒâ€œN DE SESSION_STATE")
    print("=" * 50)
    
    # Verificar claves existentes
    for clave in st.session_state.keys():
        reporte['claves_encontradas'].append(clave)
        valor = st.session_state[clave]
        print(f"Ã¢Å“â€¦ {clave}: {type(valor).__name__} = {valor}")
    
    print(f"\nÃ°Å¸â€œÅ  Total de claves en session_state: {len(st.session_state.keys())}")
    
    # Verificar claves esperadas
    print("\nÃ°Å¸Å½Â¯ VERIFICACIÃƒâ€œN DE CLAVES CRÃƒÂTICAS")
    print("-" * 30)
    
    for clave, tipo_esperado in claves_esperadas.items():
        if clave in st.session_state:
            valor = st.session_state[clave]
            if isinstance(tipo_esperado, tuple):
                tipo_correcto = any(isinstance(valor, t) for t in tipo_esperado)
            else:
                tipo_correcto = isinstance(valor, tipo_esperado)
            
            if tipo_correcto:
                print(f"Ã¢Å“â€¦ {clave}: OK ({type(valor).__name__})")
            else:
                print(f"Ã¢ÂÅ’ {clave}: Tipo incorrecto. Esperado {tipo_esperado}, encontrado {type(valor)}")
                reporte['tipos_incorrectos'].append({
                    'clave': clave,
                    'tipo_esperado': str(tipo_esperado),
                    'tipo_encontrado': type(valor).__name__,
                    'valor': str(valor)
                })
                reporte['estructura_valida'] = False
        else:
            print(f"Ã¢Å¡Â Ã¯Â¸Â {clave}: NO ENCONTRADA")
            reporte['claves_faltantes'].append(clave)
    
    # VerificaciÃƒÂ³n especÃƒÂ­fica de datos_impresion
    if 'datos_impresion' in st.session_state:
        print("\nÃ°Å¸â€œâ€¹ VERIFICACIÃƒâ€œN DE DATOS_IMPRESION")
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
                    print(f"Ã¢Å“â€¦ {campo}: {type(datos[campo]).__name__}")
                else:
                    print(f"Ã¢Å¡Â Ã¯Â¸Â {campo}: FALTANTE")
                    
            # Verificar lineas_productos si existe
            if 'lineas_productos' in datos and datos['lineas_productos']:
                print(f"Ã°Å¸â€œÂ¦ Productos: {len(datos['lineas_productos'])} elementos")
                if datos['lineas_productos']:
                    primer_producto = datos['lineas_productos'][0]
                    campos_producto = ['codigo', 'nombre', 'precio', 'cantidad', 'sub_total']
                    for campo in campos_producto:
                        estado = "Ã¢Å“â€¦" if campo in primer_producto else "Ã¢ÂÅ’"
                        print(f"  {estado} {campo}")
        else:
            print("Ã¢ÂÅ’ datos_impresion no es un diccionario")
            reporte['datos_corruptos'].append('datos_impresion')
            reporte['estructura_valida'] = False
    
    # VerificaciÃƒÂ³n de estados de impresiÃƒÂ³n
    print("\nÃ°Å¸â€“Â¨Ã¯Â¸Â VERIFICACIÃƒâ€œN DE ESTADOS DE IMPRESIÃƒâ€œN")
    print("-" * 40)
    
    estados_impresion = {
        'factura_validada': st.session_state.get('factura_validada', False),
        'impresion_en_progreso': st.session_state.get('impresion_en_progreso', False),
        'impresion_finalizada': st.session_state.get('impresion_finalizada', False)
    }
    
    for estado, valor in estados_impresion.items():
        icono = "Ã¢Å“â€¦" if valor else "Ã¢Â­â€¢"
        print(f"{icono} {estado}: {valor}")
    
    # LÃƒÂ³gica de estados
    if estados_impresion['factura_validada']:
        print("Ã°Å¸Å½Â¯ FACTURA VALIDADA - Sistema listo para imprimir")
        if estados_impresion['impresion_en_progreso']:
            print("Ã°Å¸â€â€ž IMPRESIÃƒâ€œN EN PROGRESO - Bloqueando nuevas impresiones")
        elif estados_impresion['impresion_finalizada']:
            print("Ã¢Å“â€¦ IMPRESIÃƒâ€œN FINALIZADA - Proceso completado")
        else:
            print("Ã¢ÂÂ³ ESPERANDO ACCIÃƒâ€œN - Lista para iniciar impresiÃƒÂ³n")
    else:
        print("Ã°Å¸Å¡Â« FACTURA NO VALIDADA - ImpresiÃƒÂ³n no disponible")
    
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
        print("Ã°Å¸Å½â€° ESTRUCTURA VÃƒÂLIDA - Session state correctamente configurado")
    else:
        print("Ã¢Å¡Â Ã¯Â¸Â PROBLEMAS DETECTADOS - Revisar recomendaciones")
        for rec in reporte['recomendaciones']:
            print(f"Ã°Å¸â€™Â¡ {rec}")
    
    return reporte

def mostrar_debug_session_state(prefix_key="debug"):
    """
    Muestra informaciÃƒÂ³n de debug del session_state en la interfaz
    """
    st.subheader("Ã°Å¸â€Â Debug del Session State")
    
    reporte = verificar_estructura_session_state()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Estados CrÃƒÂ­ticos:**")
        estados = {
            'factura_validada': st.session_state.get('factura_validada', 'NO DEFINIDO'),
            'impresion_en_progreso': st.session_state.get('impresion_en_progreso', 'NO DEFINIDO'),
            'impresion_finalizada': st.session_state.get('impresion_finalizada', 'NO DEFINIDO'),
            'print_status': st.session_state.get('print_status', 'NO DEFINIDO')
        }
        
        for key, value in estados.items():
            if value == 'NO DEFINIDO':
                st.warning(f"Ã¢Å¡Â Ã¯Â¸Â {key}: {value}")
            elif isinstance(value, bool) and value:
                st.success(f"Ã¢Å“â€¦ {key}: {value}")
            else:
                st.info(f"Ã¢â€žÂ¹Ã¯Â¸Â {key}: {value}")
    
    with col2:
        st.write("**Datos de FacturaciÃƒÂ³n:**")
        datos = st.session_state.get('datos_impresion', {})
        if datos:
            st.success(f"Ã¢Å“â€¦ datos_impresion: {len(datos)} campos")
            
            campos_importantes = ['nombre_cliente', 'subtotal', 'lineas_productos']
            for campo in campos_importantes:
                if campo in datos:
                    if campo == 'lineas_productos':
                        st.write(f"  - {campo}: {len(datos[campo])} productos")
                    else:
                        st.write(f"  - {campo}: {datos[campo]}")
                else:
                    st.warning(f"Ã¢Å¡Â Ã¯Â¸Â {campo}: FALTANTE")
        else:
            st.warning("Ã¢Å¡Â Ã¯Â¸Â datos_impresion: VacÃƒÂ­o")
        
        # Mostrar CUF y nÃƒÂºmero de factura
        cuf = st.session_state.get('cuf', 'NO DEFINIDO')
        ultima_factura = st.session_state.get('ultima_factura', 'NO DEFINIDO')
        
        st.write(f"**CUF**: {cuf}")
        st.write(f"**ÃƒÅ¡ltima Factura**: {ultima_factura}")
    
    # Mostrar recomendaciones si hay problemas
    if not reporte['estructura_valida']:
        st.error("Ã¢Å¡Â Ã¯Â¸Â Problemas detectados en session_state")
        for rec in reporte['recomendaciones']:
            st.warning(f"Ã°Å¸â€™Â¡ {rec}")
    else:
        st.success("Ã¢Å“â€¦ Session state en estado ÃƒÂ³ptimo")
    
    # OpciÃƒÂ³n para limpiar estados
    if st.button("Ã°Å¸Â§Â¹ Limpiar Session State", key=f"{prefix_key}_limpiar_session_state_debug"):
        from print_manager import reiniciar_estados
        reiniciar_estados()
        st.success("Ã¢Å“â€¦ Session state limpiado")
        st.rerun()

def diagnosticar_estado_fantasma(prefix_key="tab"):
    """
    Diagnostica si hay un proceso fantasma bloqueando la impresiÃƒÂ³n
    """
    st.subheader("Ã°Å¸â€˜Â» DiagnÃƒÂ³stico de Proceso Fantasma")
    
    # Verificar el estado actual
    impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)
    impresion_finalizada = st.session_state.get('impresion_finalizada', False)
    print_status = st.session_state.get('print_status', 'No definido')
    ultima_factura = st.session_state.get('ultima_factura', 'No definida')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Estado Actual:**")
        st.write(f"- impresion_en_progreso: `{impresion_en_progreso}`")
        st.write(f"- impresion_finalizada: `{impresion_finalizada}`")
        st.write(f"- print_status: `{print_status}`")
        st.write(f"- ultima_factura: `{ultima_factura}`")
    
    with col2:
        st.write("**DiagnÃƒÂ³stico:**")
        if impresion_en_progreso and not impresion_finalizada:
            st.error("Ã°Å¸Å¡Â¨ PROCESO FANTASMA DETECTADO")
            st.write("Hay un proceso marcado como 'en progreso' que nunca finalizÃƒÂ³")
            
            # Mostrar tiempo transcurrido si hay timestamp
            timestamp_inicio = st.session_state.get('timestamp_impresion_inicio')
            if timestamp_inicio:
                tiempo_transcurrido = datetime.now() - datetime.fromisoformat(timestamp_inicio)
                st.write(f"Ã¢ÂÂ±Ã¯Â¸Â Tiempo transcurrido: {tiempo_transcurrido}")
            
        elif impresion_en_progreso and impresion_finalizada:
            st.warning("Ã¢Å¡Â Ã¯Â¸Â ESTADO INCONSISTENTE")
            st.write("Proceso marcado como en progreso Y finalizado")
        elif not impresion_en_progreso and impresion_finalizada:
            st.info("Ã¢â€žÂ¹Ã¯Â¸Â IMPRESIÃƒâ€œN ANTERIOR COMPLETADA")
            st.write("Listo para nueva impresiÃƒÂ³n")
        else:
            st.success("Ã¢Å“â€¦ Estado normal")
    
    # Verificar archivos relacionados con la ÃƒÂºltima factura
    if ultima_factura and ultima_factura != 'No definida':
        st.write("**VerificaciÃƒÂ³n de Archivos:**")
        
        # Buscar archivos HTML
        html_pattern = f"debug/*{ultima_factura}*.html"
        html_files = glob.glob(html_pattern)
        
        # Buscar archivos PDF  
        pdf_pattern = f"pdfs/*{ultima_factura}*.pdf"
        pdf_files = glob.glob(pdf_pattern)
        
        # Buscar archivos de seÃƒÂ±al
        signal_pattern = f"debug/*{ultima_factura}*.signal"
        signal_files = glob.glob(signal_pattern)
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            if html_files:
                st.success(f"Ã¢Å“â€¦ HTML: {len(html_files)}")
                for f in html_files[-2:]:  # ÃƒÅ¡ltimos 2
                    st.text(f"  {os.path.basename(f)}")
            else:
                st.error("Ã¢ÂÅ’ No hay archivos HTML")
        
        with col4:
            if pdf_files:
                st.success(f"Ã¢Å“â€¦ PDF: {len(pdf_files)}")
                for f in pdf_files[-2:]:  # ÃƒÅ¡ltimos 2
                    st.text(f"  {os.path.basename(f)}")
            else:
                st.error("Ã¢ÂÅ’ No hay archivos PDF")
        
        with col5:
            if signal_files:
                st.success(f"Ã¢Å“â€¦ SeÃƒÂ±ales: {len(signal_files)}")
                for f in signal_files[-2:]:  # ÃƒÅ¡ltimos 2
                    st.text(f"  {os.path.basename(f)}")
            else:
                st.warning("Ã¢Å¡Â Ã¯Â¸Â No hay archivos de seÃƒÂ±al")
    
    # Botones de acciÃƒÂ³n
    st.write("**Acciones de DiagnÃƒÂ³stico:**")
    col6, col7, col8 = st.columns(3)
    
    with col6:
        if st.button("Ã°Å¸â€Â§ Forzar Limpieza de Estado", key=f"{prefix_key}_forzar_limpieza_estado_fantasma"):
            # Limpiar con timestamp
            st.session_state['impresion_en_progreso'] = False
            st.session_state['impresion_finalizada'] = False
            st.session_state['print_status'] = f"Ã°Å¸Â§Â¹ Estado limpiado manualmente a las {datetime.now().strftime('%H:%M:%S')}"
            
            # Remover timestamps si existen
            if 'timestamp_impresion_inicio' in st.session_state:
                del st.session_state['timestamp_impresion_inicio']
            
            st.success("Ã¢Å“â€¦ Estado limpiado forzosamente")
            st.rerun()
    
    with col7:
        if st.button("Ã°Å¸â€œÅ  Verificar Hilos", key=f"{prefix_key}_verificar_hilos_fantasma"):
            # Mostrar informaciÃƒÂ³n de hilos
            hilos_activos = threading.active_count()
            hilos = threading.enumerate()
            
            st.write(f"**Hilos activos:** {hilos_activos}")
            for hilo in hilos:
                estado = "Ã°Å¸Å¸Â¢" if hilo.is_alive() else "Ã°Å¸â€Â´"
                st.text(f"{estado} {hilo.name} (daemon: {hilo.daemon})")
    
    with col8:
        if st.button("Ã°Å¸â€”â€šÃ¯Â¸Â Ver Logs Recientes", key=f"{prefix_key}_ver_logs_fantasma"):
            # Mostrar logs recientes
            try:
                log_file = "logs/printer_20250703.log"
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        st.text_area("ÃƒÅ¡ltimos logs:", 
                                   "".join(lines[-10:]), 
                                   height=200,
                                   key=f"{prefix_key}_logs_recientes_fantasma")
                else:
                    st.warning("Ã¢ÂÅ’ No se encontrÃƒÂ³ el archivo de logs")
            except Exception as e:
                st.error(f"Error leyendo logs: {e}")

def verificar_hilos_activos(prefix_key="verificar_hilos"):
    """
    Verifica hilos de Python activos y detecta hilos de impresiÃƒÂ³n colgados
    """
    st.subheader("Ã°Å¸Â§Âµ VerificaciÃƒÂ³n de Hilos Activos")
    
    hilos = threading.enumerate()
    total_hilos = len(hilos)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total de hilos activos", total_hilos)
        
        # Categorizar hilos
        hilos_impresion = [h for h in hilos if 'print' in h.name.lower()]
        hilos_daemon = [h for h in hilos if h.daemon]
        hilos_normales = [h for h in hilos if h not in hilos_impresion and not h.daemon]
        
        st.write("**CategorizaciÃƒÂ³n:**")
        st.write(f"- Ã°Å¸Å¸Â¢ Normales: {len(hilos_normales)}")
        st.write(f"- Ã°Å¸â€“Â¨Ã¯Â¸Â ImpresiÃƒÂ³n: {len(hilos_impresion)}")
        st.write(f"- Ã°Å¸â€˜Â» Daemon: {len(hilos_daemon)}")
    
    with col2:
        st.write("**DiagnÃƒÂ³stico:**")
        if len(hilos_impresion) > 0:
            st.error(f"Ã°Å¸Å¡Â¨ {len(hilos_impresion)} hilo(s) de impresiÃƒÂ³n detectado(s)")
            st.write("Esto puede indicar un proceso de impresiÃƒÂ³n que no terminÃƒÂ³")
        elif total_hilos > 5:
            st.warning(f"Ã¢Å¡Â Ã¯Â¸Â Muchos hilos activos ({total_hilos})")
        else:
            st.success("Ã¢Å“â€¦ Estado normal de hilos")

def verificar_archivos_senal(prefix_key="verificar_archivos"):
    """
    Verifica archivos de seÃƒÂ±alizaciÃƒÂ³n que podrÃƒÂ­an estar causando problemas
    """
    st.subheader("Ã°Å¸â€œÂ VerificaciÃƒÂ³n de Archivos de SeÃƒÂ±al")
    
    # Buscar archivos de seÃƒÂ±al
    signal_files = glob.glob("debug/*.signal")
    
    if signal_files:
        st.warning(f"Ã¢Å¡Â Ã¯Â¸Â {len(signal_files)} archivo(s) de seÃƒÂ±al encontrado(s)")
        
        for archivo in signal_files:
            nombre = os.path.basename(archivo)
            st.write(f"- {nombre}")
        
        if st.button("Ã°Å¸â€”â€˜Ã¯Â¸Â Limpiar Archivos de SeÃƒÂ±al", key=f"{prefix_key}_limpiar_archivos_senal"):
            eliminados = 0
            for archivo in signal_files:
                try:
                    os.remove(archivo)
                    eliminados += 1
                except Exception as e:
                    st.error(f"Error eliminando {archivo}: {e}")
            
            if eliminados > 0:
                st.success(f"Ã¢Å“â€¦ {eliminados} archivo(s) eliminado(s)")
                st.rerun()
    else:
        st.success("Ã¢Å“â€¦ No hay archivos de seÃƒÂ±al pendientes")

def verificar_recargas_streamlit(prefix_key="verificar_recargas"):
    """
    Verifica si hay problemas con recargas de Streamlit
    """
    st.subheader("Ã°Å¸â€â€ž VerificaciÃƒÂ³n de Recargas de Streamlit")
    
    # Contador de sesiÃƒÂ³n para detectar recargas
    if 'session_counter' not in st.session_state:
        st.session_state['session_counter'] = 0
        st.session_state['primera_carga'] = datetime.now().isoformat()
    
    st.session_state['session_counter'] += 1
    st.session_state['ultima_recarga'] = datetime.now().isoformat()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Contador de sesiÃƒÂ³n", st.session_state['session_counter'])
        
        primera_carga = datetime.fromisoformat(st.session_state['primera_carga'])
        st.write(f"**Primera carga:** {primera_carga.strftime('%H:%M:%S')}")
        
        if st.session_state['session_counter'] > 1:
            ultima_recarga = datetime.fromisoformat(st.session_state['ultima_recarga'])
            st.write(f"**ÃƒÅ¡ltima recarga:** {ultima_recarga.strftime('%H:%M:%S')}")
            
            tiempo_sesion = ultima_recarga - primera_carga
            st.write(f"**Tiempo de sesiÃƒÂ³n:** {tiempo_sesion}")
    
    with col2:
        st.write("**DiagnÃƒÂ³stico de Persistencia:**")
        
        # Verificar si estados crÃƒÂ­ticos persisten entre recargas
        if st.session_state['session_counter'] > 1:
            impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)
            
            if impresion_en_progreso:
                st.error("Ã°Å¸Å¡Â¨ PROBLEMA DETECTADO")
                st.write("El estado 'impresion_en_progreso' persiste entre recargas")
                st.write("Esto indica que el estado no se limpia correctamente")
            else:
                st.success("Ã¢Å“â€¦ Estado se limpia correctamente")
        else:
            st.info("Ã¢â€žÂ¹Ã¯Â¸Â Primera carga de la sesiÃƒÂ³n")
    
    # BotÃƒÂ³n para simular recarga
    if st.button("Ã°Å¸â€â€ž Simular Recarga", key=f"{prefix_key}_simular_recarga_streamlit"):
        st.rerun()
    
    # InformaciÃƒÂ³n adicional
    st.write("**InformaciÃƒÂ³n de la SesiÃƒÂ³n:**")
    st.write(f"- ID de sesiÃƒÂ³n: `{id(st.session_state)}`")
    st.write(f"- Claves en session_state: {len(st.session_state.keys())}")

def ejecutar_diagnostico_completo(prefix_key="tab"):
    """
    Ejecuta todos los verificadores en una interfaz organizada
    
    Args:
        prefix_key: Prefijo para las claves de los elementos UI para evitar duplicados
    """
    st.title("Ã°Å¸â€Â DiagnÃƒÂ³stico Completo del Sistema de ImpresiÃƒÂ³n")
    st.write("Este panel ejecuta todos los verificadores para encontrar la causa del bloqueo de impresiÃƒÂ³n.")
    
    # MenÃƒÂº de tabs para organizar los verificadores
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Ã°Å¸â€˜Â» Estado Fantasma", 
        "Ã°Å¸Â§Âµ Hilos", 
        "Ã°Å¸â€œÂ Archivos SeÃƒÂ±al", 
        "Ã°Å¸â€â€ž Recargas", 
        "Ã°Å¸â€œÅ  Resumen"
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
    Muestra un resumen de todos los diagnÃƒÂ³sticos
    """
    st.subheader("Ã°Å¸â€Å½ Resumen del DiagnÃƒÂ³stico")

    impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)
    impresion_finalizada = st.session_state.get('impresion_finalizada', False)
    worker_status = st.session_state.get('printer_worker_status', 'desconocido')
    worker_heartbeat = st.session_state.get('printer_worker_last_heartbeat')
    ultimo_trabajo = st.session_state.get('ultimo_trabajo_impresion')

    hilos_total = threading.active_count()
    hilos_impresion = [h for h in threading.enumerate() if 'print' in h.name.lower()]
    signal_files = glob.glob('debug/*.signal')
    session_counter = st.session_state.get('session_counter', 1)

    col1, col2 = st.columns(2)
    problemas_detectados = []

    if impresion_en_progreso and not impresion_finalizada:
        problemas_detectados.append('Ã°Å¸Å¡Â¨ Proceso de impresiÃƒÂ³n en curso')
        if ultimo_trabajo and ultimo_trabajo.get('timestamp'):
            try:
                inicio = datetime.fromisoformat(ultimo_trabajo['timestamp']).timestamp()
                if time.time() - inicio > 180:
                    problemas_detectados.append('Ã°Å¸Å¡Â¨ Proceso de impresiÃƒÂ³n bloqueado (>180s)')
            except Exception:
                pass

    if worker_status not in ('running', 'desconocido'):
        problemas_detectados.append(f'Ã¢Å¡Â Ã¯Â¸Â Worker en estado {worker_status}')

    if worker_heartbeat:
        delay = time.time() - worker_heartbeat
        if delay > 120:
            problemas_detectados.append('Ã°Å¸Å¡Â¨ Sin seÃƒÂ±al del worker (>120s)')
        elif delay > 60:
            problemas_detectados.append('Ã¢Å¡Â Ã¯Â¸Â SeÃƒÂ±al del worker antigua (>60s)')

    if len(hilos_impresion) > 1:
        problemas_detectados.append(f'Ã¢Å¡Â Ã¯Â¸Â {len(hilos_impresion)} hilos de impresiÃƒÂ³n activos')

    if len(signal_files) > 5:
        problemas_detectados.append(f'Ã¢Å¡Â Ã¯Â¸Â {len(signal_files)} archivos de seÃƒÂ±al acumulados')

    if session_counter > 1 and impresion_en_progreso:
        problemas_detectados.append('Ã¢Å¡Â Ã¯Â¸Â Estado de impresiÃƒÂ³n persiste entre recargas')

    with col1:
        st.write('**Estado General:**')
        if problemas_detectados:
            st.error('Ã¢Ââ€” Problemas detectados:')
            for problema in problemas_detectados:
                st.write(f'  - {problema}')
        else:
            st.success('Ã¢Å“â€¦ No se detectaron problemas obvios')

    with col2:
        st.write('**MÃƒÂ©tricas del Sistema:**')
        st.metric('Hilos activos', hilos_total)
        st.metric('Hilos de impresiÃƒÂ³n', len(hilos_impresion))
        st.metric('Archivos de seÃƒÂ±al', len(signal_files))
        st.metric('Recargas de sesiÃƒÂ³n', session_counter)
        st.metric('Estado worker', worker_status)
        if worker_heartbeat:
            try:
                last_seen = datetime.fromtimestamp(worker_heartbeat).strftime('%H:%M:%S')
            except Exception:
                last_seen = 'N/D'
            st.metric('ÃƒÅ¡ltimo heartbeat', last_seen)
        else:
            st.metric('ÃƒÅ¡ltimo heartbeat', 'Sin datos')
        if ultimo_trabajo:
            st.metric('ÃƒÅ¡ltimo trabajo', ultimo_trabajo.get('numero_factura', 'N/D'))

    st.write('**Recomendaciones:**')

    if impresion_en_progreso and not impresion_finalizada:
        st.error('Ã°Å¸Å¡Â¨ **ACCIÃƒâ€œN PRINCIPAL:** Usar "Forzar Limpieza de Estado" en la pestaÃƒÂ±a "Estado Fantasma"')

    if worker_status == 'stopped':
        st.error('Ã°Å¸Å¡Â¨ **ACCIÃƒâ€œN PRIORITARIA:** Reiniciar el servicio de impresiÃƒÂ³n.')
    elif worker_status not in ('running', 'desconocido'):
        st.warning('Ã¢Å¡Â Ã¯Â¸Â **REVISIÃƒâ€œN:** Verificar logs del servicio de impresiÃƒÂ³n.')

    if len(hilos_impresion) > 1:
        st.warning('Ã¢Å¡Â Ã¯Â¸Â **ACCIÃƒâ€œN SECUNDARIA:** Reiniciar la aplicaciÃƒÂ³n Streamlit')

    if len(signal_files) > 5:
        st.info('Ã¢â€žÂ¹Ã¯Â¸Â **ACCIÃƒâ€œN OPCIONAL:** Limpiar archivos de seÃƒÂ±al en la pestaÃƒÂ±a "Archivos SeÃƒÂ±al"')

    if not problemas_detectados:
        st.success('Ã¢Å“â€¦ **ESTADO Ãƒâ€œPTIMO:** El sistema deberÃƒÂ­a funcionar correctamente')
