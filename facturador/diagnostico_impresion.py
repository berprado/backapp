"""
Módulo de diagnóstico para identificar problemas en el proceso de impresión de facturas.

Este módulo proporciona herramientas para debuggear y analizar el estado del sistema
de impresión cuando no funciona correctamente.
"""

import streamlit as st
import json
import os
from datetime import datetime
from logger_config import get_logger

logger = get_logger()

def mostrar_diagnostico_completo():
    """
    Función principal de diagnóstico para identificar problemas en el proceso de impresión
    """
    st.header("🔍 Diagnóstico del Sistema de Impresión")
    
    # Verificar estados críticos
    with st.expander("📊 Estado del Session State", expanded=True):
        st.write("**Estados relacionados con impresión:**")
        
        estados_criticos = [
            'factura_validada',
            'impresion_en_progreso', 
            'datos_impresion',
            'cuf',
            'ultima_factura',
            'impresion_finalizada',
            'print_status'
        ]
        
        estados_problema = []
        
        for estado in estados_criticos:
            valor = st.session_state.get(estado, "❌ NO EXISTE")
            
            if estado == 'datos_impresion' and isinstance(valor, dict):
                st.success(f"✅ **{estado}**: Diccionario con {len(valor)} elementos")
                with st.expander(f"Ver contenido de {estado}"):
                    st.json(valor)
            elif valor == "❌ NO EXISTE":
                st.error(f"❌ **{estado}**: NO EXISTE")
                estados_problema.append(estado)
            elif valor is None:
                st.warning(f"⚠️ **{estado}**: None")
                estados_problema.append(estado)
            elif valor == "":
                st.warning(f"⚠️ **{estado}**: Cadena vacía")
                estados_problema.append(estado)
            else:
                st.success(f"✅ **{estado}**: {valor}")
        
        if estados_problema:
            st.error(f"🚨 **Problemas detectados en**: {', '.join(estados_problema)}")
        else:
            st.success("🎉 **Todos los estados críticos están presentes**")
    
    # Verificar funciones de generación HTML
    with st.expander("🔧 Verificar Funciones de Generación"):
        if st.button("🧪 Probar Generación HTML"):
            probar_generacion_html()
    
    # Verificar permisos de archivos
    with st.expander("📁 Verificar Permisos de Carpetas"):
        verificar_permisos_carpetas()
    
    # Verificar importaciones
    with st.expander("📦 Verificar Importaciones de Módulos"):
        verificar_importaciones_impresion()
    
    # Debug completo del session state
    with st.expander("🐛 Debug Completo del Session State"):
        if st.button("🔍 Mostrar TODO el Session State"):
            try:
                estado_completo = dict(st.session_state)
                st.json(estado_completo)
                
                # Guardar en archivo para análisis posterior
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_file = f"debug/session_state_debug_{timestamp}.json"
                os.makedirs("debug", exist_ok=True)
                
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(estado_completo, f, indent=2, default=str)
                
                st.info(f"💾 Estado guardado en: {debug_file}")
                
            except Exception as e:
                st.error(f"Error al mostrar session state: {e}")

def probar_generacion_html():
    """
    Prueba la generación de HTML con datos de ejemplo
    """
    try:
        # Intentar importar la función de generación
        st.info("🔄 Intentando importar invoice_templates...")
        
        try:
            from invoice_templates import generate_compact_html_invoice
            st.success("✅ invoice_templates importado correctamente")
        except ImportError as e:
            st.error(f"❌ Error importando invoice_templates: {e}")
            return False
        
        # Datos de prueba simplificados
        datos_prueba = {
            'subtotal': 100.0,
            'descuento_adicional': 0.0,
            'monto_giftcard': 0.0,
            'lineas_productos': [
                {
                    'nombre': 'Producto Test', 
                    'cantidad': 1, 
                    'precio': 100.0,
                    'unidad': 'PZA'
                }
            ],
            'nombre_cliente': 'Cliente Test',
            'fecha_emision': datetime.now().strftime("%Y-%m-%d"),
            'numero_factura': '12345',
            'cuf': 'TEST_CUF_123456789'
        }
        
        st.info("🔄 Generando HTML de prueba...")
        
        # Intentar generar HTML
        html_test = generate_compact_html_invoice(**datos_prueba)
        
        if html_test:
            st.success("✅ HTML generado exitosamente")
            st.write(f"📏 Tamaño del HTML: {len(html_test)} caracteres")
            
            # Mostrar vista previa
            st.text_area(
                "Vista previa HTML (primeros 500 caracteres):", 
                html_test[:500] + "..." if len(html_test) > 500 else html_test,
                height=150
            )
            
            # Guardar archivo de prueba
            try:
                os.makedirs("debug", exist_ok=True)
                test_file = f"debug/test_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(html_test)
                st.info(f"💾 HTML de prueba guardado en: {test_file}")
            except Exception as e:
                st.warning(f"⚠️ No se pudo guardar archivo de prueba: {e}")
            
            return True
        else:
            st.error("❌ HTML generado está vacío o es None")
            return False
            
    except Exception as e:
        st.error(f"❌ Error general en generación HTML: {e}")
        st.exception(e)
        logger.error(f"Error en probar_generacion_html: {e}")
        return False

