from sqlalchemy.schema import UniqueConstraint
from database import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class Comanda(Base):
    __tablename__ = "comandas"
    id = Column(Integer, primary_key=True, index=True)
    cantidad = Column(Integer, index=True)
    id_comanda = Column(Integer, index=True)
    id_producto = Column(Integer, index=True, nullable=True)
    id_salida_combo_coctel = Column(Integer, index=True, nullable=True)
    id_bar_combo_coctel = Column(Integer, index=True, nullable=True)
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
    id_producto_combo = Column(Integer, index=True)
    tipo_salida = Column(Integer, index=True)
    estado_comanda = Column(Integer, index=True)
    estado_impresion = Column(Integer, index=True, nullable=True)
    codigo = Column(String(255), index=True, nullable=True)

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
            "codigo": self.codigo
        }

class SincronizarParametricaTipoMetodoPago(Base):
    __tablename__ = 'sincronizarparametricatipometodopago'
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), nullable=False, unique=True, index=True)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime, nullable=True)
    fecha_sincronizacion = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('codigoClasificador', name='uq_codigoClasificador'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "codigoClasificador": self.codigoClasificador,
            "descripcion": self.descripcion,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_sincronizacion": self.fecha_sincronizacion.isoformat() if self.fecha_sincronizacion else None
        }

class SincronizarParametricaTipoDocumentoIdentidad(Base):
    __tablename__ = 'sincronizarparametricatipodocumentoidentidad'

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    fecha_sincronizacion = Column(TIMESTAMP, nullable=True)
    estado_sincronizacion = Column(String(10), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "codigoClasificador": self.codigoClasificador,
            "descripcion": self.descripcion,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_sincronizacion": self.fecha_sincronizacion.isoformat() if self.fecha_sincronizacion else None,
            "estado_sincronizacion": self.estado_sincronizacion
        }

class Cliente(Base):
    __tablename__ = 'cliente'

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_cliente = Column(String(20), unique=True, nullable=False)
    codigo_tipo_documento_identidad = Column(String(5), ForeignKey('sincronizarparametricatipodocumentoidentidad.codigoClasificador'), nullable=True)
    complemento = Column(String(10), nullable=True)
    email = Column(String(255), nullable=True)
    nombre_razon_social = Column(String(255), nullable=True)
    numero_documento = Column(String(20), nullable=True)
    telefono = Column(String(15), nullable=True)
    fecha_creacion = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    fecha_modificacion = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    tipo_documento = relationship("SincronizarParametricaTipoDocumentoIdentidad")

    def to_dict(self):
        return {
            "id": self.id,
            "codigo_cliente": self.codigo_cliente,
            "codigo_tipo_documento_identidad": self.codigo_tipo_documento_identidad,
            "complemento": self.complemento,
            "email": self.email,
            "nombre_razon_social": self.nombre_razon_social,
            "numero_documento": self.numero_documento,
            "telefono": self.telefono,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_modificacion": self.fecha_modificacion.isoformat() if self.fecha_modificacion else None
        }

from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, text
from database import Base

class Cufd(Base):
    __tablename__ = 'cufd'

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(255), nullable=True)
    codigo_control = Column(String(20), nullable=True, unique=True)
    fecha_solicitud = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    fecha_vigencia = Column(TIMESTAMP, nullable=True)
    vigente = Column(Integer, nullable=True)
    id_punto_venta = Column(Integer, ForeignKey('punto_venta.id'), nullable=False)
    direccion = Column(String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "codigo_control": self.codigo_control,
            "fecha_solicitud": self.fecha_solicitud.isoformat() if self.fecha_solicitud else None,
            "fecha_vigencia": self.fecha_vigencia.isoformat() if self.fecha_vigencia else None,
            "vigente": self.vigente,
            "id_punto_venta": self.id_punto_venta,
            "direccion": self.direccion
        }
