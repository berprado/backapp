== Requirements

=== Must Have
- El sistema debe generar facturas en formato XML conforme a los esquemas del SIN.
- Debe firmar digitalmente los XML según el estándar XMLDSig.
- Debe conectarse a los servicios SOAP del SIN para:
  * Solicitar CUIS y CUFD.
  * Registrar eventos significativos.
  * Sincronizar catálogos y hora.
  * Enviar facturas (individual, contingencia, masiva).
  * Validar respuesta del SIN y almacenar código de recepción.
- Debe calcular y enviar el hash SHA-256 del XML comprimido en Gzip.
- Debe almacenar todas las facturas y sus respuestas del SIN en una base de datos relacional.
- Debe permitir imprimir o enviar por correo la representación gráfica y el XML de la factura.
- Debe gestionar errores y reintentos automáticos ante fallas de validación.
- Debe registrar y manejar eventos significativos obligatorios tras cualquier contingencia.
- Debe emitir y almacenar facturas offline en caso de contingencia, para luego ser enviadas en paquetes.
- Debe estar listo para pruebas y certificación del SIN.

=== Should Have
- Portal web para que el cliente consulte y descargue sus facturas (XML y PDF).
- Gestión multi-sucursal y multi-punto de venta.
- Módulo de administración de usuarios y permisos.
- Dashboard de monitoreo de estados de envío y validaciones.
- Almacenamiento local de facturas sin código de respuesta para verificación posterior del estado.

=== Could Have
- Integración con ERP interno para generación automática de facturas.
- Módulo de reportes y estadísticas tributarias.

=== Won’t Have (por ahora)
- Facturación con QR dinámico desde dispositivos móviles.
- Facturación desde canales offline sin reconexión posterior.

== Method

=== Arquitectura General

La solución estará compuesta por los siguientes módulos principales:

[plantuml, architecture, png]
----
@startuml
package "Sistema de Facturación Electrónica" {
  [Frontend Web] --> [API Gateway]

  package "Backend (Microservicios)" {
    [FacturaService] --> [SIN Connector]
    [ContingenciaService] --> [Storage Offline]
    [EventoService] --> [SIN Connector]
    [CatalogoService] --> [SIN Connector]
    [HorarioService] --> [SIN Connector]
    [PDFService] --> [Correo / Portal Cliente]
  }

  [API Gateway] --> [FacturaService]
  [API Gateway] --> [EventoService]
  [API Gateway] --> [ContingenciaService]
  [API Gateway] --> [PDFService]

  [SIN Connector] --> [Servicios Web SOAP del SIN]
  [FacturaService] --> [Base de Datos]
  [ContingenciaService] --> [Base de Datos]
  [EventoService] --> [Base de Datos]
}
@enduml
----

=== Flujos Clave

==== Emisión Individual

1. Solicitud de CUFD (válido por 24h).
2. Generación de XML.
3. Firma Digital XML (XMLDSig).
4. Validación contra XSD.
5. Compresión (Gzip) y cálculo hash SHA256.
6. Envío al SIN vía servicio SOAP.
7. Registro de código de recepción o errores.

==== Emisión por Contingencia

1. Detectar falla en comunicación o servicio del SIN (Timeout, 500, -1, etc).
2. Cambiar modo a "fuera de línea" y almacenar localmente las facturas (máx. 500 por paquete).
3. Obtener nuevo CUFD una vez restablecido el servicio.
4. Registrar evento significativo (tipo contingencia).
5. Enviar los paquetes al SIN.

==== Registro de Evento Significativo

1. Ante cada contingencia, registrar evento en sistema local.
2. Registrar oficialmente en el SIN dentro de 48h.

==== Verificación Estado de Factura

- Facturas emitidas durante fallos críticos deben ser verificadas posterior a la recuperación para determinar si fueron registradas o requieren anulación.

---

A continuación, vamos a describir la **estructura de base de datos** y luego los algoritmos clave. 
