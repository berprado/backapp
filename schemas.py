from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, List, Optional
from pydantic import BaseModel, ConfigDict

class ComandaBase(BaseModel):
    """Esquema base para comandas"""
    cantidad: Annotated[int, "Cantidad de productos"]
    id_comanda: int
    precio_venta: Annotated[Decimal, "Precio de venta"]
    sub_total: Annotated[Decimal, "Subtotal"]
    id_barra: int
    usuario_reg: str
    estado: str
    id_operacion: int
    tipo_salida: int
    estado_comanda: int

class ComandaCreate(ComandaBase):
    """Esquema para crear comandas (entrada)"""
    id_producto: Optional[str] = None
    id_salida_combo_coctel: Optional[int] = None
    id_bar_combo_coctel: Optional[str] = None
    producto_coctel: Optional[str] = None
    cor_subtotal_anterior: Optional[Decimal] = None
    comision: Optional[Decimal] = None
    fecha_reg: date
    fecha_mod: date
    nombre: str
    id_producto_combo: Optional[str] = None
    estado_impresion: Optional[int] = None
    codigo: Optional[str] = None

class ComandaResponse(ComandaBase):
    """Esquema para respuestas (salida)"""
    id: int
    id_producto: Optional[str] = None
    id_salida_combo_coctel: Optional[int] = None
    id_bar_combo_coctel: Optional[str] = None
    producto_coctel: Optional[str] = None
    cor_subtotal_anterior: Optional[Decimal] = None
    comision: Optional[Decimal] = None
    fecha_reg: Optional[date] = None
    fecha_mod: Optional[date] = None
    nombre: str
    id_producto_combo: Optional[str] = None
    estado_impresion: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

# Esquemas antiguos mantenidos por compatibilidad
class ComandaSchema(ComandaCreate):
    pass

class ComandaDetailSchema(ComandaResponse):
    class Config:
        from_attributes = True

class MetodoPagoSchema(BaseModel):
    id: int
    codigoClasificador: str
    descripcion: str
    fecha_creacion: datetime
    fecha_sincronizacion: datetime

class EventoSignificativoSchema(BaseModel):
    id: int
    codigoClasificador: str
    descripcion: str
    fecha_creacion: datetime
    fecha_sincronizacion: datetime