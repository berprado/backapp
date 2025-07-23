# 📚 Instrucciones Técnicas de Facturación

Este directorio contiene documentación técnica relacionada con los flujos de emisión de facturas digitales para el sistema implementado, conforme a la normativa del Servicio de Impuestos Nacionales (SIN) de Bolivia.

Cada archivo proporciona detalles operativos y técnicos que deben ser reflejados correctamente en la implementación del sistema.

---

## 📂 Archivos disponibles

### 🧾 `instrucciones_flujo_online.md`

Describe paso a paso el proceso de emisión de facturas en modalidad **en línea**, incluyendo:

- Inicialización del sistema.
- Preparación de datos.
- Generación de identificadores fiscales (CUFD y CUF).
- Construcción, firma, validación, compresión y envío del XML.
- Validación y manejo de respuesta del SIN.

### 📦 `instrucciones_flujo_offline.md`

Contiene el procedimiento detallado para la **emisión y envío de paquetes de facturas** cuando ocurre una contingencia (modo **fuera de línea**). Incluye:

- Etapas durante y después de la contingencia.
- Registro de eventos.
- Validaciones técnicas.
- Envío de paquetes al SIN y verificación del estado.

---

## 🛠 Uso sugerido

- Esta documentación sirve como guía para desarrolladores que deban modificar, mantener o auditar los flujos de facturación.
- Se recomienda usarla como checklist de validación funcional y técnica.
- En combinación con las instrucciones de `.github/copilot-instructions.md`, permite a GitHub Copilot comprender mejor el dominio funcional.

---

## ✅ Recomendación

Mantén este contenido actualizado si se realizan cambios en los procedimientos definidos por el SIN o en la lógica del sistema.

