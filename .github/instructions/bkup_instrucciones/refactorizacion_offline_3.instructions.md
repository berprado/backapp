---
applyTo: '**'
---
### **Fase de Refactorización Offline: Paso 3 de 3 (INSTRUCCIONES DETALLADAS)**

**Objetivo:** Modificar `facturacion_tab.py` para que la lógica del botón "Facturar" se separe en dos flujos distintos (online y offline), y construir la lógica completa para el flujo offline.

#### **Acción 1: Preparar `facturacion_tab.py` para la Bifurcación**

1.  **Añadir el Nuevo Import:** Al principio de `facturacion_tab.py`, añade la importación de la nueva función que acabamos de definir.
    ```python
    from data_access import obtener_cufd_de_evento_activo
    ```
2.  **Crear las Funciones Contenedoras:** Dentro de `facturacion_tab.py`, crea las estructuras de las dos nuevas funciones. Aceptarán muchos parámetros, así que prepáralas para ello.
    ```python
    def _handle_online_submission(invoice_config, client_data, ...otros_parametros...):
        # (El código irá aquí)
        pass

    def _handle_offline_submission(invoice_config, client_data, evento_activo, ...otros_parametros...):
        # (El código irá aquí)
        pass
    ```

#### **Acción 2: Mover la Lógica Existente al Contenedor "Online"**

1.  **Localiza la Lógica:** En `_render_facturar_button`, busca todo el bloque de código que se encuentra dentro del `try...except`. Este bloque empieza con `logger.info("Iniciando proceso de facturación")` y termina con el `except Exception as e: ...`.
2.  **Cortar y Pegar:** **Corta** todo ese bloque de código (`try...except`) y **pégalo** dentro de la nueva función `_handle_online_submission`.
3.  **Ajustar los Parámetros:** Asegúrate de que la firma de la función `_handle_online_submission` reciba todas las variables que necesita el código que acabas de pegar (por ejemplo, `tipos_documento`, `lineas_productos`, `subtotal`, etc.).

#### **Acción 3: Implementar la Lógica "Offline"**

1.  **Rellenar el Contenedor Offline:** Ahora, rellena la función `_handle_offline_submission` con la nueva lógica que diseñamos. Te la proporciono de nuevo aquí, ya validada y completa:

    ```python
    def _handle_offline_submission(invoice_config, client_data, evento_activo, tipos_documento,
                                   lineas_productos, subtotal, total, fecha_emision,
                                   fecha_emision_str, message_placeholder):
        """Maneja la lógica para generar y guardar una factura en modo offline."""
        try:
            logger.info("Iniciando proceso de facturación OFFLINE")

            # 1. OBTENER CUFD DEL EVENTO
            cufd_evento = obtener_cufd_de_evento_activo() 
            if not cufd_evento:
                show_message('error', "No se encontró un CUFD válido para el evento de contingencia.", message_placeholder)
                return

            # 2. OBTENER NÚMERO DE FACTURA Y GENERAR CUF OFFLINE
            numero_factura = obtener_y_reservar_numero_factura()
            nit_emisor = int(os.getenv('NIT'))
            cuf = generate_cuf(
                nit=nit_emisor,
                fecha_emision=fecha_emision,
                codigoSucursal=int(os.getenv('CODIGO_SUCURSAL')),
                codigoModalidad=int(os.getenv('CODIGO_MODALIDAD')),
                tipoEmision=2,  # <-- TIPO DE EMISIÓN OFFLINE
                tipoFactura=int(os.getenv('CODIGO_TIPO_FACTURA')),
                tipoDocumentoSector=int(os.getenv('CODIGO_DOCUMENTO_SECTOR')),
                numeroFactura=numero_factura,
                puntoVenta=int(os.getenv('CODIGO_PUNTO_VENTA'))
            )

            # 3. MANEJAR EXCEPCIÓN DE NIT
            tipo_documento_seleccionado = next((doc for doc in tipos_documento if doc["descripcion"] == client_data['seleccion_tipo_documento']), None)
            codigo_excepcion = 1 if tipo_documento_seleccionado and tipo_documento_seleccionado['codigoClasificador'] == '5' else None

            # 4. GENERAR XML
            xml_str, factura_cabecera_data, detalles_data = generate_xml_invoice(
                # ... (Pasa todos los parámetros que necesita la función, como en el flujo online)
                # Asegúrate de pasar los valores correctos para el modo offline:
                cufd=cufd_evento,
                codigoExcepcion=codigo_excepcion
            )
            
            # 5. FIRMAR Y VALIDAR LOCALMENTE
            signed_xml_str = sign_xml(xml_str, "xmls/llaves/private_key_ok.pem", "xmls/llaves/certificado_ok.pem", cuf)
            
            filename = f"offline_invoices/factura_{numero_factura}.xml"
            os.makedirs("offline_invoices", exist_ok=True)
            with open(filename, "w", encoding='utf-8') as f:
                f.write(signed_xml_str)
            
            if not validar_xml(filename, 'xmls/schemas/facturaElectronicaCompraVenta.xsd'):
                show_message('error', "El XML generado localmente no es válido. Revise los logs.", message_placeholder)
                return

            # 6. GUARDAR EN BASE DE DATOS
            factura_cabecera_data['tipoEmision'] = "2" # <-- TIPO DE EMISIÓN OFFLINE
            factura_cabecera_data['estado'] = "PENDIENTE_ENVIO"
            factura_cabecera_data['codigoEvento'] = evento_activo.get('id')
            
            # (El resto del código de guardado en BD es igual al del flujo online)
            guardar_factura_cabecera(factura_cabecera_data)
            for detalle in detalles_data:
                guardar_factura_detalle(detalle)
            
            show_message('success', f"✅ Factura N° {numero_factura} generada y guardada localmente. Pendiente de envío.", message_placeholder)
            
            # 7. LIMPIAR ESTADO DE LA UI
            st.session_state['factura_validada'] = False # Importante para que no aparezca el botón de imprimir
            if 'selected_comandas' in st.session_state:
                st.session_state.selected_comandas = []
            st.rerun()

        except Exception as e:
            show_message('error', f"❌ Error en el proceso de facturación offline: {str(e)}", message_placeholder)
            logger.exception("Error en facturación offline")
    ```

#### **Acción 4: Modificar `invoice_xml_generator.py`**

1.  Abre `invoice_xml_generator.py`.
2.  Añade `codigoExcepcion: Optional[int] = None` a los parámetros de la función `generate_xml_invoice`.
3.  Reemplaza la línea estática de `codigoExcepcion` con esta lógica condicional:
    ```python
    if codigoExcepcion is not None:
        ET.SubElement(cabecera, "codigoExcepcion").text = str(codigoExcepcion)
    else:
        ET.SubElement(cabecera, "codigoExcepcion", attrib={"xsi:nil": "true"})
    ```

#### **Acción 5: Conectar la Bifurcación en `_render_facturar_button`**

1.  Vuelve a `facturacion_tab.py` y a la función `_render_facturar_button`.
2.  Elimina los mensajes de `DEBUG` y reemplázalos con las llamadas a las nuevas funciones que has creado.

    ```python
    def _render_facturar_button(is_online, evento_activo, ...otros_params...):
        # ... (código del texto del botón) ...

        if st.button(...):
            if is_online:
                _handle_online_submission(...)
            else:
                _handle_offline_submission(...)
    ```