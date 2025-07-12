"""
Módulo para manejar la sidebar de datos del cliente y configuración de facturación.
"""
import os
import logging
import streamlit as st
from decimal import Decimal
from data_access import (
    fetch_comandas, fetch_metodos_pago, fetch_tipos_documento, fetch_cliente
)
from client_manager import save_or_fetch_client_data, verificar_nit_cliente
from ui_utils import init_session_state, show_message
from logger_config import get_logger

logger = get_logger()

from shared_utils import GIFT_CARD_CODES

def load_base_data():
    """Carga los datos base necesarios para la facturación."""
    # Inicializar session state
    init_session_state('processed_comandas', [])
    
    # Cargar datos base
    comandas, mensaje_error = fetch_comandas()
    if mensaje_error:
        st.error(mensaje_error)
        logger.error(f"Error al cargar comandas: {mensaje_error}")
        return None, None, None, mensaje_error

    metodos_pago, error_metodos = fetch_metodos_pago()
    if error_metodos:
        st.error(error_metodos)
        logger.error(f"Error al cargar métodos de pago: {error_metodos}")
        return None, None, None, error_metodos

    tipos_documento, error_documentos = fetch_tipos_documento()
    if error_documentos:
        st.error(error_documentos)
        logger.error(f"Error al cargar tipos de documento: {error_documentos}")
        return None, None, None, error_documentos
    
    return comandas, metodos_pago, tipos_documento, None

def render_sidebar_client_data(tipos_documento, message_placeholder):
    """Renderiza la sección de datos del cliente en la sidebar."""
    numero_documento = st.sidebar.text_input(
        "Número de Documento:", 
        key="numero_documento", 
        help="Ingresa el número de documento del cliente."
    )
    
    # Inicializar variables por defecto
    nit_valido = False
    nombre_cliente = ""
    complemento = None
    email = ""
    telefono = ""
    seleccion_tipo_documento = None
    codigo_clasificador_documento = None
    codigo_cliente = None
    
    if numero_documento:
        cliente_data, error = fetch_cliente(numero_documento)
        if cliente_data:
            # Cliente existente
            tipo_documento_cliente = next(
                (doc for doc in tipos_documento 
                 if doc["codigoClasificador"] == cliente_data["codigo_tipo_documento_identidad"]), 
                None
            )
            if tipo_documento_cliente:
                seleccion_tipo_documento = tipo_documento_cliente["descripcion"]
                codigo_clasificador_documento = tipo_documento_cliente["codigoClasificador"]
                st.sidebar.text_input(
                    "Tipo de Documento:", 
                    value=tipo_documento_cliente["descripcion"], 
                    disabled=True
                )
            
            if cliente_data["codigo_tipo_documento_identidad"] == '2':
                complemento = st.sidebar.text_input(
                    "Complemento:", 
                    value=cliente_data['complemento'], 
                    disabled=True
                )
            
            nombre_cliente = st.sidebar.text_input(
                "Razón Social:", 
                value=cliente_data['nombre_razon_social'].upper(), 
                disabled=True
            )

            # Mostrar email solo si existe
            if cliente_data['email']:
                email = st.sidebar.text_input(
                    "Email:", 
                    value=cliente_data['email'], 
                    disabled=True
                )

            # Mostrar teléfono solo si existe
            if cliente_data['telefono']:
                telefono = st.sidebar.text_input(
                    "Teléfono:", 
                    value=cliente_data['telefono'], 
                    disabled=True
                )
            
            codigo_cliente = cliente_data['codigo_cliente']
            nit_valido = True  # Cliente existente es válido
            logger.info(f"Cliente existente cargado: {numero_documento}")

        else:
            # Cliente nuevo
            opciones_tipos_documento = [doc["descripcion"] for doc in tipos_documento]
            seleccion_tipo_documento = st.sidebar.selectbox(
                "Tipo de Documento:", 
                opciones_tipos_documento, 
                index=2
            )
            
            tipo_documento_seleccionado = next(
                (doc for doc in tipos_documento 
                 if doc["descripcion"] == seleccion_tipo_documento), 
                None
            )
            
            if tipo_documento_seleccionado:
                codigo_clasificador_documento = tipo_documento_seleccionado["codigoClasificador"]
                
                if tipo_documento_seleccionado['codigoClasificador'] == '2':
                    complemento = st.sidebar.text_input("Complemento:", key="complemento")
                
                nombre_cliente = st.sidebar.text_input(
                    "Razón Social:", 
                    placeholder="Sin Nombre", 
                    key="nombre_cliente"
                )
                email = st.sidebar.text_input("Email:", key="email")
                telefono = st.sidebar.text_input("Teléfono:", key="telefono")

                if seleccion_tipo_documento == "NIT - NÚMERO DE IDENTIFICACIÓN TRIBUTARIA":
                    valido, mensaje = verificar_nit_cliente(numero_documento, message_placeholder)
                    if valido:
                        show_message('success', f"✔️ NIT válido: {mensaje}", message_placeholder)
                        nit_valido = True
                        logger.info(f"NIT válido verificado: {numero_documento}")
                    else:
                        show_message('error', mensaje, message_placeholder)
                        nit_valido = False
                        logger.warning(f"NIT inválido: {numero_documento}")

                guardar_cliente_button = st.sidebar.button(
                    "Guardar Cliente", 
                    key="guardar_cliente", 
                    disabled=(not nit_valido and seleccion_tipo_documento == "NIT - NÚMERO DE IDENTIFICACIÓN TRIBUTARIA")
                )
                
                if guardar_cliente_button:
                    if tipo_documento_seleccionado:
                        cliente_data = save_or_fetch_client_data(
                            numero_documento, 
                            tipo_documento_seleccionado['codigoClasificador'], 
                            complemento, 
                            email, 
                            nombre_cliente, 
                            numero_documento, 
                            telefono, 
                            message_placeholder
                        )
                        if cliente_data:
                            show_message('success', "✔️ Datos del cliente guardados correctamente.", message_placeholder)
                            codigo_cliente = numero_documento
                            logger.info(f"Nuevo cliente guardado: {numero_documento}")
                    else:
                        show_message('error', "Por favor selecciona un tipo de documento válido", message_placeholder)

    return {
        'numero_documento': numero_documento,
        'nit_valido': nit_valido,
        'nombre_cliente': nombre_cliente,
        'complemento': complemento,
        'email': email,
        'telefono': telefono,
        'seleccion_tipo_documento': seleccion_tipo_documento,
        'codigo_clasificador_documento': codigo_clasificador_documento,
        'codigo_cliente': codigo_cliente
    }

