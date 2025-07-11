"""
Modelos de datos para el sistema de facturación refactorizado.
Define las estructuras de datos con validaciones según normativas del SIN.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

# Enums para códigos del SIN
class TipoDocumento(Enum):
    """Tipos de documento de identidad."""
    CI = 1
    CEX = 2
    PAS = 3
    OD = 4
    NIT = 5

class TipoEmision(Enum):
    """Tipos de emisión de factura."""
    ONLINE = 1
    OFFLINE = 2
    MASIVA = 3

class TipoFactura(Enum):
    """Tipos de factura según el SIN."""
    COMPRA_VENTA = 1
    NOTA_FISCAL_COMPRA_VENTA = 2
    FACTURA_ESPECIAL_COMPRA_VENTA = 3

class CodigoExcepcion(Enum):
    """Códigos de excepción para validaciones."""
    SIN_EXCEPCION = 0
    NIT_INVALIDO = 1

class EstadoFactura(Enum):
    """Estados posibles de una factura."""
    BORRADOR = "BORRADOR"
    VALIDADA = "VALIDADA"
    OBSERVADA = "OBSERVADA"
    ANULADA = "ANULADA"
    RECHAZADA = "RECHAZADA"

@dataclass
class Cliente:
    """Información del cliente/comprador."""
    nit: str
    razon_social: str
    tipo_documento: TipoDocumento = TipoDocumento.NIT
    codigo_excepcion: CodigoExcepcion = CodigoExcepcion.SIN_EXCEPCION
    email: Optional[str] = None
    telefono: Optional[str] = None
    
    def __post_init__(self):
        """Validaciones post-inicialización."""
        self.validate()
    
    def validate(self):
        """Valida los datos del cliente según normativas del SIN."""
        errors = []
        
        # Validar NIT
        if not self.nit:
            errors.append("NIT es obligatorio")
        elif self.tipo_documento == TipoDocumento.NIT and self.codigo_excepcion == CodigoExcepcion.SIN_EXCEPCION:
            if not self.nit.isdigit():
                errors.append("NIT debe ser numérico cuando no hay excepción")
        
        # Validar razón social
        if not self.razon_social or len(self.razon_social.strip()) == 0:
            errors.append("Razón social es obligatoria")
        elif len(self.razon_social) > 500:
            errors.append("Razón social no puede exceder 500 caracteres")
        
        # Validar email si está presente
        if self.email and '@' not in self.email:
            errors.append("Email tiene formato inválido")
        
        if errors:
            raise ValueError(f"Errores en Cliente: {'; '.join(errors)}")

@dataclass
class DetalleFactura:
    """Detalle de un item en la factura."""
    codigo_producto: str
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    codigo_unidad_medida: int = 1  # Por defecto: unidad
    descuento: Decimal = Decimal('0')
    codigo_actividad_economica: Optional[str] = None
    
    def __post_init__(self):
        """Validaciones y cálculos post-inicialización."""
        self.validate()
    
    def validate(self):
        """Valida los datos del detalle."""
        errors = []
        
        if not self.codigo_producto:
            errors.append("Código de producto es obligatorio")
        
        if not self.descripcion or len(self.descripcion.strip()) == 0:
            errors.append("Descripción es obligatoria")
        elif len(self.descripcion) > 500:
            errors.append("Descripción no puede exceder 500 caracteres")
        
        if self.cantidad <= 0:
            errors.append("Cantidad debe ser mayor a cero")
        
        if self.precio_unitario <= 0:
            errors.append("Precio unitario debe ser mayor a cero")
        
        if self.descuento < 0:
            errors.append("Descuento no puede ser negativo")
        
        if errors:
            raise ValueError(f"Errores en DetalleFactura: {'; '.join(errors)}")
    
    @property
    def subtotal(self) -> Decimal:
        """Calcula el subtotal del item."""
        return (self.cantidad * self.precio_unitario) - self.descuento
    
    @property
    def subtotal_redondeado(self) -> Decimal:
        """Subtotal redondeado a 2 decimales."""
        return round(self.subtotal, 2)

@dataclass
class Factura:
    """Factura principal con todos sus datos."""
    # Datos básicos
    numero_factura: int
    fecha_emision: date
    cliente: Cliente
    detalles: List[DetalleFactura]
    
    # Configuración
    tipo_factura: TipoFactura = TipoFactura.COMPRA_VENTA
    tipo_emision: TipoEmision = TipoEmision.ONLINE
    codigo_sucursal: int = 0
    codigo_punto_venta: int = 0
    
    # Montos
    descuento_adicional: Decimal = Decimal('0')
    
    # Control
    cuf: Optional[str] = None
    cufd: Optional[str] = None
    cuis: Optional[str] = None
    estado: EstadoFactura = EstadoFactura.BORRADOR
    
    # Respuesta del SIN
    codigo_recepcion: Optional[str] = None
    fecha_recepcion: Optional[datetime] = None
    observaciones: List[str] = field(default_factory=list)
    
    # Archivos
    xml_path: Optional[str] = None
    pdf_path: Optional[str] = None
    
    def __post_init__(self):
        """Validaciones post-inicialización."""
        self.validate()
    
    def validate(self):
        """Valida toda la factura."""
        errors = []
        
        # Validar datos básicos
        if self.numero_factura <= 0:
            errors.append("Número de factura debe ser positivo")
        
        if not self.fecha_emision:
            errors.append("Fecha de emisión es obligatoria")
        elif self.fecha_emision > date.today():
            errors.append("Fecha de emisión no puede ser futura")
        
        if not self.detalles:
            errors.append("Factura debe tener al menos un detalle")
        
        # Validar descuento adicional
        if self.descuento_adicional < 0:
            errors.append("Descuento adicional no puede ser negativo")
        elif self.descuento_adicional > self.subtotal:
            errors.append("Descuento adicional no puede ser mayor al subtotal")
        
        if errors:
            raise ValueError(f"Errores en Factura: {'; '.join(errors)}")
    
    @property
    def subtotal(self) -> Decimal:
        """Suma de todos los subtotales de detalles."""
        return sum(detalle.subtotal_redondeado for detalle in self.detalles)
    
    @property
    def descuento_total(self) -> Decimal:
        """Descuento total (suma de detalles + descuento adicional)."""
        descuento_detalles = sum(detalle.descuento for detalle in self.detalles)
        return descuento_detalles + self.descuento_adicional
    
    @property
    def monto_total(self) -> Decimal:
        """Monto total de la factura."""
        return self.subtotal - self.descuento_adicional
    
    @property
    def monto_total_redondeado(self) -> Decimal:
        """Monto total redondeado a 2 decimales."""
        return round(self.monto_total, 2)
    
    @property
    def literal_monto(self) -> str:
        """Monto en literal (para implementar posteriormente)."""
        # TODO: Implementar conversión a literal
        return f"{self.monto_total_redondeado} BOLIVIANOS"
    
    def add_detalle(self, detalle: DetalleFactura):
        """Agrega un detalle a la factura."""
        detalle.validate()
        self.detalles.append(detalle)
    
    def remove_detalle(self, index: int):
        """Remueve un detalle por índice."""
        if 0 <= index < len(self.detalles):
            del self.detalles[index]
        else:
            raise IndexError("Índice de detalle inválido")
    
    def set_estado(self, nuevo_estado: EstadoFactura, observacion: Optional[str] = None):
        """Cambia el estado de la factura."""
        self.estado = nuevo_estado
        if observacion:
            self.observaciones.append(f"{datetime.now().isoformat()}: {observacion}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la factura a diccionario para serialización."""
        return {
            "numero_factura": self.numero_factura,
            "fecha_emision": self.fecha_emision.isoformat(),
            "cliente": {
                "nit": self.cliente.nit,
                "razon_social": self.cliente.razon_social,
                "tipo_documento": self.cliente.tipo_documento.value,
                "codigo_excepcion": self.cliente.codigo_excepcion.value,
                "email": self.cliente.email,
                "telefono": self.cliente.telefono
            },
            "detalles": [
                {
                    "codigo_producto": d.codigo_producto,
                    "descripcion": d.descripcion,
                    "cantidad": str(d.cantidad),
                    "precio_unitario": str(d.precio_unitario),
                    "descuento": str(d.descuento),
                    "subtotal": str(d.subtotal_redondeado)
                }
                for d in self.detalles
            ],
            "tipo_factura": self.tipo_factura.value,
            "tipo_emision": self.tipo_emision.value,
            "subtotal": str(self.subtotal),
            "descuento_total": str(self.descuento_total),
            "monto_total": str(self.monto_total_redondeado),
            "estado": self.estado.value,
            "cuf": self.cuf,
            "codigo_recepcion": self.codigo_recepcion,
            "observaciones": self.observaciones
        }

