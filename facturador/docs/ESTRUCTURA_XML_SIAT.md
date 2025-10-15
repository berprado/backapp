# 📋 Estructura XML de Servicios SIAT - Referencia Oficial

## 🎯 Propósito

Este documento centraliza las estructuras XML **exactas** requeridas por los servicios SOAP del SIAT para evitar errores de tipo "Unmarshalling Error: unexpected element".

**Regla de oro:** Los nombres de los elementos XML deben coincidir **exactamente** con los esperados por el SIAT, incluyendo mayúsculas/minúsculas y orden.

---

## 1️⃣ Anulación de Factura

### Servicio: `anulacionFactura`

### ❌ ERROR COMÚN:
```xml
<!-- INCORRECTO - Causa error HTTP 500 -->
<codigoMotivoAnulacion>1</codigoMotivoAnulacion>
```

### ✅ ESTRUCTURA CORRECTA:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <anulacionFactura>
      <SolicitudServicioAnulacionFactura>
        <codigoAmbiente>2</codigoAmbiente>
        <codigoDocumentoSector>1</codigoDocumentoSector>
        <codigoEmision>1</codigoEmision>
        <codigoModalidad>1</codigoModalidad>
        <codigoPuntoVenta>0</codigoPuntoVenta>
        <codigoSistema>7A2D62F849FA96C1AD4</codigoSistema>
        <codigoSucursal>0</codigoSucursal>
        <cufd>BQTM1QzQy5D1tJTQwMjY1MTU5N</cufd>
        <cuf>6FD3F983F0D0123456789ABCDEF...</cuf>
        <cuis>E8CD2A94</cuis>
        <nit>1234567890</nit>
        <tipoFacturaDocumento>1</tipoFacturaDocumento>
        <codigoMotivo>1</codigoMotivo>  ⬅️ NOMBRE CORRECTO
      </SolicitudServicioAnulacionFactura>
    </anulacionFactura>
  </soapenv:Body>
</soapenv:Envelope>
```

### 📝 Orden de elementos (IMPORTANTE):

El SIAT valida el orden. Seguir **exactamente** este orden:

1. `codigoAmbiente` - Ambiente (1=Producción, 2=Pruebas)
2. `codigoDocumentoSector` - Sector económico
3. `codigoEmision` - Tipo de emisión (1=Online, 2=Offline)
4. `codigoModalidad` - Modalidad (1=Electrónica, 2=Computarizada)
5. `codigoPuntoVenta` - Punto de venta (0 si no aplica)
6. `codigoSistema` - Código del sistema autorizado
7. `codigoSucursal` - Sucursal (0=Casa matriz)
8. `cufd` - Código único de facturación diaria
9. `cuf` - Código único de factura
10. `cuis` - Código único de inicio de sistema
11. `nit` - NIT del emisor
12. `tipoFacturaDocumento` - Tipo de documento
13. **`codigoMotivo`** ⬅️ No `codigoMotivoAnulacion`

---

## 2️⃣ Reversión de Anulación

### Servicio: `reversionAnulacionFactura`

### ✅ ESTRUCTURA CORRECTA:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <reversionAnulacionFactura>
      <SolicitudServicioReversionAnulacionFactura>
        <codigoAmbiente>2</codigoAmbiente>
        <codigoDocumentoSector>1</codigoDocumentoSector>
        <codigoEmision>1</codigoEmision>
        <codigoModalidad>1</codigoModalidad>
        <codigoPuntoVenta>0</codigoPuntoVenta>
        <codigoSistema>7A2D62F849FA96C1AD4</codigoSistema>
        <codigoSucursal>0</codigoSucursal>
        <cufd>BQTM1QzQy5D1tJTQwMjY1MTU5N</cufd>
        <cuf>6FD3F983F0D0123456789ABCDEF...</cuf>
        <cuis>E8CD2A94</cuis>
        <nit>1234567890</nit>
        <tipoFacturaDocumento>1</tipoFacturaDocumento>
      </SolicitudServicioReversionAnulacionFactura>
    </reversionAnulacionFactura>
  </soapenv:Body>
</soapenv:Envelope>
```

### 📝 Diferencia con Anulación:
- **NO tiene** el campo `codigoMotivo`
- Los demás campos son idénticos

---

## 3️⃣ Verificación de Estado

### Servicio: `verificacionEstadoFactura`

