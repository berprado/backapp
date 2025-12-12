# Dependencias internas de [facturador/database.py](facturador/database.py)

## Visión general
[facturador/database.py](facturador/database.py) configura la capa ORM con SQLAlchemy, gestiona la creación de sesiones y permite inicializar las tablas del proyecto.

## Módulos propios utilizados

- Ningún módulo interno adicional. El archivo únicamente depende de SQLAlchemy, dotenv y la biblioteca estándar.

## Conclusión
[facturador/database.py](facturador/database.py) funciona como núcleo de acceso a datos sin depender de otros módulos de la solución. Mantiene una interfaz estable para el resto de componentes ya documentados en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md).