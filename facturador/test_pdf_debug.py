#!/usr/bin/env python
"""
Test específico para debug de PDF - Simulando flujo real
"""
import os
import sys
import traceback
import time
from datetime import datetime

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from siat_pdf import html_to_pdf
from invoice_templates import generate_html_invoice
from print_manager import imprimir_en_hilo

def test_pdf_generation():
    """Test específico de generación de PDF siguiendo el flujo real"""
    print("🔧 TEST DE GENERACIÓN DE PDF (FLUJO REAL)")
    print("=" * 50)
    
    # Datos de prueba como en el flujo real
    subtotal = 150.00
    descuento_adicional = 0.00
    monto_giftcard = 0.00
    lineas_productos = [
        {
            "codigo": "PROD001",
            "nombre": "Producto de prueba",  # Cambiar descripcion por nombre
            "unidad": "PZA",
            "cantidad": 1,
            "precio": 150.00,
            "sub_total": 150.00,
            "montoDescuento": 0.00
        }
    ]
    nombre_cliente = "CLIENTE DE PRUEBA"
    fecha_emision = "2025-07-03"
    numero_factura = "TEST001"
    cuf = "TEST_CUF_PDF_DEBUG"
    nit = "344096024"
    
    try:
        # Paso 1: Generar HTML como en el flujo real
        print("📄 Generando HTML usando generate_html_invoice...")
        html_content = generate_html_invoice(
            subtotal=subtotal,
            descuento_adicional=descuento_adicional,
            monto_giftcard=monto_giftcard,
            lineas_productos=lineas_productos,
            nombre_cliente=nombre_cliente,
            fecha_emision=fecha_emision,
            numero_factura=numero_factura
        )
        print(f"✅ HTML generado: {len(html_content)} caracteres")
        
        # Paso 2: Llamar a imprimir_en_hilo (que debe generar el PDF)
        print("🖨️ Llamando a imprimir_en_hilo...")
        imprimir_en_hilo(html_content, cuf, nit, numero_factura)
        print("✅ Función imprimir_en_hilo llamada")
        
        # Paso 3: Esperar un poco para que el hilo termine
        print("⏳ Esperando que el hilo termine...")
        time.sleep(3)
        
        # Paso 4: Verificar archivos generados
        pdfs_dir = os.path.join(os.path.dirname(__file__), "pdfs")
        debug_dir = os.path.join(os.path.dirname(__file__), "debug")
        
        # Contar archivos en pdfs
        pdf_files = [f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')]
        html_files = [f for f in os.listdir(debug_dir) if f.endswith('.html')]
        
        print(f"� Archivos PDF encontrados: {len(pdf_files)}")
        print(f"� Archivos HTML encontrados: {len(html_files)}")
        
        if pdf_files:
            latest_pdf = max(pdf_files, key=lambda f: os.path.getctime(os.path.join(pdfs_dir, f)))
            pdf_path = os.path.join(pdfs_dir, latest_pdf)
            file_size = os.path.getsize(pdf_path)
            print(f"✅ PDF más reciente: {latest_pdf} ({file_size} bytes)")
            
            # Limpiar archivo de test
            if latest_pdf.startswith("test_"):
                try:
                    os.remove(pdf_path)
                    print("🧹 Archivo de test eliminado")
                except:
                    pass
            
            return True
        else:
            print("❌ No se encontraron archivos PDF")
            return False
            
    except Exception as e:
        print(f"💥 ERROR: {str(e)}")
        print(f"🔍 Traceback:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_pdf_generation()
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡TEST EXITOSO!")
    else:
        print("❌ TEST FALLÓ")
    print("=" * 50)
