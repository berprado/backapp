import os
import json
from datetime import datetime
from decimal import Decimal
from typing import Annotated, List, Optional
from fastapi import FastAPI, Depends, status, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import models_api
import crud
from schemas import ComandaResponse
from database_api import engine, SessionLocal

app = FastAPI()

# Mount the `static` directory at the root path
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

models_api.Base.metadata.create_all(bind=engine)  # Create the tables in the database

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/", status_code=200, response_model=List[ComandaResponse])
async def get_all_comandas(db: Session = Depends(get_db)):
    """
    Obtiene todas las comandas disponibles en el sistema
    """
    comandas = db.query(models_api.Comanda).all()

    if not comandas:
        raise HTTPException(status_code=404, detail="No se encontraron comandas")

    return comandas

@app.get("/favicon.ico", status_code=200)
async def favicon():
    """
    Devuelve el favicon.ico desde la carpeta static
    """
    return FileResponse('static/favicon.ico')

@app.get("/comandas/{id_comanda}", status_code=status.HTTP_200_OK, response_model=List[ComandaResponse])
async def get_comanda(id_comanda: str, db: Session = Depends(get_db)):
    """
    Obtiene una o más comandas por su ID o IDs (separados por coma)
    """
    id_comanda_list = [int(id) for id in id_comanda.split(',')]
    # Usamos el método de crud para mantener consistencia
    comandas = crud.get_comanda_data(id_comanda_list, db)
    
    if not comandas:
        raise HTTPException(status_code=404, detail=f"Comanda {id_comanda} no encontrada")

    return comandas

@app.get("/comandas/usuario/{usuario_reg}", status_code=200, response_model=List[ComandaResponse])
async def get_comandas_by_usuario(usuario_reg: str, db: Session = Depends(get_db)):
    """
    Obtiene todas las comandas registradas por un usuario específico
    """
    comandas = db.query(models_api.Comanda).filter(models_api.Comanda.usuario_reg == usuario_reg).all()

    if not comandas:
        raise HTTPException(status_code=404, detail=f"No se encontraron comandas para el usuario {usuario_reg}")

    return comandas
