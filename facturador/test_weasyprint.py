#!/usr/bin/env python3
"""
Test específico para verificar WeasyPrint y la generación de PDF
"""

import os
import sys
from datetime import datetime

def test_weasyprint():
    """Test específico para WeasyPrint"""
    
    print("🧪 Test de WeasyPrint")
    print("=" * 40)
    
    # Test 1: Verificar importación
    print("📦 Test 1: Importación de WeasyPrint")
    try:
        from weasyprint import HTML
        print("✅ WeasyPrint importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando WeasyPrint: {e}")
        print("💡 Solución: pip install weasyprint")
        return False
    except Exception as e:
        print(f"❌ Error inesperado con WeasyPrint: {e}")
        return False
    
    # Test 2: Generar PDF simple
    print("\n📄 Test 2: Generación de PDF simple")
    try:
        html_simple = """
        <!DOCTYPE html>
        <html>
        <head><title>Test PDF</title></head>
        <body>
            <h1>Test de Generación PDF</h1>
            <p>Este es un test simple para verificar WeasyPrint.</p>
            <p>Fecha: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        </body>
        </html>
        """
        
        output_path = f"test_weasyprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        HTML(string=html_simple).write_pdf(output_path)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ PDF generado: {output_path} ({file_size} bytes)")
            
            # Limpiar archivo de test
            try:
                os.remove(output_path)
                print("🧹 Archivo de test eliminado")
            except:
                pass
                
            return True
        else:
            print("❌ PDF no se generó")
            return False
            
    except Exception as e:
        print(f"❌ Error generando PDF simple: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_siat_pdf_module():
    """Test del módulo siat_pdf específicamente"""
    
    print("\n🧪 Test del módulo siat_pdf")
    print("=" * 40)
    
    # Importar el módulo
    try:
        sys.path.append('.')
        from siat_pdf import html_to_pdf
        print("✅ Módulo siat_pdf importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando siat_pdf: {e}")
        return False
    
    # Test con HTML de factura real
    print("\n📄 Test con HTML de factura")
    try:
        # HTML similar al que genera la factura
        html_factura = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Factura Test</title>
            <style>
                body { font-family: monospace; font-size: 10px; }
                table { width: 100%; border-collapse: collapse; }
                .header { text-align: center; font-weight: bold; }
            </style>
        </head>
        <body>
            <table>
                <tr><th class="header">FACTURA TEST</th></tr>
                <tr><td>Fecha: """ + datetime.now().strftime("%Y-%m-%d") + """</td></tr>
                <tr><td>Producto Test: $100.00</td></tr>
                <tr><td>Total: $100.00</td></tr>
            </table>
        </body>
        </html>
        """
        
        output_path = f"test_factura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        resultado = html_to_pdf(html_factura, output_path)
        
        if resultado and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ PDF de factura generado: {output_path} ({file_size} bytes)")
            
            # Limpiar archivo de test
            try:
                os.remove(output_path)
                print("🧹 Archivo de test eliminado")
            except:
                pass
                
            return True
        else:
            print("❌ PDF de factura no se generó")
            return False
            
    except Exception as e:
        print(f"❌ Error generando PDF de factura: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_directorio_permisos():
    """Test de permisos de directorio"""
    
    print("\n🧪 Test de Permisos de Directorios")
    print("=" * 40)
    
    # Verificar directorio pdfs
    pdfs_dir = "pdfs"
    if not os.path.exists(pdfs_dir):
        try:
            os.makedirs(pdfs_dir)
            print(f"✅ Directorio {pdfs_dir} creado")
        except Exception as e:
            print(f"❌ Error creando directorio {pdfs_dir}: {e}")
            return False
    else:
        print(f"✅ Directorio {pdfs_dir} existe")
    
    # Verificar permisos de escritura
    if os.access(pdfs_dir, os.W_OK):
        print(f"✅ Permisos de escritura en {pdfs_dir}")
        
        # Test de escritura real
        test_file = os.path.join(pdfs_dir, "test_permisos.txt")
        try:
            with open(test_file, "w") as f:
                f.write("Test de permisos")
            print(f"✅ Test de escritura exitoso")
            
            # Limpiar
            os.remove(test_file)
            print("🧹 Archivo de test eliminado")
            
            return True
        except Exception as e:
            print(f"❌ Error en test de escritura: {e}")
            return False
    else:
        print(f"❌ Sin permisos de escritura en {pdfs_dir}")
        return False

if __name__ == "__main__":
    print("🔧 DIAGNÓSTICO COMPLETO DE PDF")
    print("=" * 50)
    
    tests = [
        ("WeasyPrint", test_weasyprint),
        ("Módulo siat_pdf", test_siat_pdf_module), 
        ("Permisos de directorio", test_directorio_permisos)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE TESTS:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"  {status} - {test_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ La generación de PDF debería funcionar correctamente")
    else:
        print("💥 ALGUNOS TESTS FALLARON")
        print("❌ Revisa los errores anteriores para solucionarlos")
    print("=" * 50)
