# Documentación Actualizada — Sincronización Segura entre Productos, Combos y `productos_siat`

## 1. Introducción

Este documento describe el flujo completo, actualizado y seguro para mantener sincronizados:

- Productos simples (`alm_producto`)
- Combos (`bar_combo_coctel`)
- Tabla unificada para facturación (`productos_siat`)

Incluye:
- Lógica de negocio
- Triggers implementados
- Script de sincronización masiva
- Script de verificación anti-duplicados
- Procedimiento seguro de sincronización
- Flujo oficial de trabajo para entornos producción → prueba

---

## 2. Objetivos alcanzados

### ✔ Automatización completa
Ahora se sincronizan de forma automática:
- Productos HAB + comandables (ind_permite_comandar = 70)
- Combos HAB

### ✔ Seguridad e integridad
Se añadió un mecanismo que **verifica duplicados antes de sincronizar**, garantizando:
- No duplicar códigos en productos
- No duplicar códigos en combos
- No duplicar códigos en `productos_siat`
- No permitir que un mismo código exista en producto y combo simultáneamente

### ✔ Sincronización masiva idempotente
Se puede ejecutar las veces que sea necesario sin riesgo de corrupción de datos.

### ✔ Procedimiento seguro (`sp_sync_productos_siat_seguro`)
Es un único comando:

```sql
CALL sp_sync_productos_siat_seguro();
```

Que:
1. Verifica duplicados  
2. Solo si todo está correcto → ejecuta la sincronización completa

---

## 3. Reglas de negocio

### 3.1 Productos sincronizables
Se sincronizan solo si cumplen:

- `estado = 'HAB'`
- `ind_permite_comandar = 70`
- `codigo` válido (no vacío, no NULL)
- Se extrae unidad de medida = **primera palabra de la descripción**

### 3.2 Combos sincronizables

- `estado = 'HAB'`
- `codigo` válido
- unidad de medida = primera palabra de la descripción

### 3.3 Tabla `productos_siat`
Todas las filas deben tener código único global y almacenar:

- código
- nombre
- unidad de medida
- tipo_origen = 'producto' o 'combo'
- id_origen = id del artículo en su tabla original

---

## 4. Triggers implementados

### 4.1 INSERT productos (`alm_producto`)

```sql
CREATE TRIGGER trg_insert_producto_to_siat
AFTER INSERT ON alm_producto
FOR EACH ROW
BEGIN
  IF NEW.estado = 'HAB'
     AND NEW.ind_permite_comandar = 70
     AND NEW.codigo IS NOT NULL
     AND NEW.codigo <> '' THEN

    INSERT INTO adminerp_copy.productos_siat (
        codigo, nombre, unidad_medida, tipo_origen, id_origen
    )
    VALUES (
        NEW.codigo,
        NEW.nombre,
        SUBSTRING_INDEX(NEW.descripcion, ' ', 1),
        'producto',
        NEW.id
    )
    ON DUPLICATE KEY UPDATE
        nombre = VALUES(nombre),
        unidad_medida = VALUES(unidad_medida),
        tipo_origen = 'producto',
        id_origen = NEW.id,
        fecha_actualizacion = CURRENT_TIMESTAMP;
  END IF;
END;
```

---

### 4.2 UPDATE productos (`alm_producto`)

```sql
CREATE TRIGGER trg_update_producto_to_siat
AFTER UPDATE ON alm_producto
FOR EACH ROW
BEGIN
  IF NEW.estado = 'HAB'
     AND NEW.ind_permite_comandar = 70
     AND NEW.codigo IS NOT NULL
     AND NEW.codigo <> '' THEN

    IF OLD.codigo <> NEW.codigo THEN
      DELETE FROM adminerp_copy.productos_siat
      WHERE tipo_origen = 'producto'
        AND id_origen = OLD.id
        AND codigo = OLD.codigo;
    END IF;

    INSERT INTO adminerp_copy.productos_siat (
        codigo, nombre, unidad_medida, tipo_origen, id_origen
    )
    VALUES (
        NEW.codigo,
        NEW.nombre,
        SUBSTRING_INDEX(NEW.descripcion, ' ', 1),
        'producto',
        NEW.id
    )
    ON DUPLICATE KEY UPDATE
        nombre = VALUES(nombre),
        unidad_medida = VALUES(unidad_medida),
        tipo_origen = 'producto',
        id_origen = NEW.id,
        fecha_actualizacion = CURRENT_TIMESTAMP;
  ELSE
    DELETE FROM adminerp_copy.productos_siat
    WHERE tipo_origen = 'producto'
      AND id_origen = OLD.id;
  END IF;
END;
```

