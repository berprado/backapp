# test_pdf.py
from siat_pdf import html_to_pdf
import os

print("Iniciando prueba de generación de PDF...")

# HTML de prueba súper simple
html_simple = "<html><body><h1>Hola Mundo</h1><p>Esto es una prueba.</p></body></html>"

# Ruta de salida
ruta_salida = os.path.join(os.getcwd(), "test_output.pdf")

print(f"Intentando generar PDF en: {ruta_salida}")

try:
    # Llamamos a la misma función que usa tu aplicación
    success = html_to_pdf(html_simple, ruta_salida)

    if success and os.path.exists(ruta_salida):
        print("\n" + "="*50)
        print("🎉 ¡ÉXITO! El archivo 'test_output.pdf' fue generado correctamente.")
        print("="*50)
        print("Esto confirma que WeasyPrint y sus dependencias están bien instaladas.")
    else:
        print("\n" + "="*50)
        print("❌ FALLO: La función html_to_pdf no retornó éxito o el archivo no fue creado.")
        print("="*50)

except Exception as e:
    print("\n" + "="*50)
    print(f"💥 ERROR CATASTRÓFICO: La función lanzó una excepción: {e}")
    import traceback
    traceback.print_exc()
    print("="*50)