-- ============================================
-- NOMBRE: Órdenes de Compra pendientes de procesar
-- CATEGORÍA: obligatoria
-- FRECUENCIA: Diaria
-- AUTOR: ADMJAJA
-- FECHA: 2025-11-21
-- VERSION: 1.0.0
-- ============================================

-- DESCRIPCIÓN:
-- Lista todas las OCs que tienen cantidades pendientes de procesar.
-- Identifica OCs abiertas, en proceso o parcialmente completadas
-- que requieren atención del equipo de Planning.

-- TABLAS INVOLUCRADAS:
-- - ORDERS (Cabecera de órdenes)
-- - ORDERDETAIL (Detalle de órdenes)
-- - SKU (Información de productos)

-- PARAMETROS:
-- {{storerkey}} - Código de almacén (default: C22)
-- {{dias_antiguedad}} - Días máximos de antigüedad (default: 30)

SELECT
    o.ORDERKEY AS oc_numero,
    o.EXTERNORDERKEY AS oc_externa,
    o.STORERKEY AS almacen,
    o.ORDERDATE AS fecha_orden,
    o.ADDDATE AS fecha_creacion,
    DATEDIFF(DAY, o.ADDDATE, CURRENT_DATE) AS dias_pendiente,
    o.STATUS AS status,
    CASE o.STATUS
        WHEN '0' THEN 'Abierta'
        WHEN '1' THEN 'En Proceso'
        WHEN '2' THEN 'Parcial'
        ELSE 'Otro'
    END AS status_descripcion,
    od.SKU AS sku,
    s.DESCR AS descripcion_sku,
    od.ORIGINALQTY AS qty_original,
    od.OPENQTY AS qty_pendiente,
    od.SHIPPEDQTY AS qty_enviada,
    CASE
        WHEN od.ORIGINALQTY > 0 THEN
            ROUND((od.OPENQTY / od.ORIGINALQTY) * 100, 2)
        ELSE 0
    END AS porcentaje_pendiente,
    od.PACKKEY AS unidad_empaque,
    od.UOM AS unidad_medida
FROM
    WMWHSE1.ORDERS o
    INNER JOIN WMWHSE1.ORDERDETAIL od ON o.ORDERKEY = od.ORDERKEY
    LEFT JOIN WMWHSE1.SKU s ON od.SKU = s.SKU AND o.STORERKEY = s.STORERKEY
WHERE
    o.STORERKEY = '{{storerkey}}'
    AND o.STATUS IN ('0', '1', '2')  -- Abierta, En Proceso, Parcial
    AND od.OPENQTY > 0  -- Solo con cantidad pendiente
    AND DATEDIFF(DAY, o.ADDDATE, CURRENT_DATE) <= {{dias_antiguedad}}
ORDER BY
    dias_pendiente DESC,
    o.ORDERKEY,
    od.SKU;
