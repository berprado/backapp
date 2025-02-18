import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener la URL de la base de datos
URL_DATABASE = os.getenv("DATABASE_URL")

# Crear la conexión a la base de datos
engine = create_engine(URL_DATABASE)

# Crear un manejador de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos ORM
Base = declarative_base()

def get_db():
    """Generador de sesiones para la base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea las tablas en la base de datos si no existen."""
    Base.metadata.create_all(bind=engine)

# Determinar el entorno basado en CODIGO_AMBIENTE (1 = Producción, 2 = Pruebas)
CODIGO_AMBIENTE = int(os.getenv("CODIGO_AMBIENTE", 2))  # 2 por defecto (Pruebas)

if __name__ == "__main__":
    if CODIGO_AMBIENTE == 2:  # Solo ejecuta esto en ambiente de pruebas
        print("Modo PRUEBAS: Inicializando la base de datos...")
        init_db()
    else:
        print("Modo PRODUCCIÓN: No se inicializa la base de datos automáticamente.")



#URL_DATABASE = "mysql+pymysql://root:admin123.@0.tcp.sa.ngrok.io:15947/adminerp"
#engine = create_engine(URL_DATABASE)
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#Base = declarative_base()