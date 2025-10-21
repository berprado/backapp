"""
DIAGNÓSTICO RÁPIDO - Ejecutar desde Streamlit
==============================================
Este script debe ejecutarse con: streamlit run diagnostico_rapido.py
"""

import streamlit as st
from estado_factura import verificar_estado_factura
from database import SessionLocal
from models import FacturaCabecera

st.set_page_config(page_title="Diagnóstico Factura #777", page_icon="🔍")

st.header("🔍 Diagnóstico Detallado: Factura #777")

# ===== PASO 1: Estado en BD Local =====
st.subheader("📊 Paso 1: Estado en Base de Datos Local")

session = SessionLocal()
try:
    factura = session.query(FacturaCabecera).filter_by(numeroFactura=777).first()
    
    if factura:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Estado", factura.estado)
            st.metric("Estado Validación", factura.estadoValidacion)
            
        with col2:
            st.metric("Resultado Validación", factura.resultadoValidacion)
            st.metric("Código Recepción", factura.codigoRecepcion[:20] + "..." if factura.codigoRecepcion else "NULL")
        
        with st.expander("📋 Datos Completos"):
            st.json({
                "numeroFactura": factura.numeroFactura,
                "cuf": factura.cuf[:30] + "...",
                "estado": factura.estado,
                "estadoValidacion": factura.estadoValidacion,
                "resultadoValidacion": factura.resultadoValidacion,
                "codigoRecepcion": factura.codigoRecepcion,
                "fechaEmision": str(factura.fechaEmision),
                "fechaAnulacion": str(factura.fechaAnulacion) if factura.fechaAnulacion else None,
                "anuladoPor": factura.anuladoPor,
                "motivoAnulacion": factura.motivoAnulacion
            })
        
        # Detectar inconsistencias
        if factura.estado == "Anulada" and factura.estadoValidacion != "ANULADA":
            st.warning("""
            ⚠️ **INCONSISTENCIA DETECTADA**
            
            - `estado`: "Anulada"
            - `estadoValidacion`: "{}

            Estas columnas deberían coincidir.
            """.format(factura.estadoValidacion))
        
    else:
        st.error("❌ Factura #777 no encontrada en la base de datos")
        st.stop()
        
finally:
    session.close()

st.divider()

# ===== PASO 2: Estado en SIAT =====
st.subheader("🌐 Paso 2: Estado en SIAT (Tiempo Real)")

if st.button("🔄 Consultar Estado en SIAT", type="primary"):
    with st.spinner("Consultando SIAT..."):
        resultado = verificar_estado_factura("777", force_check=True)
        
        st.success("✅ Respuesta recibida del SIAT")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Estado SIAT", resultado.get('estado_siat', 'N/A'))
        with col2:
            st.metric("Código Estado", resultado.get('codigo_estado_siat', 'N/A'))
        with col3:
            st.metric("Transacción", "✅ OK" if resultado.get('transaccion') else "❌ Error")
        
        st.info(f"**Mensaje:** {resultado.get('mensaje', 'N/A')}")
        
        # Análisis
        st.divider()
        st.subheader("📊 Análisis Comparativo")
        
        estado_bd = factura.estado.upper()
        estado_siat = resultado.get('estado_siat', '').upper()
        
        if estado_bd == estado_siat:
            st.success(f"""
            ✅ **ESTADOS COINCIDEN**
            
            - Base de Datos: {estado_bd}
            - SIAT: {estado_siat}
            
            Los estados están sincronizados correctamente.
            """)
        else:
            st.error(f"""
            ❌ **INCONSISTENCIA CRÍTICA**
            
            - Base de Datos Local: **{estado_bd}**
            - SIAT: **{estado_siat}**
            
            Los estados NO coinciden. Se requiere corrección.
            """)
            
            if estado_siat == "VÁLIDA" and estado_bd == "ANULADA":
                st.warning("""
                **Análisis del Problema:**
                
                La factura está marcada como ANULADA localmente, pero el SIAT 
                la tiene como VÁLIDA. Esto puede significar:
                
                1. ✅ **La reversión YA se hizo** (más probable)
                   - La anulación fue revertida exitosamente
                   - La factura volvió a estado VÁLIDO
                   - No puede revertirse nuevamente
                
                2. ❌ **La anulación nunca se completó**
                   - La BD se actualizó pero el SIAT rechazó
                   - Requiere anular nuevamente
                
                **Recomendación:** Si desea que la factura esté anulada,
                debe anularla nuevamente desde la interfaz.
                """)
