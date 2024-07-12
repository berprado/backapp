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
from fpdf import FPDF
import models
from database import engine, SessionLocal
from crud import get_comanda_data
from sqlalchemy.orm import Session
import re

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
    
# class Comanda1(BaseModel):
#     cantidad: Annotated[int, "Cantidad de productos"]
#     id_comanda: int
#     id_producto: Optional[int] = None
#     id_salida_combo_coctel: int
#     id_bar_combo_coctel: int
#     precio_venta: Annotated[float, "Precio de venta"]
#     sub_total: Annotated[float, "Subtotal"]
#     producto_coctel: str
#     cor_subtotal_anterior: Annotated[float, "Subtotal anterior"]
#     id_barra: int
#     comision: Annotated[float, "Comisión"]
#     usuario_reg: str
#     fecha_reg: str
#     fecha_mod: str
#     estado: str
#     id_operacion: int
#     producto: str
#     id_producto_combo: int
#     tipo_salida: int
#     estado_comanda: int
#     estado_impresion: int
#     codigo: str
#     categoria_nombre: str

class Comanda2(BaseModel):
    id: int
    cantidad: Annotated[int, "Cantidad de productos"]
    id_comanda: int
    id_producto: Optional[int] = None
    id_salida_combo_coctel: Optional[int] = None
    id_bar_combo_coctel: Optional[int] = None
    precio_venta: Annotated[Decimal, "Subtotal"]
    sub_total: Annotated[Decimal, "Subtotal"]
    producto_coctel: Optional[str] = None
    id_barra: int
    usuario_reg: str
    estado: str
    id_operacion: int
    nombre: str
    id_producto_combo: int
    tipo_salida: int
    estado_comanda: int
    estado_impresion: Optional[int] = None


class SincronizarParametricaTipoMetodoPago(BaseModel):
    id: int
    codigoClasificador: str
    descripcion: str
    fecha_creacion: datetime
    fecha_sincronizacion: datetime

class sincronizarParametricaEventosSignificativos(BaseModel):
    id: int
    codigoClasificador: str
    descripcion: str
    fecha_creacion: datetime
    fecha_sincronizacion: datetime

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# Commented out code
# @app.get("/com_cat", status_code=200, response_model=List[Comanda1])
# async def get_all_comandas(db: Session = Depends(get_db)):
#     comandas_cat = db.query(models.Comanda_Cat).all()

#     if not comandas_cat:
#         raise HTTPException(status_code=404, detail="No se encontraron comandas")

#     return comandas_cat

@app.get("/", status_code=200, response_model=List[Comanda2])
async def get_all_comandas(db: Session = Depends(get_db)):
    comandas = db.query(models.Comanda).all()

    if not comandas:
        raise HTTPException(status_code=404, detail="No se encontraron comandas")

    return comandas


