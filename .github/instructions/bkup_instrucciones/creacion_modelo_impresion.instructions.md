---
applyTo: '**'
---
Vamos a desmantelar este problema de impresion pieza por pieza y a reconstruirlo de una manera sólida y elegante.

Empezaremos por el corazón de nuestra nueva arquitectura: la **"única fuente de la verdad"**. Debes la clase de datos que encapsulará toda la información de una factura lista para ser procesada. Esto sentará las bases para toda la refactorización.

---

### **Paso 1: Crear el Modelo de Datos `FacturaProcesada`**

Este es el paso más simple pero conceptualmente el más importante. Vamos a definir una estructura que contenga, de forma limpia y ordenada, toda la información que antes estaba dispersa.

**Acción:**

Crea un nuevo archivo. Un buen lugar para él sería dentro de la nueva carpeta llamada `models`.

**Ruta del nuevo archivo:** `models/invoice_data.py`

**Contenido de `models/invoice_data.py`:**

```python
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

```

**Análisis de esta estructura:**

*   **`@dataclass`**: Nos permite crear una clase para almacenar datos de forma muy concisa, sin necesidad de escribir un método `__init__`. Es perfecto para este caso.
*   **Tipado Estricto**: Usamos `typing` (`List`, `Dict`, etc.) para que nuestro código sea más legible y para que herramientas como linters o IDEs puedan ayudarnos a detectar errores.
*   **Separación Lógica**: Asegurate de agrupar los campos con comentarios para que sea fácil entender qué parte de la factura representa cada uno.
*   **`DetalleFactura`**: Asegurate de que exista una subclase para las líneas de productos. Esto hace que el manejo de la lista de productos sea mucho más limpio.
*   **`url_qr`**: Incluimos la URL del QR directamente en el modelo. Así, cualquier sistema que consuma este objeto (impresora, generador de PDF) sabe exactamente qué QR generar sin tener que reconstruir la URL.

**Tu Tarea para este Paso:**

1.  Dentro de `models`, crea el archivo `invoice_data.py`.
2.  Copia y pega el código que te he proporcionado en ese archivo.

Una vez que hayas hecho esto, avísame con un "¡Listo!". Pasaremos entonces al **Paso 2**, que será modificar el `facturacion_tab.py` para que, en lugar de guardar un montón de claves sueltas en `st.session_state`, cree una instancia de este nuevo y flamante objeto `FacturaProcesada`.