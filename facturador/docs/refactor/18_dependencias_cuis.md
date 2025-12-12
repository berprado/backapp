# Dependencias internas de [facturador/cuis.py](facturador/cuis.py)

## Visión general
[facturador/cuis.py](facturador/cuis.py) expone una interfaz Streamlit para solicitar y administrar códigos CUIS, reutilizando la infraestructura de base de datos y la capa de acceso normativo.

## Módulos propios utilizados

1. **[facturador/database.py](facturador/database.py)**  
   - Componentes: get_db, init_db.  
   - Rol: inicializar la base de datos en ambientes de prueba y entregar sesiones al flujo Streamlit.

2. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: solicitar_cuis, insertar_cuis_manual.  
   - Rol: encapsular las llamadas SOAP de CUIS y la inserción manual de registros.

3. **[facturador/models.py](facturador/models.py)**  
   - Modelos: Cuis, PuntoVenta.  
   - Rol: consultar el CUIS vigente y validar la existencia del punto de venta asociado.

## Conclusión
[facturador/cuis.py](facturador/cuis.py) se apoya en la infraestructura detallada en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md). Esta documentación garantiza visibilidad de la capa Streamlit dentro del plan continuado en [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).