@app.get("/metodos_pago", response_model=List[SincronizarParametricaTipoMetodoPago])
async def get_metodos_pago(ids: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if ids:
        ids_list = [int(id) for id in ids.split(",")]
        metodos_pago = db.query(models.SincronizarParametricaTipoMetodoPago).filter(models.SincronizarParametricaTipoMetodoPago.id.in_(ids_list)).all()
    else:
        metodos_pago = db.query(models.SincronizarParametricaTipoMetodoPago).all()
    
    if not metodos_pago:
        raise HTTPException(status_code=404, detail="No se encontraron métodos de pago")
    
    return metodos_pago

@app.get("/eventos_significativos", response_model=List[sincronizarParametricaEventosSignificativos])
async def get_eventos_significtivos(ids: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if ids:
        ids_list = [int(id) for id in ids.split(",")]
        eventos_significativos = db.query(models.sincronizarParametricaEventosSignificativos).filter(models.sincronizarParametricaEventosSignificativos.id.in_(ids_list)).all()
    else:
        eventos_significativos = db.query(models.sincronizarParametricaEventosSignificativos).all()
    
    if not eventos_significativos:
        raise HTTPException(status_code=404, detail="No se encontraron eventos significativos")
    
    return eventos_significativos

@app.get("/get_json_files", response_model=List[str])
async def get_json_files():
    files = os.listdir('archivos')
    return files

@app.get("/generate_invoice/{file}")
async def generate_invoice(file: str):
    if not os.path.isfile(f'archivos/{file}'):
        raise HTTPException(status_code=404, detail="File not found")

    pdf = FPDF()

    # Add code here to generate the invoice in PDF format  using the FPDF library
    # Generate the invoice content
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add invoice details
    db = db_dependency

    pdf.cell(0, 10, "Invoice", ln=True, align="C")
    pdf.cell(0, 10, f"File: {file}", ln=True, align="C")
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")

    # Add invoice items
    pdf.ln(20)
    pdf.cell(40, 10, "Product", border=1)
    comandas = db.query(models.Comanda).all()

    pdf.cell(40, 10, "Quantity", border=1)
    pdf.cell(40, 10, "Price", border=1)
    pdf.cell(40, 10, "Subtotal", border=1)
    pdf.ln(10)

    # Iterate over the comandas and add them to the invoice
    for comanda in comandas:
        pdf.cell(40, 10, comanda.producto, border=1)
        pdf.cell(40, 10, str(comanda.cantidad), border=1)
        pdf.cell(40, 10, str(comanda.precio_venta), border=1)
        pdf.cell(40, 10, str(comanda.sub_total), border=1)
        pdf.ln(10)

    # Save the invoice as a PDF file
    pdf.output('invoice.pdf', 'F')
    return {"message": "Invoice generated successfully"}

@app.get("/comandas/{id_comanda}", status_code=status.HTTP_200_OK, response_model=List[Comanda2])
async def get_comanda(id_comanda: str, db: Session = Depends(get_db)):
    id_comanda_list = [int(id) for id in id_comanda.split(',')]
    comandas = [comanda for id in id_comanda_list for comanda in db.query(models.Comanda).filter(models.Comanda.id_comanda == id).all()]

    if not comandas:
        raise HTTPException(status_code=404, detail=f"Comanda {id_comanda} no encontrada")

    return comandas

@app.get("/comandas/operacion/{id_operacion}", status_code=200, response_model=List[Comanda2])
async def get_comandas_by_operacion(id_operacion: int, estado_impresion: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Comanda).filter(models.Comanda.id_operacion == id_operacion)

    if estado_impresion is not None:
        if estado_impresion.lower() == "null":
            query = query.filter(models.Comanda.estado_impresion.is_(None))
        else:
            try:
                estado_impresion_int = int(estado_impresion)
                query = query.filter(models.Comanda.estado_impresion == estado_impresion_int)
            except ValueError:
                raise HTTPException(status_code=400, detail="estado_impresion debe ser un número o 'null'")

    comandas = query.all()

    if not comandas:
        raise HTTPException(status_code=404, detail=f"No se encontraron comandas para la operación {id_operacion} con el estado de impresión especificado")

    return comandas
@app.get("/save_comandas")
async def save_comandas(comandas: str, db: Session = Depends(get_db)):
    # Validación de entrada
    if not re.match(r'^(\d+,)*\d+$', comandas):
        raise HTTPException(status_code=400, detail="Invalid comandas format")

    # Manejo de errores para la conversión a int
    try:
        comandas_list = [int(comanda_id) for comanda_id in comandas.split(',')]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid comanda_id")

    all_comandas_data = get_comanda_data(comandas_list, db)

    # Metadata
    metadatos = {
        "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cantidad_comandas": len(all_comandas_data)
    }

    # File structure with metadata and data
    archivo_con_metadatos = {
        "metadatos": metadatos,
        "comandas": all_comandas_data
    }

    # Generate a unique file name with the current date and time
    nombre_archivo = f'archivos/comandas_result_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json'

    # Write the data to the JSON file
    try:
        with open(nombre_archivo, 'w') as f:
            json.dump(archivo_con_metadatos, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": f"Comandas guardadas con éxito en el archivo {nombre_archivo}"}
  

  
@app.get("/favicon.ico", status_code=200)
async def favicon():
    return FileResponse('static/favicon.ico')

@app.get("/comandas/usuario/{usuario_reg}", status_code=200, response_model=List[Comanda2])
async def get_comandas_by_usuario(usuario_reg: str, db: Session = Depends(get_db)):
    comandas = db.query(models.Comanda).filter(models.Comanda.usuario_reg == usuario_reg).all()

    if not comandas:
        raise HTTPException(status_code=404, detail=f"No se encontraron comandas para el usuario {usuario_reg}")

    return comandas

