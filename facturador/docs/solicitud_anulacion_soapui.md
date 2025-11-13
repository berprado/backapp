##Anulacion:
Para anular una factura emitida debemos proporcionar el numero de la factura para luego conectarnos a la base de datos y obtener de la tabla 'factura_cabecera' el valor del 'cuf' correspondiente al numero de factura proporcionado.
Tambien es necesario obtener de la tabla 'cufd' el valor de la columna 'codigo' con el valor correspondiente en la colummna 'vigente' igual a 1. Ese 'codigo' que viene a ser el codigo vigente al momento de anular la factura debe ser enviado en la solicitud como '<cufd>'
Por otro lado, necesitamos especificar el motivo de la anulacion, para eso se debe mostrar un st.selectbox con los valores de la columna 'descripción' disponibles la tabla 'sincronizarparametricamotivoanulacion'
La descripcion seleccionada tiene un valor correspondiente disponible en la columna 'codigoClasificador' que debe ser enviado en la solicitud como '<codigoMotivo>'
Habiendo obtenido los valores para '<cufd>', '<cuf>' y '<codigoMotivo>' tenemos, junto a los datos del archivo .env, toda la informacion necesaria para realizar la solicitud de anulacion cuya estructura esta detallada a continuación.

#Solicitud Raw:

```
POST https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta HTTP/1.1
Accept-Encoding: gzip,deflate
Content-Type: text/xml;charset=UTF-8
SOAPAction: ""
apikey: TokenApi eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJCT0xJVklBTkZPT0QiLCJjb2RpZ29TaXN0ZW1hIjoiN0M0OEY3NkRBRkU0RjIwOUI5RDBENjYiLCJuaXQiOiJINHNJQUFBQUFBQUFBRE0yTVRHd05ETXdNZ0VBREF1Nk9Ra0FBQUE9IiwiaWQiOjYzNTMzOCwiZXhwIjoxNzI1MTQ1MTYyLCJpYXQiOjE3MTk4ODkxMzMsIm5pdERlbGVnYWRvIjozNDQwOTYwMjQsInN1YnNpc3RlbWEiOiJTRkUifQ.G_N3cv-KSvcPjkkBQLHqE11cQa3LIFnRjnxHQdA9W5Fl7OnkKBl0ATihT2MxCXHfGSg7_205av-a2bWU1k__BQ
Content-Length: 1507
Host: pilotosiatservicios.impuestos.gob.bo
Connection: Keep-Alive
User-Agent: Apache-HttpClient/4.5.5 (Java/16.0.2)

<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
						<soapenv:Header/>
						<soapenv:Body>
							<siat:anulacionFactura>
								<SolicitudServicioAnulacionFactura>
									<!--type: int-->
									<codigoAmbiente>2</codigoAmbiente>
									<!--type: int-->
									<codigoDocumentoSector>1</codigoDocumentoSector>
									<!--type: int-->
									<codigoEmision>1</codigoEmision>
									<!--type: int-->
									<codigoModalidad>1</codigoModalidad>
									<!--Optional:-->
									<!--type: int-->
									<codigoPuntoVenta>0</codigoPuntoVenta>
									<!--type: string-->
									<codigoSistema>7C48F76DAFE4F209B9D0D66</codigoSistema>
									<!--type: int-->
									<codigoSucursal>0</codigoSucursal>
									<!--type: string-->
									<cufd>BQW9Dfm9pQUE=N0jIwOUI5RDBENjY=QlVSbmZWZUlZVUFM0OEY3NkRBRkU0R</cufd>
									<!--type: string-->
									<cuis>ECD914AC</cuis>
									<!--type: long-->
									<nit>344096024</nit>
									<!--type: int-->
									<tipoFacturaDocumento>1</tipoFacturaDocumento>
									<!--type: int-->
									<codigoMotivo>1</codigoMotivo>
									<!--type: string-->
									<cuf>178B43EFDB95C02411B9A789AFE0C9DFE409C89D8021987ACFD8E8E74</cuf>
								</SolicitudServicioAnulacionFactura>
							</siat:anulacionFactura>
						</soapenv:Body>
					</soapenv:Envelope>
```

Aqui detallo a manera de ejemplo tres tipos de posibles respuestas a nuestra solicitud de anulacion. Una respuesta anulando la factura, una respuesta rechazando la anulacion por que esta ya se ha realizado y una tercera rechazando la anulacion por que la factura que se desea anular no existe en el servidor remoto.
Las estructuras de las respuestas estan detallada a continuación.

#Respuesta Raw anulando la factura:

```
HTTP/1.1 200 
Date: Fri, 30 Aug 2024 06:54:32 GMT
Content-Type: text/xml;charset=UTF-8
Content-Length: 396
Connection: keep-alive

<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
						<soap:Body>
							<ns2:anulacionFacturaResponse xmlns:ns2="https://siat.impuestos.gob.bo/">
								<RespuestaServicioFacturacion>
									<codigoDescripcion>ANULACION CONFIRMADA</codigoDescripcion>
									<codigoEstado>905</codigoEstado>
									<transaccion>true</transaccion>
								</RespuestaServicioFacturacion>
							</ns2:anulacionFacturaResponse>
						</soap:Body>
					</soap:Envelope>
```

#Respuesta Raw informando que ya se anulo previamente la factura:

```
HTTP/1.1 200 
Date: Fri, 30 Aug 2024 06:58:53 GMT
Content-Type: text/xml;charset=UTF-8
Content-Length: 531
Connection: keep-alive

<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
						<soap:Body>
							<ns2:anulacionFacturaResponse xmlns:ns2="https://siat.impuestos.gob.bo/">
								<RespuestaServicioFacturacion>
									<codigoDescripcion>ANULACION RECHAZADA</codigoDescripcion>
									<codigoEstado>906</codigoEstado>
									<mensajesList>
										<codigo>936</codigo>
										<descripcion>LA FACTURA O NOTA DE CREDITO-DEBITO YA SE ENCUENTRA ANULADA</descripcion>
									</mensajesList>
									<transaccion>false</transaccion>
								</RespuestaServicioFacturacion>
							</ns2:anulacionFacturaResponse>
						</soap:Body>
					</soap:Envelope>
					
```
#Respuesta Raw informando que la factura no existe 
```
HTTP/1.1 200 
Date: Fri, 30 Aug 2024 07:29:27 GMT
Content-Type: text/xml;charset=UTF-8
Content-Length: 528
Connection: keep-alive

<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
						<soap:Body>
							<ns2:anulacionFacturaResponse xmlns:ns2="https://siat.impuestos.gob.bo/">
								<RespuestaServicioFacturacion>
									<codigoDescripcion>ANULACION RECHAZADA</codigoDescripcion>
									<codigoEstado>906</codigoEstado>
									<mensajesList>
										<codigo>924</codigo>
										<descripcion>LA FACTURA O NOTA, NO EXISTE EN LA BASE DE DATOS DEL SIN</descripcion>
									</mensajesList>
									<transaccion>false</transaccion>
								</RespuestaServicioFacturacion>
							</ns2:anulacionFacturaResponse>
						</soap:Body>
					</soap:Envelope>
	```