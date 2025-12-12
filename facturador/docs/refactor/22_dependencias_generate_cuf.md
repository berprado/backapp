# Dependencias internas de [facturador/generate_cuf.py](facturador/generate_cuf.py)

## Visión general
[facturador/generate_cuf.py](facturador/generate_cuf.py) genera el Código Único de Facturación combinando parámetros normativos, dígito verificador y código de control vigente.

## Módulos propios utilizados

1. **[facturador/database.py](facturador/database.py)**  
   - Componentes: SessionLocal.  
   - Rol: abrir sesiones para recuperar el CUFD vigente.

2. **[facturador/models.py](facturador/models.py)**  
   - Modelos: Cufd.  
   - Rol: mapear el modelo utilizado al obtener el código de control.

3. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger, get_facturacion_logger.  
   - Rol: registrar información y errores durante el cálculo del CUF.

## Conclusión
[facturador/generate_cuf.py](facturador/generate_cuf.py) reutiliza la infraestructura documentada en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md) y respalda el flujo descrito en [facturador/docs/refactor/03_dependencias_main.md](facturador/docs/refactor/03_dependencias_main.md) para mantener la trazabilidad del CUF generado.