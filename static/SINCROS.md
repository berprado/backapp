# Sincronización Códigos y Catálogos

Conforme a normativa vigente, la sincronización de catálogos de facturación debe realizarse diariamente a través de los Servicios Web correspondientes. Es el proceso por el cual se descargan las diferentes tablas de paramétricas utilizados por el Sistema de Facturación (códigos de productos y servicios, países, códigos de eventos significativos, códigos de mensajes de servicios, entre otros) a objeto de mantener actualizadas las tablas localmente. El consumo de estos servicios requiere de un Token Delegado.

## Servicios SOAP / Parámetros Entrada y Salida

| Servicio | Entrada | Salida |
| --- | --- | --- |
| Códigos de Actividades | Fecha y Hora | Lista de Códigos |
| Códigos de Actividades Documento Sector | Fecha y Hora | Transacción |
| Códigos de Leyendas Facturas | Fecha y Hora | Lista de Mensajes |
| Códigos de Mensajes Servicios | Fecha y Hora | Lista de Códigos |
| Códigos de Productos y Servicios | Fecha y Hora | Lista de Códigos |
| Códigos de Eventos Significativos | Fecha y Hora | Lista de Códigos |
| Códigos de Motivos Anulación | Fecha y Hora | Lista de Códigos |
| Códigos de País Origen | Fecha y Hora | Lista de Códigos |
| Códigos de Tipo Documento Identidad | Fecha y Hora | Lista de Códigos |
| Códigos de Tipo Documento Sector | Fecha y Hora | Lista de Códigos |
| Códigos de Tipo Emisión | Fecha y Hora | Lista de Códigos |
| Códigos de Tipo Habitación | Fecha y Hora | Lista de Códigos |
| Códigos de Tipo Método Pago | Fecha y Hora | Lista de Códigos |
| Códigos de Tipo Moneda | Fecha y Hora | Lista de Códigos |
| Códigos de Tipo Punto de Venta | Fecha y Hora | Lista de Códigos |
| Códigos de Tipo Factura | Fecha y Hora | Lista de Códigos |
| Códigos de Unidad de Medida | Fecha y Hora | Lista de Códigos |

### Descripción Parámetros de Entrada

| Entrada | Tipo Dato | Obligatorio | Descripción |
| --- | --- | --- | --- |
| codigoAmbiente | Numérico | Sí | Describe el tipo de ambiente utilizado. Los valores permitidos son: Producción: 1, Pruebas y Piloto: 2 |
| codigoSistema | Alfanumérico | Sí | Código de Sistema asignado al momento de realizar la solicitud de autorización. |
| nit | Numérico | Sí | NIT perteneciente al emisor de la Factura. |
| cuis | Alfanumérico | Sí | Valor único para una sucursal y/o punto de venta. |
| codigoSucursal | Numérico | Sí | Valor que identifica a la sucursal donde se realiza la emisión de la Factura: Casa Matriz: 0, Sucursal: 1, 2,..,n |
| codigoPuntoVenta | Numérico | No | Solo se envía el número del punto de venta cuando se realizará la sincronización para el mismo (1, 2,.., n). Caso contrario, enviar 0. |

### Descripción Parámetros de Salida

| Salida | Tipo Dato |
| --- | --- |
| Lista de Códigos | Alfanumérico |
| Transacción | Booleano |
| Lista de Mensajes | Alfanumérico |

## Servicios de Sincronización

A continuación, se detallan los servicios disponibles y los parámetros asociados:

1. **sincronizarActividades**  
   - Parámetros:  
     - codigoAmbiente: int  
     - codigoPuntoVenta: int (opcional, nillable)  
     - codigoSistema: string  
     - codigoSucursal: int  
     - cuis: string  
     - nit: long  

2. **sincronizarFechaHora**  
   - Parámetros: (Mismos que sincronizarActividades)

3. **sincronizarListaActividadesDocumentoSector**  
   - Parámetros: (Mismos que sincronizarActividades)

4. **sincronizarListaLeyendasFactura**  
   - Parámetros: (Mismos que sincronizarActividades)

5. **sincronizarListaMensajesServicios**  
   - Parámetros: (Mismos que sincronizarActividades)

6. **sincronizarListaProductosServicios**  
   - Parámetros: (Mismos que sincronizarActividades)

7. **sincronizarParametricaEventosSignificativos**  
   - Parámetros: (Mismos que sincronizarActividades)

8. **sincronizarParametricaMotivoAnulacion**  
   - Parámetros: (Mismos que sincronizarActividades)

9. **sincronizarParametricaPaisOrigen**  
   - Parámetros: (Mismos que sincronizarActividades)

10. **sincronizarParametricaTipoDocumentoIdentidad**  
    - Parámetros: (Mismos que sincronizarActividades)

11. **sincronizarParametricaTipoDocumentoSector**  
    - Parámetros: (Mismos que sincronizarActividades)

12. **sincronizarParametricaTipoEmision**  
    - Parámetros: (Mismos que sincronizarActividades)

13. **sincronizarParametricaTipoHabitacion**  
    - Parámetros: (Mismos que sincronizarActividades)

14. **sincronizarParametricaTipoMetodoPago**  
    - Parámetros: (Mismos que sincronizarActividades)

15. **sincronizarParametricaTipoMoneda**  
    - Parámetros: (Mismos que sincronizarActividades)

16. **sincronizarParametricaTipoPuntoVenta**  
    - Parámetros: (Mismos que sincronizarActividades)

17. **sincronizarParametricaTiposFactura**  
    - Parámetros: (Mismos que sincronizarActividades)

18. **sincronizarParametricaUnidadMedida**  
    - Parámetros: (Mismos que sincronizarActividades)

19. **verificarComunicacion**  
    - No specific parameters detailed for input
