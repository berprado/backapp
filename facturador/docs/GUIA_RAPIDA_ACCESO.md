# ⚡ Guía Rápida: Acceso a la Pestaña Unificada

## 🎯 En 3 Pasos

### 1️⃣ Inicia la Aplicación
```powershell
cd c:\Users\Bernardo\Desktop\backapp\facturador
streamlit run main.py
```

### 2️⃣ Verifica el Estado
```
Sidebar debe mostrar:
🟢 SISTEMA ONLINE
```

### 3️⃣ Haz Clic en la Pestaña
```
Barra de pestañas → "Anular/Revertir"
```

---

## 🎨 Interfaz Visual

```
┌─────────────────────────────────────────────────────────────┐
│  BACKINVOICE 💎                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┬──────────────┬──────────┬───────────┬─────── │
│  │Facturar │Ver Facturas  │Clientes  │Validar NIT│...     │
│  └─────────┴──────────────┴──────────┴───────────┴─────── │
│                                                             │
│  ┌───────────────┬──────────────────┬──────────────────┬── │
│  │Gestionar CUIS │ ▶ Anular/Revertir│  Diagnostico    │   │
│  └───────────────┴──────────────────┴──────────────────┴── │
│                        ↑                                    │
│                   NUEVA PESTAÑA                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Dentro de la Pestaña

```
┌──────────────────────────────────────────────────────────────┐
│  Gestión de Anulación y Reversión                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┬─────────────────────────┐           │
│  │ 🚫 Anular Factura  │ 🔄 Revertir Anulación   │  ← Elige  │
│  └────────────────────┴─────────────────────────┘           │
│                                                              │
│  📋 [Contenido según la operación seleccionada]             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## ✅ Cambios Implementados

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Pestañas** | 2 separadas | 1 unificada |
| **Nombre** | "Anular Factura"<br>"Revertir Anulacion" | "Anular/Revertir" |
| **Código** | ~115 líneas<br>70% duplicado | ~450 líneas<br>0% duplicado |
| **Archivo** | `anular_factura_tab.py`<br>`revertir_anulacion_tab.py` | `anular_revertir_tab.py` |

---

## 🚨 Solución Rápida de Problemas

### ❌ No veo la pestaña
```
Causa: Sistema offline
Solución: Verifica conexión → Botón "🔄 Reconectar"
```

### ❌ Error de importación
```
Causa: Archivo no encontrado
Solución: Verifica que existe:
  c:\Users\Bernardo\Desktop\backapp\facturador\tabs\anular_revertir_tab.py
```

### ❌ Aparecen pestañas viejas
```
Causa: Caché de Streamlit
Solución: En el navegador presiona: C (limpiar) → R (recargar)
```

---

## 📚 Documentación Completa

- **Este archivo**: Acceso rápido
- `ACCESO_PESTAÑA_UNIFICADA.md`: Guía detallada
- `REFACTOR_ANULAR_REVERTIR.md`: Documentación técnica
- `MIGRACION_ANULAR_REVERTIR.md`: Guía de integración

---

**Estado:** ✅ IMPLEMENTADO  
**Última actualización:** 12 de enero de 2025
