# Dependencias internas de [facturador/cufd.py](facturador/cufd.py)

## Visión general
[facturador/cufd.py](facturador/cufd.py) gestiona la creación de la tabla CUFD y la solicitud de un nuevo Código Único de Facturación Diaria contra el servicio de códigos del SIAT.

## Módulos propios utilizados

- Ningún módulo interno adicional. El archivo utiliza bibliotecas estándar, `requests`, `zeep` y el conector MySQL directamente.

## Conclusión
[facturador/cufd.py](facturador/cufd.py) opera como script autónomo. Mantenerlo aislado facilita migrar su lógica a las capas documentadas en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md) cuando se integre al flujo principal.