@dataclass
class ConfiguracionSistema:
    """Configuración del sistema de facturación."""
    nit_emisor: str
    razon_social_emisor: str
    codigo_sucursal: int
    codigo_punto_venta: int
    codigo_actividad_economica: str
    cuis: str
    ambiente: int  # 1=Producción, 2=Pruebas
    modalidad: int  # 1=Electrónica en línea, 2=Computarizada en línea
    
    # URLs de servicios
    url_servicios_siat: str
    url_recepcion_facturas: str
    url_verificacion_estado: str
    
    # Certificados
    certificado_path: str
    private_key_path: str
    
    def validate(self):
        """Valida la configuración del sistema."""
        errors = []
        
        if not self.nit_emisor or not self.nit_emisor.isdigit():
            errors.append("NIT emisor debe ser numérico")
        
        if not self.razon_social_emisor:
            errors.append("Razón social emisor es obligatoria")
        
        if self.ambiente not in [1, 2]:
            errors.append("Ambiente debe ser 1 (Producción) o 2 (Pruebas)")
        
        if self.modalidad not in [1, 2]:
            errors.append("Modalidad debe ser 1 (Electrónica) o 2 (Computarizada)")
        
        if not self.cuis:
            errors.append("CUIS es obligatorio")
        
        if errors:
            raise ValueError(f"Errores en ConfiguracionSistema: {'; '.join(errors)}")

# Funciones de utilidad para crear objetos de prueba
def crear_cliente_prueba() -> Cliente:
    """Crea un cliente de prueba."""
    return Cliente(
        nit="99001",
        razon_social="CLIENTE DE PRUEBA",
        tipo_documento=TipoDocumento.NIT,
        codigo_excepcion=CodigoExcepcion.NIT_INVALIDO
    )

def crear_detalle_prueba() -> DetalleFactura:
    """Crea un detalle de prueba."""
    return DetalleFactura(
        codigo_producto="PROD001",
        descripcion="Producto de prueba",
        cantidad=Decimal('1'),
        precio_unitario=Decimal('100.00')
    )

def crear_factura_prueba() -> Factura:
    """Crea una factura de prueba completa."""
    cliente = crear_cliente_prueba()
    detalle = crear_detalle_prueba()
    
    return Factura(
        numero_factura=1,
        fecha_emision=date.today(),
        cliente=cliente,
        detalles=[detalle],
        tipo_emision=TipoEmision.ONLINE
    )
