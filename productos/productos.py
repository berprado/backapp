import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configuración de la conexión a MySQL usando .env
def create_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE')
        )
        return connection
    except Error as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return None

# Crear la tabla productos_siat si no existe
def create_table_if_not_exists(connection):
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos_siat (
        id INT(11) NOT NULL AUTO_INCREMENT,
        categoria VARCHAR(255) DEFAULT NULL,
        codigo VARCHAR(191) UNIQUE NOT NULL,  # Ajuste la longitud del VARCHAR
        codigo_sin INT(11) DEFAULT NULL,
        nombre VARCHAR(255) DEFAULT NULL,
        precio_venta DECIMAL(10, 2) DEFAULT NULL,
        codigo_unidad_medida INT(11) DEFAULT NULL,
        unidad_medida VARCHAR(255) DEFAULT NULL,  # Añadido la columna unidad_medida
        unidad_medida_sin INT(11) DEFAULT NULL,
        codigoActividad VARCHAR(255) DEFAULT NULL,
        fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        estado_sincronizacion VARCHAR(255) DEFAULT NULL,
        PRIMARY KEY (id),
        UNIQUE KEY unique_codigo (codigo)
    ) ENGINE=INNODB,
    CHARACTER SET utf8mb4,
    COLLATE utf8mb4_unicode_ci;
    ''')
    connection.commit()

# Definir la correspondencia entre los nombres y los códigos de las unidades de medida
unidades_medida = {
    'BALDE': 1,
    'BOT. PERS.': 2,
    'BOTELLA': 3,
    'CAJETILLA': 4,
    'CANASTA': 5,
    'CHOPP': 6,
    'COPA': 7,
    'HORA': 8,
    'JARRA': 9,
    'LATA': 10,
    'PLATO': 11,
    'SHOT': 12,
    'TABLA': 13,
    'TAZA': 14,
    'TICKET': 15,
    'UNID.': 16,
    'VASO': 17
}

# Insertar o actualizar datos en la tabla productos_siat
def insert_or_update_data(connection, df):
    cursor = connection.cursor()
    for index, row in df.iterrows():
        # Obtener el código de la unidad de medida
        unidad_medida_codigo = unidades_medida.get(row['unidad_medida'], unidades_medida['UNID.'])

        cursor.execute('''
        INSERT INTO productos_siat (categoria, codigo, codigo_sin, nombre, precio_venta, codigo_unidad_medida, unidad_medida, unidad_medida_sin, codigoActividad, fecha_creacion)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON DUPLICATE KEY UPDATE
        categoria=VALUES(categoria),
        codigo_sin=VALUES(codigo_sin),
        nombre=VALUES(nombre),
        precio_venta=VALUES(precio_venta),
        codigo_unidad_medida=VALUES(codigo_unidad_medida),
        unidad_medida=VALUES(unidad_medida),  # Añadido la columna unidad_medida en la actualización
        unidad_medida_sin=VALUES(unidad_medida_sin),
        codigoActividad=VALUES(codigoActividad),
        fecha_actualizacion=CURRENT_TIMESTAMP
        ''', (
            row['categoria'], row['codigo'], row['codigo_sin'], row['nombre'],
            row['precio_venta'], unidad_medida_codigo, row['unidad_medida'], row['unidad_medida_sin'], row['codigoActividad']
        ))
        st.write(tuple(row))  # Imprimir el tuple para verificar
    connection.commit()

# Actualizar la unidad de medida de un producto existente
def update_product_unit(connection, product_code, new_unit):
    cursor = connection.cursor()
    # Obtener el código de la unidad de medida
    unidad_medida_codigo = unidades_medida.get(new_unit, unidades_medida['UNID.'])

    cursor.execute('''
    UPDATE productos_siat 
    SET codigo_unidad_medida=%s, unidad_medida=%s, fecha_actualizacion=CURRENT_TIMESTAMP 
    WHERE codigo=%s
    ''', (unidad_medida_codigo, new_unit, product_code))
    connection.commit()

# Interfaz de usuario con Streamlit
def main():
    st.title("Importar y Actualizar Datos de Productos")

    # Editar Unidades de Medida
    st.header("Editar Unidades de Medida")
    unidades_existentes = list(unidades_medida.keys())
    unidad_medida_existente = st.selectbox("Seleccionar unidad de medida existente para editar:", unidades_existentes)
    nueva_unidad_medida = st.text_input("Nueva unidad de medida (si desea agregar):")
    
    if st.button("Agregar Nueva Unidad de Medida"):
        if nueva_unidad_medida:
            if nueva_unidad_medida not in unidades_medida:
                unidades_medida[nueva_unidad_medida] = max(unidades_medida.values()) + 1
                st.success("Unidad de medida agregada exitosamente.")
            else:
                st.warning("La unidad de medida ya existe.")
        else:
            st.error("Debe ingresar una nueva unidad de medida.")
    
    # Editar la unidad de medida de un producto existente
    st.header("Actualizar Unidad de Medida de Producto")
    product_code = st.text_input("Código del producto:")
    new_unit_medida = st.selectbox("Nueva unidad de medida:", unidades_existentes + ([nueva_unidad_medida] if nueva_unidad_medida else []))
    
    if st.button("Actualizar Unidad de Medida"):
        if product_code and new_unit_medida:
            update_product_unit(create_connection(), product_code, new_unit_medida)
            st.success("Unidad de medida del producto actualizada exitosamente.")
        else:
            st.error("Debe ingresar el código del producto y seleccionar una nueva unidad de medida.")

    # Subir y procesar archivo Excel
    st.header("Importar Datos desde Archivo Excel")
    uploaded_file = st.file_uploader("Subir archivo Excel", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write("Vista previa del archivo subido:")
        st.write(df.head())

        # Asegurarse de que los tipos de datos sean correctos
        df['categoria'] = df['categoria'].astype(str)
        df['codigo'] = df['codigo'].astype(str)
        df['codigo_sin'] = df['codigo_sin'].astype(int)
        df['nombre'] = df['nombre'].astype(str)
        df['precio_venta'] = df['precio_venta'].astype(float)
        df['unidad_medida'] = df['unidad_medida'].astype(str)
        df['unidad_medida_sin'] = df['unidad_medida_sin'].astype(int)
        df['codigoActividad'] = df['codigoActividad'].astype(str)

        connection = create_connection()
        if connection:
            create_table_if_not_exists(connection)
            insert_or_update_data(connection, df)
            st.success("Datos importados y actualizados correctamente.")
            connection.close()
        else:
            st.error("No se pudo establecer la conexión con la base de datos.")

if __name__ == '__main__':
    main()
