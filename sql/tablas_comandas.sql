--
-- Set default database
--
USE adminerp_copy;

--
-- Create table `bar_combo_coctel`
--
CREATE TABLE bar_combo_coctel
  (
    id           INT(11)      NOT NULL AUTO_INCREMENT,
    nombre       VARCHAR(255) NOT NULL,
    codigo       VARCHAR(255) NOT NULL,
    descripcion  VARCHAR(255) DEFAULT NULL,
    id_categoria INT(11)      DEFAULT NULL,
    id_barra     INT(11)      DEFAULT NULL,
    usuario_reg  VARCHAR(255) NOT NULL,
    fecha_reg    DATE         DEFAULT NULL,
    fecha_mod    DATE         DEFAULT NULL,
    estado       VARCHAR(3)   NOT NULL,
    PRIMARY KEY (id)
  )
ENGINE = INNODB,
AUTO_INCREMENT = 381,
AVG_ROW_LENGTH = 172,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci,
COMMENT = 'Almacena información sobre los combos o cócteles disponibles en el bar.',
ROW_FORMAT = COMPACT;

--
-- Create foreign key
--
ALTER TABLE bar_combo_coctel
ADD CONSTRAINT fk_bar_combo_coctel_alm_categoria FOREIGN KEY (id_categoria)
REFERENCES alm_categoria (id);

--
-- Create foreign key
--
ALTER TABLE bar_combo_coctel
ADD CONSTRAINT fk_bar_combo_coctel_bar_barra FOREIGN KEY (id_barra)
REFERENCES bar_barra (id);

DELIMITER $$

--
-- Create trigger `trg_update_combo_to_siat`
--
CREATE
DEFINER = 'root'@'localhost'
TRIGGER trg_update_combo_to_siat
AFTER UPDATE
ON bar_combo_coctel
FOR EACH ROW
BEGIN
IF NEW.estado = 'HAB'
THEN
  INSERT INTO adminerp_copy.productos_siat
        (
          codigo,
          nombre,
          unidad_medida,
          tipo_origen,
          id_origen
        )
  VALUES
      (
        NEW.codigo, NEW.nombre, SUBSTRING_INDEX (NEW.descripcion, ' ', 1), 'combo', NEW.id
      )
  ON DUPLICATE KEY UPDATE
  nombre = VALUES(
    nombre),
  unidad_medida = VALUES(
    unidad_medida),
  tipo_origen = 'combo',
  id_origen = NEW.id,
  fecha_actualizacion = CURRENT_TIMESTAMP;
ELSE
  DELETE
  FROM
          adminerp_copy.productos_siat
  WHERE
          tipo_origen = 'combo'
          AND id_origen = OLD.id;
END IF;
END
$$

--
-- Create trigger `trg_insert_combo_to_siat`
--
CREATE
DEFINER = 'root'@'localhost'
TRIGGER trg_insert_combo_to_siat
AFTER INSERT
ON bar_combo_coctel
FOR EACH ROW
BEGIN
IF NEW.estado = 'HAB'
THEN
  INSERT INTO adminerp_copy.productos_siat
        (
          codigo,
          nombre,
          unidad_medida,
          tipo_origen,
          id_origen
        )
  VALUES
      (
        NEW.codigo, NEW.nombre, SUBSTRING_INDEX (NEW.descripcion, ' ', 1), 'combo', NEW.id
      )
  ON DUPLICATE KEY UPDATE
  nombre = VALUES(
    nombre),
  unidad_medida = VALUES(
    unidad_medida),
  tipo_origen = 'combo',
  id_origen = NEW.id,
  fecha_actualizacion = CURRENT_TIMESTAMP;
END IF;
END
$$

DELIMITER ;

--
-- Create table `bar_comanda`
--
CREATE TABLE bar_comanda
  (
    id                 INT(11)      NOT NULL AUTO_INCREMENT,
    fecha              DATETIME     DEFAULT NULL,
    id_barra           INT(11)      DEFAULT NULL,
    id_mesa            INT(11)      DEFAULT NULL,
    id_operacion       INT(11)      NOT NULL,
    id_usuario         INT(11)      NOT NULL,
    estado_comanda     INT(11)      NOT NULL,
    estado_impresion   INT(11)      DEFAULT NULL,
    tipo_salida        INT(11)      DEFAULT NULL,
    cor_motivo         VARCHAR(255) DEFAULT NULL,
    cor_registrado_por VARCHAR(255) DEFAULT NULL,
    razon_social       VARCHAR(255) DEFAULT NULL,
    nit                VARCHAR(255) DEFAULT NULL,
    id_factura         INT(11)      DEFAULT NULL,
    nro_factura        INT(11)      DEFAULT NULL,
    usuario_reg        VARCHAR(255) NOT NULL,
    fecha_reg          DATE         DEFAULT NULL,
    fecha_mod          DATE         DEFAULT NULL,
    estado             VARCHAR(3)   NOT NULL,
    PRIMARY KEY (id)
  )
