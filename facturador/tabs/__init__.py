"""
Módulo de pestañas para la interfaz de usuario del facturador.
"""

# Importaciones explícitas para facilitar el uso desde ui_copy.py
from . import facturacion_tab
from . import facturas_tab
from . import validar_nit_tab
from . import clientes_tab
from . import verificar_factura_tab
from . import cuis_tab
from . import anular_revertir_tab  # ✅ Nuevo módulo unificado
from . import diagnostico_tab

# DEPRECADO: Módulos antiguos que serán eliminados en futuras versiones
# from . import anular_factura_tab
# from . import revertir_anulacion_tab

__all__ = [
    'facturacion_tab',
    'facturas_tab',
    'validar_nit_tab',
    'clientes_tab',
    'verificar_factura_tab',
    'cuis_tab',
    'anular_revertir_tab',
    'diagnostico_tab',
]
