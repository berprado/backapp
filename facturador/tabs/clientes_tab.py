"""
Módulo para la pestaña de gestión de clientes.
"""
import streamlit as st
from data_access import fetch_all_clientes, fetch_cliente
from ui_utils import init_session_state
from logger_config import get_logger

logger = get_logger()

def render():
    """Renderiza la pestaña de lista de clientes."""
    st.header("📋 Lista de Clientes")
    
    # Inicializar variables de estado para paginación
    init_session_state('clientes_page', 0)
    init_session_state('clientes_search', "")
    
    # Configuración de paginación
    REGISTROS_POR_PAGINA = 20
    
    # Barra de búsqueda
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        busqueda = st.text_input(
            "🔍 Buscar cliente", 
            value=st.session_state.clientes_search,
            placeholder="Buscar por nombre, documento o código..."
        )
    with col2:
        if st.button("🔄 Buscar"):
            st.session_state.clientes_search = busqueda
            st.session_state.clientes_page = 0  # Reset a primera página
            st.rerun()
    with col3:
        if st.button("🧹 Limpiar"):
            st.session_state.clientes_search = ""
            st.session_state.clientes_page = 0
            st.rerun()
    
    # Obtener datos de clientes
    offset = st.session_state.clientes_page * REGISTROS_POR_PAGINA
    clientes, total_registros, error = fetch_all_clientes(
        limite=REGISTROS_POR_PAGINA,
        offset=offset,
        busqueda=st.session_state.clientes_search if st.session_state.clientes_search else None
    )
    
    if error:
        st.error(f"Error al obtener clientes: {error}")
        logger.error(f"Error al obtener clientes: {error}")
    elif not clientes:
        if st.session_state.clientes_search:
            st.warning("No se encontraron clientes que coincidan con la búsqueda.")
        else:
            st.info("No hay clientes registrados en el sistema.")
    else:
        # Mostrar estadísticas
        total_paginas = (total_registros - 1) // REGISTROS_POR_PAGINA + 1 if total_registros > 0 else 0
        pagina_actual = st.session_state.clientes_page + 1
        
        st.info(f"📊 **Total de clientes**: {total_registros} | **Página**: {pagina_actual}/{total_paginas}")
        
        # Crear DataFrame para mostrar en tabla
        if clientes:
            # Preparar datos para la tabla
            datos_tabla = []
            for cliente in clientes:
                datos_tabla.append({
                    "ID": cliente.get("id", ""),
                    "Código": cliente.get("codigo_cliente", ""),
                    "Nombre/Razón Social": cliente.get("nombre_razon_social", ""),
                    "Documento": cliente.get("numero_documento", ""),
                    "Tipo Doc": cliente.get("codigo_tipo_documento_identidad", ""),
                    "Email": cliente.get("email", ""),
                    "Teléfono": cliente.get("telefono", ""),
                    "Complemento": cliente.get("complemento", "")
                })
            
            # Mostrar tabla
            st.dataframe(
                datos_tabla,
                use_container_width=True,
                hide_index=True
            )
            
            # Controles de paginación
            if total_paginas > 1:
                _render_pagination_controls(total_paginas, pagina_actual)
        
        # Mostrar detalles de cliente seleccionado (opcional)
        _render_client_details()

def _render_pagination_controls(total_paginas, pagina_actual):
    """Renderiza los controles de paginación."""
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⬅️ Primera", disabled=(st.session_state.clientes_page == 0)):
            st.session_state.clientes_page = 0
            st.rerun()
    
    with col2:
        if st.button("◀️ Anterior", disabled=(st.session_state.clientes_page == 0)):
            st.session_state.clientes_page -= 1
            st.rerun()
    
    with col3:
        st.write(f"Página {pagina_actual} de {total_paginas}")
    
    with col4:
        if st.button("▶️ Siguiente", disabled=(st.session_state.clientes_page >= total_paginas - 1)):
            st.session_state.clientes_page += 1
            st.rerun()
    
    with col5:
        if st.button("➡️ Última", disabled=(st.session_state.clientes_page >= total_paginas - 1)):
            st.session_state.clientes_page = total_paginas - 1
            st.rerun()

def _render_client_details():
    """Renderiza la sección de detalles de cliente específico."""
    with st.expander("ℹ️ Ver detalles de cliente específico"):
        documento_detalle = st.text_input("Ingrese número de documento para ver detalles:")
        if st.button("Ver Detalles") and documento_detalle:
            cliente_detalle, error_detalle = fetch_cliente(documento_detalle)
            if error_detalle:
                st.error(error_detalle)
                logger.error(f"Error al obtener detalles del cliente {documento_detalle}: {error_detalle}")
            else:
                st.json(cliente_detalle)
                logger.info(f"Detalles del cliente {documento_detalle} mostrados exitosamente")