def render_sidebar_invoice_config(comandas, metodos_pago):
    """Renderiza la configuración de facturación en la sidebar."""
    # Selección de comandas
    id_comanda_set = set(comanda["id_comanda"] for comanda in comandas)
    available_comandas = [
        comanda for comanda in id_comanda_set 
        if comanda not in st.session_state.processed_comandas
    ]

    selected_id_comanda = st.sidebar.multiselect(
        "Selecciona las comandas", 
        available_comandas, 
        key="selected_comandas", 
        placeholder="Comandas Generadas", 
        help="Selecciona las comandas que componen la factura."
    )

    # Método de pago
    opciones_metodos_pago = [metodo["descripcion"] for metodo in metodos_pago]
    indice_metodo_pago_predeterminado = next(
        (i for i, metodo in enumerate(metodos_pago) if metodo["codigoClasificador"] == 1), 
        0
    )

    seleccion_metodo_pago = st.sidebar.selectbox(
        "Tipo de Pago:", 
        opciones_metodos_pago, 
        index=66, 
        key="metodo_pago"
    )

    metodo_pago_seleccionado = next(
        (metodo for metodo in metodos_pago if metodo["descripcion"] == seleccion_metodo_pago), 
        None
    )

    codigo_clasificador_metodo_pago = None
    if metodo_pago_seleccionado:
        codigo_clasificador_metodo_pago = int(metodo_pago_seleccionado["codigoClasificador"])

    # Dígitos de tarjeta si es necesario
    ultimos_digitos_tarjeta = None
    if seleccion_metodo_pago == "TARJETA":
        ultimos_digitos_tarjeta = st.sidebar.text_input(
            "Ingresa los últimos 4 dígitos de la tarjeta:", 
            max_chars=4, 
            key="ultimos_digitos_tarjeta"
        )

    # Descuentos
    on = st.sidebar.checkbox("Aplicar Descuento")
    descuento_adicional = Decimal(0.00)
    monto_giftcard = Decimal(0.00)

    if on:
        descuento_adicional = st.sidebar.number_input(
            "Descuento Adicional:", 
            min_value=0, 
            step=5, 
            key="descuento_adicional"
        )
        if descuento_adicional is None:
            descuento_adicional = Decimal(0.00)
        else:
            descuento_adicional = Decimal(descuento_adicional)

    # Gift card si el método de pago lo permite
    if codigo_clasificador_metodo_pago is not None:
        if codigo_clasificador_metodo_pago in GIFT_CARD_CODES:
            monto_giftcard = st.sidebar.number_input(
                "Gift Card:", 
                min_value=0, 
                step=5, 
                key="monto_giftcard"
            )
            if monto_giftcard is None:
                monto_giftcard = Decimal(0.00)
            else:
                monto_giftcard = Decimal(monto_giftcard)
        else:
            monto_giftcard = Decimal(0.00)
    else:
        monto_giftcard = Decimal(0.00)

    return {
        'selected_id_comanda': selected_id_comanda,
        'seleccion_metodo_pago': seleccion_metodo_pago,
        'metodo_pago_seleccionado': metodo_pago_seleccionado,
        'codigo_clasificador_metodo_pago': codigo_clasificador_metodo_pago,
        'ultimos_digitos_tarjeta': ultimos_digitos_tarjeta,
        'descuento_adicional': descuento_adicional,
        'monto_giftcard': monto_giftcard
    }
