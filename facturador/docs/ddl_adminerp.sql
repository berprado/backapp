-- 
-- Set character set the client will use to send SQL statements to the server
--
SET NAMES 'utf8';

--
-- Set default database
--
USE adminerp;

--
-- Create table `seg_usuario`
--
CREATE TABLE seg_usuario (
  id int(11) NOT NULL AUTO_INCREMENT,
  paterno varchar(255) NOT NULL,
  materno varchar(255) NOT NULL,
  nombres varchar(255) NOT NULL,
  nro_documento varchar(255) NOT NULL,
  email varchar(255) NOT NULL,
  sigla varchar(255) DEFAULT NULL,
  p_cargo int(11) NOT NULL,
  usuario varchar(255) NOT NULL,
  contrasena varchar(255) NOT NULL,
  observaciones varchar(255) DEFAULT NULL,
  fechacreacion date NOT NULL,
  tipousuario varchar(1) NOT NULL,
  fechainiciovigencia date NOT NULL,
  fechafinvigencia date NOT NULL,
  pantallaprincipal varchar(255) DEFAULT NULL,
  conformidad varchar(1) DEFAULT NULL,
  habilitado varchar(1) NOT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 24,
AVG_ROW_LENGTH = 712,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `bar_barra`
--
CREATE TABLE bar_barra (
  id int(11) NOT NULL AUTO_INCREMENT,
  nombre varchar(255) DEFAULT NULL,
  descripcion varchar(255) DEFAULT NULL,
  denominativo varchar(255) DEFAULT NULL,
  id_usuario int(11) NOT NULL,
  impresora varchar(255) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 4,
AVG_ROW_LENGTH = 5461,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_barra_seg_usuario1_idx` on table `bar_barra`
--
ALTER TABLE bar_barra
ADD INDEX fk_bar_barra_seg_usuario1_idx (id_usuario);

--
-- Create foreign key
--
ALTER TABLE bar_barra
ADD CONSTRAINT fk_bar_barra_seg_usuario1 FOREIGN KEY (id_usuario)
REFERENCES seg_usuario (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_solicitud_producto`
--
CREATE TABLE bar_solicitud_producto (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha_solicitud date DEFAULT NULL,
  ind_estado_solicitud int(11) NOT NULL COMMENT 'parameter table',
  descripcion_solicitud varchar(255) DEFAULT NULL COMMENT 'solo comentarios de alamacenes',
  id_barra int(11) NOT NULL,
  fecha_atencion date DEFAULT NULL,
  descripcion_atencion varchar(255) DEFAULT NULL,
  responsable_solicitud varchar(255) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 15,
AVG_ROW_LENGTH = 1170,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_solicitud_producto_bar_barra1_idx` on table `bar_solicitud_producto`
--
ALTER TABLE bar_solicitud_producto
ADD INDEX fk_bar_solicitud_producto_bar_barra1_idx (id_barra);

--
-- Create foreign key
--
ALTER TABLE bar_solicitud_producto
ADD CONSTRAINT fk_bar_solicitud_producto_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_ingreso_producto`
--
CREATE TABLE bar_ingreso_producto (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha date DEFAULT NULL,
  correlativo int(11) DEFAULT NULL,
  id_barra int(11) NOT NULL,
  id_solicitud_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_ingreso_producto_bar_barra1_idx` on table `bar_ingreso_producto`
--
ALTER TABLE bar_ingreso_producto
ADD INDEX fk_bar_ingreso_producto_bar_barra1_idx (id_barra);

--
-- Create index `fk_bar_ingreso_producto_bar_solicitud_producto1_idx` on table `bar_ingreso_producto`
--
ALTER TABLE bar_ingreso_producto
ADD INDEX fk_bar_ingreso_producto_bar_solicitud_producto1_idx (id_solicitud_producto);

--
-- Create foreign key
--
ALTER TABLE bar_ingreso_producto
ADD CONSTRAINT fk_bar_ingreso_producto_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_ingreso_producto
ADD CONSTRAINT fk_bar_ingreso_producto_bar_solicitud_producto1 FOREIGN KEY (id_solicitud_producto)
REFERENCES bar_solicitud_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_orden_pedido`
--
CREATE TABLE bar_orden_pedido (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha_solicitud date NOT NULL,
  responsable varchar(255) DEFAULT NULL,
  lugar_entrega varchar(255) DEFAULT NULL,
  fecha_entrega date DEFAULT NULL,
  ind_estado_orden int(11) NOT NULL,
  observaciones varchar(255) DEFAULT NULL,
  id_barra int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 7,
AVG_ROW_LENGTH = 2730,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_orden_pedido
ADD CONSTRAINT bar_orden_pedido_bar_barra FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_mesa`
--
CREATE TABLE bar_mesa (
  id int(11) NOT NULL AUTO_INCREMENT,
  numero int(11) DEFAULT NULL,
  descripcion varchar(255) DEFAULT NULL,
  ubicacion varchar(255) DEFAULT NULL,
  id_barra int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 4,
AVG_ROW_LENGTH = 5461,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_mesa_bar_barra1_idx` on table `bar_mesa`
--
ALTER TABLE bar_mesa
ADD INDEX fk_bar_mesa_bar_barra1_idx (id_barra);

--
-- Create foreign key
--
ALTER TABLE bar_mesa
ADD CONSTRAINT fk_bar_mesa_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_barra_mesera`
--
CREATE TABLE bar_barra_mesera (
  id int(11) NOT NULL AUTO_INCREMENT,
  descripcion_asignacion varchar(255) DEFAULT NULL,
  fecha_asignacion date NOT NULL,
  descripcion_desasignacion varchar(255) DEFAULT NULL,
  fecha_desasignacion date DEFAULT NULL,
  id_barra int(11) NOT NULL,
  id_usuario int(11) NOT NULL,
  impresora varchar(255) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 23,
AVG_ROW_LENGTH = 744,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_barra_mesera_bar_barra1_idx` on table `bar_barra_mesera`
--
ALTER TABLE bar_barra_mesera
ADD INDEX fk_bar_barra_mesera_bar_barra1_idx (id_barra);

--
-- Create index `fk_bar_barra_mesera_seg_usuario1_idx` on table `bar_barra_mesera`
--
ALTER TABLE bar_barra_mesera
ADD INDEX fk_bar_barra_mesera_seg_usuario1_idx (id_usuario);

--
-- Create foreign key
--
ALTER TABLE bar_barra_mesera
ADD CONSTRAINT fk_bar_barra_mesera_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_barra_mesera
ADD CONSTRAINT fk_bar_barra_mesera_seg_usuario1 FOREIGN KEY (id_usuario)
REFERENCES seg_usuario (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `ope_dia`
--
CREATE TABLE ope_dia (
  id int(11) NOT NULL AUTO_INCREMENT,
  dia varchar(255) NOT NULL,
  descripcion varchar(255) DEFAULT NULL,
  indEsPrincipal int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 3,
AVG_ROW_LENGTH = 8192,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `ope_operacion`
--
CREATE TABLE ope_operacion (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha date NOT NULL,
  nombre_operacion varchar(255) NOT NULL,
  estado_operacion int(11) NOT NULL,
  ind_tiene_cover varchar(1) DEFAULT NULL,
  monto_cover decimal(10, 2) DEFAULT NULL,
  comision decimal(10, 2) NOT NULL,
  id_dia int(11) NOT NULL,
  observaciones varchar(255) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 455,
AVG_ROW_LENGTH = 144,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_ope_operacion_ope_dia1_idx` on table `ope_operacion`
--
ALTER TABLE ope_operacion
ADD INDEX fk_ope_operacion_ope_dia1_idx (id_dia);

--
-- Create foreign key
--
ALTER TABLE ope_operacion
ADD CONSTRAINT fk_ope_operacion_ope_dia1 FOREIGN KEY (id_dia)
REFERENCES ope_dia (id);

--
-- Create table `ope_novedades`
--
CREATE TABLE ope_novedades (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha datetime DEFAULT NULL,
  usuario varchar(255) NOT NULL,
  evento varchar(255) NOT NULL,
  id_operacion int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg datetime DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 11369,
AVG_ROW_LENGTH = 139,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_inventario_cierre_ope_operacion1` on table `ope_novedades`
--
ALTER TABLE ope_novedades
ADD INDEX fk_bar_inventario_cierre_ope_operacion1 (id_operacion);

--
-- Create foreign key
--
ALTER TABLE ope_novedades
ADD CONSTRAINT fk_ope_novedades_ope_operacion FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `ope_movimiento`
--
CREATE TABLE ope_movimiento (
  id int(11) NOT NULL AUTO_INCREMENT,
  monto decimal(10, 2) NOT NULL,
  efectivo decimal(10, 2) DEFAULT NULL,
  diferencia decimal(10, 2) DEFAULT NULL,
  motivo varchar(255) DEFAULT NULL COMMENT 'Cual es el motivo del movimiento de dinero',
  ind_tipo_movimiento int(11) NOT NULL,
  id_operacion int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 2,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE ope_movimiento
ADD CONSTRAINT fk_ope_movimiento_ope_operacion FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `ope_cover`
--
CREATE TABLE ope_cover (
  id int(11) NOT NULL AUTO_INCREMENT,
  monto decimal(10, 2) NOT NULL,
  fecha datetime NOT NULL,
  cantidad int(11) NOT NULL,
  id_operacion int(11) NOT NULL,
  id_usuario int(11) NOT NULL,
  estado_impresion int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_ope_cover_ope_operacion1_idx` on table `ope_cover`
--
ALTER TABLE ope_cover
ADD INDEX fk_ope_cover_ope_operacion1_idx (id_operacion);

--
-- Create index `fk_ope_cover_seg_usuario1_idx` on table `ope_cover`
--
ALTER TABLE ope_cover
ADD INDEX fk_ope_cover_seg_usuario1_idx (id_usuario);

--
-- Create foreign key
--
ALTER TABLE ope_cover
ADD CONSTRAINT fk_ope_cover_ope_operacion1 FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE ope_cover
ADD CONSTRAINT fk_ope_cover_seg_usuario1 FOREIGN KEY (id_usuario)
REFERENCES seg_usuario (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `ope_conciliacion`
--
CREATE TABLE ope_conciliacion (
  id int(11) NOT NULL AUTO_INCREMENT,
  total_comandas int(11) NOT NULL,
  ventas decimal(10, 2) NOT NULL,
  efectivo decimal(10, 2) NOT NULL,
  con_tarjeta decimal(10, 2) DEFAULT NULL,
  diferencia decimal(10, 2) NOT NULL,
  observaciones varchar(255) DEFAULT NULL COMMENT '0: conciliacion exitosa 1: hubo problemas de conciliacion',
  id_operacion int(11) NOT NULL,
  id_usuario int(11) DEFAULT NULL,
  id_barra int(11) DEFAULT NULL,
  ind_estado_conciliacion int(11) NOT NULL COMMENT '0: conciliacion con novedades 1: conciliacion correcta',
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 1090,
AVG_ROW_LENGTH = 120,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_ope_conciliacion_ope_operacion1_idx` on table `ope_conciliacion`
--
ALTER TABLE ope_conciliacion
ADD INDEX fk_ope_conciliacion_ope_operacion1_idx (id_operacion);

--
-- Create index `fk_ope_conciliacion_seg_usuario1_idx` on table `ope_conciliacion`
--
ALTER TABLE ope_conciliacion
ADD INDEX fk_ope_conciliacion_seg_usuario1_idx (id_usuario);

--
-- Create index `ib_barra` on table `ope_conciliacion`
--
ALTER TABLE ope_conciliacion
ADD INDEX ib_barra (id_barra);

--
-- Create foreign key
--
ALTER TABLE ope_conciliacion
ADD CONSTRAINT fk_ope_conciliacion_ope_operacion1 FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE ope_conciliacion
ADD CONSTRAINT fk_ope_conciliacion_seg_usuario1 FOREIGN KEY (id_usuario)
REFERENCES seg_usuario (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE ope_conciliacion
ADD CONSTRAINT ope_conciliacion_ibfk_1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id);

--
-- Create table `bar_inventario_fisico`
--
CREATE TABLE bar_inventario_fisico (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha date DEFAULT NULL,
  observaciones varchar(255) DEFAULT NULL,
  procesado_por varchar(255) DEFAULT NULL,
  estado_registro int(11) NOT NULL,
  id_barra int(11) NOT NULL,
  id_operacion int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 119,
AVG_ROW_LENGTH = 140,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_inventario_fisico
ADD CONSTRAINT bar_inventario_fisico_bar_barra FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_inventario_fisico
ADD CONSTRAINT bar_inventario_fisico_ope_operacion FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_comanda`
--
CREATE TABLE bar_comanda (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha datetime DEFAULT NULL,
  id_barra int(11) DEFAULT NULL,
  id_mesa int(11) DEFAULT NULL,
  id_operacion int(11) NOT NULL,
  id_usuario int(11) NOT NULL,
  estado_comanda int(11) NOT NULL,
  estado_impresion int(11) DEFAULT NULL,
  tipo_salida int(11) DEFAULT NULL,
  cor_motivo varchar(255) DEFAULT NULL,
  cor_registrado_por varchar(255) DEFAULT NULL,
  razon_social varchar(255) DEFAULT NULL,
  nit varchar(255) DEFAULT NULL,
  id_factura int(11) DEFAULT NULL,
  nro_factura int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 31483,
AVG_ROW_LENGTH = 83,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

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
-- Create table `bar_comanda_impresion`
--
CREATE TABLE bar_comanda_impresion (
  id int(11) NOT NULL AUTO_INCREMENT,
  id_comanda int(11) NOT NULL,
  nombre_barra varchar(255) DEFAULT NULL,
  impresora varchar(255) DEFAULT NULL,
  texto text DEFAULT NULL,
  ind_estado_impresion int(11) NOT NULL COMMENT 'si fue impreso o no',
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 30386,
AVG_ROW_LENGTH = 516,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_comanda_impresion
ADD CONSTRAINT fk_bar_comanda_impresion_bar_comanda1 FOREIGN KEY (id_comanda)
REFERENCES bar_comanda (id);

--
-- Create table `bar_ajuste`
--
CREATE TABLE bar_ajuste (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha date DEFAULT NULL,
  numero_documento varchar(255) DEFAULT NULL,
  observaciones varchar(255) DEFAULT NULL,
  recepcionado_por varchar(255) DEFAULT NULL,
  ind_estado_ingreso int(11) NOT NULL COMMENT '0: pendiente, 1: procesaro, 3: cancelado',
  ind_tipo_movimiento int(11) DEFAULT NULL,
  id_operacion int(11) DEFAULT NULL,
  id_barra int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 72,
AVG_ROW_LENGTH = 230,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_ajuste
ADD CONSTRAINT bar_ajuste_ibfk_1 FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_ajuste
ADD CONSTRAINT bar_ajuste_ibfk_2 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_almacen`
--
CREATE TABLE alm_almacen (
  id int(11) NOT NULL AUTO_INCREMENT,
  nombre varchar(255) DEFAULT NULL,
  direccion varchar(255) DEFAULT NULL,
  sigla varchar(255) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 4,
AVG_ROW_LENGTH = 5461,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `bar_salida_inventario`
--
CREATE TABLE bar_salida_inventario (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha_salida date NOT NULL,
  correlativo int(11) DEFAULT NULL,
  responsable varchar(255) NOT NULL,
  ind_estado_salida int(11) NOT NULL,
  observaciones_salida varchar(255) DEFAULT NULL,
  fecha_recepcion date DEFAULT NULL,
  observaciones_recepcion varchar(255) DEFAULT NULL,
  responsable_recepcion varchar(255) DEFAULT NULL,
  id_almacen int(11) DEFAULT NULL,
  id_barra int(11) DEFAULT NULL,
  id_operacion int(11) DEFAULT NULL,
  ind_tipo_salida int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 68,
AVG_ROW_LENGTH = 244,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_salida_inventario
ADD CONSTRAINT bar_salida_inventario_ibfk_1 FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id);

--
-- Create foreign key
--
ALTER TABLE bar_salida_inventario
ADD CONSTRAINT fk_bar_salida_inventario_alm_almacen1 FOREIGN KEY (id_almacen)
REFERENCES alm_almacen (id);

--
-- Create foreign key
--
ALTER TABLE bar_salida_inventario
ADD CONSTRAINT fk_bar_salida_inventario_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id);

--
-- Create table `alm_devolucion`
--
CREATE TABLE alm_devolucion (
  id int(11) NOT NULL AUTO_INCREMENT,
  cliente varchar(255) DEFAULT NULL,
  motivo varchar(255) DEFAULT NULL,
  id_operacion int(11) NOT NULL,
  id_almacen int(11) NOT NULL,
  id_usuario int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_alm_devolucion_ope_operacion1_idx` on table `alm_devolucion`
--
ALTER TABLE alm_devolucion
ADD INDEX fk_alm_devolucion_ope_operacion1_idx (id_operacion);

--
-- Create index `fk_alm_devolucion_alm_almacen1_idx` on table `alm_devolucion`
--
ALTER TABLE alm_devolucion
ADD INDEX fk_alm_devolucion_alm_almacen1_idx (id_almacen);

--
-- Create index `fk_alm_devolucion_seg_usuario1_idx` on table `alm_devolucion`
--
ALTER TABLE alm_devolucion
ADD INDEX fk_alm_devolucion_seg_usuario1_idx (id_usuario);

--
-- Create foreign key
--
ALTER TABLE alm_devolucion
ADD CONSTRAINT fk_alm_devolucion_alm_almacen1 FOREIGN KEY (id_almacen)
REFERENCES alm_almacen (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_devolucion
ADD CONSTRAINT fk_alm_devolucion_ope_operacion1 FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_devolucion
ADD CONSTRAINT fk_alm_devolucion_seg_usuario1 FOREIGN KEY (id_usuario)
REFERENCES seg_usuario (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `gen_area`
--
CREATE TABLE gen_area (
  id int(11) NOT NULL AUTO_INCREMENT,
  nombre varchar(255) DEFAULT NULL,
  descripcion varchar(255) DEFAULT NULL,
  sigla varchar(255) DEFAULT NULL,
  responsable varchar(255) DEFAULT NULL,
  cargo varchar(255) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `alm_proveedor`
--
CREATE TABLE alm_proveedor (
  id int(11) NOT NULL AUTO_INCREMENT,
  nombre varchar(255) NOT NULL,
  nombre_contacto varchar(255) DEFAULT NULL,
  telefonos varchar(255) DEFAULT NULL,
  email varchar(255) DEFAULT NULL,
  direccion varchar(255) DEFAULT NULL,
  ciudad varchar(255) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 15,
AVG_ROW_LENGTH = 1170,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `alm_salida_inventario`
--
CREATE TABLE alm_salida_inventario (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha_salida date NOT NULL,
  correlativo int(11) DEFAULT NULL,
  responsable varchar(255) NOT NULL,
  ind_estado_salida int(11) NOT NULL,
  observaciones_salida varchar(255) DEFAULT NULL,
  fecha_recepcion date DEFAULT NULL,
  observaciones_recepcion varchar(255) DEFAULT NULL,
  responsable_recepcion varchar(255) DEFAULT NULL,
  ind_tipo_salida int(11) DEFAULT NULL,
  id_almacen int(11) NOT NULL,
  id_barra int(11) DEFAULT NULL,
  id_proveedor int(11) DEFAULT NULL,
  id_area int(11) DEFAULT NULL,
  id_operacion int(11) DEFAULT NULL,
  ind_tipo_movimiento int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 917,
AVG_ROW_LENGTH = 178,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_alm_salida_inventario_alm_almacen1_idx` on table `alm_salida_inventario`
--
ALTER TABLE alm_salida_inventario
ADD INDEX fk_alm_salida_inventario_alm_almacen1_idx (id_almacen);

--
-- Create index `fk_alm_salida_inventario_bar_barra1_idx` on table `alm_salida_inventario`
--
ALTER TABLE alm_salida_inventario
ADD INDEX fk_alm_salida_inventario_bar_barra1_idx (id_barra);

--
-- Create foreign key
--
ALTER TABLE alm_salida_inventario
ADD CONSTRAINT alm_salida_inventario_ibfk_1 FOREIGN KEY (id_proveedor)
REFERENCES alm_proveedor (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_salida_inventario
ADD CONSTRAINT alm_salida_inventario_ibfk_2 FOREIGN KEY (id_area)
REFERENCES gen_area (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_salida_inventario
ADD CONSTRAINT alm_salida_inventario_ibfk_3 FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_salida_inventario
ADD CONSTRAINT fk_alm_salida_inventario_alm_almacen1 FOREIGN KEY (id_almacen)
REFERENCES alm_almacen (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_salida_inventario
ADD CONSTRAINT fk_alm_salida_inventario_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_ingreso`
--
CREATE TABLE alm_ingreso (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha date DEFAULT NULL,
  numero_documento varchar(255) DEFAULT NULL,
  observaciones varchar(255) DEFAULT NULL,
  recepcionado_por varchar(255) DEFAULT NULL,
  ind_estado_ingreso varchar(1) NOT NULL COMMENT '0: pendiente, 1: procesaro, 3: cancelado',
  ind_tipo_documento int(11) DEFAULT NULL,
  ind_tipo_pago int(11) DEFAULT NULL,
  ind_tipo_ingreso int(11) DEFAULT NULL,
  id_proveedor int(11) DEFAULT NULL,
  id_almacen int(11) NOT NULL,
  id_operacion int(11) DEFAULT NULL,
  id_barra int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 661,
AVG_ROW_LENGTH = 148,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_alm_ingreso_alm_proveedor1_idx` on table `alm_ingreso`
--
ALTER TABLE alm_ingreso
ADD INDEX fk_alm_ingreso_alm_proveedor1_idx (id_proveedor);

--
-- Create index `fk_alm_ingreso_alm_almacen1_idx` on table `alm_ingreso`
--
ALTER TABLE alm_ingreso
ADD INDEX fk_alm_ingreso_alm_almacen1_idx (id_almacen);

--
-- Create foreign key
--
ALTER TABLE alm_ingreso
ADD CONSTRAINT alm_ingreso_ibfk_1 FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_ingreso
ADD CONSTRAINT alm_ingreso_ibfk_2 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_ingreso
ADD CONSTRAINT fk_alm_ingreso_alm_almacen1 FOREIGN KEY (id_almacen)
REFERENCES alm_almacen (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_ingreso
ADD CONSTRAINT fk_alm_ingreso_alm_proveedor1 FOREIGN KEY (id_proveedor)
REFERENCES alm_proveedor (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_categoria`
--
CREATE TABLE alm_categoria (
  id int(11) NOT NULL AUTO_INCREMENT,
  nombre varchar(255) NOT NULL,
  descripcion varchar(255) DEFAULT NULL,
  p_grupo_categoria int(11) NOT NULL COMMENT 'se define datos como: bebidas, bocaditos, prendas, souvenirs',
  desde int(11) DEFAULT NULL,
  hasta int(11) DEFAULT NULL,
  correlativo int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 21,
AVG_ROW_LENGTH = 819,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `bar_salida_combo_coctel`
--
CREATE TABLE bar_salida_combo_coctel (
  id int(11) NOT NULL AUTO_INCREMENT,
  nombre varchar(255) NOT NULL,
  codigo varchar(255) NOT NULL,
  descripcion varchar(255) DEFAULT NULL,
  id_barra int(11) DEFAULT NULL,
  id_categoria int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 29148,
AVG_ROW_LENGTH = 90,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_salida_combo_coctel
ADD CONSTRAINT fk_bar_salida_coctel_alm_categoria11 FOREIGN KEY (id_categoria)
REFERENCES alm_categoria (id);

--
-- Create foreign key
--
ALTER TABLE bar_salida_combo_coctel
ADD CONSTRAINT fk_bar_salida_coctel_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id);

--
-- Create table `bar_combo_coctel`
--
CREATE TABLE bar_combo_coctel (
  id int(11) NOT NULL AUTO_INCREMENT,
  nombre varchar(255) NOT NULL,
  codigo varchar(255) NOT NULL,
  descripcion varchar(255) DEFAULT NULL,
  id_categoria int(11) DEFAULT NULL,
  id_barra int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 275,
AVG_ROW_LENGTH = 179,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

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

--
-- Create table `alm_producto`
--
CREATE TABLE alm_producto (
  id int(11) NOT NULL AUTO_INCREMENT,
  nombre varchar(255) NOT NULL,
  descripcion varchar(255) DEFAULT NULL,
  correlativo int(11) NOT NULL,
  id_categoria int(11) NOT NULL,
  id_proveedor int(11) DEFAULT NULL,
  codigo varchar(255) DEFAULT NULL,
  medida decimal(10, 2) NOT NULL,
  p_unidad_medida int(11) NOT NULL,
  cantidad_detalle decimal(10, 2) DEFAULT NULL,
  p_unidad_medida_detalle int(11) DEFAULT NULL,
  minimo_stock decimal(10, 2) DEFAULT NULL,
  maximo_stock decimal(10, 2) DEFAULT NULL,
  minimo_stock_barra decimal(10, 2) DEFAULT NULL,
  maximo_stock_barra decimal(10, 2) DEFAULT NULL,
  file mediumblob DEFAULT NULL,
  filename varchar(255) DEFAULT NULL,
  ind_permite_comandar int(11) DEFAULT NULL,
  id_barra int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 405,
AVG_ROW_LENGTH = 203,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_producto_categoria_idx` on table `alm_producto`
--
ALTER TABLE alm_producto
ADD INDEX fk_producto_categoria_idx (id_categoria);

--
-- Create index `fk_alm_producto_alm_proveedor1_idx` on table `alm_producto`
--
ALTER TABLE alm_producto
ADD INDEX fk_alm_producto_alm_proveedor1_idx (id_proveedor);

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

--
-- Create table `ope_precio_venta`
--
CREATE TABLE ope_precio_venta (
  id int(11) NOT NULL AUTO_INCREMENT,
  precio_venta decimal(10, 2) NOT NULL,
  id_dia int(11) NOT NULL,
  id_producto int(11) DEFAULT NULL,
  id_combo_coctel int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 1244,
AVG_ROW_LENGTH = 79,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_ope_precio_venta_ope_dia1_idx` on table `ope_precio_venta`
--
ALTER TABLE ope_precio_venta
ADD INDEX fk_ope_precio_venta_ope_dia1_idx (id_dia);

--
-- Create index `fk_ope_precio_venta_alm_producto1_idx` on table `ope_precio_venta`
--
ALTER TABLE ope_precio_venta
ADD INDEX fk_ope_precio_venta_alm_producto1_idx (id_producto);

--
-- Create index `fk_ope_precio_venta_bar_combo_coctel1_idx` on table `ope_precio_venta`
--
ALTER TABLE ope_precio_venta
ADD INDEX fk_ope_precio_venta_bar_combo_coctel1_idx (id_combo_coctel);

--
-- Create foreign key
--
ALTER TABLE ope_precio_venta
ADD CONSTRAINT fk_ope_precio_venta_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE ope_precio_venta
ADD CONSTRAINT fk_ope_precio_venta_bar_combo_coctel1 FOREIGN KEY (id_combo_coctel)
REFERENCES bar_combo_coctel (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE ope_precio_venta
ADD CONSTRAINT fk_ope_precio_venta_ope_dia1 FOREIGN KEY (id_dia)
REFERENCES ope_dia (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_valoracion`
--
CREATE TABLE bar_valoracion (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha date DEFAULT NULL,
  ind_tipo_operacion int(11) DEFAULT NULL,
  correlativo int(11) DEFAULT NULL,
  precio_unitario decimal(10, 5) DEFAULT NULL,
  fisico_ingreso decimal(10, 2) DEFAULT NULL,
  fisico_salida decimal(10, 2) DEFAULT NULL,
  fisico_saldo decimal(20, 2) DEFAULT NULL,
  valor_ingreso decimal(10, 2) DEFAULT NULL,
  valor_salida decimal(10, 2) DEFAULT NULL,
  valor_saldo decimal(10, 2) DEFAULT NULL,
  id_producto int(11) NOT NULL,
  id_barra int(11) DEFAULT NULL,
  id_sucursal int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 3368,
AVG_ROW_LENGTH = 138,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_valoracion
ADD CONSTRAINT fk_bar_valoracion_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_valoracion
ADD CONSTRAINT fk_bar_valoracion_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_paloteo_cierre`
--
CREATE TABLE bar_paloteo_cierre (
  id int(11) NOT NULL AUTO_INCREMENT,
  inicial_paq decimal(10, 2) DEFAULT NULL,
  inicial_detalle decimal(10, 2) DEFAULT NULL,
  ingreso_paq decimal(10, 2) DEFAULT NULL,
  ingreso_detalle decimal(10, 2) DEFAULT NULL,
  ventas_paq decimal(10, 2) DEFAULT NULL,
  ventas_detalle decimal(10, 2) DEFAULT NULL,
  actual_paq decimal(10, 2) DEFAULT NULL,
  actual_detalle decimal(10, 2) DEFAULT NULL,
  fisico_paq decimal(10, 2) DEFAULT NULL,
  fisico_detalle decimal(10, 2) DEFAULT NULL,
  diferencia_paq decimal(10, 2) DEFAULT NULL,
  diferencia_detalle decimal(10, 2) DEFAULT NULL,
  id_barra int(11) NOT NULL,
  id_operacion int(11) NOT NULL,
  id_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg datetime DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 122117,
AVG_ROW_LENGTH = 104,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_paloteo_cierre
ADD CONSTRAINT fk_bar_paloteo_cierre_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_paloteo_cierre
ADD CONSTRAINT fk_bar_paloteo_cierre_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_paloteo_cierre
ADD CONSTRAINT fk_bar_paloteo_cierre_ope_operacion1 FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_inventario_operacion`
--
CREATE TABLE bar_inventario_operacion (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad_paq decimal(10, 2) DEFAULT NULL,
  cantidad_detalle decimal(10, 2) DEFAULT NULL,
  inicial_paq decimal(10, 2) DEFAULT NULL,
  inicial_detalle decimal(10, 2) DEFAULT NULL,
  id_barra int(11) NOT NULL,
  id_operacion int(11) NOT NULL,
  id_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 86565,
AVG_ROW_LENGTH = 79,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_inventario_operacion_bar_barra1_idx` on table `bar_inventario_operacion`
--
ALTER TABLE bar_inventario_operacion
ADD INDEX fk_bar_inventario_operacion_bar_barra1_idx (id_barra);

--
-- Create index `fk_bar_inventario_operacion_ope_operacion1_idx` on table `bar_inventario_operacion`
--
ALTER TABLE bar_inventario_operacion
ADD INDEX fk_bar_inventario_operacion_ope_operacion1_idx (id_operacion);

--
-- Create index `fk_bar_inventario_operacion_alm_producto1_idx` on table `bar_inventario_operacion`
--
ALTER TABLE bar_inventario_operacion
ADD INDEX fk_bar_inventario_operacion_alm_producto1_idx (id_producto);

--
-- Create foreign key
--
ALTER TABLE bar_inventario_operacion
ADD CONSTRAINT fk_bar_inventario_operacion_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_inventario_operacion
ADD CONSTRAINT fk_bar_inventario_operacion_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_inventario_operacion
ADD CONSTRAINT fk_bar_inventario_operacion_ope_operacion1 FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_inventario_cierre`
--
CREATE TABLE bar_inventario_cierre (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad_paq decimal(10, 2) DEFAULT NULL,
  cantidad_detalle decimal(10, 2) DEFAULT NULL,
  id_barra int(11) NOT NULL,
  id_operacion int(11) NOT NULL,
  id_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg datetime DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 390566,
AVG_ROW_LENGTH = 81,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_inventario_cierre
ADD CONSTRAINT fk_bar_inventario_cierre_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_inventario_cierre
ADD CONSTRAINT fk_bar_inventario_cierre_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_inventario_cierre
ADD CONSTRAINT fk_bar_inventario_cierre_ope_operacion1 FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_inventario`
--
CREATE TABLE bar_inventario (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad_paq decimal(10, 2) DEFAULT NULL,
  cantidad_detalle decimal(10, 2) DEFAULT NULL,
  id_producto int(11) NOT NULL,
  id_barra int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod datetime DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 226,
AVG_ROW_LENGTH = 72,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_inventario_alm_producto1_idx` on table `bar_inventario`
--
ALTER TABLE bar_inventario
ADD INDEX fk_bar_inventario_alm_producto1_idx (id_producto);

--
-- Create index `fk_bar_inventario_bar_barra1_idx` on table `bar_inventario`
--
ALTER TABLE bar_inventario
ADD INDEX fk_bar_inventario_bar_barra1_idx (id_barra);

--
-- Create foreign key
--
ALTER TABLE bar_inventario
ADD CONSTRAINT fk_bar_inventario_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_inventario
ADD CONSTRAINT fk_bar_inventario_bar_barra1 FOREIGN KEY (id_barra)
REFERENCES bar_barra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_detalle_solicitud`
--
CREATE TABLE bar_detalle_solicitud (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad decimal(10, 2) DEFAULT NULL,
  id_solicitud_producto int(11) NOT NULL,
  id_producto int(11) NOT NULL,
  ind_paq_detalle varchar(1) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 32,
AVG_ROW_LENGTH = 528,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_detalle_solicitud_bar_solicitud_producto1_idx` on table `bar_detalle_solicitud`
--
ALTER TABLE bar_detalle_solicitud
ADD INDEX fk_bar_detalle_solicitud_bar_solicitud_producto1_idx (id_solicitud_producto);

--
-- Create index `fk_bar_detalle_solicitud_alm_producto1_idx` on table `bar_detalle_solicitud`
--
ALTER TABLE bar_detalle_solicitud
ADD INDEX fk_bar_detalle_solicitud_alm_producto1_idx (id_producto);

--
-- Create foreign key
--
ALTER TABLE bar_detalle_solicitud
ADD CONSTRAINT fk_bar_detalle_solicitud_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_solicitud
ADD CONSTRAINT fk_bar_detalle_solicitud_bar_solicitud_producto1 FOREIGN KEY (id_solicitud_producto)
REFERENCES bar_solicitud_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_detalle_salida_inv`
--
CREATE TABLE bar_detalle_salida_inv (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad decimal(10, 2) DEFAULT NULL,
  ind_paq_detalle varchar(1) DEFAULT NULL,
  id_salida_inventario int(11) NOT NULL,
  id_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 384,
AVG_ROW_LENGTH = 130,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_salida_inv
ADD CONSTRAINT fk_bar_detalle_salida_inv_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id);

--
-- Create foreign key
--
ALTER TABLE bar_detalle_salida_inv
ADD CONSTRAINT fk_bar_detalle_salida_inv_bar_salida_inventario1 FOREIGN KEY (id_salida_inventario)
REFERENCES bar_salida_inventario (id);

--
-- Create table `bar_detalle_sal_combo_coctel`
--
CREATE TABLE bar_detalle_sal_combo_coctel (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad decimal(10, 2) DEFAULT NULL,
  ind_paq_detalle varchar(1) NOT NULL,
  id_producto int(11) NOT NULL,
  id_salida_combo_coctel int(11) NOT NULL,
  id_comanda int(11) DEFAULT NULL,
  si_es_opcional int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 48424,
AVG_ROW_LENGTH = 76,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_detalle_sal_combo_coctel_alm_producto1_idx` on table `bar_detalle_sal_combo_coctel`
--
ALTER TABLE bar_detalle_sal_combo_coctel
ADD INDEX fk_bar_detalle_sal_combo_coctel_alm_producto1_idx (id_producto);

--
-- Create index `fk_bar_detalle_sal_combo_coctel_bar_salida_combo_coctel1_idx` on table `bar_detalle_sal_combo_coctel`
--
ALTER TABLE bar_detalle_sal_combo_coctel
ADD INDEX fk_bar_detalle_sal_combo_coctel_bar_salida_combo_coctel1_idx (id_salida_combo_coctel);

--
-- Create foreign key
--
ALTER TABLE bar_detalle_sal_combo_coctel
ADD CONSTRAINT bar_detalle_sal_combo_coctel_ibfk_1 FOREIGN KEY (id_comanda)
REFERENCES bar_comanda (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_sal_combo_coctel
ADD CONSTRAINT fk_bar_detalle_sal_combo_coctel_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_sal_combo_coctel
ADD CONSTRAINT fk_bar_detalle_sal_combo_coctel_bar_salida_combo_coctel1 FOREIGN KEY (id_salida_combo_coctel)
REFERENCES bar_salida_combo_coctel (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_detalle_orden_pedido`
--
CREATE TABLE bar_detalle_orden_pedido (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad decimal(10, 2) NOT NULL,
  id_producto int(11) NOT NULL,
  id_orden_pedido int(11) NOT NULL,
  stock_barra decimal(10, 2) DEFAULT NULL,
  ind_estado_orden int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 425,
AVG_ROW_LENGTH = 138,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_orden_pedido
ADD CONSTRAINT bar_detalle_orden_pedido_alm_producto FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_orden_pedido
ADD CONSTRAINT bar_detalle_orden_pedido_bar_orden_pedido FOREIGN KEY (id_orden_pedido)
REFERENCES bar_orden_pedido (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_detalle_ingreso`
--
CREATE TABLE bar_detalle_ingreso (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad decimal(10, 2) DEFAULT NULL,
  ind_paq_detalle varchar(1) DEFAULT NULL,
  id_producto int(11) NOT NULL,
  id_ingreso_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_detalle_ingreso_alm_producto1_idx` on table `bar_detalle_ingreso`
--
ALTER TABLE bar_detalle_ingreso
ADD INDEX fk_bar_detalle_ingreso_alm_producto1_idx (id_producto);

--
-- Create index `fk_bar_detalle_ingreso_bar_ingreso_producto1_idx` on table `bar_detalle_ingreso`
--
ALTER TABLE bar_detalle_ingreso
ADD INDEX fk_bar_detalle_ingreso_bar_ingreso_producto1_idx (id_ingreso_producto);

--
-- Create foreign key
--
ALTER TABLE bar_detalle_ingreso
ADD CONSTRAINT fk_bar_detalle_ingreso_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_ingreso
ADD CONSTRAINT fk_bar_detalle_ingreso_bar_ingreso_producto1 FOREIGN KEY (id_ingreso_producto)
REFERENCES bar_ingreso_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_detalle_fisico`
--
CREATE TABLE bar_detalle_fisico (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad_unidad decimal(10, 2) NOT NULL,
  cantidad_detalle decimal(10, 2) NOT NULL,
  id_producto int(11) NOT NULL,
  id_inventario_fisico int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 3352,
AVG_ROW_LENGTH = 73,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_fisico
ADD CONSTRAINT bar_detalle_fisico_alm_producto FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_fisico
ADD CONSTRAINT bar_detalle_fisico_bar_inventario_fisico FOREIGN KEY (id_inventario_fisico)
REFERENCES bar_inventario_fisico (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_detalle_combo_bar`
--
CREATE TABLE bar_detalle_combo_bar (
  id int(11) NOT NULL AUTO_INCREMENT,
  id_producto int(11) NOT NULL,
  id_combo_coctel int(11) NOT NULL,
  cantidad decimal(10, 2) NOT NULL,
  ind_paq_detalle varchar(1) NOT NULL,
  ind_tipo_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 666,
AVG_ROW_LENGTH = 123,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_detalle_combo_bar_alm_producto1_idx` on table `bar_detalle_combo_bar`
--
ALTER TABLE bar_detalle_combo_bar
ADD INDEX fk_bar_detalle_combo_bar_alm_producto1_idx (id_producto);

--
-- Create index `fk_bar_detalle_combo_bar_bar_combo_coctel1_idx` on table `bar_detalle_combo_bar`
--
ALTER TABLE bar_detalle_combo_bar
ADD INDEX fk_bar_detalle_combo_bar_bar_combo_coctel1_idx (id_combo_coctel);

--
-- Create foreign key
--
ALTER TABLE bar_detalle_combo_bar
ADD CONSTRAINT fk_bar_detalle_combo_bar_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_combo_bar
ADD CONSTRAINT fk_bar_detalle_combo_bar_bar_combo_coctel1 FOREIGN KEY (id_combo_coctel)
REFERENCES bar_combo_coctel (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `bar_detalle_comanda_salida`
--
CREATE TABLE bar_detalle_comanda_salida (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad decimal(10, 2) NOT NULL,
  id_comanda int(11) NOT NULL,
  id_producto int(11) DEFAULT NULL,
  id_salida_combo_coctel int(11) DEFAULT NULL,
  id_bar_combo_coctel int(11) DEFAULT NULL,
  precio_venta decimal(10, 2) NOT NULL,
  sub_total decimal(10, 2) NOT NULL,
  producto_coctel varchar(255) DEFAULT NULL,
  cor_subtotal_anterior decimal(10, 2) DEFAULT NULL,
  id_barra int(11) DEFAULT NULL,
  comision decimal(10, 2) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 40488,
AVG_ROW_LENGTH = 95,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_bar_salida_barra_bar_comanda1_idx` on table `bar_detalle_comanda_salida`
--
ALTER TABLE bar_detalle_comanda_salida
ADD INDEX fk_bar_salida_barra_bar_comanda1_idx (id_comanda);

--
-- Create index `fk_bar_salida_barra_alm_producto1_idx` on table `bar_detalle_comanda_salida`
--
ALTER TABLE bar_detalle_comanda_salida
ADD INDEX fk_bar_salida_barra_alm_producto1_idx (id_producto);

--
-- Create index `fk_bar_detalle_comanda_salida_bar_salida_combo_coctel1_idx` on table `bar_detalle_comanda_salida`
--
ALTER TABLE bar_detalle_comanda_salida
ADD INDEX fk_bar_detalle_comanda_salida_bar_salida_combo_coctel1_idx (id_salida_combo_coctel);

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

--
-- Create table `bar_detalle_ajuste`
--
CREATE TABLE bar_detalle_ajuste (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad decimal(10, 2) NOT NULL,
  precio_costo decimal(10, 2) NOT NULL,
  precio_costo_real decimal(10, 5) DEFAULT NULL,
  observaciones varchar(255) DEFAULT NULL,
  ind_paq_detalle varchar(1) DEFAULT NULL COMMENT '1: display 0:detalle',
  id_ajuste int(11) NOT NULL,
  id_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 558,
AVG_ROW_LENGTH = 118,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_ajuste
ADD CONSTRAINT fk_bar_detalle_ajuste_alm_producto_idx FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE bar_detalle_ajuste
ADD CONSTRAINT fk_bar_detalle_ajuste_bar_ajuste_idx FOREIGN KEY (id_ajuste)
REFERENCES bar_ajuste (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_valoracion_gral`
--
CREATE TABLE alm_valoracion_gral (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha date DEFAULT NULL,
  ind_tipo_operacion int(11) DEFAULT NULL,
  correlativo int(11) DEFAULT NULL,
  precio_unitario decimal(10, 5) DEFAULT NULL,
  fisico_ingreso decimal(10, 2) DEFAULT NULL,
  fisico_salida decimal(10, 2) DEFAULT NULL,
  fisico_saldo decimal(20, 2) DEFAULT NULL,
  valor_ingreso decimal(10, 2) DEFAULT NULL,
  valor_salida decimal(10, 2) DEFAULT NULL,
  valor_saldo decimal(10, 2) DEFAULT NULL,
  id_producto int(11) NOT NULL,
  numero_factura varchar(255) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 3254,
AVG_ROW_LENGTH = 141,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE alm_valoracion_gral
ADD CONSTRAINT fk_alm_valoracion_gral_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_valoracion`
--
CREATE TABLE alm_valoracion (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha date DEFAULT NULL,
  ind_tipo_operacion int(11) DEFAULT NULL,
  correlativo int(11) DEFAULT NULL,
  precio_unitario decimal(10, 5) DEFAULT NULL,
  fisico_ingreso decimal(10, 2) DEFAULT NULL,
  fisico_salida decimal(10, 2) DEFAULT NULL,
  fisico_saldo decimal(10, 2) DEFAULT NULL,
  valor_ingreso decimal(10, 2) DEFAULT NULL,
  valor_salida decimal(10, 2) DEFAULT NULL,
  valor_saldo decimal(10, 2) DEFAULT NULL,
  id_producto int(11) NOT NULL,
  id_almacen int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 1622,
AVG_ROW_LENGTH = 198,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE alm_valoracion
ADD CONSTRAINT fk_alm_valoracion_alm_almacen1 FOREIGN KEY (id_almacen)
REFERENCES alm_almacen (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_valoracion
ADD CONSTRAINT fk_alm_valoracion_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_paloteo_cierre`
--
CREATE TABLE alm_paloteo_cierre (
  id int(11) NOT NULL AUTO_INCREMENT,
  inicial_paq decimal(10, 2) DEFAULT NULL,
  inicial_detalle decimal(10, 2) DEFAULT NULL,
  ingreso_paq decimal(10, 2) DEFAULT NULL,
  ingreso_detalle decimal(10, 2) DEFAULT NULL,
  salida_paq decimal(10, 2) DEFAULT NULL,
  salida_detalle decimal(10, 2) DEFAULT NULL,
  actual_paq decimal(10, 2) DEFAULT NULL,
  actual_detalle decimal(10, 2) DEFAULT NULL,
  id_almacen int(11) NOT NULL,
  id_operacion int(11) NOT NULL,
  id_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg datetime DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 84687,
AVG_ROW_LENGTH = 112,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE alm_paloteo_cierre
ADD CONSTRAINT fk_alm_paloteo_cierre_alm_almacen FOREIGN KEY (id_almacen)
REFERENCES alm_almacen (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_paloteo_cierre
ADD CONSTRAINT fk_alm_paloteo_cierre_alm_producto FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_paloteo_cierre
ADD CONSTRAINT fk_alm_paloteo_cierre_ope_operacion FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_inventario_operacion`
--
CREATE TABLE alm_inventario_operacion (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad_paq decimal(10, 2) DEFAULT NULL,
  cantidad_detalle decimal(10, 2) DEFAULT NULL,
  id_almacen int(11) NOT NULL,
  id_operacion int(11) NOT NULL,
  id_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 81946,
AVG_ROW_LENGTH = 70,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE alm_inventario_operacion
ADD CONSTRAINT fk_alm_inventario_operacion_alm_almacen FOREIGN KEY (id_almacen)
REFERENCES alm_almacen (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_inventario_operacion
ADD CONSTRAINT fk_alm_inventario_operacion_alm_producto FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_inventario_operacion
ADD CONSTRAINT fk_alm_inventario_operacion_ope_operacion FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_inventario_cierre`
--
CREATE TABLE alm_inventario_cierre (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad_paq decimal(10, 2) DEFAULT NULL,
  cantidad_detalle decimal(10, 2) DEFAULT NULL,
  id_almacen int(11) NOT NULL,
  id_operacion int(11) NOT NULL,
  id_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg datetime DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 196015,
AVG_ROW_LENGTH = 70,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE alm_inventario_cierre
ADD CONSTRAINT fk_alm_inventario_cierre_alm_almacen FOREIGN KEY (id_almacen)
REFERENCES alm_almacen (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_inventario_cierre
ADD CONSTRAINT fk_alm_inventario_cierre_alm_producto FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_inventario_cierre
ADD CONSTRAINT fk_alm_inventario_cierre_ope_operacion FOREIGN KEY (id_operacion)
REFERENCES ope_operacion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_inventario`
--
CREATE TABLE alm_inventario (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad_paq decimal(10, 2) DEFAULT NULL,
  cantidad_detalle decimal(10, 2) DEFAULT NULL,
  id_producto int(11) NOT NULL,
  id_almacen int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 225,
AVG_ROW_LENGTH = 73,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_alm_inventario_alm_producto1_idx` on table `alm_inventario`
--
ALTER TABLE alm_inventario
ADD INDEX fk_alm_inventario_alm_producto1_idx (id_producto);

--
-- Create index `fk_alm_inventario_alm_almacen1_idx` on table `alm_inventario`
--
ALTER TABLE alm_inventario
ADD INDEX fk_alm_inventario_alm_almacen1_idx (id_almacen);

--
-- Create foreign key
--
ALTER TABLE alm_inventario
ADD CONSTRAINT fk_alm_inventario_alm_almacen1 FOREIGN KEY (id_almacen)
REFERENCES alm_almacen (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_inventario
ADD CONSTRAINT fk_alm_inventario_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_detalle_salida_inv`
--
CREATE TABLE alm_detalle_salida_inv (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad decimal(10, 2) DEFAULT NULL,
  ind_paq_detalle varchar(1) DEFAULT NULL,
  id_salida_inventario int(11) NOT NULL,
  id_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 3788,
AVG_ROW_LENGTH = 66,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_alm_detalle_salida_inv_alm_salida_inventario1_idx` on table `alm_detalle_salida_inv`
--
ALTER TABLE alm_detalle_salida_inv
ADD INDEX fk_alm_detalle_salida_inv_alm_salida_inventario1_idx (id_salida_inventario);

--
-- Create index `fk_alm_detalle_salida_inv_alm_producto1_idx` on table `alm_detalle_salida_inv`
--
ALTER TABLE alm_detalle_salida_inv
ADD INDEX fk_alm_detalle_salida_inv_alm_producto1_idx (id_producto);

--
-- Create foreign key
--
ALTER TABLE alm_detalle_salida_inv
ADD CONSTRAINT fk_alm_detalle_salida_inv_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_detalle_salida_inv
ADD CONSTRAINT fk_alm_detalle_salida_inv_alm_salida_inventario1 FOREIGN KEY (id_salida_inventario)
REFERENCES alm_salida_inventario (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_detalle_ingreso`
--
CREATE TABLE alm_detalle_ingreso (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad decimal(10, 2) NOT NULL,
  precio_costo decimal(10, 2) NOT NULL,
  precio_costo_real decimal(10, 5) DEFAULT NULL,
  observaciones varchar(255) DEFAULT NULL,
  ind_paq_detalle varchar(1) DEFAULT NULL COMMENT '1: display 0:detalle',
  id_ingreso int(11) NOT NULL,
  id_producto int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 2198,
AVG_ROW_LENGTH = 83,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_alm_detalle_ingreso_alm_ingreso1_idx` on table `alm_detalle_ingreso`
--
ALTER TABLE alm_detalle_ingreso
ADD INDEX fk_alm_detalle_ingreso_alm_ingreso1_idx (id_ingreso);

--
-- Create index `fk_alm_detalle_ingreso_alm_producto1_idx` on table `alm_detalle_ingreso`
--
ALTER TABLE alm_detalle_ingreso
ADD INDEX fk_alm_detalle_ingreso_alm_producto1_idx (id_producto);

--
-- Create foreign key
--
ALTER TABLE alm_detalle_ingreso
ADD CONSTRAINT fk_alm_detalle_ingreso_alm_ingreso1 FOREIGN KEY (id_ingreso)
REFERENCES alm_ingreso (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_detalle_ingreso
ADD CONSTRAINT fk_alm_detalle_ingreso_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_detalle_devolucion`
--
CREATE TABLE alm_detalle_devolucion (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad_paq decimal(10, 2) DEFAULT NULL,
  cantidad_detallle decimal(10, 2) DEFAULT NULL,
  id_producto int(11) NOT NULL,
  id_devolucion int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_alm_detalle_devolucion_alm_producto1_idx` on table `alm_detalle_devolucion`
--
ALTER TABLE alm_detalle_devolucion
ADD INDEX fk_alm_detalle_devolucion_alm_producto1_idx (id_producto);

--
-- Create index `fk_alm_detalle_devolucion_alm_devolucion1_idx` on table `alm_detalle_devolucion`
--
ALTER TABLE alm_detalle_devolucion
ADD INDEX fk_alm_detalle_devolucion_alm_devolucion1_idx (id_devolucion);

--
-- Create foreign key
--
ALTER TABLE alm_detalle_devolucion
ADD CONSTRAINT fk_alm_detalle_devolucion_alm_devolucion1 FOREIGN KEY (id_devolucion)
REFERENCES alm_devolucion (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_detalle_devolucion
ADD CONSTRAINT fk_alm_detalle_devolucion_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `seg_rol`
--
CREATE TABLE seg_rol (
  id int(11) NOT NULL AUTO_INCREMENT,
  nombre varchar(255) NOT NULL,
  codigo varchar(255) NOT NULL,
  pantallaprincipal varchar(255) DEFAULT NULL,
  observaciones varchar(255) DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 67,
AVG_ROW_LENGTH = 1638,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `seg_permiso`
--
CREATE TABLE seg_permiso (
  id int(11) NOT NULL AUTO_INCREMENT,
  id_usuario int(11) NOT NULL,
  id_rol int(11) NOT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 89,
AVG_ROW_LENGTH = 321,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `seg_permiso_seg_usuario_FK` on table `seg_permiso`
--
ALTER TABLE seg_permiso
ADD INDEX seg_permiso_seg_usuario_FK (id_usuario);

--
-- Create index `seg_permiso_seg_rol_FK` on table `seg_permiso`
--
ALTER TABLE seg_permiso
ADD INDEX seg_permiso_seg_rol_FK (id_rol);

--
-- Create foreign key
--
ALTER TABLE seg_permiso
ADD CONSTRAINT seg_permiso_ibfk_1 FOREIGN KEY (id_usuario)
REFERENCES seg_usuario (id);

--
-- Create foreign key
--
ALTER TABLE seg_permiso
ADD CONSTRAINT seg_permiso_ibfk_2 FOREIGN KEY (id_rol)
REFERENCES seg_rol (id);

--
-- Create table `seg_menu`
--
CREATE TABLE seg_menu (
  id int(11) NOT NULL AUTO_INCREMENT,
  id_menu int(11) DEFAULT NULL,
  identificador varchar(255) DEFAULT NULL,
  nivel int(11) DEFAULT NULL,
  nombre varchar(255) DEFAULT NULL,
  descripcion varchar(255) DEFAULT NULL,
  url varchar(255) DEFAULT NULL,
  tipo int(11) DEFAULT NULL COMMENT '1 si es PC y 2 si es para movil',
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 54,
AVG_ROW_LENGTH = 315,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE seg_menu
ADD CONSTRAINT seg_menu_seg_menu_FK FOREIGN KEY (id_menu)
REFERENCES seg_menu (id);

--
-- Create table `seg_menurol`
--
CREATE TABLE seg_menurol (
  id int(11) NOT NULL AUTO_INCREMENT,
  id_menu int(11) DEFAULT NULL,
  id_rol int(11) DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 109,
AVG_ROW_LENGTH = 157,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE seg_menurol
ADD CONSTRAINT seg_menurol_seg_menu_FK FOREIGN KEY (id_menu)
REFERENCES seg_menu (id);

--
-- Create foreign key
--
ALTER TABLE seg_menurol
ADD CONSTRAINT seg_menurol_seg_rol_FK FOREIGN KEY (id_rol)
REFERENCES seg_rol (id);

--
-- Create table `master_table`
--
CREATE TABLE master_table (
  id int(11) NOT NULL AUTO_INCREMENT,
  nombre varchar(255) DEFAULT NULL,
  descripcion varchar(255) DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 25,
AVG_ROW_LENGTH = 682,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `parameter_table`
--
CREATE TABLE parameter_table (
  id int(11) NOT NULL AUTO_INCREMENT,
  nombre varchar(255) DEFAULT NULL,
  descripcion varchar(255) DEFAULT NULL,
  texto1 varchar(255) DEFAULT NULL,
  texto2 varchar(255) DEFAULT NULL,
  fechaInicio date DEFAULT NULL,
  fechaFin date DEFAULT NULL,
  numero1 int(11) DEFAULT NULL,
  numero2 decimal(10, 2) DEFAULT NULL,
  id_master int(11) DEFAULT NULL,
  orden int(11) DEFAULT NULL,
  requerido varchar(1) DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 87,
AVG_ROW_LENGTH = 197,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create foreign key
--
ALTER TABLE parameter_table
ADD CONSTRAINT parameter_table_master_table_FK FOREIGN KEY (id_master)
REFERENCES master_table (id);

--
-- Create table `ope_cuentas_cobrar`
--
CREATE TABLE ope_cuentas_cobrar (
  id int(11) NOT NULL AUTO_INCREMENT,
  nombre varchar(255) NOT NULL,
  fecha date NOT NULL,
  motivo varchar(255) NOT NULL,
  monto decimal(10, 2) NOT NULL,
  a_cuenta decimal(10, 2) DEFAULT NULL,
  saldo decimal(10, 2) DEFAULT NULL,
  estado_cobro varchar(1) DEFAULT NULL COMMENT '1: cobrado0: pendiente',
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 4,
AVG_ROW_LENGTH = 8192,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `ope_pago`
--
CREATE TABLE ope_pago (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha date DEFAULT NULL,
  monto decimal(10, 2) DEFAULT NULL,
  descripcion varchar(255) DEFAULT NULL,
  id_cuentas_cobrar int(11) NOT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 2,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_ope_pago_op_cuentas_cobrar1_idx` on table `ope_pago`
--
ALTER TABLE ope_pago
ADD INDEX fk_ope_pago_op_cuentas_cobrar1_idx (id_cuentas_cobrar);

--
-- Create foreign key
--
ALTER TABLE ope_pago
ADD CONSTRAINT fk_ope_pago_op_cuentas_cobrar1 FOREIGN KEY (id_cuentas_cobrar)
REFERENCES ope_cuentas_cobrar (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `alm_orden_compra`
--
CREATE TABLE alm_orden_compra (
  id int(11) NOT NULL AUTO_INCREMENT,
  fecha_solicitud date NOT NULL,
  responsable varchar(255) DEFAULT NULL,
  lugar_entrega varchar(255) DEFAULT NULL,
  fecha_entrega date DEFAULT NULL,
  ind_estado_orden int(11) NOT NULL,
  observaciones varchar(255) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 13,
AVG_ROW_LENGTH = 1365,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `alm_detalle_orden_compra`
--
CREATE TABLE alm_detalle_orden_compra (
  id int(11) NOT NULL AUTO_INCREMENT,
  cantidad decimal(10, 2) NOT NULL,
  id_producto int(11) NOT NULL,
  id_orden_compra int(11) NOT NULL,
  stock_almacen decimal(10, 2) DEFAULT NULL,
  stock_barra decimal(10, 2) DEFAULT NULL,
  costo_unitario decimal(10, 2) DEFAULT NULL,
  id_proveedor int(11) DEFAULT NULL,
  ind_estado_orden int(11) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 2331,
AVG_ROW_LENGTH = 92,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create index `fk_alm_detalle_orden_compra_alm_producto1_idx` on table `alm_detalle_orden_compra`
--
ALTER TABLE alm_detalle_orden_compra
ADD INDEX fk_alm_detalle_orden_compra_alm_producto1_idx (id_producto);

--
-- Create index `fk_alm_detalle_orden_compra_alm_orden_compra1_idx` on table `alm_detalle_orden_compra`
--
ALTER TABLE alm_detalle_orden_compra
ADD INDEX fk_alm_detalle_orden_compra_alm_orden_compra1_idx (id_orden_compra);

--
-- Create foreign key
--
ALTER TABLE alm_detalle_orden_compra
ADD CONSTRAINT alm_detalle_orden_compra_ibfk_1 FOREIGN KEY (id_proveedor)
REFERENCES alm_proveedor (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_detalle_orden_compra
ADD CONSTRAINT fk_alm_detalle_orden_compra_alm_orden_compra1 FOREIGN KEY (id_orden_compra)
REFERENCES alm_orden_compra (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create foreign key
--
ALTER TABLE alm_detalle_orden_compra
ADD CONSTRAINT fk_alm_detalle_orden_compra_alm_producto1 FOREIGN KEY (id_producto)
REFERENCES alm_producto (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Create table `seg_acceso`
--
CREATE TABLE seg_acceso (
  id int(11) NOT NULL AUTO_INCREMENT,
  usuario varchar(255) NOT NULL,
  fecha datetime NOT NULL,
  ip varchar(255) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 17303,
AVG_ROW_LENGTH = 95,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `report_ventas`
--
CREATE TABLE report_ventas (
  id int(11) NOT NULL AUTO_INCREMENT,
  barra varchar(255) NOT NULL,
  nro_comanda int(11) NOT NULL,
  personal varchar(255) NOT NULL,
  grupo varchar(255) NOT NULL,
  id_grupo int(11) DEFAULT NULL,
  sub_total decimal(10, 2) NOT NULL,
  comision decimal(10, 2) NOT NULL,
  idOperacion int(11) DEFAULT NULL,
  idUsuario int(11) DEFAULT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 36382,
AVG_ROW_LENGTH = 103,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `report_paloteo`
--
CREATE TABLE report_paloteo (
  id int(11) NOT NULL AUTO_INCREMENT,
  prodcuto varchar(255) NOT NULL,
  categoria varchar(255) NOT NULL,
  codigo varchar(255) NOT NULL,
  contenido varchar(255) NOT NULL,
  detalle varchar(255) NOT NULL,
  inicial_display decimal(10, 2) NOT NULL,
  inicial_detalle decimal(10, 2) NOT NULL,
  ventas_display decimal(10, 2) NOT NULL,
  ventas_detalle decimal(10, 2) NOT NULL,
  actual_display decimal(10, 2) NOT NULL,
  actual_detalle decimal(10, 2) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;

--
-- Create table `gen_key`
--
CREATE TABLE gen_key (
  id int(11) NOT NULL AUTO_INCREMENT,
  tipo_licencia varchar(255) NOT NULL,
  desde varchar(255) DEFAULT NULL,
  hasta varchar(255) DEFAULT NULL,
  serial varchar(255) NOT NULL,
  observaciones varchar(255) DEFAULT NULL,
  usuario_reg varchar(255) NOT NULL,
  fecha_reg date DEFAULT NULL,
  fecha_mod date DEFAULT NULL,
  estado varchar(3) NOT NULL,
  PRIMARY KEY (id)
)
ENGINE = INNODB,
AUTO_INCREMENT = 2,
CHARACTER SET latin1,
COLLATE latin1_swedish_ci;