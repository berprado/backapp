"""
Script para corregir el estado inconsistente de la factura #777
Basado en la verificación SIAT que confirma estado = VÁLIDA
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Cargar variables de entorno desde .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Obtener configuración de la base de datos del .env
DB_USER = os.getenv('MYSQL_USER', 'root')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'admin123.')
DB_HOST = os.getenv('MYSQL_HOST', 'localhost')
DB_PORT = os.getenv('MYSQL_PORT', '3306')
DB_NAME = os.getenv('MYSQL_DATABASE', 'adminerp_copy')

print(f"🔌 Conectando a: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Configurar conexión a la base de datos
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def corregir_estado_factura_777():
    """
    Corrige el estado de la factura #777 para que coincida con SIAT.
    SIAT confirma: Estado = VÁLIDA
    """
    session = SessionLocal()
    
    try:
        print("\n" + "="*70)
        print("🔧 CORRECCIÓN DE ESTADO - FACTURA #777")
        print("="*70)
        
        # 1. Mostrar estado actual
        print("\n📋 Estado ACTUAL en BD Local:")
        resultado = session.execute(
            text("""
                SELECT 
                    numeroFactura,
                    estado,
                    estadoValidacion,
                    resultadoValidacion,
                    fechaAnulacion,
                    motivoAnulacion,
                    codigoRecepcion
                FROM factura_cabecera 
                WHERE numeroFactura = 777
            """)
        ).fetchone()
        
        if resultado:
            print(f"   Número: {resultado[0]}")
            print(f"   estado: {resultado[1]} ❌")
            print(f"   estadoValidacion: {resultado[2]}")
            print(f"   resultadoValidacion: {resultado[3]}")
            print(f"   fechaAnulacion: {resultado[4]}")
            print(f"   motivoAnulacion: {resultado[5]}")
            print(f"   codigoRecepcion: {resultado[6]}")
        else:
            print("   ❌ Factura no encontrada")
            return False
        
        # 2. Mostrar estado SIAT confirmado
        print("\n✅ Estado CONFIRMADO en SIAT:")
        print("   Estado: VÁLIDA")
        print("   Fecha: 16/10/2025 02:49:47")
        print("   Monto: 115.00 Bs.")
        print("   CUF: 178B43EFDB9D6D8CF0242E32CFCAB29D0B923E1BA16C53B6C3E032F74")
        
        # 3. Solicitar confirmación
        print("\n" + "="*70)
        print("⚠️  ACCIÓN A REALIZAR:")
        print("="*70)
        print("   Se actualizará la BD local para sincronizar con SIAT:")
        print("   • estado: 'Anulada' → 'Valida'")
        print("   • estadoValidacion: mantener 'VALIDA'")
        print("   • resultadoValidacion: mantener 'VALIDADA'")
        print("   • fechaAnulacion: → NULL")
        print("   • motivoAnulacion: → NULL")
        
        respuesta = input("\n¿Continuar con la corrección? (s/n): ").strip().lower()
        
        if respuesta != 's':
            print("\n❌ Operación cancelada por el usuario.")
            return False
        
        # 4. Ejecutar corrección
        print("\n🔄 Ejecutando corrección...")
        session.execute(
            text("""
                UPDATE factura_cabecera
                SET 
                    estado = 'Valida',
                    estadoValidacion = 'VALIDA',
                    resultadoValidacion = 'VALIDADA',
                    fechaAnulacion = NULL,
                    motivoAnulacion = NULL
                WHERE numeroFactura = 777
            """)
        )
        session.commit()
        
        # 5. Verificar resultado
        print("\n✅ Corrección aplicada. Verificando...")
        resultado_final = session.execute(
            text("""
                SELECT 
                    numeroFactura,
                    estado,
                    estadoValidacion,
                    resultadoValidacion,
                    fechaAnulacion,
                    motivoAnulacion
                FROM factura_cabecera 
                WHERE numeroFactura = 777
            """)
        ).fetchone()
        
        print("\n📋 Estado CORREGIDO en BD Local:")
        print(f"   Número: {resultado_final[0]}")
        print(f"   estado: {resultado_final[1]} ✅")
        print(f"   estadoValidacion: {resultado_final[2]} ✅")
        print(f"   resultadoValidacion: {resultado_final[3]} ✅")
        print(f"   fechaAnulacion: {resultado_final[4]} ✅")
        print(f"   motivoAnulacion: {resultado_final[5]} ✅")
        
        print("\n" + "="*70)
        print("✅ SINCRONIZACIÓN COMPLETADA")
        print("="*70)
        print("La factura #777 ahora está sincronizada con el estado real en SIAT.")
        print("Estado: VÁLIDA tanto en BD local como en SIAT.")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR durante la corrección: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    print("\n🔍 Script de Corrección - Factura #777")
    print("Verificación SIAT confirmó: Estado = VÁLIDA\n")
    
    exito = corregir_estado_factura_777()
    
    if exito:
        print("\n✅ Proceso completado exitosamente.")
        print("Puedes verificar el estado nuevamente en la UI de la aplicación.")
    else:
        print("\n❌ Proceso no completado.")
    
    input("\nPresiona ENTER para salir...")
