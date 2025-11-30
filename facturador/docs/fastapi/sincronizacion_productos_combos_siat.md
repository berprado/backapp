# Documentación de Sincronización entre Productos/Combos y productos_siat

## 1. Introducción
Este documento describe el trabajo realizado para garantizar la sincronización completa y automática entre:
- Productos simples (`alm_producto`)
- Combos (`bar_combo_coctel`)
- Catálogo de facturación (`productos_siat`)

La sincronización es fundamental para el correcto funcionamiento del sistema de facturación electrónica SIAT, ya que todos los ítems que se pueden comandar deben existir también en `productos_siat`.

---

## 2. Objetivos alcanzados

### ✔ Sincronización automática vía triggers
Ya existían dos triggers para combos. Se añadieron dos triggers equivalentes para productos simples comandables.

### ✔ Sincronización masiva inicial
Se creó un script que:
- Limpia datos desfasados en `productos_siat`.
- Inserta/actualiza combos HAB.
- Inserta/actualiza productos HAB + 70 (comandables).
- Asegura coherencia total antes de la activación de los nuevos triggers.

### ✔ Validación de unicidad de códigos
Se creó un script para comprobar:
- Duplicados internos en productos HAB+70.
- Duplicados internos en combos HAB.
- Conflictos entre códigos de productos y combos.

El sistema no presentó duplicados, lo cual garantiza que `codigo` puede usarse como clave única global.

---

## 3. Lógica de negocio utilizada

### 3.1 Productos simples (`alm_producto`)
Se consideran sincronizables cuando:
- `estado = 'HAB'`
- `ind_permite_comandar = 70`
- `codigo` válido (no NULL, no vacío)

### 3.2 Combos (`bar_combo_coctel`)
Se consideran sincronizables cuando:
- `estado = 'HAB'`
- `codigo` válido

### 3.3 Unidad de medida
Por decisión temporal, la unidad de medida se extrae como:
```
SUBSTRING_INDEX(descripcion, ' ', 1)
```
Ejemplo: `"BOTELLA 37 LENGUAS 1LT"` → `BOTELLA`.

---

## 4. Triggers implementados

### 4.1 Trigger: AFTER INSERT en alm_producto
```sql
CREATE TRIGGER adminerp_copy.trg_insert_producto_to_siat
AFTER INSERT ON adminerp_copy.alm_producto
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

### 4.2 Trigger: AFTER UPDATE en alm_producto
```sql
CREATE TRIGGER adminerp_copy.trg_update_producto_to_siat
AFTER UPDATE ON adminerp_copy.alm_producto
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

## 5. Script de sincronización masiva inicial

```sql
CREATE TABLE IF NOT EXISTS adminerp_copy.productos_siat_backup_20251129 AS
SELECT * FROM adminerp_copy.productos_siat;

SET autocommit=0;
START TRANSACTION;

DELETE ps
FROM adminerp_copy.productos_siat ps
LEFT JOIN adminerp_copy.bar_combo_coctel c
  ON ps.tipo_origen='combo' AND ps.id_origen=c.id
WHERE ps.tipo_origen='combo'
  AND (c.id IS NULL OR c.estado<>'HAB');

INSERT INTO adminerp_copy.productos_siat (
  codigo, nombre, unidad_medida, tipo_origen, id_origen
)
SELECT
  c.codigo,
  c.nombre,
  SUBSTRING_INDEX(c.descripcion,' ',1),
  'combo',
  c.id
FROM adminerp_copy.bar_combo_coctel c
WHERE c.estado='HAB'
  AND c.codigo IS NOT NULL AND c.codigo<>''
ON DUPLICATE KEY UPDATE
  nombre=VALUES(nombre),
  unidad_medida=VALUES(unidad_medida),
  tipo_origen='combo',
  id_origen=VALUES(id_origen),
  fecha_actualizacion=CURRENT_TIMESTAMP;

DELETE ps
FROM adminerp_copy.productos_siat ps
LEFT JOIN adminerp_copy.alm_producto p
  ON ps.tipo_origen='producto' AND ps.id_origen=p.id
WHERE ps.tipo_origen='producto'
  AND (p.id IS NULL
    OR p.estado<>'HAB'
    OR p.ind_permite_comandar<>70
    OR p.codigo IS NULL
    OR p.codigo='');

INSERT INTO adminerp_copy.productos_siat (
  codigo, nombre, unidad_medida, tipo_origen, id_origen
)
SELECT
  p.codigo,
  p.nombre,
  SUBSTRING_INDEX(p.descripcion,' ',1),
  'producto',
  p.id
FROM adminerp_copy.alm_producto p
WHERE p.estado='HAB'
  AND p.ind_permite_comandar=70
  AND p.codigo IS NOT NULL AND p.codigo<>''
ON DUPLICATE KEY UPDATE
  nombre=VALUES(nombre),
  unidad_medida=VALUES(unidad_medida),
  tipo_origen='producto',
  id_origen=VALUES(id_origen),
  fecha_actualizacion=CURRENT_TIMESTAMP;

COMMIT;
SET autocommit=1;
```

---

## 6. Scripts de validación

### 6.1 Duplicados en productos HAB+70
```sql
SELECT codigo, COUNT(*) AS veces
FROM adminerp_copy.alm_producto
WHERE estado='HAB' AND ind_permite_comandar=70
  AND codigo IS NOT NULL AND codigo<>''
GROUP BY codigo
HAVING COUNT(*)>1;
```

### 6.2 Duplicados en combos HAB
```sql
SELECT codigo, COUNT(*) AS veces
FROM adminerp_copy.bar_combo_coctel
WHERE estado='HAB'
  AND codigo IS NOT NULL AND codigo<>''
GROUP BY codigo
HAVING COUNT(*)>1;
```

### 6.3 Códigos repetidos entre productos y combos
```sql
SELECT p.codigo
FROM adminerp_copy.alm_producto p
JOIN adminerp_copy.bar_combo_coctel c ON p.codigo=c.codigo
WHERE p.estado='HAB'
  AND p.ind_permite_comandar=70
  AND c.estado='HAB';
```

---

## 7. Conclusiones

- Ahora tanto **productos simples** como **combos** se reflejan correctamente en `productos_siat`.
- No existen códigos duplicados, lo cual permite utilizar `codigo` como clave única global.
- La sincronización automática a futuro queda garantizada gracias a los triggers.
- La unidad de medida se extrae temporalmente de la descripción mediante la primera palabra.
- Más adelante podemos corregir descripciones inconsistentes y aplicar un catálogo SIAT real.

---

**Backstage Bar — Sistema de Facturación y Comandas**  
Documentación generada automáticamente.
