"""
Módulo unificado para gestión de anulación y reversión de facturas.

Este módulo combina las funcionalidades de anulación de facturas válidas
y reversión de anulaciones en una sola interfaz, mejorando la experiencia
del usuario y reduciendo la duplicación de código.

Características:
- Interfaz unificada con st.segmented_control (Streamlit 1.50.0)
- Validación automática del estado de facturas
- Mensajes contextuales según la operación seleccionada
- Logging exhaustivo de todas las operaciones
- Cumplimiento normativo del SIN (Servicio de Impuestos Nacionales)

Normativa aplicable:
- Anulación: Hasta el día 9 del mes siguiente a la emisión
- Reversión: Hasta el día 9 del mes siguiente a la emisión (una sola vez)

Autor: Sistema de Facturación
Fecha: 2025-01-12
Versión: 1.0.0
"""

import streamlit as st
from anulacion import anular_factura
from reversion import enviar_solicitud_reversion, procesar_respuesta_reversion
from data_access import obtener_cuf_por_numero_factura, obtener_motivos_anulacion
from ui_utils import show_message
from logger_config import get_logger

logger = get_logger()


def render():
    """
    Renderiza la interfaz unificada de anulación y reversión de facturas.
    
    Esta función es el punto de entrada principal del módulo y gestiona
    la lógica de presentación y control de flujo para ambas operaciones.
    
    Workflow:
    1. Usuario selecciona operación (Anular o Revertir)
    2. Ingresa número de factura
    3. Sistema valida y muestra información contextual
    4. Usuario completa campos adicionales (solo para anulación: motivo)
    5. Sistema procesa la solicitud y muestra resultado
    
    Returns:
        None: La función modifica el estado de Streamlit directamente
    """
    # Título principal de la pestaña
    st.header("🔧 Gestión de Facturas: Anulación y Reversión")
    
    # Logging de acceso a la pestaña
    log_enabled = st.session_state.get("main_active_tab_name") == "Anular o Revertir"
    if log_enabled:
        logger.info("Usuario accedió a la pestaña 'Gestión de Facturas (Anular/Revertir)'")
    
    # =========================================================================
    # SELECTOR DE OPERACIÓN (st.segmented_control - Streamlit 1.50.0)
    # =========================================================================
    
    st.markdown("### 📋 Seleccione la operación")
    
    operacion = st.segmented_control(
        label="Tipo de operación:",
        options=["Anular Factura", "Revertir Anulación"],
        default="Anular Factura",
        selection_mode="single",
        key="operacion_factura_selector",
        help="""
        **Anular Factura:** Invalida una factura válida (emitida por error o con datos incorrectos).
        **Revertir Anulación:** Restaura una factura anulada a su estado válido original.
        """
    )
    
    # Log de la operación seleccionada
    if log_enabled:
        logger.debug(f"Operación seleccionada: {operacion}")
    
    # =========================================================================
    # INFORMACIÓN CONTEXTUAL SEGÚN LA OPERACIÓN
    # =========================================================================
    
    st.markdown("---")  # Separador visual
    
    if operacion == "Anular Factura":
        st.info(
            "ℹ️ **Anulación de Factura**\n\n"
            "• Invalida una factura **válida** que fue emitida por error.\n"
            "• **Plazo:** Hasta el día **9 del mes siguiente** a la emisión.\n"
            "• Se debe especificar un **motivo** según el catálogo del SIN.\n"
            "• El comprador debe ser notificado de esta operación."
        )
    else:  # Revertir Anulación
        st.info(
            "ℹ️ **Reversión de Anulación**\n\n"
            "• Restaura una factura **anulada** a su estado válido original.\n"
            "• **Plazo:** Hasta el día **9 del mes siguiente** a la emisión original.\n"
            "• Solo puede hacerse **UNA vez** por factura.\n"
            "• Las facturas revertidas **NO pueden volver a ser anuladas**."
        )
    
    # =========================================================================
    # CAMPO COMÚN: NÚMERO DE FACTURA
    # =========================================================================
    
    st.markdown("### 🔢 Datos de la Factura")
    
    numero_factura = st.text_input(
        label="Número de factura:",
        placeholder="Ejemplo: 12345",
        help="Ingrese el número de la factura sobre la que desea realizar la operación",
        key=f"num_factura_{operacion.lower().replace(' ', '_').replace('ó', 'o')}"
    )
    
    # =========================================================================
    # VALIDACIÓN AUTOMÁTICA Y FEEDBACK EN TIEMPO REAL
    # =========================================================================
    
    if numero_factura and numero_factura.strip():
        # Intentar obtener información de la factura
        cuf, factura = obtener_cuf_por_numero_factura(numero_factura.strip())
        
        if factura and not isinstance(factura, str):
            # Factura encontrada - Mostrar su estado actual
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Cliente:** {getattr(factura, 'nombreRazonSocial', 'N/A')}")
                st.markdown(f"**Monto:** Bs. {getattr(factura, 'montoTotal', 0):.2f}")
                st.markdown(f"**Fecha emisión:** {getattr(factura, 'fechaEmision', 'N/A')}")
            
            with col2:
                estado_actual = getattr(factura, 'estado', 'Desconocido')
                
                if estado_actual == "Validada" or estado_actual == "Valida":
                    st.success("✅ VÁLIDA")
                elif estado_actual == "Anulada":
                    st.error("🚫 ANULADA")
                else:
                    st.warning(f"⚠️ {estado_actual}")
            
            # Validación contextual: sugerir operación correcta
            if operacion == "Anular Factura" and estado_actual == "Anulada":
                st.warning(
                    "⚠️ **Atención:** Esta factura ya está **ANULADA**. "
                    "Si desea restaurarla, seleccione 'Revertir Anulación'."
                )
            elif operacion == "Revertir Anulación" and (estado_actual == "Validada" or estado_actual == "Valida"):
                st.warning(
                    "⚠️ **Atención:** Esta factura está **VÁLIDA**. "
                    "Si desea anularla, seleccione 'Anular Factura'."
                )
        elif numero_factura.strip():
            # Factura no encontrada
            st.error(f"❌ No se encontró la factura N° {numero_factura}")
    
    # =========================================================================
    # SECCIÓN ESPECÍFICA SEGÚN LA OPERACIÓN SELECCIONADA
    # =========================================================================
    
    st.markdown("---")
    
    # Placeholder para mensajes de resultado
    message_placeholder = st.empty()
    
    if operacion == "Anular Factura":
        _render_seccion_anulacion(numero_factura, message_placeholder)
    else:  # Revertir Anulación
        _render_seccion_reversion(numero_factura, message_placeholder)


