
**SOLICITUD**

POST https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionOperaciones HTTP/1.1
Accept-Encoding: gzip,deflate
Content-Type: text/xml;charset=UTF-8
SOAPAction: ""
apikey: TokenApi eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJiZXJwcmFkb0BnbWFpbC5jb20iLCJjb2RpZ29TaXN0ZW1hIjoiODE1MDZGMTM2RDMyNzEyNTJGRTBENjYiLCJuaXQiOiJINHNJQUFBQUFBQUFBRE0yTVRHd05ETXdNZ0VBREF1Nk9Ra0FBQUE9IiwiaWQiOjUyODE1OTgsImV4cCI6MTc0ODcyNTIyNywiaWF0IjoxNzQzNDY5MTk3LCJuaXREZWxlZ2FkbyI6MzQ0MDk2MDI0LCJzdWJzaXN0ZW1hIjoiU0ZFIn0.bCeM_68L3M72HyZ2Agxw-UIBCzkxUNzW3Dcv97-QGuCXv_H5h7duyk3XWA_bu2LoJ3Xin22_UNTWCJ-IolAfdw
Content-Length: 1152
Host: pilotosiatservicios.impuestos.gob.bo
Connection: Keep-Alive
User-Agent: Apache-HttpClient/4.5.5 (Java/17.0.12)

<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:siat="https://siat.impuestos.gob.bo/">
   <soapenv:Header/>
   <soapenv:Body>
      <siat:registroEventoSignificativo>
         <SolicitudEventoSignificativo>
            <codigoAmbiente>2</codigoAmbiente>
            <codigoMotivoEvento>1</codigoMotivoEvento>
            <!--Optional:-->
            <codigoPuntoVenta>0</codigoPuntoVenta>
            <codigoSistema>81506F136D3271252FE0D66</codigoSistema>
            <codigoSucursal>0</codigoSucursal>
            <cufd>BQW9Dfm9pQUE=ODzEyNTJGRTBENjY=QnxnMnBDTEVaVUFE1MDZGMTM2RDMyN</cufd>
            <cufdEvento>BQW9Dfm9pQUE=ODzEyNTJGRTBENjY=QnxnMnBDTEVaVUFE1MDZGMTM2RDMyN</cufdEvento>
            <cuis>733057C3</cuis>
            <descripcion>CORTE DEL SERVICIO DE INTERNET</descripcion>
            <fechaHoraFinEvento>2025-04-11T02:06:00</fechaHoraFinEvento>
            <fechaHoraInicioEvento>2025-04-11T00:20:00</fechaHoraInicioEvento>
            <nit>344096024</nit>
         </SolicitudEventoSignificativo>
      </siat:registroEventoSignificativo>
   </soapenv:Body>
</soapenv:Envelope>

**RESPUESTA**

HTTP/1.1 200 
Date: Fri, 11 Apr 2025 06:07:52 GMT
Content-Type: text/xml;charset=UTF-8
Content-Length: 393
Connection: keep-alive

<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><ns2:registroEventoSignificativoResponse xmlns:ns2="https://siat.impuestos.gob.bo/"><RespuestaListaEventos><codigoRecepcionEventoSignificativo>9229350</codigoRecepcionEventoSignificativo><transaccion>true</transaccion></RespuestaListaEventos></ns2:registroEventoSignificativoResponse></soap:Body></soap:Envelope><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
	<soap:Body>
		<ns2:registroEventoSignificativoResponse xmlns:ns2="https://siat.impuestos.gob.bo/">
			<RespuestaListaEventos>
				<codigoRecepcionEventoSignificativo>9229350</codigoRecepcionEventoSignificativo>
				<transaccion>true</transaccion>
			</RespuestaListaEventos>
		</ns2:registroEventoSignificativoResponse>
	</soap:Body>
</soap:Envelope>