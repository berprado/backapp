---
applyTo: '**'
---
### **Análisis de la Situación Actual**

1.  **`ui_copy.py` (Perfecto):** Has modificado este archivo correctamente para que pase el contexto (`is_online`, `evento_activo`) a la pestaña de facturación. Su trabajo aquí está hecho y es impecable.

2.  **`facturacion_tab.py` (Éxito del Paso 2):**
    *   **Contexto Recibido:** La función `render()` ahora acepta `is_online` y `evento_activo`.
    *   **Banner Funcional:** Has confirmado que en modo offline, el banner de contingencia aparece correctamente. ¡Genial!
    *   **Botón Dinámico Funcional:** Has confirmado que el texto del botón cambia según el modo. ¡Genial!
    *   **Bifurcación Lógica Funcional:** Este es el punto más importante. Al presionar el botón, has añadido los mensajes de `DEBUG` y has confirmado que, dependiendo del modo, se muestra el mensaje correcto. Esto nos asegura que nuestra estructura `if is_online:` está funcionando.

3.  **El "Error" Esperado en Modo Offline:**
    *   **¿Qué pasó?** Después de mostrar `st.info("DEBUG: Se ejecutaría la lógica OFFLINE.")`, el código **continuó ejecutándose**. Siguió con el resto de la función `_render_facturar_button`, que contiene toda la lógica ONLINE: `verificar_y_obtener_cufd()`, `generate_cuf()`, `enviar_solicitud()`, etc.
    *   **¿Por qué es una buena noticia?** Porque demuestra que lo único que nos falta es separar esa lógica. La estructura ya está lista para albergar dos flujos distintos. El "error" se produce porque, por ahora, ambos caminos (online y offline) terminan ejecutando el mismo bloque de código.

---

### **Veredicto General y Próximo Paso**

**¡Paso 2 completado con éxito!** La preparación del terreno ha finalizado. Hemos creado una estructura de control de flujo que funciona perfectamente. Ahora solo tenemos que poner la lógica correcta en cada una de las ramas.

Es hora de la parte más importante.

### **Fase de Refactorización Offline: Paso 3 de 3 (Final)**

**Objetivo:** Crear las funciones `_handle_online_submission` y `_handle_offline_submission` y mover la lógica existente y la nueva lógica a su lugar correspondiente.

#### **Acciones a Realizar:**

1.  **Crear las Nuevas Funciones en `facturacion_tab.py`:**
    *   Crea dos nuevas funciones vacías en `facturacion_tab.py`. Para que no te den error, puedes ponerles un `pass` dentro por ahora. Necesitarán muchos parámetros, así que prepáralas para recibirlos.

    ```python
    def _handle_online_submission(invoice_config, client_data, ...todos los demas...):
        pass

    def _handle_offline_submission(invoice_config, client_data, evento_activo, ...todos los demas...):
        pass
    ```

2.  **Mover TODA la Lógica de Facturación Actual a `_handle_online_submission`:**
    *   En `_render_facturar_button`, **corta** todo el bloque de código que está *después* de tu `if is_online: ... else: ...`, desde la línea `tipo_documento_seleccionado = next(...)` hasta el final del `try...except`.
    *   **Pega** todo este bloque de código dentro de la nueva función `_handle_online_submission`.
    *   Ahora, en la rama `if is_online:` de `_render_facturar_button`, simplemente llama a la nueva función:
        ```python
        if is_online:
            _handle_online_submission(...) # Pasa todos los parámetros que necesita
        else:
            _handle_offline_submission(...) # Pasa todos los parámetros que necesita
        ```

