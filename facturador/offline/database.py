# database.py
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def conectar_db():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        cursorclass=pymysql.cursors.DictCursor
    )

def get_eventos_parametricos():
    db = conectar_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT codigoClasificador, descripcion FROM sincronizarparametricaeventossignificativos")
        return cursor.fetchall()

def get_cufd_vigente():
    db = conectar_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT codigo FROM cufd WHERE vigente = 1 ORDER BY fecha_solicitud DESC LIMIT 1")
        result = cursor.fetchone()
        return result['codigo'] if result else None

def insertar_evento_local(codigo_evento, descripcion, fecha_inicio, cufd):
    db = conectar_db()
    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO eventos_significativos_registrados
            (codigo_evento, descripcion, fecha_inicio, fecha_fin, cufd)
            VALUES (%s, %s, %s, %s, %s)
        """, (codigo_evento, descripcion, fecha_inicio, fecha_inicio, cufd))
        db.commit()
def obtener_evento_abierto():
    db = conectar_db()
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM eventos_significativos_registrados
            WHERE fecha_inicio = fecha_fin AND codigo_recepcion IS NULL
            ORDER BY fecha_inicio DESC LIMIT 1
        """)
        return cursor.fetchone()

def actualizar_evento_final(evento_id, fecha_fin, codigo_recepcion):
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
