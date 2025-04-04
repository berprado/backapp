from sqlalchemy.schema import UniqueConstraint
from database import Base
from sqlalchemy import Enum, Boolean, Column, Integer, String, TIMESTAMP, Numeric, Date, DateTime, ForeignKey, text, Text, BigInteger, DECIMAL, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime





class Comanda(Base):
    __tablename__ = "comandas"
    __table_args__ = {'extend_existing': True}
    
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
    fecha_reg = Column(TIMESTAMP, server_default=func.now())
    fecha_mod = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
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




class Cliente(Base):
    __tablename__ = 'cliente'
    __table_args__ = {'extend_existing': True}

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

    tipo_documento = relationship("SincronizarParametricaTipoDocumentoIdentidad", back_populates="clientes")
    

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


class Cufd(Base):
    __tablename__ = 'cufd'
    __table_args__ = {'extend_existing': True}

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


    
class FacturaCabecera(Base):
    __tablename__ = 'factura_cabecera'
    __table_args__ = {'extend_existing': True}
    nitEmisor = Column(BigInteger, nullable=False)
    razonSocialEmisor = Column(String(200), nullable=False)
    municipio = Column(String(25), nullable=False)
    telefono = Column(String(25))
    numeroFactura = Column(Integer, primary_key=True, nullable=False)
    cuf = Column(String(100), nullable=False, unique=True)
    cufd = Column(String(100), nullable=False)
    codigoSucursal = Column(Integer, nullable=False)
    direccion = Column(String(500), nullable=False)
    codigoPuntoVenta = Column(Integer)
    fechaEmision = Column(DateTime, nullable=False)
    nombreRazonSocial = Column(String(500))
    codigoTipoDocumentoIdentidad = Column(Integer, nullable=False)
    numeroDocumento = Column(String(20), nullable=False)
    complemento = Column(String(5))
    codigoCliente = Column(String(100), nullable=False)
    codigoMetodoPago = Column(Integer, nullable=False)
    numeroTarjeta = Column(BigInteger)
    montoTotal = Column(DECIMAL(17, 2), nullable=False)
    montoTotalSujetoIva = Column(DECIMAL(17, 2), nullable=False)
    codigoMoneda = Column(Integer, nullable=False, default=1)
    tipoCambio = Column(DECIMAL(17, 2), nullable=False, default=1.00)
    montoTotalMoneda = Column(DECIMAL(17, 2), nullable=False)
    montoGiftCard = Column(DECIMAL(17, 2))
    descuentoAdicional = Column(DECIMAL(17, 2), nullable=False, default=0.00)
    codigoExcepcion = Column(Integer)
    cafc = Column(String(50))
    leyenda = Column(String(200), nullable=False)
    usuario = Column(String(100), nullable=False)
    codigoDocumentoSector = Column(Integer, nullable=False, default=1)
    estadoValidacion = Column(String(50), nullable=False, default='VALIDADA')
    fechaCreacion = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    creadoPor = Column(String(100), nullable=False, default='ADMIN')
    fechaActualizacion = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    actualizadoPor = Column(String(100), nullable=False, default='ADMIN')
    detallesFirmaDigital = Column(Text)
    mensajeError = Column(Text)
    fechaValidacion = Column(TIMESTAMP)
    resultadoValidacion = Column(String(100))
    estadoFirma = Column(String(20), nullable=False, default='Pendiente')
    mensajeErrorFirma = Column(Text)
    fechaErrorFirma = Column(TIMESTAMP)
    intentosFirma = Column(Integer, nullable=False, default=0)
    estado = Column(String(20), nullable=False, default='Activa')
    fechaAnulacion = Column(DateTime)
    anuladaPor = Column(String(100))
    motivoAnulacion = Column(Text)
    enlaceSiat = Column(String(255))
    codigoRecepcion = Column(String(255))
    tipoEmision = Column(String(10), nullable=False, default='ONLINE')
    codigoEvento = Column(String(10))
    descripcionEvento = Column(String(255))
    fechaInicioEvento = Column(DateTime)
    fechaFinEvento = Column(DateTime)
    idPaquete = Column(String(50))
    estadoPaquete = Column(String(20))
    numeroSecuencia = Column(Integer)
    estadoContingencia = Column(String(20))
    fechaSincronizacion = Column(DateTime)
  

    def to_dict(self):
        return {
            'nitEmisor': self.nitEmisor,
            'razonSocialEmisor': self.razonSocialEmisor,
            'municipio': self.municipio,
            'telefono': self.telefono,
            'numeroFactura': self.numeroFactura,
            'cuf': self.cuf,
            'cufd': self.cufd,
            'codigoSucursal': self.codigoSucursal,
            'direccion': self.direccion,
            'codigoPuntoVenta': self.codigoPuntoVenta,
            'fechaEmision': self.fechaEmision.isoformat() if self.fechaEmision else None,
            'nombreRazonSocial': self.nombreRazonSocial,
            'codigoTipoDocumentoIdentidad': self.codigoTipoDocumentoIdentidad,
            'numeroDocumento': self.numeroDocumento,
            'complemento': self.complemento,
            'codigoCliente': self.codigoCliente,
            'codigoMetodoPago': self.codigoMetodoPago,
            'numeroTarjeta': self.numeroTarjeta,
            'montoTotal': float(self.montoTotal),
            'montoTotalSujetoIva': float(self.montoTotalSujetoIva),
            'codigoMoneda': self.codigoMoneda,
            'tipoCambio': float(self.tipoCambio),
            'montoTotalMoneda': float(self.montoTotalMoneda),
            'montoGiftCard': float(self.montoGiftCard) if self.montoGiftCard is not None else None,
            'descuentoAdicional': float(self.descuentoAdicional),
            'codigoExcepcion': self.codigoExcepcion,
            'cafc': self.cafc,
            'leyenda': self.leyenda,
            'usuario': self.usuario,
            'codigoDocumentoSector': self.codigoDocumentoSector,
            'estadoValidacion': self.estadoValidacion,
            'fechaCreacion': self.fechaCreacion.isoformat() if self.fechaCreacion else None,
            'creadoPor': self.creadoPor,
            'fechaActualizacion': self.fechaActualizacion.isoformat() if self.fechaActualizacion else None,
            'actualizadoPor': self.actualizadoPor,
            'detallesFirmaDigital': self.detallesFirmaDigital,
            'mensajeError': self.mensajeError,
            'fechaValidacion': self.fechaValidacion.isoformat() if self.fechaValidacion else None,
            'resultadoValidacion': self.resultadoValidacion,
            'estadoFirma': self.estadoFirma,
            'mensajeErrorFirma': self.mensajeErrorFirma,
            'fechaErrorFirma': self.fechaErrorFirma.isoformat() if self.fechaErrorFirma else None,
            'intentosFirma': self.intentosFirma,
            'estado': self.estado,
            'fechaAnulacion': self.fechaAnulacion.isoformat() if self.fechaAnulacion else None,
            'anuladaPor': self.anuladaPor,
            'motivoAnulacion': self.motivoAnulacion,
            'enlaceSiat': self.enlaceSiat,
            'codigoRecepcion': self.codigoRecepcion,
            'tipoEmision': self.tipoEmision,
            'codigoEvento': self.codigoEvento,
            'descripcionEvento': self.descripcionEvento,
            'fechaInicioEvento': self.fechaInicioEvento.isoformat() if self.fechaInicioEvento else None,
            'fechaFinEvento': self.fechaFinEvento.isoformat() if self.fechaFinEvento else None,
            'idPaquete': self.idPaquete,
            'estadoPaquete': self.estadoPaquete,
            'numeroSecuencia': self.numeroSecuencia,
            'estadoContingencia': self.estadoContingencia,
            'fechaSincronizacion': self.fechaSincronizacion.isoformat() if self.fechaSincronizacion else None,
        }


