from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

DB_USER = os.getenv("MYSQL_USER", "")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_HOST = os.getenv("MYSQL_HOST", "")
DB_PORT = os.getenv("MYSQL_PORT", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "")

URL_DATABASE = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear el engine para conectar a la base de datos
engine = create_engine(URL_DATABASE)

# Crear la fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para modelos declarativos
Base = declarative_base()

# Conexión alternativa comentada
#URL_DATABASE = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@0.tcp.sa.ngrok.io:15947/{DB_NAME}"
#engine = create_engine(URL_DATABASE)
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#Base = declarative_base()
