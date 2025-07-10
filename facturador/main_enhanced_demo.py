"""
DEMOSTRACIÓN: Cómo podría mejorarse main.py manteniendo compatibilidad total.

Este archivo es SOLO una demostración de cómo se podría implementar una versión
mejorada de main.py usando el nuevo communication_manager, SIN modificar el
archivo main.py actual.

IMPORTANTE: Este archivo NO reemplaza main.py. Es solo una demostración opcional.
"""

import streamlit as st
from datetime import datetime
import os
import sys

# Asegurar que estamos importando desde el directorio correcto 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports del sistema (IGUALES que en main.py)
from database import get_eventos_parametricos, get_cufd_vigente, obtener_evento_abierto, insertar_evento_local
from ui_copy import main as online_main
from contingencia_auto import finalizar_evento_si_conectado

# Import para el debug del session_state
try:
    from verificador_session_state import mostrar_debug_session_state
except ImportError:
    def mostrar_debug_session_state():
        st.error("No se pudo importar el verificador de session_state")

# NUEVO: Import opcional del servicio mejorado
try:
    from communication_manager import communication_manager, EstadoComunicacion, TipoContingencia
    ENHANCED_SERVICE_AVAILABLE = True
except ImportError:
    # Fallback a la función original si no está disponible
    from soap_services import verificar_comunicacion
    ENHANCED_SERVICE_AVAILABLE = False

from logger_config import get_logger

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

# NUEVO: Intentar importar verificador de session_state
try:
    from verificador_session_state import mostrar_debug_session_state, verificar_estructura_session_state
except ImportError:
    def mostrar_debug_session_state():
        st.warning("⚠️ Verificador de session_state no disponible")
    def verificar_estructura_session_state():
        return {"estructura_valida": True}

def main_enhanced():
    """
    Versión MEJORADA de main() que usa el nuevo servicio cuando está disponible,
    pero mantiene TOTAL compatibilidad con la implementación original.
    """
    st.title("🧠 Sistema de Facturación BACKINVOICE")
    
    # PASO 1: Intentar finalizar eventos pendientes (IGUAL que original)
    if _intentar_finalizar_eventos_pendientes():
        st.success("✅ Se finalizó el evento pendiente y se procesaron las facturas.")
    
    # PASO 2: Verificar comunicación (MEJORADO si está disponible, ORIGINAL si no)
    if ENHANCED_SERVICE_AVAILABLE:
        _verificar_comunicacion_mejorada()
    else:
        _verificar_comunicacion_original()

def _intentar_finalizar_eventos_pendientes() -> bool:
    """
    Intenta finalizar eventos pendientes - IGUAL que en main.py original.
    """
    try:
        resultado = finalizar_evento_si_conectado()
        logger.info(f"Resultado finalización eventos: {resultado}")
        return bool(resultado)
    except Exception as e:
        logger.error(f"Error al finalizar eventos pendientes: {e}")
        st.warning("⚠️ No se pudieron procesar eventos pendientes.")
        return False

def _verificar_comunicacion_original():
    """
    Verificación ORIGINAL usando soap_services.verificar_comunicacion()
    EXACTAMENTE igual que en main.py original.
    """
    st.info("🔄 Usando verificación estándar...")
    
    # Código IDÉNTICO al main.py original
    mensaje, conectado, tipo_deducido = verificar_comunicacion()

    if conectado:
        st.success("✅ Conexión establecida con el SIN.")
        online_main()
    else:
        st.error("❌ No se pudo conectar al SIN. Se activará la contingencia.")
        
        # Paso 2: Verificar si ya hay un evento abierto
        evento_existente = obtener_evento_abierto()
        
        if evento_existente:
            st.info("[✅] Ya existe un evento abierto. Continúa en modo offline.")
        else:
            st.warning("[⚠️] No hay evento abierto. Creando evento de contingencia...")
            
            # Obtener eventos paramétricos
            eventos = get_eventos_parametricos()
            if eventos:
                # Selecciona el evento tipo 1 (Corte de Internet) por defecto (comparando como string)
                evento_tipo_1 = next((e for e in eventos if str(e["codigoClasificador"]).strip() == "1"), None)
                if evento_tipo_1:
                    cufd = get_cufd_vigente()
                    if cufd:
                        fecha_inicio = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        insertar_evento_local(
                            codigo_evento=evento_tipo_1["codigoClasificador"],
                            descripcion=evento_tipo_1["descripcion"],
                            fecha_inicio=fecha_inicio,
                            cufd=cufd
                        )
                        st.success("✅ Evento de contingencia registrado correctamente.")
                    else:
                        st.error("No se encontró un CUFD vigente para registrar el evento.")
                else:
                    st.error("No se encontró el evento tipo 1 en la parametrización.")