### ✅ ESTRUCTURA CORRECTA:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <verificacionEstadoFactura>
      <SolicitudServicioVerificacionEstadoFactura>
        <codigoAmbiente>2</codigoAmbiente>
        <codigoDocumentoSector>1</codigoDocumentoSector>
        <codigoEmision>1</codigoEmision>
        <codigoModalidad>1</codigoModalidad>
        <codigoPuntoVenta>0</codigoPuntoVenta>
        <codigoSistema>7A2D62F849FA96C1AD4</codigoSistema>
        <codigoSucursal>0</codigoSucursal>
        <cufd>BQTM1QzQy5D1tJTQwMjY1MTU5N</cufd>
        <cuf>6FD3F983F0D0123456789ABCDEF...</cuf>
        <cuis>E8CD2A94</cuis>
        <nit>1234567890</nit>
        <tipoFacturaDocumento>1</tipoFacturaDocumento>
      </SolicitudServicioVerificacionEstadoFactura>
    </verificacionEstadoFactura>
  </soapenv:Body>
</soapenv:Envelope>
```

---

## 4️⃣ Solicitud de CUFD

### Servicio: `cufd`

### ✅ ESTRUCTURA CORRECTA:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <cufd>
      <SolicitudCufd>
        <codigoAmbiente>2</codigoAmbiente>
        <codigoModalidad>1</codigoModalidad>
        <codigoPuntoVenta>0</codigoPuntoVenta>
        <codigoSistema>7A2D62F849FA96C1AD4</codigoSistema>
        <codigoSucursal>0</codigoSucursal>
        <cuis>E8CD2A94</cuis>
        <nit>1234567890</nit>
      </SolicitudCufd>
    </cufd>
  </soapenv:Body>
</soapenv:Envelope>
```

### 📝 Diferencias:
- **NO incluye** `cufd` (porque es lo que estamos solicitando)
- **NO incluye** `cuf`, `codigoDocumentoSector`, `codigoEmision`, `tipoFacturaDocumento`
- Solo 7 campos

---

## 5️⃣ Solicitud de CUIS

### Servicio: `cuis`

### ✅ ESTRUCTURA CORRECTA:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <cuis>
      <SolicitudCuis>
        <codigoAmbiente>2</codigoAmbiente>
        <codigoModalidad>1</codigoModalidad>
        <codigoPuntoVenta>0</codigoPuntoVenta>
        <codigoSistema>7A2D62F849FA96C1AD4</codigoSistema>
        <codigoSucursal>0</codigoSucursal>
        <nit>1234567890</nit>
      </SolicitudCuis>
    </cuis>
  </soapenv:Body>
</soapenv:Envelope>
```

### 📝 Diferencias:
- **NO incluye** `cuis` (porque es lo que estamos solicitando)
- **NO incluye** `cufd`, `cuf`, `codigoDocumentoSector`, `codigoEmision`, `tipoFacturaDocumento`
- Solo 6 campos

---

## 📊 Tabla Comparativa de Campos

| Campo | Anulación | Reversión | Verificación | CUFD | CUIS |
|-------|-----------|-----------|--------------|------|------|
| `codigoAmbiente` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `codigoDocumentoSector` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `codigoEmision` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `codigoModalidad` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `codigoPuntoVenta` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `codigoSistema` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `codigoSucursal` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `cufd` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `cuf` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `cuis` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `nit` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `tipoFacturaDocumento` | ✅ | ✅ | ✅ | ❌ | ❌ |
| **`codigoMotivo`** | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 🚨 Errores Comunes y Soluciones

### Error 1: "unexpected element (uri:"", local:"XXX")"

**Causa:** Nombre de elemento incorrecto o en orden incorrecto.

**Ejemplo real:**
```
unexpected element (uri:"", local:"codigoMotivoAnulacion"). 
Expected elements are <{}codigoMotivo>,...
```

**Solución:**
- Verificar nombre **exacto** del elemento
- Verificar **orden** de los elementos
- Referirse a esta documentación

---

### Error 2: "cvc-complex-type.2.4.a: Invalid content was found"

**Causa:** Elemento faltante o campo obligatorio no enviado.

**Solución:**
- Verificar que todos los campos obligatorios estén presentes
- Verificar que no haya campos `None` o vacíos

---

### Error 3: "cvc-datatype-valid.1.2.1: '' is not a valid value"

**Causa:** Campo vacío cuando se esperaba un valor.

**Solución:**
```python
# INCORRECTO
ET.SubElement(solicitud, "cuf").text = None

# CORRECTO
if cuf:
    ET.SubElement(solicitud, "cuf").text = cuf
else:
    raise ValueError("CUF no puede estar vacío")
```

---

## 🔍 Cómo Diagnosticar Errores XML

### 1. Activar logging de XML completo:

```python
# En logger_config.py
logger.setLevel(logging.DEBUG)
```

### 2. Ver el XML enviado en logs:

```bash
# PowerShell
cd C:\Users\Bernardo\Desktop\backapp\facturador\logs
tail -n 100 app.log | Select-String "XML completo"
```

### 3. Copiar el XML y validar manualmente:

```python
import xml.etree.ElementTree as ET

