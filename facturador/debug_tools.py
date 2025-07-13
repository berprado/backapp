"""
Herramientas de depuración para el sistema de facturación.

Este módulo contiene funciones utilizadas para diagnóstico y depuración,
extraídas del archivo main_enhanced_demo.py para mantener el código
principal limpio y estable.

IMPORTANTE: Este módulo NO debe importarse en main.py. Está diseñado
para ser usado exclusivamente durante el desarrollo y depuración.
"""

import streamlit as st
import os
import sys
from datetime import datetime

# Intentar importar verificador de session_state
try:
    from verificador_session_state import mostrar_debug_session_state, verificar_estructura_session_state
except ImportError:
    def mostrar_debug_session_state():
        st.warning("⚠️ Verificador de session_state no disponible")
    def verificar_estructura_session_state():
        return {"estructura_valida": True}

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
        
        if st.button("🧪 Probar Verificación Mejorada"):
            try:
                from communication_manager import communication_manager
                with st.spinner("Ejecutando verificación mejorada..."):
                    resultado = communication_manager.verificar_comunicacion_completa()
                st.json(resultado)
            except Exception as e:
                st.error(f"Error: {e}")


def diagnostico_app():
    """
    Aplicación de diagnóstico independiente para desarrollo y depuración.
    """
    st.set_page_config(page_title="Diagnóstico del Sistema", page_icon="🧰", layout="wide")
    
    st.title("🧰 Herramientas de Diagnóstico")
    
    tab1, tab2, tab3 = st.tabs([
        "🖨️ Diagnóstico de Impresión", 
        "🌐 Diagnóstico de Comunicación",
        "💾 Diagnóstico de Estado"
    ])
    
    with tab1:
        debug_impresion_button()
        
    with tab2:
        mostrar_comparacion_servicios()
        
    with tab3:
        try:
            mostrar_debug_session_state()
        except:
            st.error("No se pudo cargar el verificador de estado")
            

if __name__ == "__main__":
    diagnostico_app()
