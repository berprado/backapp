import pymysql
from datetime import datetime

# Configuración de la conexión a la base de datos
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "admin123.",
    "database": "adminerp_copy",
    "charset": "utf8mb4"
}

def fetch_data(query, connection):
    """Ejecuta una consulta SQL y devuelve los resultados."""
    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()

def execute_query(query, connection, data=None):
    """Ejecuta una consulta SQL con datos opcionales."""
    with connection.cursor() as cursor:
        if data:
            cursor.executemany(query, data)
        else:
            cursor.execute(query)
        connection.commit()

def sync_productos_siat():
    """Sincroniza la tabla productos_siat con la vista productos_combinados_copy."""
    connection = pymysql.connect(**DB_CONFIG)
    try:
        # 1. Obtener datos de la vista y la tabla
        vista_data = fetch_data("SELECT * FROM productos_combinados_copy", connection)
        siat_data = fetch_data("SELECT * FROM productos_siat", connection)

        siat_codes = {row['codigo']: row for row in siat_data}

        # 2. Insertar nuevos registros
        insert_query = """
        INSERT INTO productos_siat (
            categoria, codigo, codigo_sin, nombre, precio_venta,
            codigo_unidad_medida, unidad_medida, unidad_medida_sin, codigoActividad
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        new_records = []
        for row in vista_data:
            if row['codigo'] not in siat_codes:
                unidad_medida = row['unidad_medida']
                if row['categoria'] == 'VODKAS':
                    if row['nombre'].startswith('V'):
                        unidad_medida = 'VASO'
                    elif row['nombre'].startswith('C'):
                        unidad_medida = 'BOTELLA'

                new_records.append((
                    row['categoria'], row['codigo'], row['codigo_sin'], row['nombre'],
                    row['precio_venta'], None, unidad_medida,
                    row['unidad_medida_sin'], row['codigoActividad']
                ))
        if new_records:
            execute_query(insert_query, connection, new_records)

        # 3. Actualizar registros existentes
        update_query = """
        UPDATE productos_siat
        SET 
            categoria = %s, codigo_sin = %s, nombre = %s, precio_venta = %s,
            unidad_medida = %s, unidad_medida_sin = %s, codigoActividad = %s,
            fecha_actualizacion = %s
        WHERE codigo = %s
        """

        for row in vista_data:
            if row['codigo'] in siat_codes:
                current_row = siat_codes[row['codigo']]
                unidad_medida = row['unidad_medida']
                if row['categoria'] == 'VODKAS':
                    if row['nombre'].startswith('V'):
                        unidad_medida = 'VASO'
                    elif row['nombre'].startswith('C'):
                        unidad_medida = 'BOTELLA'

                if (row['categoria'] != current_row['categoria'] or
                    row['codigo_sin'] != current_row['codigo_sin'] or
                    row['nombre'] != current_row['nombre'] or
                    row['precio_venta'] != current_row['precio_venta'] or
                    unidad_medida != current_row['unidad_medida'] or
                    row['unidad_medida_sin'] != current_row['unidad_medida_sin'] or
                    row['codigoActividad'] != current_row['codigoActividad']):
                    execute_query(update_query, connection, (
                        row['categoria'], row['codigo_sin'], row['nombre'],
                        row['precio_venta'], unidad_medida,
                        row['unidad_medida_sin'], row['codigoActividad'],
                        datetime.now(), row['codigo']
                    ))

        # 4. Marcar registros eliminados
        vista_codes = {row['codigo'] for row in vista_data}
        delete_query = """
        UPDATE productos_siat
        SET estado_sincronizacion = 'ELIMINADO'
        WHERE codigo NOT IN (%s)
        """

        codes_to_delete = set(siat_codes.keys()) - vista_codes
        if codes_to_delete:
            execute_query(delete_query, connection, (','.join(codes_to_delete),))

        print("Sincronización completada con éxito.")

    except Exception as e:
        print(f"Error durante la sincronización: {e}")

    finally:
        connection.close()

if __name__ == "__main__":
    sync_productos_siat()
