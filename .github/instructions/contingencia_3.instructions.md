---
applyTo: '**'
---
# 📋 Instrucciones para corregir `send_batch` y asegurar parámetros normativos

## 1. Corrección del nombre del servicio
En tu error aparece:
```
Service has no operation 'recepcionPaqueteFactura'
```
👉 El nombre correcto según **contingencia_completo.md** es:
```python
client.service.RecepcionPaqueteFactura(**solicitud)
```

---

## 2. Parámetros obligatorios
Tu diccionario `solicitud` debe incluir todos los campos normativos:

- `codigoAmbiente`  
- `codigoPuntoVenta` (0 si no aplica)  
- `codigoSistema`  
- `codigoSucursal`  
- `nit`  
- `codigoDocumentoSector`  
- `codigoEmision = 2` (offline)  
- `codigoModalidad`  
- `cufd`  
- `cuis`  
- `tipoFacturaDocumento`  
- `archivo` (paquete comprimido en base64)  
- `fechaEnvio` (timestamp actual en formato `%Y-%m-%dT%H:%M:%S.%f`)  
- `hashArchivo` (SHA256)  
- `cantidadFacturas` (facturas incluidas en el paquete)  
- `codigoEvento` (devuelto al registrar el evento significativo)  

---

## 3. Ejemplo de `send_batch` corregido
```python
def send_batch(self, xml_path, gzip_path, cufd, batch_numbers, codigo_evento):
    """
    Envía un paquete de facturas comprimidas al SIN.
    """
    with open(gzip_path, "rb") as f:
        archivo_gzip = f.read()

    base64_file = base64.b64encode(archivo_gzip).decode("utf-8")
    sha256_hash = hashlib.sha256(archivo_gzip).hexdigest()

    solicitud = {
        'codigoAmbiente': self.config['codigoAmbiente'],
        'codigoPuntoVenta': self.config.get('codigoPuntoVenta', 0),
        'codigoSistema': self.config['codigoSistema'],
        'codigoSucursal': self.config['codigoSucursal'],
        'nit': self.config['nit'],
        'codigoDocumentoSector': self.config['codigoDocumentoSector'],
        'codigoEmision': 2,  # offline
        'codigoModalidad': self.config['codigoModalidad'],
        'cufd': cufd,
        'cuis': self.config['cuis'],
        'tipoFacturaDocumento': self.config['tipoFacturaDocumento'],
        'archivo': base64_file,
        'fechaEnvio': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
        'hashArchivo': sha256_hash,
        'cantidadFacturas': len(batch_numbers),
        'codigoEvento': codigo_evento
    }

    logging.info(f"[📦] Enviando paquete con {len(batch_numbers)} facturas, evento {codigo_evento}")

    client = self._get_client("FacturaCompraVenta")
    response = client.service.RecepcionPaqueteFactura(**solicitud)

    logging.info(f"[📡] Respuesta RecepcionPaqueteFactura: {response}")
    return response
```

---

## 4. Verificaciones recomendadas

Antes de invocar el servicio:
1. **Archivo comprimido**:  
   ```python
   assert os.path.exists(gzip_path) and os.path.getsize(gzip_path) > 0
   ```

2. **Hash**:  
   - Confirmar que `sha256_hash` se genera correctamente.  

3. **Parámetros clave**:  
   - `cufd` válido.  
   - `codigoEvento` existente.  
   - `cantidadFacturas >= 1`.  

4. **Fecha de envío**:  
   - Siempre usar `datetime.now()`.  

---

## ✅ Resultado esperado
- El error de operación desaparecerá.  
- El servicio reconocerá `RecepcionPaqueteFactura`.  
- Las facturas offline dejarán de quedarse en `PENDIENTE_ENVIO`.  