class FacturaDetalle(Base):
    __tablename__ = 'factura_detalle'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    numeroFactura = Column(Integer, ForeignKey('factura_cabecera.numeroFactura'), nullable=False)
    actividadEconomica = Column(String(10), nullable=False)
    codigoProductoSin = Column(Integer, nullable=False, default=99100)
    codigoProducto = Column(String(50), nullable=False)
    descripcion = Column(String(500), nullable=False)
    cantidad = Column(DECIMAL(17, 2), nullable=False)
    unidadMedida = Column(Integer, nullable=False)
    precioUnitario = Column(DECIMAL(17, 2), nullable=False)
    montoDescuento = Column(DECIMAL(17, 2))
    subTotal = Column(DECIMAL(17, 2), nullable=False)
    numeroSerie = Column(String(1500))
    numeroImei = Column(String(1500))
    

    def to_dict(self):
        return {
            'id': self.id,
            'numeroFactura': self.numeroFactura,
            'actividadEconomica': self.actividadEconomica,
            'codigoProductoSin': self.codigoProductoSin,
            'codigoProducto': self.codigoProducto,
            'descripcion': self.descripcion,
            'cantidad': float(self.cantidad),
            'unidadMedida': self.unidadMedida,
            'precioUnitario': float(self.precioUnitario),
            'montoDescuento': float(self.montoDescuento) if self.montoDescuento is not None else None,
            'subTotal': float(self.subTotal),
            'numeroSerie': self.numeroSerie,
            'numeroImei': self.numeroImei
        }
    