def verificar_permisos_carpetas():
    """
    Verifica si las carpetas necesarias existen y tienen permisos
    """
    carpetas_necesarias = ['debug', 'pdfs', 'xmls', 'logs']
    
    for carpeta in carpetas_necesarias:
        ruta = os.path.join(os.getcwd(), carpeta)
        
        if os.path.exists(ruta):
            if os.access(ruta, os.W_OK):
                st.success(f"✅ {carpeta}/ - Existe y tiene permisos de escritura")
            else:
                st.error(f"❌ {carpeta}/ - Existe pero SIN permisos de escritura")
        else:
            st.warning(f"⚠️ {carpeta}/ - NO existe")
            if st.button(f"Crear carpeta {carpeta}/", key=f"crear_{carpeta}"):
                try:
                    os.makedirs(ruta, exist_ok=True)
                    st.success(f"✅ Carpeta {carpeta}/ creada")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error creando {carpeta}/: {e}")

def verificar_importaciones_impresion():
    """
    Verifica que todas las dependencias de impresión estén disponibles
    """
    modulos_requeridos = [
        ('invoice_templates', 'generate_compact_html_invoice'),
        ('print_manager', 'imprimir_en_hilo'),  
        ('thermal_printer', 'ThermalPrinter'),
        ('siat_pdf', 'html_to_pdf'),
        ('printer_utils', 'html_to_escpos_text'),
        ('logger_config', 'get_printer_logger')
    ]
    
    resultados = {}
    
    for modulo, funcion in modulos_requeridos:
        try:
            mod = __import__(modulo)
            if hasattr(mod, funcion):
                st.success(f"✅ {modulo}.{funcion} - Disponible")
                resultados[modulo] = "OK"
            else:
                st.error(f"❌ {modulo}.{funcion} - Módulo existe pero función no encontrada")
                resultados[modulo] = "FUNCION_NO_ENCONTRADA"
        except ImportError as e:
            st.error(f"❌ {modulo} - No se puede importar: {e}")
            resultados[modulo] = f"IMPORT_ERROR: {e}"
        except Exception as e:
            st.error(f"❌ {modulo} - Error inesperado: {e}")
            resultados[modulo] = f"ERROR: {e}"
    
    # Mostrar resumen
    modulos_ok = sum(1 for r in resultados.values() if r == "OK")
    total_modulos = len(modulos_requeridos)
    
    if modulos_ok == total_modulos:
        st.success(f"🎉 Todos los módulos ({modulos_ok}/{total_modulos}) están disponibles")
    else:
        st.error(f"🚨 Solo {modulos_ok}/{total_modulos} módulos están disponibles")
    
    return resultados

def simular_datos_factura():
    """
    Simula los datos necesarios para una factura de prueba
    """
    st.header("🧪 Simulador de Datos de Factura")
    
    if st.button("🎯 Configurar Datos de Prueba"):
        # Simular una factura validada
        st.session_state['factura_validada'] = True
        st.session_state['impresion_en_progreso'] = False
        st.session_state['impresion_finalizada'] = False
        
        # Datos básicos
        st.session_state['cuf'] = 'TEST_CUF_' + datetime.now().strftime('%Y%m%d%H%M%S')
        st.session_state['ultima_factura'] = '12345'
        
        # Datos de impresión
        st.session_state['datos_impresion'] = {
            'subtotal': 150.0,
            'descuento_adicional': 10.0,
            'monto_giftcard': 0.0,
            'lineas_productos': [
                {
                    'nombre': 'Producto de Prueba 1',
                    'cantidad': 2,
                    'precio': 75.0,
                    'unidad': 'PZA'
                },
                {
                    'nombre': 'Producto de Prueba 2', 
                    'cantidad': 1,
                    'precio': 15.0,
                    'unidad': 'PZA'
                }
            ],
            'nombre_cliente': 'Cliente de Prueba',
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
        
        st.success("✅ Datos de prueba configurados correctamente")
        st.info("🔄 Recarga la página para ver los cambios en el diagnóstico")

if __name__ == "__main__":
    mostrar_diagnostico_completo()
    st.divider()
    simular_datos_factura()
