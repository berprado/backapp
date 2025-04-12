from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime
from sqlalchemy.schema import UniqueConstraint
from database import Base



class Comanda(Base):
    __tablename__ = "comandas"
    id = Column(Integer, primary_key=True, index=True)
    cantidad = Column(Integer, index=True)
    id_comanda = Column(Integer, index=True)
    id_producto = Column(String, index=True, nullable=True)
    id_salida_combo_coctel = Column(Integer, index=True, nullable=True)
    id_bar_combo_coctel = Column(String, index=True, nullable=True)
    precio_venta = Column(Numeric(10, 2), index=True)
    sub_total = Column(Numeric(10, 2), index=True)
    producto_coctel = Column(String, index=True, nullable=True)
    cor_subtotal_anterior = Column(Numeric(10, 2), index=True, nullable=True)
    id_barra = Column(Integer, index=True)
    comision = Column(Numeric(10, 2), index=True, nullable=True)
    usuario_reg = Column(String, index=True)
    fecha_reg = Column(Date, index=True)
    fecha_mod = Column(Date, index=True)
    estado = Column(String(3), index=True)
    id_operacion = Column(Integer, index=True)
    nombre = Column(String, index=True)
    id_producto_combo = Column(String, index=True)
    tipo_salida = Column(Integer, index=True)
    estado_comanda = Column(Integer, index=True)
    estado_impresion = Column(Integer, index=True, nullable=True)
    

    



class Comanda_Cat(Base):
    __tablename__ = "comandas_cat"
    id = Column(Integer, primary_key=True, index=True)
    cantidad = Column(Integer, index=True)
    id_comanda = Column(Integer, index=True)
    id_producto = Column(Integer, index=True, nullable=True)
    id_salida_combo_coctel = Column(Integer, index=True, nullable=True)
    id_bar_combo_coctel = Column(Integer, index=True, nullable=True)
    precio_venta = Column(Numeric(10,2), index=True)
    sub_total = Column(Numeric(10,2), index=True)
    producto_coctel = Column(String, index=True, nullable=True)
    cor_subtotal_anterior = Column(Numeric(10,2), index=True, nullable=True)
    id_barra = Column(Integer, index=True)
    comision = Column(Numeric(10,2), index=True, nullable=True)
    usuario_reg = Column(String, index=True)
    fecha_reg = Column(Date, index=True)
    fecha_mod = Column(Date, index=True)    
    estado = Column(String(3), index=True)
    id_operacion = Column(Integer, index=True)
    nombre = Column(String, index=True)
    id_producto_combo = Column(Integer, index=True)
    tipo_salida = Column(Integer, index=True)
    estado_comanda = Column(Integer, index=True)
    estado_impresion = Column(Integer, index=True, nullable=True)
    codigo = Column(String(255), index=True, nullable=True)
    categoria_nombre = Column(String(255), index=True, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "cantidad": int(self.cantidad),
            "id_comanda": self.id_comanda,
            "id_producto": self.id_producto,
            "id_salida_combo_coctel": self.id_salida_combo_coctel,
            "id_bar_combo_coctel": self.id_bar_combo_coctel,
            "precio_venta": str(self.precio_venta),
            "sub_total": str(self.sub_total),
            "producto_coctel": self.producto_coctel,
            "cor_subtotal_anterior": str(self.cor_subtotal_anterior),
            "id_barra": self.id_barra,
            "comision": str(self.comision),
            "usuario_reg": self.usuario_reg,
            "fecha_reg": self.fecha_reg.isoformat() if self.fecha_reg else None,
            "fecha_mod": self.fecha_mod.isoformat() if self.fecha_mod else None,
            "estado": self.estado,
            "id_operacion": self.id_operacion,
            "nombre": self.nombre,
            "id_producto_combo": self.id_producto_combo,
            "tipo_salida": self.tipo_salida,
            "estado_comanda": self.estado_comanda,
            "estado_impresion": self.estado_impresion,
            "codigo": self.codigo,
            "categoria_nombre": self.categoria_nombre
        }


