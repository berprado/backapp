# __init__.py para el paquete models
# Este archivo permite que la carpeta models sea reconocida como un paquete de Python

# En lugar de importar de facturador.models (que causa un ciclo de importación),
# exponemos nuestros propios modelos

# Importamos nuestros nuevos modelos de datos
from .invoice_data import FacturaProcesada, DetalleFactura

# No importamos los modelos del archivo models.py aquí, ya que eso causa
# una importación circular. Los otros archivos deben seguir importando directamente 
# desde facturador.models
