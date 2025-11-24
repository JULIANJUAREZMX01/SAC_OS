-- ============================================
-- NOMBRE: Distribuciones del día actual
-- CATEGORÍA: obligatoria
-- FRECUENCIA: Diaria
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Obtiene todas las distribuciones programadas o creadas
-- para el día actual. Agrupa por OC y tienda destino
-- para validación contra órdenes de compra.

-- TABLAS INVOLUCRADAS:
-- - ORDERS (Cabecera - tipo distribución)
-- - ORDERDETAIL (Detalle de distribución)
-- - SKU (Información de productos)
-- - STORER (Información de tiendas)

-- PARAMETROS:
-- {{fecha_inicio}} - Fecha inicio (YYYY-MM-DD)
-- {{fecha_fin}} - Fecha fin (YYYY-MM-DD)
-- {{storerkey}} - Código de almacén origen (default: C22)

SELECT
    o.ORDERKEY AS distro_numero,
    o.EXTERNORDERKEY AS distro_externa,
    o.EXTERNALORDERKEY2 AS oc_referencia,
    o.STORERKEY AS almacen_origen,
    o.CONSIGNEEKEY AS tienda_destino,
    st.COMPANY AS nombre_tienda,
    o.ORDERDATE AS fecha_distro,
    o.ADDDATE AS fecha_creacion,
    o.DELIVERYDATE AS fecha_entrega,
    o.STATUS AS status,
    CASE o.STATUS
        WHEN '0' THEN 'Abierta'
        WHEN '1' THEN 'En Proceso'
        WHEN '2' THEN 'Parcial'
        WHEN '5' THEN 'Cerrada'
        WHEN '9' THEN 'Completada'
        WHEN '95' THEN 'Cancelada'
        ELSE 'Desconocido'
    END AS status_descripcion,
    od.SKU AS sku,
    sk.DESCR AS descripcion_sku,
    od.ORIGINALQTY AS qty_solicitada,
    od.OPENQTY AS qty_pendiente,
    od.SHIPPEDQTY AS qty_enviada,
    od.PACKKEY AS tipo_empaque,
    sk.INNERPACK AS inner_pack,
    CASE
        WHEN sk.INNERPACK > 0 THEN
            ROUND(od.ORIGINALQTY / sk.INNERPACK, 2)
        ELSE od.ORIGINALQTY
    END AS cajas_solicitadas,
    od.UOM AS unidad_medida
FROM
    WMWHSE1.ORDERS o
    INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
    LEFT JOIN WMWHSE1.SKU sk ON od.SKU = sk.SKU AND o.STORERKEY = sk.STORERKEY
    LEFT JOIN WMWHSE1.STORER st ON o.CONSIGNEEKEY = st.STORERKEY
WHERE
    o.STORERKEY = '{{storerkey}}'
    AND o.ORDERTYPE IN ('DISTRO', 'SO', 'XD')  -- Tipos de distribución
    AND o.STATUS NOT IN ('95')  -- Excluir canceladas
    AND (
        DATE(o.ADDDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}'
        OR DATE(o.ORDERDATE) BETWEEN '{{fecha_inicio}}' AND '{{fecha_fin}}'
    )
ORDER BY
    o.CONSIGNEEKEY,
    o.ORDERKEY,
    od.SKU;
