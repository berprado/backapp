import streamlit as st
from datetime import datetime
from sqlalchemy.orm import Session
from database import get_db
from data_access import solicitar_cuis, insertar_cuis_manual
from models import Cuis, PuntoVenta
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener el codigo_punto_venta desde .env
codigo_punto_venta = int(os.getenv("CODIGO_PUNTO_VENTA"))

def calcular_dias_vigencia(fecha_vigencia):
    """Calcula los días restantes de vigencia del CUIS."""
    hoy = datetime.now()
    diferencia = fecha_vigencia - hoy
    return diferencia.days

def obtener_cuis_vigente(db: Session, codigo_punto_venta: int):
    """Obtiene el CUIS vigente de la base de datos, si existe."""
    cuis_vigente = db.query(Cuis).filter(Cuis.vigente == 1, Cuis.codigo_punto_venta == codigo_punto_venta).first()
    return cuis_vigente

def solicitar_nuevo_cuis(db: Session, codigo_punto_venta: int):
    """Solicita un nuevo CUIS y muestra el resultado al usuario."""
    resultado = solicitar_cuis(db)

    if resultado['success']:
        # Volver a obtener el nuevo CUIS para mostrarlo al usuario
        nuevo_cuis = obtener_cuis_vigente(db, codigo_punto_venta)
        if nuevo_cuis:
            st.success(f"Nuevo CUIS solicitado: {nuevo_cuis.codigo}")
            st.info("Puedes copiar este CUIS para pegarlo en el archivo .env.")
            st.text_area("CUIS", nuevo_cuis.codigo)
    else:
        st.error(f"No se pudo solicitar un nuevo CUIS: {resultado['message']}")

def main():
    st.title("Gestión de CUIS")

    # Obtener la sesión de la base de datos
    db = next(get_db())

    # Verificar si el codigo_punto_venta existe en la tabla punto_venta
    punto_venta = db.query(PuntoVenta).filter(PuntoVenta.codigo_punto_venta == codigo_punto_venta).first()
    if not punto_venta:
        st.error(f"El codigo_punto_venta {codigo_punto_venta} no existe en la tabla punto_venta.")
        return

    # Verificar si existe un CUIS vigente en la base de datos
    cuis_vigente = obtener_cuis_vigente(db, codigo_punto_venta)

    if cuis_vigente:
        # Calcular los días restantes de vigencia
        dias_restantes = calcular_dias_vigencia(cuis_vigente.fecha_vigencia)
        
        st.success(f"CUIS vigente encontrado: {cuis_vigente.codigo}")
        st.info(f"Punto de Venta asignado: {punto_venta.nombre_punto_venta}")
        st.info(f"Días restantes de vigencia: {dias_restantes}")

        if dias_restantes > 5:
            st.warning("No es necesario solicitar un nuevo CUIS en este momento.")
            st.button("Solicitar Nuevo CUIS", disabled=True)
        else:
            if st.button("Solicitar Nuevo CUIS"):
                solicitar_nuevo_cuis(db, codigo_punto_venta)
    else:
        st.warning("No se encontró un CUIS vigente en la base de datos.")
        resultado = solicitar_cuis(db)
        
        if not resultado['success'] and "EXISTE UN CUIS VIGENTE" in resultado['message']:
            st.error("Se encontró un CUIS vigente según el servicio SOAP, pero no está almacenado en la base de datos.")
            
            # Detalles del CUIS según la respuesta SOAP
            codigo_cuis = resultado.get('codigo')
            fecha_vigencia = resultado.get('fecha_vigencia')

            # Mostrar el botón para insertar manualmente el CUIS
            if st.button("Insertar CUIS Manualmente"):
                insertar_resultado = insertar_cuis_manual(db, codigo_cuis, fecha_vigencia, codigo_punto_venta)
                if insertar_resultado['success']:
                    st.success("CUIS insertado correctamente en la base de datos.")
                else:
                    st.error(f"Error al insertar CUIS: {insertar_resultado['message']}")

        else:
            if st.button("Solicitar Nuevo CUIS"):
                solicitar_nuevo_cuis(db, codigo_punto_venta)

if __name__ == "__main__":
    main()