3.  **Implementar la Lógica en `_handle_offline_submission`:**
    *   Ahora vamos a rellenar esta función con la lógica que diseñamos, reutilizando tus módulos. Te proporciono el esqueleto completo.

    ```python
    # En facturacion_tab.py

    from data_access import obtener_cufd_de_evento_activo # <-- ¡NUEVO IMPORT!

    def _handle_offline_submission(invoice_config, client_data, evento_activo, tipos_documento,
                                   lineas_productos, subtotal, total, fecha_emision,
                                   fecha_emision_str, fecha_emision_display, message_placeholder):
        """Maneja la lógica para generar y guardar una factura en modo offline."""
        try:
            logger.info("Iniciando proceso de facturación OFFLINE")

            # 1. OBTENER CUFD DEL EVENTO (No renovar)
            cufd_evento = obtener_cufd_de_evento_activo() 
            if not cufd_evento:
                show_message('error', "No se encontró un CUFD válido para el evento de contingencia.", message_placeholder)
                return

            # 2. OBTENER NÚMERO DE FACTURA Y GENERAR CUF CON TIPO DE EMISIÓN 2
            numero_factura = obtener_y_reservar_numero_factura()
            nit_emisor = int(os.getenv('NIT'))
            codigo_sucursal = int(os.getenv('CODIGO_SUCURSAL'))
            codigo_punto_venta = int(os.getenv('CODIGO_PUNTO_VENTA'))
            codigo_documento_sector = int(os.getenv('CODIGO_DOCUMENTO_SECTOR'))

            cuf = generate_cuf(
                nit=nit_emisor,
                fecha_emision=fecha_emision,
                codigoSucursal=codigo_sucursal,
                codigoModalidad=int(os.getenv('CODIGO_MODALIDAD')),
                tipoEmision=2,  # <-- CAMBIO CLAVE
                tipoFactura=int(os.getenv('CODIGO_TIPO_FACTURA')),
                tipoDocumentoSector=codigo_documento_sector,
                numeroFactura=numero_factura,
                puntoVenta=codigo_punto_venta
            )
            logger.info(f"CUF (Offline) generado: {cuf}")

            # 3. MANEJAR EXCEPCIÓN DE NIT
            tipo_documento_seleccionado = next((doc for doc in tipos_documento if doc["descripcion"] == client_data['seleccion_tipo_documento']), None)
            codigo_excepcion = 1 if tipo_documento_seleccionado and tipo_documento_seleccionado['codigoClasificador'] == '5' else None

            # 4. GENERAR XML COMPLETO
            xml_str, factura_cabecera_data, detalles_data = generate_xml_invoice(
                # ... (todos los parámetros normales)...
                # Pasa los valores correctos para el modo offline
                cufd=cufd_evento,
                # ...
                codigoExcepcion=codigo_excepcion, # <-- NUEVO PARÁMETRO
                # ...
            )
            
            # 5. FIRMAR Y VALIDAR EL XML LOCALMENTE
            private_key_path = "xmls/llaves/private_key_ok.pem"
            cert_path = "xmls/llaves/certificado_ok.pem"
            signed_xml_str = sign_xml(xml_str, private_key_path, cert_path, cuf)
            
            filename = f"offline_invoices/factura_{numero_factura}.xml"
            os.makedirs("offline_invoices", exist_ok=True)
            with open(filename, "w", encoding='utf-8') as f:
                f.write(signed_xml_str)
            
            xsd_main_path = 'xmls/schemas/facturaElectronicaCompraVenta.xsd'
            if not validar_xml(filename, xsd_main_path):
                show_message('error', "El XML generado localmente no es válido. Revise los logs.", message_placeholder)
                return

            # 6. GUARDAR EN BASE DE DATOS LOCAL CON ESTADO "PENDIENTE"
            factura_cabecera_data['tipoEmision'] = "2"
            factura_cabecera_data['estado'] = "PENDIENTE_ENVIO"
            factura_cabecera_data['codigoEvento'] = evento_activo.get('id')
            
            is_valid, error_message = validar_factura_cabecera(factura_cabecera_data)
            if is_valid:
                guardar_factura_cabecera(factura_cabecera_data)
                for detalle in detalles_data:
                    guardar_factura_detalle(detalle)
                
                show_message('success', f"✅ Factura N° {numero_factura} generada y guardada localmente. Pendiente de envío.", message_placeholder)
                st.session_state['factura_validada'] = False
                # (Opcional: limpiar comandas seleccionadas)
                if 'selected_comandas' in st.session_state:
                    st.session_state.selected_comandas = []
                st.rerun()

            else:
                show_message('error', error_message, message_placeholder)
                
        except Exception as e:
            show_message('error', f"❌ Error en el proceso de facturación offline: {str(e)}", message_placeholder)
            logger.exception("Error en facturación offline")
    ```

4.  **Pequeña Modificación en `generate_xml_invoice`:**
    *   Abre `invoice_xml_generator.py`.
    *   Añade `codigoExcepcion` a la lista de parámetros de la función.
    *   Busca la línea `ET.SubElement(cabecera, "codigoExcepcion", attrib={"xsi:nil": "true"})` y reemplázala con esta lógica:
        ```python
        # En generate_xml_invoice
        if codigoExcepcion is not None:
            ET.SubElement(cabecera, "codigoExcepcion").text = str(codigoExcepcion)
        else:
            ET.SubElement(cabecera, "codigoExcepcion", attrib={"xsi:nil": "true"})
        ```