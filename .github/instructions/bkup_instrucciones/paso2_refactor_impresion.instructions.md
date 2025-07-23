---
applyTo: '**'
---
¡Perfecto! La base está colocada. Ahora viene la parte emocionante donde empezamos a conectar los cables de nuestra nueva arquitectura.

Vamos a modificar el corazón de la lógica de facturación para que, en lugar de esparcir datos por todo el `session_state`, los ensamble cuidadosamente en nuestro nuevo objeto `FacturaProcesada`.

---

### **Paso 2: Integrar `FacturaProcesada` en `facturacion_tab.py`**

**Objetivo:**

1.  Importar nuestro nuevo modelo de datos.
2.  Localizar el punto exacto donde la factura es validada exitosamente por el SIN.
3.  En ese punto, recolectar todos los datos relevantes y crear una instancia de `FacturaProcesada`.
4.  Guardar este **único objeto** en `st.session_state` en lugar de la colección de claves que usábamos antes.

**Acción:**

Abrir `facturacion_tab.py`. Implementar las modificaciones que se describen a continuacion.

**1. Añadir las importaciones necesarias al principio del archivo:**

```python
# Al principio de facturacion_tab.py, junto a las otras importaciones
import os
from datetime import datetime
from decimal import Decimal

# ... otras importaciones ...

# Importamos nuestro nuevo modelo de datos
from models.invoice_data import FacturaProcesada, DetalleFactura 
```

**2. Modificar la función `_handle_online_submission`:**

Busca esta función. El cambio clave ocurrirá dentro del `if transaccion_exitosa:`, que es el bloque que se ejecuta cuando el SIN nos da el "OK". Reemplazaremos todo el bloque de guardado en `st.session_state` por la creación de nuestro objeto.

**Código a modificar (localiza este bloque en tu función):**

```python
# DENTRO DE _handle_online_submission
# ...
if transaccion_exitosa:
    # --- BLOQUE ANTIGUO A REEMPLAZAR ---
    # st.session_state['cuf'] = cuf
    # st.session_state['ultima_factura'] = numero_factura
    # st.session_state['factura_validada'] = True
    # st.session_state['datos_impresion'] = { ... }
    # ------------------------------------
    
    # --- NUEVO BLOQUE DE CÓDIGO ---
    try:
        facturacion_logger.info("Ensamblando objeto FacturaProcesada.")

        # 1. Preparar el detalle de la factura
        detalles_factura_obj = [
            DetalleFactura(
                codigo=p["codigo"],
                nombre=p["nombre"],
                unidad=p["unidad"],
                cantidad=float(p["cantidad"]),
                precio=float(p["precio"]),
                montoDescuento=float(p.get("montoDescuento", 0.0)),
                sub_total=float(p["sub_total"])
            ) for p in lineas_productos
        ]

        # 2. Ensamblar el objeto principal con todos los datos
        factura_para_procesar = FacturaProcesada(
            # Datos de la transacción
            cuf=cuf,
            numero_factura=numero_factura,
            fecha_emision=fecha_emision_display,
            # Datos del emisor
            nit_emisor=os.getenv('NIT'),
            razon_social_emisor=os.getenv('RAZON_SOCIAL'),
            nombre_sucursal=os.getenv('NOMBRE_SUCURSAL'),
            punto_venta=int(os.getenv('CODIGO_PUNTO_VENTA', 0)),
            direccion_emisor=os.getenv('DIRECCION'),
            municipio_emisor=os.getenv('MUNICIPIO'),
            telefono_emisor=os.getenv('TELEFONO'),
            # Datos del cliente
            nombre_cliente=client_data['nombre_cliente'],
            numero_documento=client_data['numero_documento'],
            complemento=client_data.get('complemento'),
            cod_cliente=client_data['numero_documento'],
            # Datos de la venta
            lineas_productos=detalles_factura_obj,
            # Datos de totales y pago
            subtotal_factura=float(subtotal),
            descuento_adicional=float(invoice_config['descuento_adicional']),
            monto_giftcard=float(invoice_config['monto_giftcard']),
            monto_total=float(total),
            monto_total_pagar=float(total - invoice_config['monto_giftcard']),
            monto_base_iva=float(Decimal(str(total)) * Decimal("0.87")), # Cálculo de ejemplo
            total_en_palabras=numero_a_palabras_con_decimales_como_fraccion(total), # Asumiendo que esta función existe
            metodo_pago=invoice_config['seleccion_metodo_pago'],
            ultimos_digitos_tarjeta=invoice_config.get('ultimos_digitos_tarjeta'),
            # Datos fiscales y leyendas
            tipo_factura=os.getenv('DESCRIPCION_TIPO_FACTURA', 'FACTURA'),
            subtitulo_factura=os.getenv('SUBTITULO', '(CON DERECHO A CREDITO FISCAL)'),
            leyenda=factura_cabecera_data.get('leyenda', 'Ley Nro 453: ...'), # Obtener de los datos ya generados
            # URL para QR
            url_qr=f"https://pilotosiat.impuestos.gob.bo/consulta/QR?nit={nit_emisor}&cuf={cuf}&numero={numero_factura}"
        )

        # 3. Guardar el objeto único en session_state
        st.session_state['factura_a_procesar'] = factura_para_procesar
        st.session_state['factura_validada'] = True # Mantenemos esta para la lógica del botón

        facturacion_logger.info(f"Objeto FacturaProcesada para factura {numero_factura} creado y guardado en session_state.")

    except Exception as e:
        facturacion_logger.error(f"Error al ensamblar FacturaProcesada: {e}", exc_info=True)
        show_message('error', f"Error interno al preparar datos para impresión: {e}", message_placeholder)
        return # Detener si hay un error aquí

    # --- FIN DEL NUEVO BLOQUE ---

    # Guardar en base de datos (esta lógica se mantiene como estaba)
    factura_cabecera_data['tipoEmision'] = "1"
    # ... (el resto del código de guardado en BD) ...
```