def _verificar_comunicacion_mejorada():
    """
    Verificación MEJORADA usando el nuevo communication_manager.
    MANTIENE toda la funcionalidad original pero con mejoras adicionales.
    """
    st.info("🔄 Usando verificación mejorada con diagnóstico completo...")
    
    with st.spinner("Verificando comunicación con el SIN..."):
        # Usar el servicio mejorado que internamente usa las funciones originales
        resultado_completo = communication_manager.verificar_comunicacion_completa()
    
    # Extraer información para compatibilidad con main.py original
    principal = resultado_completo["verificacion_principal"]
    conectado = principal["conectado"] if principal else False
    mensaje = principal["mensaje"] if principal else "Error desconocido"
    
    # Mostrar información adicional en sidebar
    with st.sidebar:
        estado = resultado_completo["estado_general"]
        if estado == EstadoComunicacion.ONLINE.value:
            st.success("🟢 **SISTEMA ONLINE**")
        else:
            st.error("🔴 **SISTEMA OFFLINE**")
        
        st.caption(f"📊 {resultado_completo['recomendacion']}")
        
        # Mostrar detalles de servicios
        with st.expander("🔧 Detalles de Servicios"):
            servicios = resultado_completo["verificaciones_servicios"]
            for nombre, detalle in servicios.items():
                if detalle["conectado"]:
                    st.success(f"✅ {nombre}")
                else:
                    st.error(f"❌ {nombre}")
    
    # MISMA lógica que main.py original para compatibilidad
    if conectado:
        st.success("✅ Conexión establecida con el SIN.")
        
        # Información adicional sobre el diagnóstico
        with st.expander("📊 Ver Diagnóstico Completo"):
            servicios_ok = sum(1 for s in resultado_completo["verificaciones_servicios"].values() if s["conectado"])
            total_servicios = len(resultado_completo["verificaciones_servicios"])
            st.metric("Servicios Funcionando", f"{servicios_ok}/{total_servicios}")
            
            if servicios_ok < total_servicios:
                st.warning(f"⚠️ Algunos servicios presentan problemas. El sistema funcionará con limitaciones.")
        
        online_main()
    else:
        st.error("❌ No se pudo conectar al SIN. Se activará la contingencia.")
        
        # Mostrar tipo de contingencia recomendado
        tipo_contingencia = principal.get("tipo_contingencia") if principal else None
        if tipo_contingencia:
            try:
                nombre_contingencia = TipoContingencia(tipo_contingencia).name
                st.info(f"🔧 **Tipo de contingencia recomendado**: {nombre_contingencia}")
            except:
                st.info(f"🔧 **Código de contingencia**: {tipo_contingencia}")
        
        # MISMA lógica que main.py original
        evento_existente = obtener_evento_abierto()
        
        if evento_existente:
            st.info("[✅] Ya existe un evento abierto. Continúa en modo offline.")
        else:
            st.warning("[⚠️] No hay evento abierto. Creando evento de contingencia...")
            
            # Obtener eventos paramétricos
            eventos = get_eventos_parametricos()
            if eventos:
                # Selecciona el evento tipo 1 (Corte de Internet) por defecto (comparando como string)
                evento_tipo_1 = next((e for e in eventos if str(e["codigoClasificador"]).strip() == "1"), None)
                if evento_tipo_1:
                    cufd = get_cufd_vigente()
                    if cufd:
                        fecha_inicio = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        insertar_evento_local(
                            codigo_evento=evento_tipo_1["codigoClasificador"],
                            descripcion=evento_tipo_1["descripcion"],
                            fecha_inicio=fecha_inicio,
                            cufd=cufd
                        )
                        st.success("✅ Evento de contingencia registrado correctamente.")
                    else:
                        st.error("No se encontró un CUFD vigente para registrar el evento.")
                else:
                    st.error("No se encontró el evento tipo 1 en la parametrización.")

