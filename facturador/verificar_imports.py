"""
Script independiente para verificar todas las importaciones necesarias
para el sistema de impresión de facturas.

Ejecuta este script para diagnosticar problemas de importación antes
de intentar usar el sistema principal.
"""

import sys
import os
from datetime import datetime

# Asegurar que estamos en el directorio correcto
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def verificar_modulo(nombre_modulo, funcion_o_clase=None):
    """
    Verifica si un módulo puede ser importado y opcionalmente si contiene una función/clase específica
    """
    try:
        modulo = __import__(nombre_modulo)
        
        if funcion_o_clase:
            if hasattr(modulo, funcion_o_clase):
                return True, f"✅ {nombre_modulo}.{funcion_o_clase} - OK"
            else:
                return False, f"❌ {nombre_modulo}.{funcion_o_clase} - Módulo OK pero función/clase no encontrada"
        else:
            return True, f"✅ {nombre_modulo} - OK"
            
    except ImportError as e:
        return False, f"❌ {nombre_modulo} - ImportError: {e}"
    except Exception as e:
        return False, f"❌ {nombre_modulo} - Error: {e}"

def verificar_dependencias_sistema():
    """
    Verifica todas las dependencias del sistema de impresión
    """
    print("🔍 VERIFICACIÓN DE DEPENDENCIAS DEL SISTEMA DE IMPRESIÓN")
    print("=" * 60)
    
    # Módulos principales del sistema
    modulos_principales = [
        ("streamlit", "write"),
        ("datetime", "datetime"),
        ("os", "path"),
        ("sys", "path"),
        ("json", "dumps"),
        ("threading", "Thread")
    ]
    
    print("\n📦 MÓDULOS ESTÁNDAR DE PYTHON:")
    for modulo, funcion in modulos_principales:
        resultado, mensaje = verificar_modulo(modulo, funcion)
        print(f"  {mensaje}")
    
    # Módulos específicos del proyecto
    modulos_proyecto = [
        ("database", "get_eventos_parametricos"),
        ("ui_copy", "main(online=True)"),
        ("contingencia_auto", "finalizar_evento_si_conectado"),
        ("soap_services", "verificar_comunicacion"),
        ("logger_config", "get_logger")
    ]
    
    print("\n🏗️ MÓDULOS PRINCIPALES DEL PROYECTO:")
    errores_principales = 0
    for modulo, funcion in modulos_proyecto:
        resultado, mensaje = verificar_modulo(modulo, funcion)
        print(f"  {mensaje}")
        if not resultado:
            errores_principales += 1
    
    # Módulos de impresión
    modulos_impresion = [
        ("invoice_templates", "generate_compact_html_invoice"),
        ("print_manager", "imprimir_en_hilo"),
        ("thermal_printer", "ThermalPrinter"),
        ("siat_pdf", "html_to_pdf"),
        ("printer_utils", "html_to_escpos_text")
    ]
    
    print("\n🖨️ MÓDULOS DE IMPRESIÓN:")
    errores_impresion = 0
    for modulo, funcion in modulos_impresion:
        resultado, mensaje = verificar_modulo(modulo, funcion)
        print(f"  {mensaje}")
        if not resultado:
            errores_impresion += 1
    
    # Librerías externas críticas
    librerías_externas = [
        ("escpos", None),
        ("bs4", "BeautifulSoup"),
        ("requests", "get"),
        ("lxml", None)
    ]
    
    print("\n📚 LIBRERÍAS EXTERNAS:")
    errores_externos = 0
    for libreria, funcion in librerías_externas:
        resultado, mensaje = verificar_modulo(libreria, funcion)
        print(f"  {mensaje}")
        if not resultado:
            errores_externos += 1
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN:")
    
    if errores_principales == 0:
        print("✅ Módulos principales: TODOS OK")
    else:
        print(f"❌ Módulos principales: {errores_principales} errores")
    
    if errores_impresion == 0:
        print("✅ Módulos de impresión: TODOS OK")
    else:
        print(f"❌ Módulos de impresión: {errores_impresion} errores")
    
    if errores_externos == 0:
        print("✅ Librerías externas: TODAS OK")
    else:
        print(f"❌ Librerías externas: {errores_externos} errores")
    
    total_errores = errores_principales + errores_impresion + errores_externos
    
    if total_errores == 0:
        print("\n🎉 SISTEMA LISTO PARA FUNCIONAR")
    else:
        print(f"\n🚨 SE ENCONTRARON {total_errores} ERRORES QUE DEBEN RESOLVERSE")
    
    return total_errores == 0