ENGINE = INNODB,
AUTO_INCREMENT = 53696,
AVG_ROW_LENGTH = 88,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci,
ROW_FORMAT = COMPACT;

--
-- Create index `fk_bar_comanda_bar_mesa1_idx` on table `bar_comanda`
--
ALTER TABLE bar_comanda
ADD INDEX fk_bar_comanda_bar_mesa1_idx (id_mesa);

--
-- Create index `fk_bar_comanda_ope_operacion1_idx` on table `bar_comanda`
--
ALTER TABLE bar_comanda
ADD INDEX fk_bar_comanda_ope_operacion1_idx (id_operacion);

--
-- Create index `fk_bar_comanda_seg_usuario1_idx` on table `bar_comanda`
--
ALTER TABLE bar_comanda
ADD INDEX fk_bar_comanda_seg_usuario1_idx (id_usuario);

--
-- Create foreign key
--
ALTER TABLE bar_comanda
ADD CONSTRAINT fk_bar_comanda_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id);

--
-- Create foreign key
--
ALTER TABLE bar_comanda
ADD CONSTRAINT fk_bar_comanda_bar_mesa1 FOREIGN KEY (id_mesa)
REFERENCES bar_mesa (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_comanda
ADD CONSTRAINT fk_bar_comanda_ope_operacion1 FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_comanda
ADD CONSTRAINT fk_bar_comanda_seg_usuario1 FOREIGN KEY (id_usuario)
REFERENCES seg_usuario (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_producto`
--
CREATE TABLE alm_producto
  (
    id                      INT(11)        NOT NULL AUTO_INCREMENT,
    nombre                  VARCHAR(255)   NOT NULL,
    descripcion             VARCHAR(255)   DEFAULT NULL,
    correlativo             INT(11)        NOT NULL,
    id_categoria            INT(11)        NOT NULL,
    id_proveedor            INT(11)        DEFAULT NULL,
    codigo                  VARCHAR(255)   DEFAULT NULL,
    medida                  DECIMAL(10, 2) NOT NULL,
    p_unidad_medida         INT(11)        NOT NULL,
    cantidad_detalle        DECIMAL(10, 2) DEFAULT NULL,
    p_unidad_medida_detalle INT(11)        DEFAULT NULL,
    minimo_stock            DECIMAL(10, 2) DEFAULT NULL,
    maximo_stock            DECIMAL(10, 2) DEFAULT NULL,
    minimo_stock_barra      DECIMAL(10, 2) DEFAULT NULL,
    maximo_stock_barra      DECIMAL(10, 2) DEFAULT NULL,
    file                    MEDIUMBLOB     DEFAULT NULL,
    filename                VARCHAR(255)   DEFAULT NULL,
    ind_permite_comandar    INT(11)        DEFAULT NULL,
    id_barra                INT(11)        DEFAULT NULL,
    usuario_reg             VARCHAR(255)   NOT NULL,
    fecha_reg               DATE           DEFAULT NULL,
    fecha_mod               DATE           DEFAULT NULL,
    estado                  VARCHAR(3)     NOT NULL,
    PRIMARY KEY (id)
  )
ENGINE = INNODB,
AUTO_INCREMENT = 476,
AVG_ROW_LENGTH = 207,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci,
ROW_FORMAT = COMPACT;

--
-- Create index `fk_alm_producto_alm_proveedor1_idx` on table `alm_producto`
--
ALTER TABLE alm_producto
ADD INDEX fk_alm_producto_alm_proveedor1_idx (id_proveedor);

--
-- Create index `fk_producto_categoria_idx` on table `alm_producto`
--
ALTER TABLE alm_producto
ADD INDEX fk_producto_categoria_idx (id_categoria);

--
-- Create foreign key
--
ALTER TABLE alm_producto
ADD CONSTRAINT fk_alm_producto_alm_proveedor1 FOREIGN KEY (id_proveedor)
REFERENCES alm_proveedor (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_producto
ADD CONSTRAINT fk_alm_producto_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id);

--
-- Create foreign key
--
ALTER TABLE alm_producto
ADD CONSTRAINT fk_producto_categoria FOREIGN KEY (id_categoria)
REFERENCES alm_categoria (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

DELIMITER $$

--
-- Create trigger `trg_update_producto_to_siat`
--
CREATE
DEFINER = 'root'@'localhost'
TRIGGER trg_update_producto_to_siat
AFTER UPDATE
ON alm_producto
FOR EACH ROW
BEGIN
IF NEW.estado = 'HAB'
  AND
  NEW.ind_permite_comandar = 70
THEN
  INSERT INTO adminerp_copy.productos_siat
        (
          codigo,
          nombre,
          unidad_medida,
          tipo_origen,
          id_origen
        )
  VALUES
      (
        NEW.codigo, NEW.nombre, SUBSTRING_INDEX (NEW.descripcion, ' ', 1), 'producto', NEW.id
      )
  ON DUPLICATE KEY UPDATE
  nombre = VALUES(
    nombre),
  unidad_medida = VALUES(
    unidad_medida),
  tipo_origen = 'producto',
  id_origen = NEW.id,
  fecha_actualizacion = CURRENT_TIMESTAMP;
ELSE
  DELETE
  FROM
          adminerp_copy.productos_siat
  WHERE
          tipo_origen = 'producto'
          AND id_origen = OLD.id;
END IF;
END
$$

--
-- Create trigger `trg_insert_producto_to_siat`
--
CREATE
DEFINER = 'root'@'localhost'
TRIGGER trg_insert_producto_to_siat
AFTER INSERT
ON alm_producto
FOR EACH ROW
BEGIN
IF NEW.estado = 'HAB'
  AND
  NEW.ind_permite_comandar = 70
THEN
  INSERT INTO adminerp_copy.productos_siat
        (
          codigo,
          nombre,
          unidad_medida,
          tipo_origen,
          id_origen
        )
  VALUES
      (
        NEW.codigo, NEW.nombre, SUBSTRING_INDEX (NEW.descripcion, ' ', 1), 'producto', NEW.id
      )
  ON DUPLICATE KEY UPDATE
  nombre = VALUES(
    nombre),
  unidad_medida = VALUES(
    unidad_medida),
  tipo_origen = 'producto',
  id_origen = NEW.id,
  fecha_actualizacion = CURRENT_TIMESTAMP;
END IF;
END
$$

DELIMITER ;

--
-- Create table `bar_detalle_comanda_salida`
--
CREATE TABLE bar_detalle_comanda_salida
  (
    id                     INT(11)        NOT NULL AUTO_INCREMENT,
    cantidad               DECIMAL(10, 2) NOT NULL,
    id_comanda             INT(11)        NOT NULL,
    id_producto            INT(11)        DEFAULT NULL,
    id_salida_combo_coctel INT(11)        DEFAULT NULL,
    id_bar_combo_coctel    INT(11)        DEFAULT NULL,
    precio_venta           DECIMAL(10, 2) NOT NULL,
    sub_total              DECIMAL(10, 2) NOT NULL,
    producto_coctel        VARCHAR(255)   DEFAULT NULL,
    cor_subtotal_anterior  DECIMAL(10, 2) DEFAULT NULL,
    id_barra               INT(11)        DEFAULT NULL,
    comision               DECIMAL(10, 2) DEFAULT NULL,
    usuario_reg            VARCHAR(255)   NOT NULL,
    fecha_reg              DATE           DEFAULT NULL,
    fecha_mod              DATE           DEFAULT NULL,
    estado                 VARCHAR(3)     NOT NULL,
    PRIMARY KEY (id)
  )
ENGINE = INNODB,
AUTO_INCREMENT = 70586,
AVG_ROW_LENGTH = 86,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci,
ROW_FORMAT = COMPACT;

--
-- Create index `fk_bar_detalle_comanda_salida_bar_salida_combo_coctel1_idx` on table `bar_detalle_comanda_salida`
--
ALTER TABLE bar_detalle_comanda_salida
ADD INDEX fk_bar_detalle_comanda_salida_bar_salida_combo_coctel1_idx (id_salida_combo_coctel);

--
-- Create index `fk_bar_salida_barra_alm_producto1_idx` on table `bar_detalle_comanda_salida`
--
ALTER TABLE bar_detalle_comanda_salida
ADD INDEX fk_bar_salida_barra_alm_producto1_idx (id_producto);

--
-- Create index `fk_bar_salida_barra_bar_comanda1_idx` on table `bar_detalle_comanda_salida`
--
ALTER TABLE bar_detalle_comanda_salida
ADD INDEX fk_bar_salida_barra_bar_comanda1_idx (id_comanda);

--
-- Create foreign key
--
ALTER TABLE bar_detalle_comanda_salida
ADD CONSTRAINT bar_detalle_comanda_salida_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id);

--
-- Create foreign key
--
ALTER TABLE bar_detalle_comanda_salida
ADD CONSTRAINT bar_detalle_comanda_salida_ibfk_1 FOREIGN KEY (id_bar_combo_coctel)
REFERENCES bar_combo_coctel (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_comanda_salida
ADD CONSTRAINT fk_bar_detalle_comanda_salida_bar_salida_combo_coctel1 FOREIGN KEY (id_salida_combo_coctel)
REFERENCES bar_salida_combo_coctel (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_comanda_salida
ADD CONSTRAINT fk_bar_salida_barra_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_comanda_salida
ADD CONSTRAINT fk_bar_salida_barra_bar_comanda1 FOREIGN KEY (id_comanda)
REFERENCES bar_comanda (id) ON DELETE NO ACTION ON UPDATE NO ACTION;