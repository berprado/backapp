# 🧩 Dependencias Internas del Sistema de Facturación

Este documento técnico resume los módulos propios del sistema que interactúan directamente con los principales puntos de entrada de la aplicación: `main.py` y `ui_copy.py`. Esta vista es útil para comprender cómo se organiza la lógica y qué componentes están acoplados a la ejecución principal.

---

## 🚀 Puntos de entrada analizados

- `main.py`: módulo principal de arranque del sistema.
- `ui_copy.py`: interfaz de usuario desarrollada con Streamlit.

---

## 📦 Módulos propios que interactúan con `main.py`

Esta lista se ha generado tras una revisión exhaustiva del archivo.

| Módulo               | Funciones / Responsabilidad                                                                               |
|----------------------|-----------------------------------------------------------------------------------------------------------|
| `soap_services`      | `verificar_comunicacion` – Verifica conectividad con el SIN                                              |
| `database`           | `get_eventos_parametricos`, `get_cufd_vigente`, `obtener_evento_abierto`, `insertar_evento_local`        |
| `ui_copy`            | `main` – Se llama como interfaz principal del sistema en modo **en línea**                               |
| `contingencia_auto`  | `finalizar_evento_si_conectado` – Intenta cerrar eventos abiertos si se recupera la conexión             |

---

## 🖥️ Módulos propios que interactúan con `ui_copy.py`

Lista confirmada tras revisión exhaustiva del archivo:

| Módulo                        | Funciones / Elementos Importados                                                                 |
|------------------------------|---------------------------------------------------------------------------------------------------|
| `data_access`                | `fetch_comandas`, `fetch_metodos_pago`, `fetch_tipos_documento`, `fetch_cliente`, `fetch_random_leyenda`, `guardar_factura_cabecera`, `guardar_factura_detalle`, `obtener_nombre_unidad_medida`, `obtener_motivos_anulacion`, `obtener_cuf_por_numero_factura`, `obtener_facturas_por_estado`, `obtener_factura_completa` |
| `business_logic`             | `calculate_totals`, `collect_product_lines`, `generate_invoice_link`, `generate_qr`              |
| `invoice_xml_generator`      | `generate_xml_invoice`                                                                           |
| `database`                   | `SessionLocal`                                                                                    |
| `facturador.models`          | `Cufd`, `Cliente`                                                                                 |
| `generate_cuf`               | `generate_cuf`                                                                                    |
| `cufd`                       | `solicitar_cufd`                                                                                  |
| `cuis`                       | *(importado directamente)*                                                                       |
| `zeeper`                     | `validar_xml`, `comprimir_xml`, `obtener_hash`, `enviar_solicitud`                                |
| `verifica_stream`            | *(importado directamente)*                                                                       |
| `estado_factura`             | `verificar_estado_factura`                                                                        |
| `anulacion`                  | `anular_factura`                                                                                  |
| `reversion`                  | `enviar_solicitud_reversion`, `procesar_respuesta_reversion`                                     |
| `facturador.response_handler`| `parse_siat_response`, `display_siat_response`                                                    |
| `invoice_templates`          | `generate_compact_html_invoice`                                                                   |
| `thermal_printer`            | `ThermalPrinter`                                                                                  |
| `siat_pdf`                   | `html_to_pdf`                                                                                     |
| `mostrar_lista_facturas`     | `mostrar_lista_facturas`                                                                          |

---

## 📝 Notas

- Si se agregan nuevos módulos a la aplicación, esta lista deberá actualizarse.
- También puede ser útil construir un grafo de dependencias o usar herramientas como `pydeps` o `import-tracker` para visualizaciones automáticas.

