#!/usr/bin/env python3
"""
Script de prueba para verificar el monitoreo automático de contingencias.
Este script simula una pérdida de conexión y verifica que el sistema registre automáticamente el evento.
"""

import sys
import os
import time

# Agregar el directorio raíz al path
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

# Agregar el directorio facturador al path
FACTURADOR_PATH = os.path.join(ROOT_PATH, 'facturador')
if FACTURADOR_PATH not in sys.path:
    sys.path.insert(0, FACTURADOR_PATH)

def test_automatic_monitoring():
    """Prueba el monitoreo automático de contingencias."""
    print("🧪 Iniciando prueba de monitoreo automático...")
    
    try:
        # Importar las funciones necesarias
        from facturador.contingency_manager import get_contingency_manager
        from facturador.significant_events import get_significant_events
        from facturador.data_access import obtener_evento_abierto
        
        print("✅ Importaciones exitosas")
        
        # Obtener el gestor de contingencias
        contingency_manager = get_contingency_manager()
        
        # Verificar estado inicial
        print("\n📋 Estado inicial:")
        eventos_antes = get_significant_events(limit=5, only_open=True)
        print(f"   Eventos activos antes: {len(eventos_antes)}")
        
        status = contingency_manager.get_status()
        print(f"   Estado del gestor: {status.get('status', 'Desconocido')}")
        print(f"   Monitor activo: {contingency_manager.monitoring_thread and contingency_manager.monitoring_thread.is_alive()}")
        
        # Iniciar monitoreo si no está activo
        if not contingency_manager.monitoring_thread or not contingency_manager.monitoring_thread.is_alive():
            print("\n🔧 Iniciando monitoreo automático...")
            contingency_manager.start_monitoring()
            time.sleep(2)  # Esperar un poco para que se inicie
        else:
            print("\n✅ Monitoreo ya está activo")
        
        # Verificar configuración de umbrales
        print(f"\n⚙️ Configuración del monitoreo:")
        print(f"   Intervalo de verificación: {contingency_manager.check_interval} segundos")
        print(f"   Umbral de fallos: {contingency_manager.failure_threshold}")
        print(f"   Fallos consecutivos actuales: {contingency_manager.consecutive_failures}")
        
        # Mostrar estado del hilo de monitoreo
        if contingency_manager.monitoring_thread:
            print(f"   Hilo de monitoreo activo: ✅ {contingency_manager.monitoring_thread.is_alive()}")
            print(f"   Nombre del hilo: {contingency_manager.monitoring_thread.name}")
        
        print("\n📢 Para probar:")
        print("   1. Desconecta tu internet")
        print("   2. Espera aproximadamente 60-90 segundos")
        print("   3. El sistema debería detectar automáticamente la pérdida y crear un evento")
        print("   4. Ejecuta este script nuevamente para verificar")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_monitoring_results():
    """Verifica si el monitoreo automático ha detectado cambios."""
    print("🔍 Verificando resultados del monitoreo...")
    
    try:
        from facturador.contingency_manager import get_contingency_manager
        from facturador.significant_events import get_significant_events
        
        # Obtener estado actual
        contingency_manager = get_contingency_manager()
        status = contingency_manager.get_status()
        eventos_actuales = get_significant_events(limit=5, only_open=True)
        
        print(f"\n📊 Estado actual:")
        print(f"   Estado del gestor: {status.get('status', 'Desconocido')}")
        print(f"   Eventos activos: {len(eventos_actuales)}")
        print(f"   Fallos consecutivos: {contingency_manager.consecutive_failures}")
        print(f"   Éxitos consecutivos: {contingency_manager.consecutive_successes}")
        
        if eventos_actuales:
            evento = eventos_actuales[0]
            print(f"\n✅ Evento más reciente:")
            print(f"      ID: {evento.get('id')}")
            print(f"      Descripción: {evento.get('descripcion')}")
            print(f"      Código: {evento.get('codigo_evento')}")
            print(f"      Fecha inicio: {evento.get('fecha_inicio')}")
        
        if status.get('status') == 'contingency':
            print(f"\n🎯 ¡ÉXITO! El sistema detectó automáticamente la pérdida de conexión")
            print(f"   Tiempo de inicio de contingencia: {status.get('contingency_start_time')}")
            print(f"   Tipo de evento: {status.get('event_type')}")
            print(f"   Descripción: {status.get('event_description')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error al verificar resultados: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        success = check_monitoring_results()
    else:
        success = test_automatic_monitoring()
    
    if success:
        print("\n✅ Prueba completada.")
        if len(sys.argv) <= 1:
            print("\nPara verificar resultados después de desconectar internet, ejecuta:")
            print("python test_monitoring.py --check")
    else:
        print("\n❌ Hay problemas con el monitoreo automático.")