class ProductoSiat(Base):
    __tablename__ = 'productos_siat'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo_origen = Column(Enum('producto', 'combo', name='tipo_origen_enum'), nullable=False)  # Campo faltante
    id_origen = Column(Integer, nullable=True)  # Campo faltante
    categoria = Column(String(255), nullable=True)
    codigo = Column(String(191), nullable=False, unique=True)  # Ajustar la longitud del VARCHAR y agregar unique
    codigo_sin = Column(Integer, nullable=True)
    nombre = Column(String(255), nullable=True)
    precio_venta = Column(DECIMAL(10, 2), nullable=True)
    codigo_unidad_medida = Column(Integer, nullable=True)
    unidad_medida = Column(String(255), nullable=True)  # Añadir la columna unidad_medida
    unidad_medida_sin = Column(Integer, nullable=True)
    codigoActividad = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    fecha_actualizacion = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    estado_sincronizacion = Column(String(255), nullable=True)
   

    def to_dict(self):
        return {
            "id": self.id,
            "tipo_origen": self.tipo_origen,  # Incluir el nuevo campo
            "id_origen": self.id_origen,      # Incluir el nuevo campo
            "categoria": self.categoria,
            "codigo": self.codigo,
            "codigo_sin": self.codigo_sin,
            "nombre": self.nombre,
            "precio_venta": float(self.precio_venta) if self.precio_venta else None,
            "codigo_unidad_medida": self.codigo_unidad_medida,
            "unidad_medida": self.unidad_medida,  # Incluir unidad_medida
            "unidad_medida_sin": self.unidad_medida_sin,
            "codigoActividad": self.codigoActividad,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            "estado_sincronizacion": self.estado_sincronizacion
        }

class BarComboCoctel(Base):
    __tablename__ = 'bar_combo_coctel'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    codigo = Column(String(255), nullable=False)
    descripcion = Column(String(255), nullable=True)
    id_categoria = Column(Integer, ForeignKey('alm_categoria.id'), nullable=True)
    id_barra = Column(Integer, ForeignKey('bar_barra.id'), nullable=True)
    usuario_reg = Column(String(255), nullable=False)
    fecha_reg = Column(Date, nullable=True)
    fecha_mod = Column(Date, nullable=True)
    estado = Column(String(3), nullable=False)

    # Relaciones
    categoria = relationship("AlmCategoria", foreign_keys=[id_categoria])
    barra = relationship("BarBarra", foreign_keys=[id_barra])

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "codigo": self.codigo,
            "descripcion": self.descripcion,
            "id_categoria": self.id_categoria,
            "id_barra": self.id_barra,
            "usuario_reg": self.usuario_reg,
            "fecha_reg": self.fecha_reg.isoformat() if self.fecha_reg else None,
            "fecha_mod": self.fecha_mod.isoformat() if self.fecha_mod else None,
            "estado": self.estado
        }

