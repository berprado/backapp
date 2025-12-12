# Dependencias internas de [facturador/tabs/facturacion_tab.py](facturador/tabs/facturacion_tab.py)

## Visión general
[facturador/tabs/facturacion_tab.py](facturador/tabs/facturacion_tab.py) implementa la experiencia completa de facturación en línea y contingencia, orquestando cálculos, generación de XML, firmado, envío, almacenamiento y coordinación con la impresión.

## Módulos propios utilizados

1. **[facturador/database.py](facturador/database.py)**  
   - Componentes: SessionLocal (importación directa y diferida).  
   - Rol: abrir sesiones ORM para validar y renovar CUFD.

2. **[facturador/data_models/__init__.py](facturador/data_models/__init__.py)**  
   - Modelos: FacturaProcesada, DetalleFactura.  
   - Rol: estructurar la factura consolidada que se usa en la vista previa y la impresión.

3. **[facturador/data_access.py](facturador/data_access.py)**  
   - Funciones: fetch_tipos_documento, obtener_cufd_de_evento_activo, guardar_factura_cabecera, guardar_factura_detalle.  
   - Rol: traer catálogos normativos y persistir la factura emitida.

4. **[facturador/business_logic.py](facturador/business_logic.py)**  
   - Funciones: calculate_totals, collect_product_lines, generate_invoice_link.  
   - Rol: calcular montos y preparar datos comerciales para el XML y la UI.

5. **[facturador/invoice_xml_generator.py](facturador/invoice_xml_generator.py)**  
   - Funciones: generate_xml_invoice.  
   - Rol: componer el XML normativo previo a la firma.

6. **[facturador/invoice_templates.py](facturador/invoice_templates.py)**  
   - Funciones: generate_html_invoice, generate_html_invoice_legacy, generate_compact_html_invoice, numero_a_palabras_con_decimales_como_fraccion.  
   - Rol: generar vistas previas HTML y leyendas impresas.

7. **[facturador/validators.py](facturador/validators.py)**  
   - Funciones: validar_factura_cabecera, validar_factura_detalle.  
   - Rol: validar la factura antes del envío y almacenar errores de negocio.

8. **[facturador/xml_signer.py](facturador/xml_signer.py)**  
   - Funciones: sign_xml.  
   - Rol: firmar digitalmente el XML cumpliendo el estándar exigido por el SIN.

9. **[facturador/generate_cuf.py](facturador/generate_cuf.py)**  
   - Funciones: generate_cuf.  
   - Rol: construir el CUF previo al envío.

10. **[facturador/cufd.py](facturador/cufd.py)**  
    - Funciones: solicitar_cufd.  
    - Rol: renovar el CUFD cuando caduca en plena operación.

11. **[facturador/zeeper.py](facturador/zeeper.py)**  
    - Funciones: validar_xml, comprimir_xml, obtener_hash, enviar_solicitud.  
    - Rol: validar, comprimir y transmitir el XML firmado al SIAT.

12. **[facturador/response_handler.py](facturador/response_handler.py)**  
    - Funciones: parse_siat_response, display_siat_response.  
    - Rol: interpretar respuestas normativas y mostrar feedback al usuario.

13. **[facturador/invoice_manager.py](facturador/invoice_manager.py)**  
    - Funciones: obtener_y_reservar_numero_factura, revertir_incremento_numero_factura.  
    - Rol: administrar la numeración correlativa y revertir reservas fallidas.

14. **[facturador/print_manager.py](facturador/print_manager.py)**  
    - Funciones: initialize_print_state, solicitar_impresion, get_print_state_summary.  
    - Rol: desencadenar trabajos de impresión y monitorear su estado.

15. **[facturador/facturacion_sidebar.py](facturador/facturacion_sidebar.py)**  
    - Funciones: load_base_data, render_sidebar_client_data, render_sidebar_invoice_config, reset_sidebar_fields.  
    - Rol: reutilizar la construcción de la UI y datos de la barra lateral.

16. **[facturador/ui_utils.py](facturador/ui_utils.py)**  
    - Funciones: show_message.  
    - Rol: unificar el manejo de mensajes contextuales.

17. **[facturador/logger_config.py](facturador/logger_config.py)**  
    - Funciones: get_logger, get_facturacion_logger, get_xml_logger, get_printer_logger.  
    - Rol: registrar eventos diferenciados para operación, facturación, XML e impresión.

## Conclusión
[facturador/tabs/facturacion_tab.py](facturador/tabs/facturacion_tab.py) es el núcleo operativo descrito en [facturador/docs/refactor/03_dependencias_main.md](facturador/docs/refactor/03_dependencias_main.md). Este inventario de dependencias habilita refactors puntuales sobre generación, firmado, envío e impresión siguiendo las guías de contingencia (`contingencia_*.md`) y el plan maestro [facturador/docs/refactor/01_plan_refactorizacion_ui.md](facturador/docs/refactor/01_plan_refactorizacion_ui.md).