xml_string = """<tu xml aquí>"""
tree = ET.fromstring(xml_string)

# Imprimir estructura
for elem in tree.iter():
    print(f"Tag: {elem.tag}, Text: {elem.text}")
```

### 4. Comparar con estructura de referencia:

- Abrir este documento
- Buscar el servicio correspondiente
- Comparar nombre por nombre, orden por orden

---

## 📚 Catálogo de Códigos de Motivo

### Códigos válidos para `codigoMotivo` en Anulación:

| Código | Descripción |
|--------|-------------|
| 1 | Emitido con error (datos incorrectos) |
| 2 | Devolución de mercancía |
| 3 | Descuento por volumen |
| 4 | Descuento por pronto pago |
| 5 | Corrección de precio |
| 6 | Duplicado |
| 7 | Cliente no retiró mercancía |
| 8 | Otro (especificar en observaciones) |

**Nota:** Estos códigos deben estar sincronizados en tu BD local en la tabla `sincronizar_parametrica_motivo_anulacion`.

---

## 🛠️ Implementación en Código

### Ejemplo correcto en `siat_service_client.py`:

```python
def construir_solicitud_anulacion(self, cuf: str, codigo_motivo: int) -> bytes:
    """Construye solicitud de anulación con estructura correcta."""
    
    envelope, metodo = self._construir_envelope_base("anulacionFactura")
    solicitud = ET.SubElement(metodo, "SolicitudServicioAnulacionFactura")
    
    # Agregar campos en el ORDEN EXACTO esperado por el SIAT
    self._agregar_parametros_comunes(solicitud)  # Agrega los 12 campos base
    
    ET.SubElement(solicitud, "cuf").text = cuf
    
    # ✅ CORRECTO: Usar "codigoMotivo"
    ET.SubElement(solicitud, "codigoMotivo").text = str(codigo_motivo)
    
    # ❌ INCORRECTO: NO usar "codigoMotivoAnulacion"
    # ET.SubElement(solicitud, "codigoMotivoAnulacion").text = str(codigo_motivo)
    
    return ET.tostring(envelope, encoding='utf-8', method='xml')
```

---

## 🧪 Testing

### Script de prueba para validar estructura XML:

```python
# test_estructura_xml.py

from siat_service_client import get_siat_client
import xml.etree.ElementTree as ET

def test_estructura_anulacion():
    """Valida que el XML de anulación tenga la estructura correcta."""
    
    client = get_siat_client()
    
    # Generar XML de prueba
    xml_bytes = client.construir_solicitud_anulacion(
        cuf="A" * 64,  # CUF de prueba
        codigo_motivo=1
    )
    
    # Parsear XML
    tree = ET.fromstring(xml_bytes)
    
    # Buscar el elemento codigoMotivo
    codigo_motivo_elem = tree.find('.//{*}codigoMotivo')
    
    # Validaciones
    assert codigo_motivo_elem is not None, "❌ Falta elemento codigoMotivo"
    assert codigo_motivo_elem.text == "1", f"❌ Valor incorrecto: {codigo_motivo_elem.text}"
    
    # Verificar que NO exista codigoMotivoAnulacion
    codigo_motivo_anulacion = tree.find('.//{*}codigoMotivoAnulacion')
    assert codigo_motivo_anulacion is None, "❌ Elemento codigoMotivoAnulacion no debe existir"
    
    print("✅ Estructura XML de anulación es correcta")

if __name__ == "__main__":
    test_estructura_anulacion()
```

---

## 📖 Referencias Oficiales

- **Documentación SIAT:** https://www.impuestos.gob.bo/siat
- **Manual Técnico de Facturación Electrónica:** Versión 3.0
- **WSDL de Servicios:** https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta?wsdl

---

## ✅ Checklist de Verificación

Antes de enviar cualquier solicitud SOAP al SIAT:

- [ ] Nombres de elementos coinciden **exactamente** con esta referencia
- [ ] Orden de elementos coincide con esta referencia
- [ ] No hay elementos `None` o vacíos
- [ ] Tipos de datos son correctos (string, int según corresponda)
- [ ] El XML está bien formado (sin caracteres especiales no escapados)
- [ ] Los valores tienen longitud correcta (ej: CUF = 64 caracteres)
- [ ] El encoding es UTF-8

---

**Versión:** 1.0.0  
**Fecha:** 15 de octubre de 2025  
**Última actualización:** Corrección de `codigoMotivoAnulacion` → `codigoMotivo`  
**Estado:** ✅ Validado contra ambiente de pruebas SIAT