# =============================================================================
# SECCIÓN DE ANULACIÓN
# =============================================================================

def _render_seccion_anulacion(numero_factura: str, message_placeholder):
    """
    Renderiza la sección específica para anulación de facturas.
    
    Args:
        numero_factura (str): Número de factura ingresado por el usuario
        message_placeholder: Contenedor de Streamlit para mensajes de resultado
    """
    st.markdown("### 📝 Motivo de Anulación")
    
    # Obtener motivos desde la base de datos
    opciones_motivos = obtener_motivos_anulacion()
    
    if opciones_motivos:
        descripcion_motivo = st.selectbox(
            label="Seleccione el motivo:",
            options=opciones_motivos,
            help="Motivos oficiales según el catálogo del SIN",
            key="motivo_anulacion_selector"
        )
    else:
        st.error("❌ No se encontraron motivos de anulación disponibles en la base de datos.")
        logger.error("No se encontraron motivos de anulación en la base de datos")
        descripcion_motivo = None
    
    st.markdown("---")
    
    # Botón de acción para anulación
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            label="🚫 Anular Factura",
            type="primary",
            use_container_width=True,
            key="btn_anular_factura"
        ):
            _procesar_anulacion(numero_factura, descripcion_motivo, message_placeholder)


def _procesar_anulacion(numero_factura: str, descripcion_motivo: str, message_placeholder):
    """
    Procesa la solicitud de anulación de una factura.
    
    Este método coordina todo el flujo de anulación:
    1. Valida que los campos estén completos
    2. Llama al servicio de anulación
    3. Procesa la respuesta del SIAT
    4. Actualiza la base de datos local
    5. Muestra el resultado al usuario
    
    Args:
        numero_factura (str): Número de la factura a anular
        descripcion_motivo (str): Descripción del motivo de anulación
        message_placeholder: Contenedor para mostrar mensajes
    
    Returns:
        None: Los resultados se muestran directamente en la UI
    """
    # Limpiar mensajes previos
    message_placeholder.empty()
    
    # Validación de campos requeridos
    if not numero_factura or not numero_factura.strip():
        show_message('warning', "⚠️ Por favor, ingrese el número de la factura.", message_placeholder)
        logger.warning("Intento de anulación sin número de factura")
        return
    
    if not descripcion_motivo:
        show_message('warning', "⚠️ Por favor, seleccione un motivo de anulación.", message_placeholder)
        logger.warning(f"Intento de anulación sin motivo - Factura: {numero_factura}")
        return
    
    # Log del inicio del proceso
    logger.info(f"[ANULACIÓN] Iniciando anulación de factura #{numero_factura} con motivo: {descripcion_motivo}")
    
    # Mostrar indicador de procesamiento
    with st.spinner("Procesando anulación en el SIAT..."):
        # Llamar a la función de anulación
        exito, mensaje = anular_factura(numero_factura.strip(), descripcion_motivo)
    
    # Procesar resultado y mostrar mensaje
    if exito:
        show_message('success', f"✅ {mensaje}", message_placeholder)
        logger.info(f"[ANULACIÓN] ✅ Exitosa para factura #{numero_factura}: {mensaje}")
        
        # Mostrar información adicional de éxito
        st.balloons()  # Animación de celebración
        st.success(
            f"**Factura #{numero_factura} anulada correctamente**\n\n"
            f"• Motivo: {descripcion_motivo}\n"
            f"• Recuerde notificar al cliente de esta operación."
        )
    else:
        show_message('error', f"❌ {mensaje}", message_placeholder)
        logger.error(f"[ANULACIÓN] ❌ Error en factura #{numero_factura}: {mensaje}")
        
        # Mostrar sugerencias según el tipo de error
        if "plazo" in mensaje.lower():
            st.warning("💡 **Sugerencia:** La factura está fuera del plazo de anulación (9 días del mes siguiente).")
        elif "anulada" in mensaje.lower():
            st.info("💡 **Sugerencia:** Si desea restaurar esta factura, use la opción 'Revertir Anulación'.")


