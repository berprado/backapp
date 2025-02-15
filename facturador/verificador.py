from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from database import get_db

# Lista de tablas clave que queremos verificar
TABLAS_CLAVE = [
    "empresa", "sucursal", "punto_venta", "cuis", "cufd", "sincronizarparametricatipopuntoventa", "cliente", "cliente_factura", "factura_cabecera", "factura_detalle", "productos", "productos_siat" 
]

def verificar_tablas(db: Session):
    """Verifica si las tablas clave existen y si tienen datos."""

    # Obtener lista de tablas existentes en la base de datos
    inspector = inspect(db.bind)  # ✅ Nueva forma recomendada en SQLAlchemy 1.4+
    tablas_existentes = inspector.get_table_names()

    print("\n📊 **Estado de las Tablas en la Base de Datos:**\n")

    for tabla in TABLAS_CLAVE:
        if tabla in tablas_existentes:
            # Contar cuántos registros tiene la tabla usando text()
            resultado = db.execute(text(f"SELECT COUNT(*) FROM {tabla}")).fetchone()
            total_registros = resultado[0] if resultado else 0
            estado = "✅ **EXISTE**" if total_registros > 0 else "⚠️ **VACÍA**"
            print(f"🔹 **Tabla `{tabla}`:** {estado} ({total_registros} registros)")
        else:
            print(f"❌ **Tabla `{tabla}` NO EXISTE.**")

if __name__ == "__main__":
    # Obtener la conexión a la base de datos
    db = next(get_db())

    # Verificar estado de las tablas
    verificar_tablas(db)
