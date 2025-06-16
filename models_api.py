from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime
from sqlalchemy.schema import UniqueConstraint
from database_api import Base  # Actualizada la importación desde database_api

class Comanda(Base):
    __tablename__ = "comandas"  # Vista SQL que muestra datos de comandas
    id = Column(Integer, primary_key=True, index=True)
    cantidad = Column(Integer, index=True)
    id_comanda = Column(Integer, index=True)
    id_producto = Column(String, index=True, nullable=True)  # String para reflejar los códigos
    id_salida_combo_coctel = Column(Integer, index=True, nullable=True)
    id_bar_combo_coctel = Column(String, index=True, nullable=True)  # String para reflejar los códigos
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
    nombre = Column(String, index=True)  # Nombre del producto según la vista SQL
    id_producto_combo = Column(String, index=True)  # String para reflejar los códigos
    tipo_salida = Column(Integer, index=True)
    estado_comanda = Column(Integer, index=True)
    estado_impresion = Column(Integer, index=True, nullable=True)
    
    def to_dict(self):
        """Convierte el modelo a un diccionario para serialización"""
        precio_venta_val = getattr(self, "precio_venta", None)
        sub_total_val = getattr(self, "sub_total", None)
        cor_subtotal_val = getattr(self, "cor_subtotal_anterior", None)
        comision_val = getattr(self, "comision", None)
        fecha_reg_val = getattr(self, "fecha_reg", None)
        fecha_mod_val = getattr(self, "fecha_mod", None)
        
        return {
            "id": getattr(self, "id", None),
            "cantidad": getattr(self, "cantidad", None),
            "id_comanda": getattr(self, "id_comanda", None),
            "id_producto": getattr(self, "id_producto", None),
            "id_salida_combo_coctel": getattr(self, "id_salida_combo_coctel", None),
            "id_bar_combo_coctel": getattr(self, "id_bar_combo_coctel", None),
            "precio_venta": float(precio_venta_val) if precio_venta_val is not None else None,
            "sub_total": float(sub_total_val) if sub_total_val is not None else None,
            "producto_coctel": getattr(self, "producto_coctel", None),
            "cor_subtotal_anterior": float(cor_subtotal_val) if cor_subtotal_val is not None else None,
            "id_barra": getattr(self, "id_barra", None),
            "comision": float(comision_val) if comision_val is not None else None,
            "usuario_reg": getattr(self, "usuario_reg", None),
            "fecha_reg": fecha_reg_val.isoformat() if fecha_reg_val is not None else None,
            "fecha_mod": fecha_mod_val.isoformat() if fecha_mod_val is not None else None,
            "estado": getattr(self, "estado", None),
            "id_operacion": getattr(self, "id_operacion", None),
            "nombre": getattr(self, "nombre", None),
            "id_producto_combo": getattr(self, "id_producto_combo", None),
            "tipo_salida": getattr(self, "tipo_salida", None),
            "estado_comanda": getattr(self, "estado_comanda", None),
            "estado_impresion": getattr(self, "estado_impresion", None),
        }

class Comanda_Cat(Base):
    __tablename__ = "comandas_cat"
    id = Column(Integer, primary_key=True, index=True)
    cantidad = Column(Integer, index=True)
    id_comanda = Column(Integer, index=True)
    id_producto = Column(Integer, index=True, nullable=True)
    id_salida_combo_coctel = Column(Integer, index=True, nullable=True)
    id_bar_combo_coctel = Column(Integer, index=True, nullable=True)
    precio_venta = Column(Numeric(10,2), index=True)
    
    def to_dict(self):
        """Convierte el modelo a un diccionario para serialización"""
        precio_venta_val = getattr(self, "precio_venta", None)
        
        return {
            "id": getattr(self, "id", None),
            "cantidad": getattr(self, "cantidad", None),
            "id_comanda": getattr(self, "id_comanda", None),
            "id_producto": getattr(self, "id_producto", None),
            "id_salida_combo_coctel": getattr(self, "id_salida_combo_coctel", None),
            "id_bar_combo_coctel": getattr(self, "id_bar_combo_coctel", None),
            "precio_venta": float(precio_venta_val) if precio_venta_val is not None else None
        }
