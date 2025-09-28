# Logging Audit - facturador/tabs

## Criteria
- Module uses central helpers from `logger_config` (`get_logger`, `get_facturacion_logger`, etc.).
- Module avoids direct import of `logging` or custom handler setup.
- Messages leverage the configured logger without redefining formatters or handlers.

## Modules Aligned With Central Logging
- facturador/tabs/anular_factura_tab.py
- facturador/tabs/clientes_tab.py
- facturador/tabs/cuis_tab.py
- facturador/tabs/diagnostico_tab.py
- facturador/tabs/facturacion_tab.py
- facturador/tabs/facturas_tab.py
- facturador/tabs/revertir_anulacion_tab.py
- facturador/tabs/validar_nit_tab.py

## Modules Requiring Follow Up
- facturador/tabs/verificar_factura_tab.py
  - Defines its own logger (`logging.getLogger('verificacion')`) and handlers instead of using `logger_config`.
  - Uses a different log format and file destination (`logs/verificacion.log`).

## Suggested Next Steps
1. Expose `get_verificacion_logger()` (o nombre similar) desde `logger_config` con la configuracion compartida.
2. Actualizar `verificar_factura_tab.py` para usar unicamente el helper central y eliminar la configuracion local.
3. Ejecutar `python scripts/check_logging_imports.py` antes de subir cambios (y agregarlo al pipeline de CI) para asegurar que no aparezcan nuevos `import logging` fuera de los modulos permitidos.

## Herramienta de verificacion
El script `scripts/check_logging_imports.py` recorre los archivos `.py` especificados (o todo el repositorio si no se pasan rutas) y falla si detecta importaciones directas de `logging` fuera de `facturador/logger_config.py`.