# También necesitamos definir las clases para las tablas relacionadas 
class AlmCategoria(Base):
    __tablename__ = 'alm_categoria'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    # Añadir otros campos según sea necesario
    # Este es un modelo mínimo para establecer la relación

class BarBarra(Base):
    __tablename__ = 'bar_barra'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    # Añadir otros campos según sea necesario
    # Este es un modelo mínimo para establecer la relación

class PuntoVenta(Base):
    __tablename__ = 'punto_venta'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_punto_venta = Column(Integer, nullable=False, unique=True)  # O revisar si debe ser la clave primaria
    nombre_punto_venta = Column(String(255), nullable=True)
    descripcion = Column(String(255), nullable=True)
    tipo = Column(String(255), nullable=True)
    estado = Column(Enum('Habilitado', 'Deshabilitado'), nullable=False, default='Habilitado')
    cod_sucursal = Column(Integer, nullable=False)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_modificacion = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con CUIS
    cuis = relationship("Cuis", back_populates="punto_venta")
   

    def to_dict(self):
        return {
            'id': self.id,
            'codigo_punto_venta': self.codigo_punto_venta,
            'nombre_punto_venta': self.nombre_punto_venta,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'estado': self.estado,
            'cod_sucursal': self.cod_sucursal,
            'fecha_creacion': self.fecha_creacion,
            'fecha_modificacion': self.fecha_modificacion
        }

class Cuis(Base):
    __tablename__ = 'cuis'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(10), nullable=True)  # Ajustado para permitir NULL si la base de datos lo permite
    fecha_solicitud = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)  # Agregado este campo
    fecha_vigencia = Column(DateTime, nullable=True)
    vigente = Column(Boolean, default=True)
    codigo_punto_venta = Column(Integer, ForeignKey('punto_venta.codigo_punto_venta'), nullable=False)

    # Relación con PuntoVenta
    punto_venta = relationship("PuntoVenta", back_populates="cuis")
    

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'fecha_solicitud': self.fecha_solicitud,  # Añadido al diccionario
            'fecha_vigencia': self.fecha_vigencia,
            'vigente': self.vigente,
            'codigo_punto_venta': self.codigo_punto_venta,
            'punto_venta': self.punto_venta.to_dict() if self.punto_venta else None
        }
class SincronizarParametricaMotivoAnulacion(Base):
    __tablename__ = 'sincronizarparametricamotivoanulacion'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigoClasificador = Column(String(5), nullable=False, unique=True)  # Código del clasificador
    descripcion = Column(String(255), nullable=True)  # Descripción del motivo de anulación
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())  # Fecha de creación
    fecha_sincronizacion = Column(TIMESTAMP, nullable=True)  # Fecha de sincronización
    estado_sincronizacion = Column(String(10), nullable=True)  # Estado de sincronización
   
    # Método to_dict para convertir la instancia en un diccionario
    def to_dict(self):
        return {
            'id': self.id,
            'codigoClasificador': self.codigoClasificador,
            'descripcion': self.descripcion,
            'fecha_creacion': self.fecha_creacion,
            'fecha_sincronizacion': self.fecha_sincronizacion,
            'estado_sincronizacion': self.estado_sincronizacion
        }

class SincronizarListaMensajesServicios(Base):
    __tablename__ = 'sincronizarlistamensajesservicios'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(10), nullable=False, unique=True)  # Código clasificador
    descripcion = Column(String(255), nullable=True)  # Descripción del mensaje
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())  # Fecha de creación
    fecha_sincronizacion = Column(TIMESTAMP, nullable=True)  # Fecha de sincronización
    estado_sincronizacion = Column(String(10), nullable=True)  # Estado de sincronización
   
    # Método to_dict opcional para convertir el objeto en un diccionario
    def to_dict(self):
        return {
            'id': self.id,
            'codigoClasificador': self.codigoClasificador,
            'descripcion': self.descripcion,
            'fecha_creacion': self.fecha_creacion,
            'fecha_sincronizacion': self.fecha_sincronizacion,
            'estado_sincronizacion': self.estado_sincronizacion
        }

