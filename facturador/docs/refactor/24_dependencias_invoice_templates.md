# Dependencias internas de [facturador/invoice_templates.py](facturador/invoice_templates.py)

## Vision general
[facturador/invoice_templates.py](facturador/invoice_templates.py) genera plantillas HTML y de texto para facturas, convierte montos a palabras y arma el QR integrando datos normativos y comerciales.

## Modulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: fetch_random_leyenda.  
   - Rol: obtener leyendas normativas aleatorias para inyectarlas en la representacion grafica y de texto.

2. **[facturador/business_logic.py](facturador/business_logic.py)**  
   - Funciones: generate_qr.  
   - Rol: construir el codigo QR en base64 que se inserta en el HTML compacto cuando hay CUF disponible.

3. **[facturador/data_models.py](facturador/data_models.py)**  
   - Modelos: FacturaProcesada.  
   - Rol: tipar la entrada de generate_html_invoice y mapear cada linea de producto al formato requerido por las plantillas.

## Conclusion
Las plantillas reutilizan la capa de datos descrita en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md) y la logica fiscal documentada en [facturador/docs/refactor/13_dependencias_business_logic.md](facturador/docs/refactor/13_dependencias_business_logic.md), manteniendo coherencia con el plan de interfaz de [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).
