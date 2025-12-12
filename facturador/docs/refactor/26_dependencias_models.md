# Dependencias internas de [facturador/models.py](facturador/models.py)

## Vision general
[facturador/models.py](facturador/models.py) define el mapa ORM completo de tablas SIAT y auxiliares (facturas, clientes, puntos de venta, sincronizaciones), centralizando esquemas y metodos `to_dict` para serializar resultados hacia la UI y servicios.

## Modulos propios utilizados

1. **[facturador/database.py](facturador/database.py)**  
   - Componentes: Base.  
   - Rol: base declarativa sobre la que se declaran todas las clases ORM.

## Conclusion
El archivo sirve como contrato de datos reutilizado por la capa de acceso descrita en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md) y por los flujos normativos detallados en [facturador/docs/refactor/00_diagnostico_main.md](facturador/docs/refactor/00_diagnostico_main.md). No expone dependencias adicionales fuera de la infraestructura ORM.