class SincronizarParametricaTipoEmision(Base):
    __tablename__ = 'sincronizarparametricatipoemision'
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    fecha_sincronizacion = Column(TIMESTAMP, nullable=True)
    estado_sincronizacion = Column(String(10), nullable=True)

    __table_args__ = (
        UniqueConstraint('codigoClasificador', name='uq_codigoClasificador'), {'extend_existing': True}
         
        
    )

    def to_dict(self):
        return {
            "id": self.id,
            "codigoClasificador": self.codigoClasificador,
            "descripcion": self.descripcion,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_sincronizacion": self.fecha_sincronizacion.isoformat() if self.fecha_sincronizacion else None,
            "estado_sincronizacion": self.estado_sincronizacion
        }
    
class SincronizarParametricaEventosSignificativos(Base):
    __tablename__ = 'sincronizarparametricaeventossignificativos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    fecha_sincronizacion = Column(TIMESTAMP, nullable=True)
    estado_sincronizacion = Column(String(10), nullable=True)

    __table_args__ = (
        UniqueConstraint('codigoClasificador', name='uq_codigoClasificador'), {'extend_existing': True}
    )

    def to_dict(self):
        return {
            "id": self.id,
            "codigoClasificador": self.codigoClasificador,
            "descripcion": self.descripcion,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_sincronizacion": self.fecha_sincronizacion.isoformat() if self.fecha_sincronizacion else None,
            "estado_sincronizacion": self.estado_sincronizacion,
        }
    