def verificar_estructura_archivos():
    """
    Verifica que los archivos necesarios existan en el sistema
    """
    print("\n📁 VERIFICACIÓN DE ESTRUCTURA DE ARCHIVOS:")
    
    archivos_criticos = [
        "main_enhanced_demo.py",
        "ui_copy.py", 
        "database.py",
        "soap_services.py",
        "invoice_templates.py",
        "print_manager.py",
        "thermal_printer.py",
        "siat_pdf.py",
        "logger_config.py"
    ]
    
    archivos_faltantes = []
    
    for archivo in archivos_criticos:
        ruta = os.path.join(current_dir, archivo)
        if os.path.exists(ruta):
            print(f"  ✅ {archivo}")
        else:
            print(f"  ❌ {archivo} - NO ENCONTRADO")
            archivos_faltantes.append(archivo)
    
    carpetas_necesarias = ["debug", "pdfs", "xmls", "logs"]
    
    print("\n📂 CARPETAS NECESARIAS:")
    for carpeta in carpetas_necesarias:
        ruta = os.path.join(current_dir, carpeta)
        if os.path.exists(ruta):
            print(f"  ✅ {carpeta}/")
        else:
            print(f"  ⚠️ {carpeta}/ - No existe (se creará automáticamente)")
    
    return len(archivos_faltantes) == 0

def generar_reporte_diagnostico():
    """
    Genera un reporte completo del estado del sistema
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_reporte = f"diagnostico_sistema_{timestamp}.txt"
    
    # Crear carpeta de reportes si no existe
    carpeta_reportes = os.path.join(current_dir, "debug")
    os.makedirs(carpeta_reportes, exist_ok=True)
    
    ruta_reporte = os.path.join(carpeta_reportes, nombre_reporte)
    
    # Redirigir la salida a archivo
    import io
    from contextlib import redirect_stdout
    
    with open(ruta_reporte, 'w', encoding='utf-8') as f:
        with redirect_stdout(f):
            print(f"REPORTE DE DIAGNÓSTICO DEL SISTEMA DE IMPRESIÓN")
            print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Directorio: {current_dir}")
            print("=" * 80)
            
            verificar_dependencias_sistema()
            verificar_estructura_archivos()
            
            print(f"\n" + "=" * 80)
            print(f"Reporte guardado en: {ruta_reporte}")
    
    return ruta_reporte

if __name__ == "__main__":
    print("🚀 INICIANDO VERIFICACIÓN DEL SISTEMA DE IMPRESIÓN")
    print(f"📍 Directorio actual: {current_dir}")
    
    # Verificar dependencias
    sistema_ok = verificar_dependencias_sistema()
    
    # Verificar archivos
    archivos_ok = verificar_estructura_archivos()
    
    # Generar reporte
    reporte = generar_reporte_diagnostico()
    print(f"\n💾 Reporte completo guardado en: {reporte}")
    
    if sistema_ok and archivos_ok:
        print("\n🎉 EL SISTEMA ESTÁ LISTO PARA FUNCIONAR")
        exit(0)
    else:
        print("\n🚨 EL SISTEMA TIENE PROBLEMAS QUE DEBEN RESOLVERSE")
        exit(1)
