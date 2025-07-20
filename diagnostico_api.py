"""
Script de diagnóstico para verificar la conectividad con la API y la base de datos.
"""
import os
import sys
import requests
from sqlalchemy import create_engine, text
import time
import traceback
import json

# Configuración
API_URL = "http://127.0.0.1:8000/"
DB_URL = "mysql+pymysql://root:admin123.@localhost:3306/adminerp_copy"

def check_api_running():
    """Verifica si la API está ejecutándose."""
    print("\n--- Verificando si la API está ejecutándose ---")
    try:
        response = requests.get(API_URL, timeout=5)
        print(f"Status code: {response.status_code}")
        print(f"Respuesta: {response.text[:500]}..." if len(response.text) > 500 else f"Respuesta: {response.text}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ No se pudo conectar a la API en {API_URL}")
        print("   Asegúrate de que el servidor FastAPI esté en ejecución.")
        print("   Puedes iniciarlo con el comando: uvicorn api:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error al verificar la API: {e}")
        print(traceback.format_exc())
        return False

def check_db_connection():
    """Verifica la conexión a la base de datos."""
    print("\n--- Verificando conexión a la base de datos ---")
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Conexión a la base de datos exitosa.")
            
            # Verificar tablas relevantes
            print("\n--- Verificando tablas de la base de datos ---")
            try:
                comanda_result = connection.execute(text("SELECT COUNT(*) FROM comandas")).fetchone()
                print(f"✅ Tabla 'comandas' encontrada. Número de registros: {comanda_result[0]}")
            except Exception as e:
                print(f"❌ Error al verificar la tabla 'comandas': {e}")
            return True
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        print(traceback.format_exc())
        return False

def check_full_api_flow():
    """Realiza una verificación completa del flujo de la API."""
    print("\n--- Realizando una solicitud completa a la API ---")
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Solicitud exitosa. Recibidos {len(data)} registros.")
            if data:
                print(f"Ejemplo de un registro: {json.dumps(data[0], indent=2, default=str)}")
            return True
        else:
            print(f"❌ La API respondió con código de estado {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error al realizar solicitud completa: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=== DIAGNÓSTICO DE API Y BASE DE DATOS ===")
    
    api_running = check_api_running()
    db_connected = check_db_connection()
    
    if api_running and db_connected:
        print("\n✅ La base de datos y la API parecen estar funcionando.")
        check_full_api_flow()
    else:
        print("\n⚠️ Se encontraron problemas que deben resolverse.")
        
        if not api_running:
            print("""
SOLUCIÓN PARA LA API:
1. Abre una terminal y navega a la carpeta del proyecto
2. Ejecuta: uvicorn api:app --reload
3. Verifica que la API inicie sin errores
4. Prueba acceder a http://127.0.0.1:8000/ en tu navegador
            """)
            
        if not db_connected:
            print("""
SOLUCIÓN PARA LA BASE DE DATOS:
1. Verifica que el servidor MySQL esté ejecutándose
2. Confirma que las credenciales en 'database_api.py' sean correctas
3. Asegúrate de que la base de datos 'adminerp_copy' exista
4. Verifica que el usuario tenga permisos para acceder a la base de datos
            """)
    
    print("\n=== FIN DEL DIAGNÓSTICO ===")
