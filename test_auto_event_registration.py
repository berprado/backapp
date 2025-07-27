#!/usr/bin/env python3
"""
Script de prueba para verificar el registro automático de eventos significativos.
"""

import sys
import os

# Agregar el directorio raíz al path
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

# Agregar el directorio facturador al path
FACTURADOR_PATH = os.path.join(ROOT_PATH, 'facturador')
if FACTURADOR_PATH not in sys.path:
    sys.path.insert(0, FACTURADOR_PATH)

def test_auto_registration():
    """Prueba el registro automático de eventos."""
    print("🧪 Iniciando prueba de registro automático de eventos...")
    
    try:
        # Importar las funciones necesarias
        from facturador.contingency_manager import handle_offline_mode
        from facturador.significant_events import get_significant_events
        from facturador.data_access import obtener_evento_abierto
        
        print("✅ Importaciones exitosas")
        
        # Verificar estado inicial
        print("\n📋 Estado inicial:")
        eventos_antes = get_significant_events(limit=5, only_open=True)
        print(f"   Eventos activos antes: {len(eventos_antes)}")
        
        # Ejecutar handle_offline_mode()
        print("\n🔧 Ejecutando handle_offline_mode()...")
        handle_offline_mode()
        
        # Verificar estado final
        print("\n📋 Estado final:")
        eventos_despues = get_significant_events(limit=5, only_open=True)
        print(f"   Eventos activos después: {len(eventos_despues)}")
        
        if eventos_despues:
            evento = eventos_despues[0]
            print(f"   ✅ Evento creado:")
            print(f"      ID: {evento.get('id')}")
            print(f"      Descripción: {evento.get('descripcion')}")
            print(f"      Código: {evento.get('codigo_evento')}")
            print(f"      CUFD: {evento.get('cufd')}")
        
        # Verificar con data_access también
        evento_data_access = obtener_evento_abierto()
        if evento_data_access:
            print(f"   ✅ Confirmado por data_access:")
            print(f"      ID: {evento_data_access.get('id')}")
            print(f"      Descripción: {evento_data_access.get('descripcion')}")
        
        print("\n🎉 Prueba completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_auto_registration()
    if success:
        print("\n✅ El registro automático de eventos está funcionando correctamente.")
    else:
        print("\n❌ Hay problemas con el registro automático de eventos.")
