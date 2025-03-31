from datetime import datetime
from decimal import Decimal
from typing import Annotated, List, Optional
from pydantic import BaseModel

class ComandaSchema(BaseModel):
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

class ComandaDetailSchema(BaseModel):
    id: int
    cantidad: Annotated[int, "Cantidad de productos"]
    id_comanda: int
    id_producto: Optional[str] = None
    id_salida_combo_coctel: Optional[int] = None
    id_bar_combo_coctel: Optional[str] = None
    precio_venta: Annotated[Decimal, "Subtotal"]
    sub_total: Annotated[Decimal, "Subtotal"]
    producto_coctel: Optional[str] = None
    id_barra: int
    usuario_reg: str
    estado: str
    id_operacion: int
    nombre: str
    id_producto_combo: Optional[str] = None
    tipo_salida: int
    estado_comanda: int
    estado_impresion: Optional[int] = None

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