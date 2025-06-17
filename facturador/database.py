# database.py

import os
from dotenv import load_dotenv

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
if URL_DATABASE is None:
    raise ValueError("La variable de entorno DATABASE_URL no está definida")

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
import pymysql.cursors

def conectar_db():
    """Conexión directa para queries críticos"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", ""),
        user=os.getenv("MYSQL_USER", ""),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", ""),
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
