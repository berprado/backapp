"""
Módulo para la administración de facturas.

Este módulo contiene funciones para guardar facturas en la base de datos,
listar facturas, paginar resultados y otras operaciones relacionadas con
la administración de facturas.
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from data_access import (
    guardar_factura_cabecera, guardar_factura_detalle,
    obtener_facturas_por_estado, obtener_factura_completa, obtener_cuf_por_numero_factura
)
from logger_config import get_facturacion_logger
import threading

# Configuración de logger
facturacion_logger = get_facturacion_logger()

# Lock global para evitar condiciones de carrera en entornos multiusuario
numero_factura_lock = threading.Lock()

def guardar_factura_en_bd(factura_cabecera_data, detalles_factura):
    """
    Guarda la cabecera y detalles de una factura en la base de datos.
    
    Args:
        factura_cabecera_data (dict): Datos de la cabecera de la factura
        detalles_factura (list): Lista de diccionarios con detalles de la factura
    
    Returns:
        tuple: (bool, str) donde bool indica si la operación fue exitosa
               y str contiene un mensaje de éxito o error
    """
    try:
        # Asegurarse de que tipoEmision esté presente
        if 'tipoEmision' not in factura_cabecera_data:
            # Si no está presente, asignar valor por defecto (1 = online)
            factura_cabecera_data['tipoEmision'] = "1"
        
        # Intentar guardar la cabecera de la factura
        guardar_factura_cabecera(factura_cabecera_data)
        
        # Si la cabecera se guardó correctamente, guardar los detalles
        for detalle in detalles_factura:
            guardar_factura_detalle(detalle)
        
        return True, "Factura guardada correctamente"
    except SQLAlchemyError as e:
        facturacion_logger.error(f"Error SQL al guardar la factura: {e}")
        
        # Verificar si es un error de columna faltante para tipoEmision
        if "Unknown column 'tipoEmision'" in str(e):
            facturacion_logger.warning("La columna tipoEmision no existe. Se requiere actualizar la estructura de la base de datos.")
            st.error("""
                **Error de estructura de base de datos**
                
                Se requiere actualizar la estructura de la tabla factura_cabecera.
                Por favor, ejecute el script SQL que se encuentra en:
                `c:\\Users\\Bernardo\\Desktop\\backapp\\facturador\\sql\\alter_factura_cabecera.sql`
                
                Este script añadirá las columnas necesarias para el manejo de contingencias.
            """)
            return False, "Error: Se requiere actualizar la estructura de la base de datos."
        
        return False, f"Error al guardar la factura: {str(e)}"
    except Exception as e:
        facturacion_logger.error(f"Error general al guardar la factura: {e}")
        return False, f"Error al guardar la factura: {str(e)}"

def obtener_y_reservar_numero_factura():
    """
    Lee y reserva el próximo número de factura de forma atómica y persistente.
    Devuelve el número reservado para la nueva factura.
    """
    with numero_factura_lock:
        try:
            if not os.path.exists("invoice_number.txt"):
                numero_factura = 1
            else:
                with open("invoice_number.txt", "r") as f:
                    contenido = f.read().strip()
                    numero_factura = int(contenido) if contenido else 1
            # Guardar el siguiente número disponible
            with open("invoice_number.txt", "w") as f:
                f.write(str(numero_factura + 1))
            return numero_factura
        except Exception as e:
            facturacion_logger.error(f"Error al reservar número de factura: {e}")
            raise RuntimeError(f"Error al reservar número de factura: {e}")

def increment_invoice_number(numero_factura):
    """
    [OBSOLETA] Usar obtener_y_reservar_numero_factura().
    """
    facturacion_logger.warning("No usar increment_invoice_number. Usar obtener_y_reservar_numero_factura().")
    return None

def mostrar_lista_facturas(estado):
    """
    Muestra una lista de facturas según su estado con paginación.
    
    Esta función obtiene facturas de la base de datos según el estado especificado,
    y las muestra en formato tabular con opciones de paginación.
    
    Args:
        estado (str): Estado de las facturas a mostrar ('TODAS', 'PENDIENTE', 'VALIDADA', etc.)
    """
    # Parámetros para la paginación con clave específica para cada estado
    page_key = f'page_{estado}'
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    page = st.session_state[page_key]
    per_page = 10
    
    # Obtener facturas según el estado
    facturas, total, error = obtener_facturas_por_estado(
        estado if estado != "TODAS" else None, 
        page, 
        per_page
    )
    
    # Mostrar mensaje de error si ocurrió alguno
    if error:
        st.error(error)
        return
    
    # Calcular total de páginas
    total_pages = (total + per_page - 1) // per_page
    
    # Mostrar información de paginación
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        # Añadir key única basada en el estado
        if st.button("◀ Anterior", key=f"prev_{estado}", disabled=(page <= 1)):
            st.session_state[page_key] -= 1
            st.rerun()
    
    with col2:
        st.write(f"Página {page} de {max(1, total_pages)} (Total: {total} facturas)")
    
    with col3:
        # Añadir key única basada en el estado
        if st.button("Siguiente ▶", key=f"next_{estado}", disabled=(page >= total_pages)):
            st.session_state[page_key] += 1
            st.rerun()
    
    # Si no hay facturas, mostrar mensaje
    if not facturas:
        if estado == "PENDIENTE":
            st.info("No hay facturas pendientes de validación")
        else:
            st.info(f"No hay facturas en estado '{estado}'")
        return
    
    # Crear un DataFrame para mostrar en forma de tabla
    df_data = []
    for f in facturas:
        # Determinar el estado para mostrar
        estado_mostrar = "⏱️ Pendiente" if f["resultadoValidacion"] is None else \
                         "✅ Validada" if f["resultadoValidacion"] == "VALIDADA" else \
                         "❌ Anulada" if f["estado"] == "Anulada" else \
                         "❓ Desconocido"        # Crear registro para el DataFrame
        # Manejar correctamente la fechaEmision (puede ser datetime u objeto string)
        fecha = f["fechaEmision"]
        if isinstance(fecha, datetime):
            fecha_formateada = fecha.strftime('%Y-%m-%d')
        else:
            fecha_formateada = str(fecha).split("T")[0]

        df_data.append({
            "Núm. Factura": f["numeroFactura"],
            "Fecha": fecha_formateada,
            "Cliente": f.get("nombreRazonSocial", "Cliente no registrado"),
            "NIT/CI": f["numeroDocumento"],
            "Monto Total": f"{float(f['montoTotal']):.2f} Bs.",
            "Estado": estado_mostrar,
            "CUF": f["cuf"][:10] + "..." + f["cuf"][-5:] if f["cuf"] else "N/A"
        })
    
    # Convertir a DataFrame
    df = pd.DataFrame(df_data)
    
    # Mostrar tabla
    st.dataframe(df, hide_index=True)
    
    # Agregar acciones para cada factura
    with st.expander("Acciones para facturas seleccionadas"):
        # Selección de factura por número
        numeros_factura = [f["numeroFactura"] for f in facturas]
        factura_seleccionada = st.selectbox(
            "Seleccione una factura para realizar acciones:", 
            numeros_factura,
            format_func=lambda x: f"Factura #{x}",
            key=f"selectbox_accion_factura_{estado}"
        )
        
        # Obtener la factura seleccionada
        factura = next((f for f in facturas if f["numeroFactura"] == factura_seleccionada), None)
        
        # Mostrar información detallada
        if factura:
            st.write(f"**Información de la Factura #{factura_seleccionada}**")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Cliente: {factura.get('nombreRazonSocial', 'Cliente no registrado')}")
                st.write(f"NIT/CI: {factura['numeroDocumento']}")
                # Manejar correctamente la fecha (puede ser datetime u objeto string)
                fecha = factura['fechaEmision']
                if isinstance(fecha, datetime):
                    fecha_formateada = fecha.strftime('%Y-%m-%d')
                else:
                    fecha_formateada = str(fecha).split('T')[0]
                st.write(f"Fecha: {fecha_formateada}")
            
            with col2:
                st.write(f"Monto Total: {float(factura['montoTotal']):.2f} Bs.")
                st.write(f"Estado: {factura.get('resultadoValidacion', 'Pendiente')}")
              # Botones de acción según estado
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Ver Detalle Completo", key=f"ver_{estado}_{factura_seleccionada}"):
                    st.session_state['factura_detalle_seleccionada'] = factura_seleccionada
                    st.rerun()
            
            with col2:
                if factura.get("resultadoValidacion") != "VALIDADA" and factura.get("estado") != "Anulada":
                    if st.button("Verificar Estado", key=f"verificar_{estado}_{factura_seleccionada}"):
                        st.session_state['verificar_factura'] = factura_seleccionada
                        st.rerun()
            
            with col3:
                if factura.get("resultadoValidacion") == "VALIDADA" and factura.get("estado") != "Anulada":
                    if st.button("Anular Factura", key=f"anular_{estado}_{factura_seleccionada}"):
                        st.session_state['anular_factura'] = factura_seleccionada
                        st.rerun()
        
        # Si existe una factura seleccionada para ver en detalle
        if 'factura_detalle_seleccionada' in st.session_state:
            factura_completa = obtener_factura_completa(st.session_state['factura_detalle_seleccionada'])
            
            if factura_completa and 'cabecera' in factura_completa:
                st.subheader(f"Detalle de Factura #{st.session_state['factura_detalle_seleccionada']}")
                
                st.write("**Información de cabecera:**")
                st.json(factura_completa['cabecera'])
                
                st.write("**Detalles de la factura:**")
                detalle_df = pd.DataFrame(factura_completa['detalles'])
                st.dataframe(detalle_df)
