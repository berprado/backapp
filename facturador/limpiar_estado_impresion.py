#!/usr/bin/env python3
"""
Script para limpiar el estado de impresión bloqueado.
Este script limpia archivos de señal antiguos y resetea cualquier estado problemático.
"""

import os
import glob
import json
from datetime import datetime

def limpiar_archivos_senal():
    """Limpia archivos de señal de impresión antiguos"""
    print("🧹 Limpiando archivos de señal antiguos...")
    
    patron_senal = "debug/print_complete_*.signal"
    archivos_senal = glob.glob(patron_senal)
    
    if archivos_senal:
        for archivo in archivos_senal:
            try:
                os.remove(archivo)
                print(f"  ✅ Eliminado: {archivo}")
            except Exception as e:
                print(f"  ❌ Error eliminando {archivo}: {e}")
    else:
        print("  ℹ️ No se encontraron archivos de señal antiguos")

def limpiar_session_state_archivo():
    """Limpia archivos de session_state de debug"""
    print("\n🧹 Limpiando archivos de session_state de debug...")
    
    patron_session = "debug/session_state_debug_*.json"
    archivos_session = glob.glob(patron_session)
    
    if archivos_session:
        for archivo in archivos_session:
            try:
                os.remove(archivo)
                print(f"  ✅ Eliminado: {archivo}")
            except Exception as e:
                print(f"  ❌ Error eliminando {archivo}: {e}")
    else:
        print("  ℹ️ No se encontraron archivos de session_state de debug")

def crear_script_reinicio():
    """Crea un script para reiniciar Streamlit limpiamente"""
    script_content = '''#!/usr/bin/env python3
"""
Script de reinicio limpio para Streamlit
"""
import streamlit as st

def limpiar_session_state():
    """Limpia el session_state completamente"""
    keys_to_remove = [
        'impresion_en_progreso',
        'impresion_finalizada', 
        'print_status',
        'debug_impresion',
        'ultimo_numero_factura',
        'ultima_impresion_timestamp'
    ]
    
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
            
    st.session_state.clear()
    st.rerun()

if __name__ == "__main__":
    st.title("🔄 Reinicio de Estado de Impresión")
    st.write("Este script limpia completamente el estado de impresión.")
    
    if st.button("🧹 Limpiar Session State"):
        limpiar_session_state()
        st.success("✅ Session State limpiado. La página se recargará automáticamente.")
'''
    
    with open("reinicio_streamlit.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("📝 Script de reinicio creado: reinicio_streamlit.py")

def mostrar_estado_sistema():
    """Muestra el estado actual del sistema"""
    print("\n📊 Estado actual del sistema:")
    
    # Verificar archivos de señal
    archivos_senal = glob.glob("debug/print_complete_*.signal")
    print(f"  📁 Archivos de señal activos: {len(archivos_senal)}")
    for archivo in archivos_senal:
        print(f"    - {archivo}")
    
    # Verificar logs de impresión recientes
    logs_printer = glob.glob("logs/printer_*.log")
    if logs_printer:
        log_mas_reciente = max(logs_printer, key=os.path.getmtime)
        print(f"  📄 Log de impresión más reciente: {log_mas_reciente}")
        
        # Leer últimas líneas del log
        try:
            with open(log_mas_reciente, "r", encoding="utf-8") as f:
                lineas = f.readlines()
                print("  📝 Últimas entradas del log:")
                for linea in lineas[-5:]:
                    print(f"    {linea.strip()}")
        except Exception as e:
            print(f"    ❌ Error leyendo log: {e}")

def main():
    print("🔧 Herramienta de Limpieza de Estado de Impresión")
    print("=" * 50)
    
    # Mostrar estado actual
    mostrar_estado_sistema()
    
    # Limpiar archivos
    limpiar_archivos_senal()
    limpiar_session_state_archivo()
    
    # Crear script de reinicio
    crear_script_reinicio()
    
    print("\n✅ Limpieza completada!")
    print("\n💡 Pasos siguientes:")
    print("1. Reinicia Streamlit (Ctrl+C y luego ejecutar de nuevo)")
    print("2. Si persiste el problema, ejecuta: streamlit run reinicio_streamlit.py")
    print("3. Luego regresa a tu aplicación principal")

if __name__ == "__main__":
    main()
