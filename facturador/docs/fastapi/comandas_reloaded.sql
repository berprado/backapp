CREATE 
	DEFINER = 'root'@'localhost'
VIEW adminerp_copy.comandas_v6
AS
	SELECT
	        `dcs`.`id`                               AS `id`,
	        `dcs`.`cantidad`                         AS `cantidad`,
	        `dcs`.`id_comanda`                       AS `id_comanda`,
	        `p`.`codigo`                             AS `id_producto`,
	        `dcs`.`id_salida_combo_coctel`           AS `id_salida_combo_coctel`,
	        `cc`.`codigo`                            AS `id_bar_combo_coctel`,
	        `dcs`.`precio_venta`                     AS `precio_venta`,
	        `dcs`.`sub_total`                        AS `sub_total`,
	        `dcs`.`producto_coctel`                  AS `producto_coctel`,
	        `dcs`.`cor_subtotal_anterior`            AS `cor_subtotal_anterior`,
	        `c`.`id_barra`                           AS `id_barra`,
	        `c`.`usuario_reg`                        AS `usuario_reg`,
	        `c`.`fecha`                              AS `fecha_emision`,
	        `dcs`.`fecha_mod`                        AS `fecha_mod`,
	        `c`.`estado`                             AS `estado`,
	        `c`.`id_operacion`                       AS `id_operacion`,
	        `c`.`id_mesa`                            AS `id_mesa`,
	        `c`.`razon_social`                       AS `razon_social`,
	        `c`.`nit`                                AS `nit`,
	        `c`.`id_factura`                         AS `id_factura`,
	        `c`.`nro_factura`                        AS `nro_factura`,
	        COALESCE(
	          `p`.`nombre`,
	          `cc`.`nombre`)                         AS `nombre`,
	        COALESCE(
	          `p`.`descripcion`,
	          `cc`.`descripcion`)                    AS `descripcion`,
	        COALESCE(
	          `p`.`codigo`,
	          `cc`.`codigo`)                         AS `id_producto_combo`,
	        `ts`.`nombre`                            AS `tipo_salida`,
	        `ec`.`nombre`                            AS `estado_comanda`,
	        `ei`.`nombre`                            AS `estado_impresion`,
	        COALESCE(
	          `catp`.`nombre`,
	          `catc`.`nombre`)                       AS `categoria`
	FROM
	        ((((((((`bar_detalle_comanda_salida` `dcs`
	    JOIN
	      `bar_comanda` `c`
	        ON ((`dcs`.`id_comanda` = `c`.`id`)))
	    LEFT JOIN
	      `alm_producto` `p`
	        ON ((`dcs`.`id_producto` = `p`.`id`)))
	    LEFT JOIN
	      `bar_combo_coctel` `cc`
	        ON ((`dcs`.`id_bar_combo_coctel` = `cc`.`id`)))
	    LEFT JOIN
	      `alm_categoria` `catp`
	        ON ((`p`.`id_categoria` = `catp`.`id`)))
	    LEFT JOIN
	      `alm_categoria` `catc`
	        ON ((`cc`.`id_categoria` = `catc`.`id`)))
	    LEFT JOIN
	      `parameter_table` `ts`
	        ON ((`c`.`tipo_salida` = `ts`.`id`)))
	    LEFT JOIN
	      `parameter_table` `ec`
	        ON ((`c`.`estado_comanda` = `ec`.`id`)))
	    LEFT JOIN
	      `parameter_table` `ei`
	        ON ((`c`.`estado_impresion` = `ei`.`id`)))
	WHERE
	        (`c`.`id_operacion` = (SELECT
	                    MAX(`bar_comanda`.`id_operacion`)
	            FROM
	                    `bar_comanda`)
	        );