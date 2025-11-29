CREATE 
	DEFINER = 'root'@'localhost'
VIEW adminerp_copy.comandas
AS
	SELECT
	        `dcs`.`id`                     AS `id`,
	        `dcs`.`cantidad`               AS `cantidad`,
	        `dcs`.`id_comanda`             AS `id_comanda`,
	        `p`.`codigo`                   AS `id_producto`,
	        `dcs`.`id_salida_combo_coctel` AS `id_salida_combo_coctel`,
	        `cc`.`codigo`                  AS `id_bar_combo_coctel`,
	        `dcs`.`precio_venta`           AS `precio_venta`,
	        `dcs`.`sub_total`              AS `sub_total`,
	        `dcs`.`producto_coctel`        AS `producto_coctel`,
	        `dcs`.`cor_subtotal_anterior`  AS `cor_subtotal_anterior`,
	        `dcs`.`id_barra`               AS `id_barra`,
	        `dcs`.`comision`               AS `comision`,
	        `dcs`.`usuario_reg`            AS `usuario_reg`,
	        `dcs`.`fecha_reg`              AS `fecha_reg`,
	        `dcs`.`fecha_mod`              AS `fecha_mod`,
	        `dcs`.`estado`                 AS `estado`,
	        `c`.`id_operacion`             AS `id_operacion`,
	        COALESCE(
	          `p`.`nombre`,
	          `cc`.`nombre`)               AS `nombre`,
	        COALESCE(
	          `p`.`codigo`,
	          `cc`.`codigo`)               AS `id_producto_combo`,
	        `c`.`tipo_salida`              AS `tipo_salida`,
	        `c`.`estado_comanda`           AS `estado_comanda`,
	        `c`.`estado_impresion`         AS `estado_impresion`
	FROM
	        (((`bar_detalle_comanda_salida` `dcs`
	    JOIN
	      `bar_comanda` `c`
	        ON ((`dcs`.`id_comanda` = `c`.`id`)))
	    LEFT JOIN
	      `alm_producto` `p`
	        ON ((`dcs`.`id_producto` = `p`.`id`)))
	    LEFT JOIN
	      `bar_combo_coctel` `cc`
	        ON ((`dcs`.`id_bar_combo_coctel` = `cc`.`id`)))
	WHERE
	        (`c`.`id_operacion` = (SELECT
	                    MAX(`bar_comanda`.`id_operacion`) AS `expr1`
	            FROM
	                    `bar_comanda`)
	        );