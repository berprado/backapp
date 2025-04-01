import os
import json
from datetime import datetime
from decimal import Decimal
from typing import Annotated, List, Optional
from fastapi import FastAPI, Depends, status, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()

# Mount the `static` directory at the root path
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

models.Base.metadata.create_all(bind=engine)  # Create the tables in the database

class Comanda(BaseModel):
    cantidad: Annotated[int, "Cantidad de productos"]
    id_comanda: int
    id_producto: Optional[int] = None
    id_salida_combo_coctel: int
    id_bar_combo_coctel: int
    precio_venta: Annotated[float, "Precio de venta"]
    sub_total: Annotated[float, "Subtotal"]
    producto_coctel: str
    cor_subtotal_anterior: Annotated[float, "Subtotal anterior"]
    id_barra: int
    comision: Annotated[float, "Comisión"]
    usuario_reg: str
    fecha_reg: str
    fecha_mod: str
    estado: str
    id_operacion: int
    producto: str
    id_producto_combo: int
    tipo_salida: int
    estado_comanda: int
    estado_impresion: int
    codigo: str

class Comanda2(BaseModel):
    id: int
    cantidad: Annotated[int, "Cantidad de productos"]
    id_comanda: int
    id_producto: Optional[str] = None  # Cambiado a Optional[str] para reflejar los códigos
    id_salida_combo_coctel: Optional[int] = None
    id_bar_combo_coctel: Optional[str] = None  # Cambiado a Optional[str] para reflejar los códigos
    precio_venta: Annotated[Decimal, "Subtotal"]
    sub_total: Annotated[Decimal, "Subtotal"]
    producto_coctel: Optional[str] = None
    id_barra: int
    usuario_reg: str
    estado: str
    id_operacion: int
    nombre: str
    id_producto_combo: Optional[str] = None  # Cambiado a Optional[str] para reflejar los códigos
    tipo_salida: int
    estado_comanda: int
    estado_impresion: Optional[int] = None

    class Config:
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/", status_code=200, response_model=List[Comanda2])
async def get_all_comandas(db: Session = Depends(get_db)):
    comandas = db.query(models.Comanda).all()

    if not comandas:
        raise HTTPException(status_code=404, detail="No se encontraron comandas")

    return comandas

@app.get("/favicon.ico", status_code=200)
async def favicon():
    return FileResponse('static/favicon.ico')

@app.get("/comandas/{id_comanda}", status_code=status.HTTP_200_OK, response_model=List[Comanda2])
async def get_comanda(id_comanda: str, db: Session = Depends(get_db)):
    id_comanda_list = [int(id) for id in id_comanda.split(',')]
    comandas = [comanda for id in id_comanda_list for comanda in db.query(models.Comanda).filter(models.Comanda.id_comanda == id).all()]

    if not comandas:
        raise HTTPException(status_code=404, detail=f"Comanda {id_comanda} no encontrada")

    return comandas

@app.get("/comandas/usuario/{usuario_reg}", status_code=200, response_model=List[Comanda2])
async def get_comandas_by_usuario(usuario_reg: str, db: Session = Depends(get_db)):
    comandas = db.query(models.Comanda).filter(models.Comanda.usuario_reg == usuario_reg).all()

    if not comandas:
        raise HTTPException(status_code=404, detail=f"No se encontraron comandas para el usuario {usuario_reg}")

    return comandas

