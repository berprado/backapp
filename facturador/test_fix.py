#!/usr/bin/env python3
"""
Test para verificar que la corrección del KeyError está funcionando correctamente.
"""

import os
import sys
sys.path.append('.')

# Configurar variables de entorno requeridas
os.environ.update({
    'NIT': '123456789',
    'RAZON_SOCIAL': 'Test Company',
    'NOMBRE_SUCURSAL': 'Sucursal Test',
    'CODIGO_PUNTO_VENTA': '0',
    'DIRECCION': 'Test Address',
    'MUNICIPIO': 'Test Municipality',
    'TELEFONO': '123456789',
    'DESCRIPCION_TIPO_FACTURA': 'FACTURA',
    'SUBTITULO': 'Test Subtitle'
})

from invoice_templates import generate_compact_html_invoice

def test_invoice_generation():
    """Test de generación de factura con datos de prueba."""
    
    # Datos de prueba con la clave 'precio' (no 'precio_venta')
    lineas_productos = [
        {
            'codigo': '001',
            'nombre': 'Producto Test',
            'unidad': 'UNIDAD',
            'cantidad': 2,
            'precio': 100.0,  # Nota: usando 'precio', no 'precio_venta'
            'sub_total': 200.0,
            'montoDescuento': 0
        }
    ]
    
    print("🔄 Iniciando test de generación HTML...")
    
    try:
        html_content = generate_compact_html_invoice(
            subtotal=200.0,
            descuento_adicional=0.0,
            monto_giftcard=0.0,
            lineas_productos=lineas_productos,
            nombre_cliente="Cliente Test",
            fecha_emision="2025-07-01 23:30:00",
            numero_factura="12345",
            metodo_de_pago="Efectivo",
            codigo_clasificador_metodo_pago=1,
            tipo_documento="NIT",
            codigo_clasificador_documento=5,
            numero_documento="123456789",
            complemento=None,
            email=None,
            telefono=None,
            ultimos_digitos_tarjeta=None,
            cuf="TEST_CUF_20250701"
        )
        
        print("✅ ¡HTML generado exitosamente!")
        print(f"📏 Longitud del HTML: {len(html_content)} caracteres")
        
        # Verificar que contiene elementos clave
        assert 'Producto Test' in html_content, "Producto no encontrado"
        assert '200.00' in html_content, "Total no encontrado"
        assert 'CLIENTE TEST' in html_content, "Cliente no encontrado (en mayúsculas)"
        
        print("✅ ¡Todas las verificaciones pasaron!")
        
        # Guardar HTML para inspección manual
        with open('test_invoice.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("💾 HTML guardado en 'test_invoice.html'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la generación: {e}")
        print(f"📊 Tipo de error: {type(e).__name__}")
        import traceback
        print("🔍 Traceback completo:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Test de corrección del KeyError 'precio_venta'")
    print("=" * 50)
    
    success = test_invoice_generation()
    
    if success:
        print("\n🎉 ¡El test pasó exitosamente! La corrección funciona.")
    else:
        print("\n💥 El test falló. Revisa los errores arriba.")
    
    print("=" * 50)