def debug_impresion_button():
    """
    Función temporal para debuggear el botón de impresión paso a paso
    """
    st.header("🐛 Debug del Botón de Impresión")
    
    # Mostrar estado actual primero
    st.subheader("📊 Estado Actual del Sistema")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Estados críticos:**")
        st.write(f"- factura_validada: {st.session_state.get('factura_validada', False)}")
        st.write(f"- impresion_en_progreso: {st.session_state.get('impresion_en_progreso', False)}")
        st.write(f"- cuf: {st.session_state.get('cuf', 'NO DEFINIDO')}")
        st.write(f"- ultima_factura: {st.session_state.get('ultima_factura', 'NO DEFINIDO')}")
    
    with col2:
        datos_impresion = st.session_state.get('datos_impresion', {})
        st.write(f"**datos_impresion**: {len(datos_impresion) if datos_impresion else 0} elementos")
        if datos_impresion:
            st.write("Claves disponibles:")
            for key in datos_impresion.keys():
                st.write(f"  - {key}")
    
    # Simular los estados necesarios para mostrar el botón
    if not st.session_state.get('factura_validada'):
        st.warning("⚠️ factura_validada = False. El botón de impresión no estará disponible.")
        if st.button("🧪 Simular Factura Validada"):
            st.session_state['factura_validada'] = True
            st.session_state['datos_impresion'] = {
                'subtotal': 100.0,
                'descuento_adicional': 0.0,
                'monto_giftcard': 0.0,
                'lineas_productos': [
                    {
                        'codigo': '001',
                        'nombre': 'Producto Test',
                        'cantidad': 1, 
                        'precio': 100.0,
                        'unidad': 'PZA',
                        'sub_total': 100.0,
                        'montoDescuento': 0.0
                    }
                ],
                'nombre_cliente': 'Cliente Test',
                'fecha_emision_str': datetime.now().strftime("%Y-%m-%d"),
                'seleccion_metodo_pago': 'Efectivo',
                'codigo_clasificador_metodo_pago': '1',
                'seleccion_tipo_documento': 'CI',
                'codigo_clasificador_documento': '1',
                'numero_documento': '12345678',
                'complemento': '',
                'email': 'test@example.com',
                'telefono': '123456789',
                'ultimos_digitos_tarjeta': ''
            }
            st.session_state['cuf'] = 'TEST_CUF_' + datetime.now().strftime('%Y%m%d%H%M%S')
            st.session_state['ultima_factura'] = '12345'
            st.success("✅ Estados simulados configurados")
            st.rerun()
    
    # Botón de impresión con logging detallado
    if st.session_state.get('factura_validada'):
        st.success("✅ Factura validada. El botón de impresión está disponible.")
        
        impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)
        
        if st.button("🖨️ Imprimir Factura (Debug)", disabled=impresion_en_progreso):
            st.write("🔄 **BOTÓN PRESIONADO** - Iniciando diagnóstico paso a paso...")
            
            # Log paso 1: Verificar datos requeridos
            st.write("### 📋 Paso 1: Verificación de Datos Requeridos")
            required_keys = ['datos_impresion', 'cuf', 'ultima_factura']
            missing_keys = [key for key in required_keys if key not in st.session_state]
            
            if missing_keys:
                st.error(f"❌ Faltan claves requeridas: {', '.join(missing_keys)}")
                return
            else:
                st.success("✅ Todas las claves requeridas están presentes")
            
            # Log paso 2: Validar contenido de datos_impresion
            st.write("### 📊 Paso 2: Validación de datos_impresion")
            datos = st.session_state.get('datos_impresion', {})
            st.write(f"📏 Datos disponibles: {len(datos)} elementos")
            
            required_data_keys = ['subtotal', 'lineas_productos', 'nombre_cliente', 'fecha_emision_str']
            missing_data = [key for key in required_data_keys if key not in datos]
            
            if missing_data:
                st.error(f"❌ Faltan datos en datos_impresion: {', '.join(missing_data)}")
                return
            else:
                st.success("✅ Datos de impresión válidos")
            
            # Log paso 3: Intentar importar invoice_templates
            st.write("### 📦 Paso 3: Importación de Módulos")
            try:
                from invoice_templates import generate_compact_html_invoice
                st.success("✅ invoice_templates importado correctamente")
            except ImportError as e:
                st.error(f"❌ Error importando invoice_templates: {e}")
                return
            except Exception as e:
                st.error(f"❌ Error inesperado al importar: {e}")
                return
            
            # Log paso 4: Intentar generar HTML
            st.write("### 🔧 Paso 4: Generación de HTML")
            try:
                # Construir argumentos para la función
                html_args = {
                    'subtotal': datos.get('subtotal'),
                    'descuento_adicional': datos.get('descuento_adicional'),
                    'monto_giftcard': datos.get('monto_giftcard'),
                    'lineas_productos': datos.get('lineas_productos'),
                    'nombre_cliente': datos.get('nombre_cliente'),
                    'fecha_emision': datos.get('fecha_emision_str'),
                    'numero_factura': st.session_state.get('ultima_factura'),
                    'metodo_de_pago': datos.get('seleccion_metodo_pago'),
                    'codigo_clasificador_metodo_pago': datos.get('codigo_clasificador_metodo_pago'),
                    'tipo_documento': datos.get('seleccion_tipo_documento'),
                    'codigo_clasificador_documento': datos.get('codigo_clasificador_documento'),
                    'numero_documento': datos.get('numero_documento'),
                    'complemento': datos.get('complemento'),
                    'email': datos.get('email'),
                    'telefono': datos.get('telefono'),
                    'ultimos_digitos_tarjeta': datos.get('ultimos_digitos_tarjeta'),
                    'cuf': st.session_state.get('cuf')
                }
                
                st.write("🔄 Llamando a generate_compact_html_invoice...")
                html_content = generate_compact_html_invoice(**html_args)
                
                if html_content:
                    st.success(f"✅ HTML generado exitosamente! Tamaño: {len(html_content)} caracteres")
                    
                    # Mostrar vista previa del HTML
                    with st.expander("👀 Vista Previa del HTML"):
                        st.text_area("HTML generado:", html_content[:1000] + "..." if len(html_content) > 1000 else html_content, height=200)
                    
                    # Log paso 5: Intentar llamar al print_manager
                    st.write("### 🖨️ Paso 5: Llamada al Print Manager")
                    try:
                        from print_manager import imprimir_en_hilo
                        st.success("✅ print_manager importado correctamente")
                        
                        # Aquí simularíamos la llamada real
                        st.info("🚀 Aquí se llamaría a imprimir_en_hilo() con:")
                        st.code(f"""
imprimir_en_hilo(
    html_content="{html_content[:50]}...",
    cuf="{st.session_state.get('cuf')}",
    nit="{os.getenv('NIT', 'NIT_NO_DEFINIDO')}",
    numero_factura="{st.session_state.get('ultima_factura')}"
)""")
                        
                        # Opción para ejecutar realmente
                        if st.button("🎯 Ejecutar Impresión REAL"):
                            st.warning("⚠️ Ejecutando impresión real...")
                            try:
                                # Llamar a la función de impresión
                                imprimir_en_hilo(
                                    html_content,
                                    st.session_state.get('cuf'),
                                    os.getenv('NIT', 'TEST_NIT'),
                                    st.session_state.get('ultima_factura')
                                )
                                
                                # La función no devuelve nada, pero actualiza el session_state
                                st.success("✅ Función imprimir_en_hilo() ejecutada correctamente")
                                st.info("🔄 La impresión se está procesando en segundo plano...")
                                
                                # Mostrar estado actual de impresión
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**Estado de impresión:**")
                                    st.write(f"- impresion_en_progreso: {st.session_state.get('impresion_en_progreso', 'NO DEFINIDO')}")
                                    st.write(f"- print_status: {st.session_state.get('print_status', 'NO DEFINIDO')}")
                                    st.write(f"- impresion_finalizada: {st.session_state.get('impresion_finalizada', 'NO DEFINIDO')}")
                                
                                with col2:
                                    st.write("**Parámetros enviados:**")
                                    st.write(f"- CUF: {st.session_state.get('cuf')}")
                                    st.write(f"- NIT: {os.getenv('NIT', 'TEST_NIT')}")
                                    st.write(f"- Número factura: {st.session_state.get('ultima_factura')}")
                                
                                # Instrucciones para verificar el resultado
                                st.info("💡 **Para verificar el resultado:**")
                                st.write("1. Revisa la carpeta `debug/` para el archivo HTML")
                                st.write("2. Revisa la carpeta `pdfs/` para el archivo PDF")
                                st.write("3. Verifica si se creó el archivo `debug/print_complete_*.signal`")
                                st.write("4. Revisa los logs de la impresora")
                                
                                # Botón para refrescar estado
                                if st.button("🔄 Refrescar Estado de Impresión"):
                                    st.rerun()
                                    
                            except Exception as e:
                                st.error(f"❌ Error en impresión real: {e}")
                                st.exception(e)
                        
                    except ImportError as e:
                        st.error(f"❌ Error importando print_manager: {e}")
                    except Exception as e:
                        st.error(f"❌ Error inesperado con print_manager: {e}")
                    
                else:
                    st.error("❌ HTML generado está vacío o es None")
                    
            except Exception as e:
                st.error(f"❌ Error en generación HTML: {e}")
                st.exception(e)
    else:
        st.info("ℹ️ El botón de impresión solo estará disponible cuando factura_validada = True")
    
    # Agregar nueva sección de verificación de session_state
    st.divider()
    st.subheader("🔍 Herramientas de Verificación Adicionales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📁 Verificar Archivos"):
            verificar_archivos_impresion()
    
    with col2:
        if st.button("🖨️ Estado Detallado"):
            mostrar_estado_impresion_detallado()
    
    with col3:
        if st.button("🔍 Debug Session State"):
            mostrar_debug_session_state()
    
    with col4:
        if st.button("🔄 Limpiar Estados"):
            keys_to_clear = ['impresion_en_progreso', 'impresion_finalizada', 'print_status']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("✅ Estados de impresión limpiados")
            st.rerun()
    
    # Nueva sección para el diagnóstico avanzado
    st.divider()
    if st.button("🚨 DIAGNÓSTICO COMPLETO - Resolver Bloqueo de Impresión", type="primary"):
        st.session_state['mostrar_diagnostico_completo'] = True
        st.rerun()
    
    # Mostrar el diagnóstico completo si está activado
    if st.session_state.get('mostrar_diagnostico_completo', False):
        from verificador_session_state import ejecutar_diagnostico_completo
        ejecutar_diagnostico_completo()
        
        if st.button("❌ Cerrar Diagnóstico"):
            st.session_state['mostrar_diagnostico_completo'] = False
            st.rerun()

