from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Database URL
URL_DATABASE = "mysql+pymysql://root:admin123.@localhost:3306/adminerp_copy"

# Create the engine to connect to the database
engine = create_engine(URL_DATABASE)

# Create a session factory for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = declarative_base()

def init_db():
    # Import all models here so that Base can recognize them before creating tables
    from models import FacturaCabecera, FacturaDetalle
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Call init_db to create tables if they do not exist
if __name__ == "__main__":
    init_db()






#URL_DATABASE = "mysql+pymysql://root:admin123.@0.tcp.sa.ngrok.io:15947/adminerp"
#engine = create_engine(URL_DATABASE)
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#Base = declarative_base()