class SincronizarActividades(Base):
    __tablename__ = 'sincronizaractividades'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoCaeb = Column(String(10), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    tipoActividad = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    fecha_sincronizacion = Column(TIMESTAMP, nullable=True)
    estado_sincronizacion = Column(String(10), nullable=True)

     # Add this to prevent multiple definitions
    def to_dict(self):
        return {
            'id': self.id,
            'codigoCaeb': self.codigoCaeb,
            'descripcion': self.descripcion,
            'tipoActividad': self.tipoActividad,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_sincronizacion': self.fecha_sincronizacion.isoformat() if self.fecha_sincronizacion else None,
            'estado_sincronizacion': self.estado_sincronizacion
        }

class SincronizarParametricaUnidadMedida(Base):
    __tablename__ = 'sincronizarparametricaunidadmedida'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
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

class SincronizarParametricaTiposFactura(Base):
    __tablename__ = 'sincronizarparametricatiposfactura'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
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

class SincronizarParametricaTipoPuntoVenta(Base):
    __tablename__ = 'sincronizarparametricatipopuntoventa'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
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

class SincronizarParametricaTipoMoneda(Base):
    __tablename__ = 'sincronizarparametricatipomoneda'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
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

class SincronizarParametricaTipoHabitacion(Base):
    __tablename__ = 'sincronizarparametricatipohabitacion'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
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

class SincronizarParametricaTipoDocumentoSector(Base):
    __tablename__ = 'sincronizarparametricatipodocumentosector'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
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

class SincronizarParametricaPaisOrigen(Base):
    __tablename__ = 'sincronizarparametricapaisorigen'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
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

class SincronizarListaProductosServicios(Base):
    __tablename__ = 'sincronizarlistaproductosservicios'
    

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoActividad = Column(String(20), nullable=False)
    codigoProducto = Column(String(20), nullable=False)
    descripcionProducto = Column(String(255), nullable=True)
    nandina = Column(Text, nullable=True)
    fecha_creacion = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    fecha_sincronizacion = Column(TIMESTAMP, nullable=True)
    estado_sincronizacion = Column(String(10), nullable=True)

    __table_args__ = (UniqueConstraint('codigoActividad', 'codigoProducto', name='unique_codigo'), {'extend_existing': True})

    def to_dict(self):
        return {
            "id": self.id,
            "codigoActividad": self.codigoActividad,
            "codigoProducto": self.codigoProducto,
            "descripcionProducto": self.descripcionProducto,
            "nandina": self.nandina,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_sincronizacion": self.fecha_sincronizacion.isoformat() if self.fecha_sincronizacion else None,
            "estado_sincronizacion": self.estado_sincronizacion
        }

class SincronizarListaActividadesDocumentoSector(Base):
    __tablename__ = 'sincronizarlistaactividadesdocumentosector'

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoActividad = Column(String(10), nullable=False)
    codigoDocumentoSector = Column(Integer, nullable=False)
    tipoDocumentoSector = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    fecha_sincronizacion = Column(TIMESTAMP, nullable=True)
    estado_sincronizacion = Column(String(10), nullable=True)

    __table_args__ = (UniqueConstraint('codigoActividad', 'codigoDocumentoSector', name='codigoActividad'), {'extend_existing': True})

    def to_dict(self):
        return {
            "id": self.id,
            "codigoActividad": self.codigoActividad,
            "codigoDocumentoSector": self.codigoDocumentoSector,
            "tipoDocumentoSector": self.tipoDocumentoSector,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_sincronizacion": self.fecha_sincronizacion.isoformat() if self.fecha_sincronizacion else None,
            "estado_sincronizacion": self.estado_sincronizacion
        }
    
class SincronizarParametricaTipoMetodoPago(Base):
    __tablename__ = 'sincronizarparametricatipometodopago'
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), nullable=False, unique=True, index=True)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime, nullable=True)
    fecha_sincronizacion = Column(DateTime, nullable=True)
    estado_sincronizacion = Column(String(10), nullable=True)  # Se añade esta columna

    __table_args__ = (
        UniqueConstraint('codigoClasificador', name='uq_codigoClasificador'), {'extend_existing': True})

    def to_dict(self):
        return {
            "id": self.id,
            "codigoClasificador": self.codigoClasificador,
            "descripcion": self.descripcion,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_sincronizacion": self.fecha_sincronizacion.isoformat() if self.fecha_sincronizacion else None,
            "estado_sincronizacion": self.estado_sincronizacion  # Se añade al diccionario
        }
    
class SincronizarParametricaTipoDocumentoIdentidad(Base):
    __tablename__ = 'sincronizarparametricatipodocumentoidentidad'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoClasificador = Column(String(5), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    fecha_sincronizacion = Column(TIMESTAMP, nullable=True)
    estado_sincronizacion = Column(String(10), nullable=True)

        # Relación con la tabla Cliente
    clientes = relationship("Cliente", back_populates="tipo_documento")
    
    def to_dict(self):
        return {
            "id": self.id,
            "codigoClasificador": self.codigoClasificador,
            "descripcion": self.descripcion,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_sincronizacion": self.fecha_sincronizacion.isoformat() if self.fecha_sincronizacion else None,
            "estado_sincronizacion": self.estado_sincronizacion
        }

class SincronizarListaLeyendasFactura(Base):
    __tablename__ = 'sincronizarlistaleyendasfactura'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigoActividad = Column(String(255), nullable=False)
    descripcionLeyenda = Column(Text, nullable=True)
    fecha_creacion = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    fecha_sincronizacion = Column(TIMESTAMP, nullable=True)
    estado_sincronizacion = Column(String(10), nullable=True)
    

    def to_dict(self):
        return {
            "id": self.id,
            "codigoActividad": self.codigoActividad,
            "descripcionLeyenda": self.descripcionLeyenda,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_sincronizacion": self.fecha_sincronizacion.isoformat() if self.fecha_sincronizacion else None,
            "estado_sincronizacion": self.estado_sincronizacion
        }
class SincronizacionEstado(Base):
    __tablename__ = "sincronizacion_estado"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    ultima_sincronizacion = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "ultima_sincronizacion": self.ultima_sincronizacion.isoformat() if self.ultima_sincronizacion else None
        }