def verificar_archivos_impresion():
    """
    Función auxiliar para verificar los archivos generados por la impresión
    """
    st.subheader("📁 Verificación de Archivos Generados")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    debug_dir = os.path.join(base_dir, "debug")
    pdfs_dir = os.path.join(base_dir, "pdfs")
    
    # Verificar carpetas
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📂 Carpeta Debug:**")
        if os.path.exists(debug_dir):
            st.success("✅ Carpeta debug existe")
            html_files = [f for f in os.listdir(debug_dir) if f.endswith('.html')]
            signal_files = [f for f in os.listdir(debug_dir) if f.endswith('.signal')]
            
            st.write(f"- Archivos HTML: {len(html_files)}")
            st.write(f"- Archivos signal: {len(signal_files)}")
            
            if html_files:
                st.write("**Últimos archivos HTML:**")
                for f in sorted(html_files)[-3:]:  # Mostrar últimos 3
                    st.write(f"  - {f}")
            
            if signal_files:
                st.write("**Archivos de señalización:**")
                for f in sorted(signal_files)[-3:]:  # Mostrar últimos 3
                    st.write(f"  - {f}")
        else:
            st.error("❌ Carpeta debug no existe")
    
    with col2:
        st.write("**📄 Carpeta PDFs:**")
        if os.path.exists(pdfs_dir):
            st.success("✅ Carpeta pdfs existe")
            pdf_files = [f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')]
            
            st.write(f"- Archivos PDF: {len(pdf_files)}")
            
            if pdf_files:
                st.write("**Últimos archivos PDF:**")
                for f in sorted(pdf_files)[-3:]:  # Mostrar últimos 3
                    file_path = os.path.join(pdfs_dir, f)
                    file_size = os.path.getsize(file_path)
                    st.write(f"  - {f} ({file_size} bytes)")
        else:
            st.error("❌ Carpeta pdfs no existe")
    
    # Verificar permisos
    st.write("**🔐 Verificación de Permisos:**")
    permisos_ok = True
    
    if os.path.exists(debug_dir):
        if os.access(debug_dir, os.W_OK):
            st.success("✅ Permisos de escritura en debug")
        else:
            st.error("❌ Sin permisos de escritura en debug")
            permisos_ok = False
    
    if os.path.exists(pdfs_dir):
        if os.access(pdfs_dir, os.W_OK):
            st.success("✅ Permisos de escritura en pdfs")
        else:
            st.error("❌ Sin permisos de escritura en pdfs")
            permisos_ok = False
    
    return permisos_ok

def mostrar_estado_impresion_detallado():
    """
    Muestra el estado detallado de la impresión
    """
    st.subheader("🖨️ Estado Detallado de Impresión")
    
    # Estado del session_state
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Estado en Session:**")
        impresion_estados = {
            'impresion_en_progreso': st.session_state.get('impresion_en_progreso', 'NO DEFINIDO'),
            'impresion_finalizada': st.session_state.get('impresion_finalizada', 'NO DEFINIDO'),
            'print_status': st.session_state.get('print_status', 'NO DEFINIDO')
        }
        
        for key, value in impresion_estados.items():
            if value == 'NO DEFINIDO':
                st.warning(f"⚠️ {key}: {value}")
            elif key == 'impresion_en_progreso' and value:
                st.info(f"🔄 {key}: {value}")
            elif key == 'impresion_finalizada' and value:
                st.success(f"✅ {key}: {value}")
            else:
                st.write(f"📊 {key}: {value}")
    
    with col2:
        st.write("**Archivos Esperados:**")
        numero_factura = st.session_state.get('ultima_factura', 'DESCONOCIDO')
        nit = os.getenv('NIT', 'TEST_NIT')
        cuf = st.session_state.get('cuf', 'SIN_CUF')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        archivos_esperados = [
            f"debug/factura_{numero_factura}_{timestamp}.html",
            f"pdfs/factura_{numero_factura}_{nit}_{cuf[-8:]}.pdf",
            f"debug/print_complete_{numero_factura}.signal"
        ]
        
        for archivo in archivos_esperados:
            if os.path.exists(archivo):
                st.success(f"✅ {archivo}")
            else:
                st.warning(f"⏳ {archivo} (puede estar generándose)")

def mostrar_comparacion_servicios():
    """
    Función de demostración que muestra las diferencias entre 
    el servicio original y el mejorado.
    """
    st.header("🔬 Comparación de Servicios de Comunicación")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📟 Servicio Original")
        st.code("""
# soap_services.py
mensaje, conectado, tipo = verificar_comunicacion()

# Características:
✅ Verificación básica
✅ Timeout 6 segundos  
✅ Clasificación de errores
❌ Solo un endpoint
❌ Sin histórico
❌ Sin análisis combinado
        """)
        
        if st.button("🧪 Probar Verificación Original"):
            try:
                from soap_services import verificar_comunicacion
                with st.spinner("Ejecutando verificación original..."):
                    resultado = verificar_comunicacion()
                st.json({
                    "mensaje": resultado[0],
                    "conectado": resultado[1], 
                    "tipo": resultado[2]
                })
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        st.subheader("🚀 Servicio Mejorado")
        st.code("""
# communication_manager.py  
resultado = manager.verificar_comunicacion_completa()

# Características:
✅ Verificación múltiple
✅ Todos los endpoints
✅ Análisis combinado
✅ Histórico de verificaciones
✅ Recomendaciones inteligentes
✅ Compatible con original
        """)
        
        if st.button("🧪 Probar Verificación Mejorada") and ENHANCED_SERVICE_AVAILABLE:
            with st.spinner("Ejecutando verificación mejorada..."):
                resultado = communication_manager.verificar_comunicacion_completa()
            st.json(resultado)

if __name__ == "__main__":
    # Mostrar selector de modo
    st.sidebar.header("🔧 Modo de Demostración")
    modo = st.sidebar.selectbox(
        "Seleccionar modo:",
        ["🚀 Mejorado (si disponible)", "📟 Original", "🔬 Comparación", "🐛 Debug Impresión", "🔍 Diagnóstico Completo"]
    )
    
    if modo == "🔬 Comparación":
        mostrar_comparacion_servicios()
    elif modo == "📟 Original":
        st.info("🔄 Forzando uso del servicio original...")
        _verificar_comunicacion_original()
    elif modo == "🐛 Debug Impresión":
        debug_impresion_button()
    elif modo == "🔍 Diagnóstico Completo":
        try:
            from diagnostico_impresion import mostrar_diagnostico_completo
            mostrar_diagnostico_completo()
        except ImportError as e:
            st.error(f"❌ No se pudo cargar el módulo de diagnóstico: {e}")
            st.info("💡 Asegúrate de que el archivo diagnostico_impresion.py esté en la misma carpeta")
    else:
        main_enhanced()
