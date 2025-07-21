# test_printer.py
import sys
from escpos.printer import Usb
from escpos.exceptions import DeviceNotFoundError

# IDs de tu impresora Epson TM-T20II
VENDOR_ID = 0x04B8
PRODUCT_ID = 0x0E15

print("="*50)
print("INICIANDO PRUEBA DE CONEXIÓN DE IMPRESORA TÉRMICA")
print(f"Buscando dispositivo con VENDOR_ID={hex(VENDOR_ID)} y PRODUCT_ID={hex(PRODUCT_ID)}")
print("="*50)

try:
    # Este es el único comando que intentaremos ejecutar.
    # Es el mismo que se llama dentro de la clase ThermalPrinter.
    printer = Usb(VENDOR_ID, PRODUCT_ID, timeout=5)
    
    print("\n" + "="*50)
    print("🎉 ¡ÉXITO! Impresora encontrada y conectada.")
    print("="*50)
    print("La impresora está respondiendo correctamente a la conexión USB.")
    print("Ahora intentando imprimir una línea de prueba...")

    try:
        printer.text("Hola Mundo! Si lees esto, la conexion es correcta.\n")
        printer.cut()
        print("✅ Línea de prueba enviada exitosamente.")
    except Exception as e_print:
        print(f"❌ ERROR AL IMPRIMIR: La impresora se conectó pero no pudo imprimir. Error: {e_print}")

except DeviceNotFoundError:
    print("\n" + "="*50)
    print("❌ ERROR: Dispositivo No Encontrado (DeviceNotFoundError).")
    print("="*50)
    print("El backend USB funciona, pero no encontró una impresora con esos IDs.")
    print("POSIBLES SOLUCIONES:")
    print("1. Verifica que la impresora esté encendida y conectada al PC.")
    print("2. Confirma los IDs de Vendedor y Producto en el 'Administrador de dispositivos' de Windows.")
    print("   (Busca la impresora, ve a Propiedades > Detalles > Id. de hardware).")

except Exception as e:
    print("\n" + "="*50)
    print(f"💥 ERROR INESPERADO: Se produjo un error durante la conexión: {type(e).__name__}")
    print("="*50)
    print(f"Detalles: {e}")
    print("\nPOSIBLES CAUSAS:")
    print("- El backend de 'libusb' no está instalado o no se encuentra. Asegúrate de que los archivos DLL están en el PATH.")
    print("- Problema con el driver 'libusbK'. Intenta reinstalarlo con Zadig.")
    print("- Otro programa puede estar usando la impresora.")
    
    # Intenta dar una pista sobre el backend
    try:
        import usb.core
        backend = usb.core.find(backend=None)
        if backend:
            print(f"\nℹ️ Backend de PyUSB detectado: {backend}")
        else:
            print("\n⚠️ No se pudo detectar un backend de PyUSB. Este es probablemente el problema principal.")
    except Exception as be:
        print(f"\n⚠️ Error al intentar detectar el backend de PyUSB: {be}")