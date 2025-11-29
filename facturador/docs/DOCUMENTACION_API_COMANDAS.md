# Documentación Técnica: API de Obtención de Comandas

## 1. Visión General
Este documento describe la arquitectura, el flujo de datos y la lógica implementada para la exposición de información de comandas a través de una API RESTful construida con **FastAPI**. 

Esta API reside en la raíz del proyecto (`C:\Users\Bernardo\Desktop\backapp\`) y actúa como la capa de acceso a datos para el sistema de facturación, cuyo código fuente se encuentra en el subdirectorio `facturador/`.

## 2. Arquitectura del Sistema
La implementación sigue una arquitectura en capas clásica para separar responsabilidades, facilitando el mantenimiento y la escalabilidad.

### Estructura de Archivos (Raíz)
*   **`database_api.py`**: **Capa de Conexión**. Configuración del motor de base de datos y sesiones.
*   **`models_api.py`**: **Capa de Datos (ORM)**. Definición de las tablas y mapeo objeto-relacional.
*   **`schemas.py`**: **Capa de Validación (DTOs)**. Esquemas Pydantic para serialización y validación de datos.
*   **`crud.py`**: **Capa de Lógica de Acceso**. Funciones puras para consultas a la base de datos.
*   **`api.py`**: **Capa de Controladores**. Definición de endpoints y gestión de peticiones HTTP.

---

## 3. Componentes Detallados

### 3.1. Configuración de Base de Datos (`database_api.py`)
Es el punto de entrada a la persistencia de datos. Utiliza `SQLAlchemy` como ORM.
*   **Gestión de Credenciales**: Utiliza `python-dotenv` para cargar credenciales sensibles (usuario, contraseña, host, puerto) desde un archivo `.env`, garantizando que no queden hardcodeadas en el código.
*   **Engine**: Crea el motor de conexión MySQL (`mysql+pymysql`).
*   **SessionLocal**: Define una fábrica de sesiones. Cada petición HTTP instanciará su propia sesión aislada.
*   **Base**: Clase declarativa base de la cual heredarán todos los modelos ORM.

### 3.2. Modelo de Datos (`models_api.py`)
Representa la estructura de la base de datos en código Python.
*   **Clase `Comanda`**: Mapea la tabla (o vista) `comandas`.
*   **Tipado Estricto**: Define columnas con tipos específicos de SQLAlchemy (`Integer`, `String`, `Numeric`, `Date`) que corresponden a la estructura SQL subyacente.
*   **Métodos Auxiliares**: Incluye `to_dict()` para conversiones manuales a diccionario, aunque la API moderna delega esta tarea a los esquemas.

### 3.3. Esquemas de Datos (`schemas.py`)
Define el "contrato" de datos que la API expone al mundo exterior.
*   **Tecnología**: Utiliza **Pydantic** para validación y serialización de alto rendimiento.
*   **`ComandaResponse`**: Es el esquema principal de salida.
    *   Hereda de `ComandaBase` para reutilizar definiciones de campos comunes.
    *   **Configuración Clave**: Utiliza `model_config = ConfigDict(from_attributes=True)`. Esta configuración es crítica, ya que permite a Pydantic leer datos directamente de los objetos ORM de SQLAlchemy sin necesidad de convertirlos previamente a diccionarios, optimizando el proceso de respuesta.

### 3.4. Lógica de Acceso a Datos (`crud.py`)
Abstrae la complejidad de las consultas SQL de los controladores de la API.
*   **Función `get_comanda_data`**:
    *   **Propósito**: Recuperar información de una o varias comandas.
    *   **Optimización**: Recibe una lista de IDs (`List[int]`) y utiliza el operador `.in_()` de SQLAlchemy. Esto permite recuperar múltiples registros en una sola consulta SQL (`SELECT * FROM comandas WHERE id IN (...)`), lo cual es mucho más eficiente que realizar una consulta por cada ID.

### 3.5. Controladores de API (`api.py`)
Orquesta el flujo de la petición, uniendo todas las capas anteriores.

#### Gestión de Sesiones (Dependency Injection)
Define la función `get_db()` que actúa como dependencia en cada endpoint:
1.  Abre una sesión de base de datos (`SessionLocal()`).
2.  Entrega la sesión al endpoint (`yield db`).
3.  **Cierra la sesión automáticamente** (`db.close()`) al finalizar la petición, incluso si ocurren errores. Esto previene fugas de conexiones en la base de datos.

#### Endpoints Principales

1.  **`GET /comandas/{id_comanda}`**
    *   **Entrada**: Recibe una cadena con uno o varios IDs separados por comas (ej. `"101,102"`).
    *   **Lógica**:
        1.  Parsea la cadena de entrada a una lista de enteros: `[101, 102]`.
        2.  Invoca a `crud.get_comanda_data` con esta lista.
        3.  Verifica si se encontraron resultados; si no, lanza `HTTP 404`.
    *   **Salida**: Retorna una lista de objetos serializados según `ComandaResponse`.
    *   **Nota**: Filtra automáticamente las comandas con `sub_total` igual a 0 (cortesías).

2.  **`GET /`**
    *   Retorna todas las comandas disponibles en la base de datos, excluyendo aquellas con `sub_total` igual a 0.

3.  **`GET /comandas/usuario/{usuario_reg}`**
    *   Filtra y retorna las comandas registradas por un usuario específico, excluyendo aquellas con `sub_total` igual a 0.

4.  **`GET /cortesias`**
    *   **Nuevo Endpoint**: Retorna exclusivamente las comandas que tienen `sub_total` igual a 0 (Cortesías).

---

## 4. Flujo de Ejecución: Paso a Paso

A continuación se describe el ciclo de vida de una petición típica desde el sistema de facturación (`facturador`) hacia la API:

1.  **Solicitud**: El módulo de facturación necesita datos de la comanda `55` y realiza una petición `GET http://localhost:8000/comandas/55`.
2.  **Inicio de Sesión**: FastAPI recibe la petición e invoca `get_db()`, abriendo una transacción con MySQL.
3.  **Enrutamiento**: La petición llega a la función `get_comanda` en `api.py`.
4.  **Procesamiento**: El ID "55" se convierte en la lista `[55]`.
5.  **Consulta (CRUD)**: Se llama a `crud.get_comanda_data`. SQLAlchemy traduce esto a SQL y ejecuta la consulta en la BD.
6.  **Mapeo (ORM)**: Los datos crudos de la BD se instancian como objetos de la clase `Comanda` (`models_api.py`).
7.  **Serialización (Schemas)**: FastAPI toma estos objetos y usa `ComandaResponse` (`schemas.py`) para convertirlos a formato JSON, validando los tipos de datos en el proceso.
8.  **Respuesta**: El JSON resultante se envía de vuelta al sistema de facturación.
9.  **Cierre**: La función `get_db()` finaliza y cierra la conexión a la base de datos.

---

## 5. POR HACER: INCONSISTENCIAS, REDUNDANCIAS Y MEJORAS

Tras un análisis del código actual, se han identificado las siguientes áreas de mejora para optimizar el rendimiento, la consistencia y la mantenibilidad del sistema.

### 5.1. Riesgos de Rendimiento (Crítico)
*   **Problema**: Los endpoints `GET /` y `GET /comandas/usuario/{usuario}` recuperan todos los registros sin límite (`.all()`). Si la tabla crece, esto puede bloquear la base de datos y causar timeouts.
*   **Acción Requerida**: Implementar **paginación** (parámetros `skip` y `limit`) en las consultas de SQLAlchemy.

### 5.2. Inconsistencia en el Patrón CRUD
*   **Problema**: Aunque existe `crud.py`, algunos endpoints en `api.py` realizan consultas directas a la base de datos.
*   **Acción Requerida**: Mover toda la lógica de consulta (filtros, queries) a funciones dentro de `crud.py` y dejar `api.py` solo como controlador.

### 5.3. Redundancia en Modelos
*   **Problema**: La clase `Comanda` en `models_api.py` incluye un método manual `to_dict()`.
*   **Acción Requerida**: Eliminar este método. La serialización ya es manejada eficientemente por Pydantic (`schemas.py`) gracias a la configuración `from_attributes=True`.

### 5.4. Diseño REST y Manejo de IDs
*   **Problema**: El endpoint `GET /comandas/{id_comanda}` acepta una cadena separada por comas para buscar múltiples IDs, lo cual no es estándar y complica la validación de tipos.
*   **Acción Requerida**: Migrar a el uso de *Query Parameters* estándar (ej. `?ids=1&ids=2`) para búsquedas múltiples.

### 5.5. Resiliencia de Conexión
*   **Problema**: La configuración de `create_engine` es básica y puede sufrir desconexiones silenciosas de MySQL ("server has gone away").
*   **Acción Requerida**: Añadir el parámetro `pool_pre_ping=True` en `database_api.py` para verificar la conexión antes de usarla.

### 5.6. Gestión de Esquema de Base de Datos
*   **Problema**: Se ejecuta `Base.metadata.create_all()` al inicio. Dado que `comandas` es una vista SQL, esto es innecesario y potencialmente conflictivo.
*   **Acción Requerida**: Eliminar la creación automática de tablas en producción y gestionar el esquema mediante migraciones o scripts SQL externos.
