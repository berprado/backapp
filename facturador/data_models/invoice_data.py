# models/invoice_data.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class DetalleFactura:
    """Representa una línea de producto en el detalle de la factura."""
    codigo: str
    nombre: str
    unidad: str
    cantidad: float
    precio: float
    montoDescuento: Optional[float]
    sub_total: float

@dataclass
class FacturaProcesada:
    """
    Contiene todos los datos de una factura validada, lista para ser
    impresa, convertida a PDF o enviada por correo.
    Esta es la ÚNICA FUENTE DE VERDAD post-validación del SIN.
    """
    # === Datos de la Transacción ===
    cuf: str
    numero_factura: int
    fecha_emision: str  # Formato "dd/mm/AAAA HH:MM:SS" para display

    # === Datos del Emisor (para referencia) ===
    nit_emisor: str
    razon_social_emisor: str
    nombre_sucursal: str
    punto_venta: int
    direccion_emisor: str
    municipio_emisor: str
    telefono_emisor: str
    
    # === Datos del Cliente ===
    nombre_cliente: str
    numero_documento: str
    complemento: Optional[str]
    cod_cliente: str # Usualmente el mismo numero_documento

    # === Datos de la Venta (Detalle) ===
    lineas_productos: List[DetalleFactura]

    # === Datos de Totales y Pago ===
    subtotal_factura: float
    descuento_adicional: float
    monto_giftcard: float
    monto_total: float
    monto_total_pagar: float
    monto_base_iva: float
    total_en_palabras: str
    metodo_pago: str
    ultimos_digitos_tarjeta: Optional[str]
    
    # === Datos Fiscales y Leyendas ===
    tipo_factura: str
    subtitulo_factura: str
    leyenda: str
    
    # === URL para QR (Generada una sola vez) ===
    url_qr: str
