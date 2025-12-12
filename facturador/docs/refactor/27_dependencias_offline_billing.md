# Dependencias internas de [facturador/offline_billing.py](facturador/offline_billing.py)

## Vision general
[facturador/offline_billing.py](facturador/offline_billing.py) gestiona la emision y seguimiento de facturas en modo contingencia: marca cabeceras, persiste detalles, genera XML locales y expone formularios Streamlit para registrar eventos significativos.

## Modulos propios utilizados

1. **[facturador/data_access.py](facturador/data_access.py)**  
   - Componentes: SessionLocal.  
   - Rol: abrir sesiones ORM para leer y escribir cabeceras/detalles en modo offline.

2. **[facturador/models.py](facturador/models.py)**  
   - Modelos: FacturaCabecera, FacturaDetalle, Cufd, SincronizarParametricaEventosSignificativos, EventoSignificativoRegistrado.  
   - Rol: mapear registros de facturas y catalogos normativos usados al preparar, guardar y listar facturas contingentes.

3. **[facturador/logger_config.py](facturador/logger_config.py)**  
   - Funciones: get_logger.  
   - Rol: obtener loggers dedicados a contingencia y facturacion para registrar cambios de estado y fallas.

4. **[facturador/invoice_xml_generator.py](facturador/invoice_xml_generator.py)** *(importacion diferida)*  
   - Funciones: generate_xml_invoice.  
   - Rol: reutilizar el generador principal para construir el XML de facturas offline antes de su envio.

5. **[facturador/contingency_manager.py](facturador/contingency_manager.py)** *(importacion diferida)*  
   - Funciones: get_contingency_manager.  
   - Rol: recuperar estado de eventos significativos activos para anotar codigo y tiempos en cabeceras offline.

## Conclusion
La logica offline reusa la infraestructura de datos documentada en [facturador/docs/refactor/04_dependencias_data_access.md](facturador/docs/refactor/04_dependencias_data_access.md) y complementa el flujo de contingencia descrito en [facturador/docs/refactor/16_dependencias_contingency_manager.md](facturador/docs/refactor/16_dependencias_contingency_manager.md). Sus importaciones diferidas preservan compatibilidad con el generador XML mientras se mantiene desacoplada la UI contingente.
