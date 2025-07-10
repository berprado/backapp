#!/usr/bin/env python3
"""
Test específico para verificar el funcionamiento del print_manager
"""

import os
import sys
import time
from datetime import datetime

sys.path.append('.')

# Configurar variables de entorno requeridas
os.environ.update({
    'NIT': '344096024',
    'RAZON_SOCIAL': 'Test Company',
    'NOMBRE_SUCURSAL': 'Sucursal Test',
    'CODIGO_PUNTO_VENTA': '0',
    'DIRECCION': 'Test Address',
    'MUNICIPIO': 'Test Municipality',
    'TELEFONO': '123456789',
    'DESCRIPCION_TIPO_FACTURA': 'FACTURA',
    'SUBTITULO': 'Test Subtitle'
})

def test_print_manager():
    """Test completo del print_manager"""
    
    print("🧪 Test del Print Manager")
    print("=" * 50)
    
    # Importar módulos necesarios
    try:
        from print_manager import imprimir_en_hilo
        from invoice_templates import generate_compact_html_invoice
        print("✅ Módulos importados correctamente")
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        return False
    
    # Generar HTML de prueba
    print("\n🔧 Generando HTML de prueba...")
    try:
        lineas_productos = [
            {
                'codigo': '001',
                'nombre': 'Producto Test Print',
                'unidad': 'UNIDAD',
                'cantidad': 1,
                'precio': 50.0,
                'sub_total': 50.0,
                'montoDescuento': 0
            }
        ]
        
        html_content = generate_compact_html_invoice(
            subtotal=50.0,
            descuento_adicional=0.0,
            monto_giftcard=0.0,
            lineas_productos=lineas_productos,
            nombre_cliente="Cliente Test Print",
            fecha_emision="2025-07-02 00:30:00",
            numero_factura="TEST001",
            metodo_de_pago="Efectivo",
            codigo_clasificador_metodo_pago=1,
            tipo_documento="NIT",
            codigo_clasificador_documento=5,
            numero_documento="123456789",
            complemento=None,
            email=None,
            telefono=None,
            ultimos_digitos_tarjeta=None,
            cuf="TEST_CUF_PRINT_" + datetime.now().strftime('%Y%m%d%H%M%S')
        )
        
        print(f"✅ HTML generado: {len(html_content)} caracteres")
        
    except Exception as e:
        print(f"❌ Error generando HTML: {e}")
        return False
    
    # Verificar directorios antes de la impresión
    print("\n📁 Verificando directorios...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    debug_dir = os.path.join(base_dir, "debug")
    pdfs_dir = os.path.join(base_dir, "pdfs")
    
    print(f"📂 Debug dir: {debug_dir}")
    print(f"📂 PDFs dir: {pdfs_dir}")
    
    # Contar archivos antes
    debug_files_before = 0
    pdf_files_before = 0
    
    if os.path.exists(debug_dir):
        debug_files_before = len([f for f in os.listdir(debug_dir) if f.endswith('.html')])
    
    if os.path.exists(pdfs_dir):
        pdf_files_before = len([f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')])
    
    print(f"📊 Archivos antes - HTML: {debug_files_before}, PDF: {pdf_files_before}")
    
    # Llamar al print_manager
    print("\n🖨️ Llamando a imprimir_en_hilo...")
    try:
        cuf = "TEST_CUF_PRINT_" + datetime.now().strftime('%Y%m%d%H%M%S')
        nit = os.getenv('NIT', 'TEST_NIT')
        numero_factura = "TEST001"
        
        print(f"🔧 Parámetros:")
        print(f"  - CUF: {cuf}")
        print(f"  - NIT: {nit}")
        print(f"  - Número factura: {numero_factura}")
        
        # La función se ejecuta en un hilo separado
        imprimir_en_hilo(html_content, cuf, nit, numero_factura)
        
        print("✅ Función imprimir_en_hilo() ejecutada (hilo iniciado)")
        
    except Exception as e:
        print(f"❌ Error ejecutando imprimir_en_hilo: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Esperar un momento para que el hilo procese
    print("\n⏱️ Esperando procesamiento del hilo...")
    for i in range(10):
        time.sleep(1)
        print(f"⏳ {i+1}/10 segundos...")
        
        # Verificar si se crearon archivos
        if os.path.exists(debug_dir):
            debug_files_now = len([f for f in os.listdir(debug_dir) if f.endswith('.html')])
            if debug_files_now > debug_files_before:
                print(f"✅ ¡Archivo HTML detectado! ({debug_files_now} vs {debug_files_before})")
                break
    
    # Verificar resultados finales
    print("\n📊 Verificando resultados...")
    
    success = True
    
    # Verificar archivos HTML
    if os.path.exists(debug_dir):
        debug_files_after = len([f for f in os.listdir(debug_dir) if f.endswith('.html')])
        if debug_files_after > debug_files_before:
            print(f"✅ Archivo HTML creado: {debug_files_after - debug_files_before} nuevos")
            # Mostrar el último archivo
            html_files = [f for f in os.listdir(debug_dir) if f.endswith('.html')]
            if html_files:
                latest_html = sorted(html_files)[-1]
                html_path = os.path.join(debug_dir, latest_html)
                html_size = os.path.getsize(html_path)
                print(f"📄 Último HTML: {latest_html} ({html_size} bytes)")
        else:
            print("❌ No se creó archivo HTML")
            success = False
    else:
        print("❌ Directorio debug no existe")
        success = False
    
    # Verificar archivos PDF
    if os.path.exists(pdfs_dir):
        pdf_files_after = len([f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')])
        if pdf_files_after > pdf_files_before:
            print(f"✅ Archivo PDF creado: {pdf_files_after - pdf_files_before} nuevos")
            # Mostrar el último archivo
            pdf_files = [f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')]
            if pdf_files:
                latest_pdf = sorted(pdf_files)[-1]
                pdf_path = os.path.join(pdfs_dir, latest_pdf)
                pdf_size = os.path.getsize(pdf_path)
                print(f"📄 Último PDF: {latest_pdf} ({pdf_size} bytes)")
        else:
            print("❌ No se creó archivo PDF")
            success = False
    else:
        print("❌ Directorio pdfs no existe")
        success = False
    
    # Verificar archivos de señalización
    signal_files = [f for f in os.listdir(debug_dir) if f.endswith('.signal')] if os.path.exists(debug_dir) else []
    if signal_files:
        print(f"✅ Archivos de señalización encontrados: {len(signal_files)}")
        latest_signal = sorted(signal_files)[-1]
        print(f"📋 Última señal: {latest_signal}")
    else:
        print("⚠️ No se encontraron archivos de señalización")
    
    return success

if __name__ == "__main__":
    success = test_print_manager()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡Test del Print Manager EXITOSO!")
        print("✅ Los archivos se generaron correctamente")
        print("💡 El problema podría estar en la configuración de la impresora térmica")
    else:
        print("💥 Test del Print Manager FALLÓ")
        print("❌ Revisa los errores anteriores")
    print("=" * 50)