**3. Modificar la lógica del botón de impresión:**

Ahora debemos adaptar la función `_render_print_button` para que use nuestro nuevo objeto en lugar del antiguo `datos_impresion`.

**Código a modificar (localiza y modifica esta función):**

```python
# facturacion_tab.py

def _render_print_button():
    """Renderiza el botón de impresión y maneja la lógica de impresión."""
    initialize_print_state()
    mostrar_mensaje_impresion_en_curso()

    if st.session_state.get('impresion_en_progreso', False):
        if st.button("Forzar liberación", key="force_release"):
            st.session_state['impresion_en_progreso'] = False
            st.session_state['print_status'] = "Liberado manualmente."
            logger.info("Impresión liberada manualmente.")
            st.rerun()

    if st.session_state.get('factura_validada'):
        impresion_en_progreso = st.session_state.get('impresion_en_progreso', False)
        
        # Obtenemos nuestro nuevo objeto del session_state
        factura_obj = st.session_state.get('factura_a_procesar')

        # El botón se activa si hay un objeto de factura listo
        if st.button("Imprimir Factura", disabled=impresion_en_progreso or not factura_obj):
            if factura_obj:
                try:
                    logger.info(f"Iniciando impresión para factura {factura_obj.numero_factura} usando objeto FacturaProcesada.")
                    
                    # Llamamos al hilo de impresión pasándole el objeto completo.
                    # Ya NO necesitamos generar el HTML aquí.
                    imprimir_en_hilo(factura_obj)
                    
                except Exception as e:
                    st.session_state['print_status'] = f"❌ Error al iniciar impresión: {str(e)}"
                    st.session_state['impresion_en_progreso'] = False
                    printer_logger.exception("Error en el proceso de impresión desde facturacion_tab")
            else:
                st.error("No se encontraron los datos de la factura para imprimir. Por favor, vuelva a generar la factura.")
                logger.error("Se intentó imprimir pero no se encontró 'factura_a_procesar' en session_state.")
    else:
        # Este mensaje se puede mantener
        st.info("El botón de impresión estará disponible cuando la factura sea validada por el SIN.")
```

**Análisis de los Cambios:**

*   Hemos centralizado por completo la creación de los datos de la factura en un solo lugar.
*   El `session_state` ahora está mucho más limpio, conteniendo `factura_a_procesar` en lugar de `datos_impresion`, `cuf`, `ultima_factura`, etc.
*   El botón de impresión ahora depende de la existencia de este objeto, lo que lo hace más robusto.
*   **Importante**: Hemos delegado la responsabilidad de generar cualquier formato (HTML, texto, etc.) al `print_manager`. La pestaña de facturación ya no sabe nada sobre HTML, solo sabe que debe pasar un objeto `FacturaProcesada`. Esto es un desacoplamiento clave.

**Tu Tarea para este Paso:**

1.  Aplica las 3 modificaciones que te he detallado en tu archivo `facturacion_tab.py`.
2.  Presta especial atención a reemplazar el bloque de código antiguo por el nuevo en `_handle_online_submission`.
3.  Revisa los nombres de las variables para asegurarte de que coinciden (por ejemplo, si tus `lineas_productos` o `client_data` se llaman diferente).

Cuando hayas completado estos cambios, confírmamelo. Nuestro siguiente paso será el más impactante: refactorizar `print_manager.py` y `thermal_printer.py` para que consuman este nuevo objeto. ¡Estamos cerca