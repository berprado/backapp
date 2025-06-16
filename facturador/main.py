# facturador/main.py

import streamlit as st
from datetime import datetime
from soap_services import verificar_comunicacion
import os
import sys
# Asegurar que estamos importando desde el directorio correcto 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Importar explícitamente desde el archivo database.py local del directorio facturador
from database import get_eventos_parametricos, get_cufd_vigente, obtener_evento_abierto, insertar_evento_local
from ui_copy import main as online_main
from contingencia_auto import finalizar_evento_si_conectado

st.set_page_config(
    page_title="BACKINVOICE",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# Sistema de facturación con contingencia automática"
    }
)

def main():
    # Paso previo: intentar finalizar evento abierto si hay conexión
    finalizar_evento_si_conectado()
    resultado = finalizar_evento_si_conectado()
    if resultado:
        st.success("✅ Se finalizó el evento pendiente y se comprimieron las facturas (si existían).")
    else:
        st.warning("ℹ️ No se pudo finalizar el evento o el sistema aún está sin conexión.")
    st.title("🧠 Inicializando Sistema de Facturación...")

    # Paso 1: Verificar conexión
    mensaje, conectado, tipo_deducido = verificar_comunicacion()

    if conectado:
        st.success("✅ Conexión establecida con el SIN.")
        online_main()
    else:
        st.error("❌ No se pudo conectar al SIN. Se activará la contingencia.")

        # Paso 2: Verificar si ya hay un evento abierto
        evento_existente = obtener_evento_abierto()
        if evento_existente:
            st.info("ℹ️ Ya existe un evento registrado en modo contingencia.")
        else:
            # Paso 3: Registrar evento automáticamente
            st.warning("⚠️ Registrando evento significativo automáticamente...")

            # Obtener CUFD vigente
            cufd = get_cufd_vigente()
            if not cufd:
                st.error("❌ No se pudo obtener CUFD vigente para registrar el evento.")
            else:
                eventos_parametricos = get_eventos_parametricos()
                tipos = {e["codigoClasificador"]: e["descripcion"] for e in eventos_parametricos}
                tipo_evento = tipo_deducido if tipo_deducido in tipos else "5"
                descripcion = tipos.get(tipo_evento, "Evento no identificado automáticamente")

                insertar_evento_local(
                    codigo_evento=tipo_evento,
                    descripcion=descripcion,
                    fecha_inicio=datetime.now(),
                    cufd=cufd
                )

                st.success(f"✅ Evento registrado localmente: {descripcion}")

        # Paso 4: Cargar la interfaz offline
        st.warning("🛠️ Activando modo offline de facturación...")

        
        # Mostrar formulario si hay evento activo
        evento = obtener_evento_abierto()
        if evento:
            with st.form("form_factura_offline"):
                st.subheader("📋 Ingresar factura offline")
                numero_factura = st.text_input("Número de Factura")
                nombre = st.text_input("Nombre o Razón Social")
                documento = st.text_input("Número de Documento")
                monto = st.number_input("Monto Total", min_value=0.0, format="%.2f")
                submit = st.form_submit_button("💾 Guardar como XML")

                if submit:
                    # Estructura del XML
                    now = datetime.now()
                    timestamp = now.strftime("%Y%m%d_%H%M%S")
                    nombre_archivo = f"offline_{evento['id']}_{timestamp}.xml"
                    ruta_archivo = os.path.join("offline", nombre_archivo)

                    # Asegurar existencia de carpeta
                    os.makedirs("offline", exist_ok=True)

                    contenido_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <facturaOffline>
        <idEvento>{evento['id']}</idEvento>
        <fecha>{now.strftime('%Y-%m-%d %H:%M:%S')}</fecha>
        <numeroFactura>{numero_factura}</numeroFactura>
        <nombre>{nombre}</nombre>
        <documento>{documento}</documento>
        <monto>{monto:.2f}</monto>
        </facturaOffline>
        """

                    with open(ruta_archivo, "w", encoding="utf-8") as f:
                        f.write(contenido_xml)

                    st.success(f"✅ Factura guardada como {nombre_archivo}")
        else:
            st.error("❌ No se encontró evento significativo activo para asociar la factura.")

if __name__ == "__main__":
    main()
