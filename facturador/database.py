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
