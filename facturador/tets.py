from sqlalchemy.orm import Session
from data_access import SessionLocal, ProductoSiat

# Iniciar una sesión de la base de datos
session = SessionLocal()

# Consultar productos por código
producto_corona = session.query(ProductoSiat).filter(ProductoSiat.codigo == '1230').first()
producto_havana = session.query(ProductoSiat).filter(ProductoSiat.codigo == '69').first()
producto_fireball_shot = session.query(ProductoSiat).filter(ProductoSiat.codigo == '40').first()

# Cerrar la sesión de la base de datos
session.close()

# Imprimir nombre y unidad de medida de cada producto
if producto_corona:
    print(f"Producto: {producto_corona.nombre}, Unidad de Medida: {producto_corona.unidad_medida}")
if producto_havana:
    print(f"Producto: {producto_havana.nombre}, Unidad de Medida: {producto_havana.unidad_medida}")
if producto_fireball_shot:
    print(f"Producto: {producto_fireball_shot.nombre}, Unidad de Medida: {producto_fireball_shot.unidad_medida}")