---

### 4.3 INSERT combos (`bar_combo_coctel`)

```sql
CREATE TRIGGER trg_insert_combo_to_siat
AFTER INSERT ON bar_combo_coctel
FOR EACH ROW
BEGIN
  IF NEW.estado = 'HAB' THEN
    INSERT INTO adminerp_copy.productos_siat (
        codigo, nombre, unidad_medida, tipo_origen, id_origen
    )
    VALUES (
      NEW.codigo,
      NEW.nombre,
      SUBSTRING_INDEX(NEW.descripcion, ' ', 1),
      'combo',
      NEW.id
    )
    ON DUPLICATE KEY UPDATE
      nombre = VALUES(nombre),
      unidad_medida = VALUES(unidad_medida),
      tipo_origen = 'combo',
      id_origen = NEW.id,
      fecha_actualizacion = CURRENT_TIMESTAMP;
  END IF;
END;
```

---

### 4.4 UPDATE combos (`bar_combo_coctel`)

```sql
CREATE TRIGGER trg_update_combo_to_siat
AFTER UPDATE ON bar_combo_coctel
FOR EACH ROW
BEGIN
  IF NEW.estado = 'HAB' THEN
    INSERT INTO adminerp_copy.productos_siat (
        codigo, nombre, unidad_medida, tipo_origen, id_origen
    )
    VALUES (
      NEW.codigo,
      NEW.nombre,
      SUBSTRING_INDEX(NEW.descripcion, ' ', 1),
      'combo',
      NEW.id
    )
    ON DUPLICATE KEY UPDATE
      nombre = VALUES(nombre),
      unidad_medida = VALUES(unidad_medida),
      tipo_origen = 'combo',
      id_origen = NEW.id,
      fecha_actualizacion = CURRENT_TIMESTAMP;
  ELSE
    DELETE FROM adminerp_copy.productos_siat
    WHERE tipo_origen = 'combo'
      AND id_origen = OLD.id;
  END IF;
END;
```

---

## 5. Procedimiento seguro: verificación + sincronización

Este es el motor del sistema. Ejecuta:

```sql
CALL sp_sync_productos_siat_seguro();
```

### Funciones del procedimiento:

1. Verifica duplicados:
   - En productos HAB+70  
   - En combos HAB  
   - En productos_siat  
   - Entre productos y combos  

2. Si encuentra algo:
   - ❌ no sincroniza  
   - muestra contadores de problemas

3. Si todo está OK:
   - ✔ limpia productos_siat  
   - ✔ sincroniza combos  
   - ✔ sincroniza productos  
   - ✔ actualiza nombres, unidades, códigos  
   - ✔ deja `productos_siat` perfecto  

---

## 6. Flujo oficial de sincronización entre entornos

### Cuando sincronizas **producción → prueba** con dbForge:

1. Ejecutar el script de dbForge  
2. Ejecutar:

```sql
CALL sp_sync_productos_siat_seguro();
```

3. Debe aparecer:

```
✔ Verificaciones OK. Sincronización de productos_siat ejecutada correctamente.
```

Si no aparece, revisar duplicados.

---

## 7. Conclusiones

- Sistema blindado contra duplicados  
- Sincronización automática robusta  
- Idempotente: se puede ejecutar mil veces  
- Flujo oficial documentado  
- `productos_siat` siempre queda consistente  
- Preparado para facturación SIAT

---

**Backstage — Sistema de Comandas y Facturación Electrónica**  
Documentación actualizada (v2)