# =============================================================================
# SECCIÓN DE REVERSIÓN
# =============================================================================

def _render_seccion_reversion(numero_factura: str, message_placeholder):
    """
    Renderiza la sección específica para reversión de anulaciones.
    
    Args:
        numero_factura (str): Número de factura ingresado por el usuario
        message_placeholder: Contenedor de Streamlit para mensajes de resultado
    """
    # Advertencia importante sobre reversión
    st.warning(
        "⚠️ **Advertencia Importante**\n\n"
        "• Una factura solo puede ser **revertida UNA vez**.\n"
        "• Después de revertir, la factura **NO podrá anularse nuevamente**.\n"
        "• Asegúrese de que realmente desea restaurar esta factura."
    )
    
    st.markdown("---")
    
    # Botón de acción para reversión
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            label="🔄 Revertir Anulación",
            type="primary",
            use_container_width=True,
            key="btn_revertir_anulacion"
        ):
            _procesar_reversion(numero_factura, message_placeholder)


def _procesar_reversion(numero_factura: str, message_placeholder):
    """
    Procesa la solicitud de reversión de una anulación.
    
    Este método coordina todo el flujo de reversión:
    1. Valida que el campo esté completo
    2. Obtiene el CUF de la factura
    3. Envía la solicitud al SIAT
    4. Procesa la respuesta
    5. Actualiza la base de datos local
    6. Muestra el resultado al usuario
    
    Args:
        numero_factura (str): Número de la factura a revertir
        message_placeholder: Contenedor para mostrar mensajes
    
    Returns:
        None: Los resultados se muestran directamente en la UI
    """
    # Limpiar mensajes previos
    message_placeholder.empty()
    
    # Validación de campo requerido
    if not numero_factura or not numero_factura.strip():
        show_message('warning', "⚠️ Por favor, ingrese el número de la factura.", message_placeholder)
        logger.warning("Intento de reversión sin número de factura")
        return
    
    # Log del inicio del proceso
    logger.info(f"[REVERSIÓN] Iniciando reversión de anulación para factura #{numero_factura}")
    
    # Mostrar indicador de procesamiento
    with st.spinner("Obteniendo información de la factura..."):
        # Obtener CUF de la factura
        cuf, factura = obtener_cuf_por_numero_factura(numero_factura.strip())
    
    if not cuf:
        show_message('error', "❌ No se encontró la factura especificada.", message_placeholder)
        logger.error(f"[REVERSIÓN] No se encontró CUF para la factura #{numero_factura}")
        return
    
    logger.info(f"[REVERSIÓN] CUF encontrado para factura #{numero_factura}: {cuf}")
    
    # Enviar solicitud al SIAT
    with st.spinner("Procesando reversión en el SIAT..."):
        exito_solicitud, respuesta_siat = enviar_solicitud_reversion(cuf)
    
    logger.info(f"[REVERSIÓN] Respuesta del SIAT recibida para factura #{numero_factura}")
    
    if exito_solicitud:
        # Procesar respuesta del SIAT
        exito_reversion, mensaje_reversion = procesar_respuesta_reversion(respuesta_siat, factura)
        
        if exito_reversion:
            show_message('success', f"✅ {mensaje_reversion}", message_placeholder)
            logger.info(f"[REVERSIÓN] ✅ Exitosa para factura #{numero_factura}: {mensaje_reversion}")
            
            # Mostrar información adicional de éxito
            st.balloons()  # Animación de celebración
            st.success(
                f"**Factura #{numero_factura} revertida correctamente**\n\n"
                f"• La factura ha sido restaurada a su estado VÁLIDO.\n"
                f"• Recuerde que esta factura ya NO puede ser anulada nuevamente.\n"
                f"• Notifique al cliente de esta operación."
            )
        else:
            show_message('error', f"❌ {mensaje_reversion}", message_placeholder)
            logger.error(f"[REVERSIÓN] ❌ Error al procesar reversión de factura #{numero_factura}: {mensaje_reversion}")
            
            # Mostrar sugerencias según el tipo de error
            if "plazo" in mensaje_reversion.lower():
                st.warning("💡 **Sugerencia:** La reversión está fuera del plazo permitido (9 días del mes siguiente).")
            elif "no está anulada" in mensaje_reversion.lower():
                st.info("💡 **Sugerencia:** Esta factura no está anulada. Verifique el número de factura.")
    else:
        show_message('error', f"❌ {respuesta_siat}", message_placeholder)
        logger.error(f"[REVERSIÓN] ❌ Error en solicitud de reversión para factura #{numero_factura}: {respuesta_siat}")
        
        # Información adicional sobre errores de comunicación
        if "timeout" in str(respuesta_siat).lower():
            st.error("💡 El servicio del SIAT no respondió a tiempo. Por favor, intente nuevamente.")
        elif "conexión" in str(respuesta_siat).lower() or "connection" in str(respuesta_siat).lower():
            st.error("💡 No se pudo conectar con el servicio del SIAT. Verifique su conexión a internet.")
