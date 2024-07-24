import os
from dotenv import load_dotenv
import mysql.connector

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración de la conexión a la base de datos
db_config = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE")
}

def crear_tabla_punto_venta():
    # Obtener las variables de entorno
    codigo_punto_venta = int(os.getenv("CODIGO_PUNTO_VENTA"))
    nombre_punto_venta = os.getenv("NOMBRE_PUNTO_VENTA")
    tipo = os.getenv("TIPO_PUNTO_VENTA")
    cod_sucursal = int(os.getenv("CODIGO_SUCURSAL"))

    # Conexión a MySQL
    with mysql.connector.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            # Crear la tabla si no existe
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {db_config["database"]}.punto_venta (
                id INT(11) NOT NULL AUTO_INCREMENT,
                codigo_punto_venta INT(11) NOT NULL,
                nombre_punto_venta VARCHAR(255) DEFAULT NULL,
                tipo VARCHAR(255) DEFAULT NULL,
                estado ENUM('Habilitado', 'Deshabilitado') NOT NULL DEFAULT 'habilitada',
                cod_sucursal INT(11) NOT NULL,
                fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE (codigo_punto_venta),
                CONSTRAINT punto_venta_ibfk_1 FOREIGN KEY (cod_sucursal)
                    REFERENCES {db_config["database"]}.sucursal (codigo_sucursal) ON DELETE NO ACTION,
                CONSTRAINT ck_codigo_punto_venta CHECK (codigo_punto_venta = 0 OR codigo_punto_venta > 0)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            # Insertar datos si la tabla está vacía
            cursor.execute(f"SELECT COUNT(*) FROM {db_config['database']}.punto_venta")
            count = cursor.fetchone()[0]
            if count == 0:
                sql = f"INSERT INTO {db_config['database']}.punto_venta (codigo_punto_venta, nombre_punto_venta, tipo, estado, cod_sucursal) VALUES (%s, %s, %s, %s, %s)"
                val = (codigo_punto_venta, nombre_punto_venta, tipo, 'habilitada', cod_sucursal)
                cursor.execute(sql, val)
                connection.commit()
                print("Datos del punto de venta insertados correctamente.")
            else:
                print("El Sistema ya cuenta con un punto de venta registrado.")

def insertar_punto_venta(codigo_punto_venta, nombre_punto_venta, tipo, estado, cod_sucursal):
    # Conexión a MySQL
    with mysql.connector.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            sql = f"INSERT INTO {db_config['database']}.punto_venta (codigo_punto_venta, nombre_punto_venta, tipo, estado, cod_sucursal) VALUES (%s, %s, %s, %s, %s)"
            val = (codigo_punto_venta, nombre_punto_venta, tipo, estado, cod_sucursal)
            try:
                cursor.execute(sql, val)
                connection.commit()
                print(f"Punto de venta {nombre_punto_venta} insertado correctamente.")
            except mysql.connector.Error as err:
                if err.errno == mysql.connector.errorcode.ER_DUP_ENTRY:
                    print(f"Error: Ya existe un punto de venta con el código {codigo_punto_venta}.")
                else:
                    print(f"Error: {err}")

def actualizar_punto_venta(codigo_punto_venta, nombre_punto_venta=None, tipo=None, estado=None):
    # Conexión a MySQL
    with mysql.connector.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            # Crear una lista de columnas a actualizar
            updates = []
            values = []
            if nombre_punto_venta:
                updates.append("nombre_punto_venta = %s")
                values.append(nombre_punto_venta)
            if tipo:
                updates.append("tipo = %s")
                values.append(tipo)
            if estado:
                updates.append("estado = %s")
                values.append(estado)

            values.append(codigo_punto_venta)
            update_query = f"UPDATE {db_config['database']}.punto_venta SET {', '.join(updates)} WHERE codigo_punto_venta = %s"
            try:
                cursor.execute(update_query, values)
                connection.commit()
                if cursor.rowcount > 0:
                    print(f"El punto de venta con código {codigo_punto_venta} se ha actualizado correctamente.")
                else:
                    print(f"No se encontró un punto de venta con el código {codigo_punto_venta}.")
            except mysql.connector.Error as err:
                print(f"Error: {err}")

if __name__ == "__main__":
    crear_tabla_punto_venta()
