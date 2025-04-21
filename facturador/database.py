# database.py

import os
from dotenv import load_dotenv
from datetime import datetime
from logger_config import get_logger

# Obtener el logger principal
logger = get_logger()

# ----------------------------------------
# Cargar variables de entorno (.env)
# ----------------------------------------
load_dotenv()

# ----------------------------------------
# 🔗 ORM con SQLAlchemy (Sistema principal)
# ----------------------------------------
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Conexión ORM
URL_DATABASE = os.getenv("DATABASE_URL")

engine = create_engine(URL_DATABASE)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Generador de sesiones SQLAlchemy"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Inicializa las tablas ORM si no existen"""
    Base.metadata.create_all(bind=engine)

CODIGO_AMBIENTE = int(os.getenv("CODIGO_AMBIENTE", 2))  # 2 por defecto

if __name__ == "__main__":
    if CODIGO_AMBIENTE == 2:
        print("Modo PRUEBAS: Inicializando la base de datos...")
        init_db()
    else:
        print("Modo PRODUCCIÓN: No se inicializa automáticamente.")


# ----------------------------------------
# 🛠️ PyMySQL directo (Contingencia y eventos)
# ----------------------------------------
import pymysql

def conectar_db():
    """Conexión directa para queries críticos"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        cursorclass=pymysql.cursors.DictCursor
    )

def get_eventos_parametricos():
    """Obtiene los eventos significativos disponibles (paramétricos)"""
    db = conectar_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT codigoClasificador, descripcion FROM sincronizarparametricaeventossignificativos")
        return cursor.fetchall()

def get_cufd_vigente():
    """Devuelve el CUFD vigente (último activo)"""
    db = conectar_db()
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT codigo FROM cufd
            WHERE vigente = 1
            ORDER BY fecha_solicitud DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        return result['codigo'] if result else None

def insertar_evento_local(codigo_evento, descripcion, fecha_inicio, cufd):
    """Inserta un nuevo evento significativo en la BD local"""
    db = conectar_db()
    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO eventos_significativos_registrados
            (codigo_evento, descripcion, fecha_inicio, fecha_fin, cufd)
            VALUES (%s, %s, %s, %s, %s)
        """, (codigo_evento, descripcion, fecha_inicio, fecha_inicio, cufd))
        db.commit()

def obtener_evento_abierto():
    """Devuelve el último evento sin cerrar (fecha_inicio = fecha_fin)"""
    db = conectar_db()
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM eventos_significativos_registrados
            WHERE fecha_inicio = fecha_fin
              AND codigo_recepcion IS NULL
            ORDER BY fecha_inicio DESC
            LIMIT 1
        """)
        return cursor.fetchone()

def actualizar_evento_final(evento_id, fecha_fin, codigo_recepcion):
    """Actualiza el evento con su fecha de cierre y código de recepción"""
    db = conectar_db()
    with db.cursor() as cursor:
        cursor.execute("""
            UPDATE eventos_significativos_registrados
            SET fecha_fin = %s,
                codigo_recepcion = %s,
                fecha_registro = NOW()
            WHERE id = %s
        """, (fecha_fin, codigo_recepcion, evento_id))
        db.commit()

def obtener_facturas_por_evento(id_evento):
    """
    Obtiene todas las facturas asociadas a un evento significativo específico.
    
    Args:
        id_evento (int): ID del evento significativo.
        
    Returns:
        list: Lista de diccionarios con los datos de las facturas, o lista vacía si no hay resultados.
    """
    logger.debug(f"Obteniendo facturas para el evento #{id_evento}")
    db = conectar_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM factura_cabecera 
                WHERE codigoEvento = %s OR tipoEmision = '2'
                ORDER BY fechaEmision DESC
            """, (id_evento,))
            facturas = cursor.fetchall()
            
        if facturas:
            logger.info(f"Se encontraron {len(facturas)} facturas para el evento #{id_evento}")
        else:
            logger.info(f"No se encontraron facturas para el evento #{id_evento}")
            
        # Verificar si hay facturas offline que no estén en la BD 
        # pero tienen el prefijo del evento en el nombre del archivo
        if os.path.exists("offline"):
            archivos = [
                f for f in os.listdir("offline")
                if (f.startswith(f"offline_{id_evento}_") or 
                    f.startswith(f"factura_offline_{id_evento}_")) and 
                f.endswith(".xml")
            ]
            
            if archivos and not facturas:
                logger.info(f"Se encontraron {len(archivos)} archivos XML para el evento #{id_evento} pero no facturas en la BD")
                # Si hay archivos pero no facturas en BD, devolver información básica
                return [{"numeroFactura": f.split('_')[2], "nombreRazonSocial": "Factura offline", "montoTotal": 0, 
                         "fechaEmision": datetime.now()} for f in archivos]
            
        return facturas
            
    except Exception as e:
        logger.error(f"Error al obtener facturas para el evento #{id_evento}: {e}")
        return []
    finally:
        db.close()
